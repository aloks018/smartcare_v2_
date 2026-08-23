// ============================================================
// SMARTCAREAI - FRONTEND APPLICATION
// Matches:
//   frontend/index.html
//   backend/app/main.py
//   backend/app/schemas.py
// ============================================================

const API = "/api";


// ============================================================
// DOM ELEMENTS
// ============================================================

const SpeechRecognition =
  window.SpeechRecognition ||
  window.webkitSpeechRecognition;

const speakButton =
  document.querySelector("#speakButton");

const speakButtonText =
  document.querySelector("#speakButtonText");

const hearButton =
  document.querySelector("#hearButton");

const analyzeButton =
  document.querySelector("#analyzeButton");

const transcriptInput =
  document.querySelector("#manualTranscript");

const locationInput =
  document.querySelector("#locationInput");

const speechModel =
  document.querySelector("#speechModel");

const languageModel =
  document.querySelector("#languageModel");

const statusText =
  document.querySelector("#statusText");

const statusDot =
  document.querySelector("#statusDot");

const analysisStatus =
  document.querySelector("#analysisStatus");

const languageValue =
  document.querySelector("#languageValue");

const intentValue =
  document.querySelector("#intentValue");

const symptomsValue =
  document.querySelector("#symptomsValue");

const specialtyValue =
  document.querySelector("#specialtyValue");

const modelValue =
  document.querySelector("#modelValue");

const urgencyBlock =
  document.querySelector("#urgencyBlock");

const urgencyLabel =
  document.querySelector("#urgencyLabel");

const urgencyMessage =
  document.querySelector("#urgencyMessage");

const disclaimerText =
  document.querySelector("#disclaimerText");

const reasonList =
  document.querySelector("#reasonList");

const providerList =
  document.querySelector("#providerList");

const sourceList =
  document.querySelector("#sourceList");

const careSearch =
  document.querySelector("#careSearch");

const searchInput =
  document.querySelector("#searchInput");

const ownershipFilter =
  document.querySelector("#ownershipFilter");

const specialtyFilter =
  document.querySelector("#specialtyFilter");

const budgetInput =
  document.querySelector("#budgetInput");

const distanceInput =
  document.querySelector("#distanceInput");

const searchStatus =
  document.querySelector("#searchStatus");


// ============================================================
// APPLICATION STATE
// ============================================================

let recognition = null;

let isListening = false;

let latestSpokenResponse = "";

let latestAnalysis = null;


// ============================================================
// SAFE DOM HELPERS
// ============================================================

function setText(element, value) {

  if (!element) {
    return;
  }

  element.textContent =
    value ?? "—";
}


function escapeHTML(value) {

  const div =
    document.createElement("div");

  div.textContent =
    String(value ?? "");

  return div.innerHTML;
}


// ============================================================
// STATUS
// ============================================================

function setStatus(
  text,
  listening = false,
  state = "normal"
) {

  setText(
    statusText,
    text
  );

  if (statusDot) {

    statusDot.classList.remove(
      "listening",
      "success",
      "error"
    );

    if (listening) {

      statusDot.classList.add(
        "listening"
      );

    }

    if (state === "success") {

      statusDot.classList.add(
        "success"
      );

    }

    if (state === "error") {

      statusDot.classList.add(
        "error"
      );

    }
  }
}


// ============================================================
// BACKEND HEALTH CHECK
// ============================================================

async function checkBackend() {

  try {

    const response =
      await fetch(
        `${API}/health`
      );

    if (!response.ok) {

      throw new Error(
        `Backend returned ${response.status}`
      );

    }

    const data =
      await response.json();

    setStatus(
      `SmartCareAI ready • ${data.providers_loaded ?? 0} providers loaded`,
      false,
      "success"
    );

  } catch (error) {

    console.error(
      "Backend health check failed:",
      error
    );

    setStatus(
      "Backend not connected. Start FastAPI on port 8000.",
      false,
      "error"
    );
  }
}


// ============================================================
// PROVIDER CARD
// ============================================================

function providerCard(provider) {

  const name =
    provider.name ||
    "Healthcare Provider";

  const providerType =
    provider.provider_type ||
    "Healthcare";

  const ownership =
    provider.ownership ||
    "Unknown";

  const specialty =
    provider.specialty ||
    "General Medicine";

  const address =
    provider.address ||
    provider.city ||
    "Address not listed";

  const fee =
    provider.consultation_fee_inr !== null &&
    provider.consultation_fee_inr !== undefined

      ? `₹${Number(
          provider.consultation_fee_inr
        ).toLocaleString("en-IN")}`

      : "Fee not listed";

  const distance =
    provider.distance_km !== null &&
    provider.distance_km !== undefined

      ? `${Number(
          provider.distance_km
        ).toFixed(1)} km`

      : "Distance unavailable";

  const matchScore =
    provider.match_score !== null &&
    provider.match_score !== undefined

      ? `${Math.round(
          provider.match_score
        )}%`

      : "—";

  const languages =
    Array.isArray(
      provider.languages
    ) &&
    provider.languages.length

      ? provider.languages.join(
          " · "
        )

      : "Not listed";

  const reasons =
    Array.isArray(
      provider.match_reasons
    )
      ? provider.match_reasons
          .slice(0, 5)
          .map(
            reason => `
              <span class="match-reason">
                ✓ ${escapeHTML(reason)}
              </span>
            `
          )
          .join("")

      : "";

  const availability =
    provider.availability
      ? `
        <p class="availability">
          🕐 ${escapeHTML(
            provider.availability
          )}
        </p>
      `
      : "";

  const verified =
    provider.verified
      ? `
        <span class="verified-badge">
          ✓ Verified
        </span>
      `
      : "";

  const phoneButton =
    provider.phone

      ? `
        <a
          class="provider-button"
          href="tel:${escapeHTML(
            provider.phone
          )}"
        >
          📞 Call
        </a>
      `

      : "";

  const websiteButton =
    provider.website

      ? `
        <a
          class="provider-button"
          href="${escapeHTML(
            provider.website
          )}"
          target="_blank"
          rel="noopener noreferrer"
        >
          🌐 Website
        </a>
      `

      : "";


  return `

    <article class="provider-card">

      <div class="provider-top">

        <div>

          <span class="provider-type">
            ${escapeHTML(
              providerType
            )}
          </span>

          <h3>
            ${escapeHTML(name)}
          </h3>

        </div>

        <div class="provider-score">

          <strong>
            ${escapeHTML(matchScore)}
          </strong>

          <small>
            AI match
          </small>

        </div>

      </div>


      <div class="meta-row">

        <span class="pill ownership ${escapeHTML(
          ownership.toLowerCase()
        )}">
          ${escapeHTML(ownership)}
        </span>

        <span class="pill">
          ${escapeHTML(specialty)}
        </span>

        ${
          provider.emergency_available
            ? `
              <span class="pill emergency-pill">
                Emergency
              </span>
            `
            : ""
        }

        ${verified}

      </div>


      <div class="provider-info">

        <div class="provider-info-item">

          <strong>
            💰 Consultation
          </strong>

          <span>
            ${escapeHTML(fee)}
          </span>

        </div>


        <div class="provider-info-item">

          <strong>
            📍 Distance
          </strong>

          <span>
            ${escapeHTML(distance)}
          </span>

        </div>


        <div class="provider-info-item">

          <strong>
            🗣 Languages
          </strong>

          <span>
            ${escapeHTML(languages)}
          </span>

        </div>

      </div>


      <p class="address">

        📍 ${escapeHTML(address)}

      </p>


      ${availability}


      ${
        reasons
          ? `
            <div class="match-reasons">
              ${reasons}
            </div>
          `
          : ""
      }


      <div class="provider-actions">

        ${phoneButton}

        ${websiteButton}

      </div>

    </article>
  `;
}


// ============================================================
// RENDER PROVIDERS
// ============================================================

function renderProviders(
  providers
) {

  if (!providerList) {
    return;
  }


  providerList.innerHTML = "";


  if (
    !Array.isArray(providers) ||
    providers.length === 0
  ) {

    providerList.innerHTML = `

      <div class="empty-state">

        <h3>
          No matching healthcare provider found
        </h3>

        <p>
          Try another location, specialty,
          ownership or distance.
        </p>

      </div>

    `;

    return;
  }


  providerList.innerHTML =
    providers
      .map(providerCard)
      .join("");
}


// ============================================================
// RENDER AI ANALYSIS
// ============================================================

function renderAnalysis(data) {

  if (!data) {
    return;
  }


  latestAnalysis =
    data;


  // ----------------------------------------------------------
  // Language
  // ----------------------------------------------------------

  setText(
    languageValue,
    data.detected_language ||
      "Unknown"
  );


  // ----------------------------------------------------------
  // Intent
  // ----------------------------------------------------------

  setText(
    intentValue,
    formatText(
      data.intent ||
        "general health search"
    )
  );


  // ----------------------------------------------------------
  // Symptoms
  // ----------------------------------------------------------

  const symptoms =
    Array.isArray(
      data.symptoms
    )
      ? data.symptoms
      : [];


  if (symptoms.length) {

    setText(
      symptomsValue,

      symptoms
        .map(
          symptom =>
            symptom.name
        )
        .join(", ")
    );

  } else {

    setText(
      symptomsValue,
      "No clear symptom detected"
    );
  }


  // ----------------------------------------------------------
  // Specialty
  // ----------------------------------------------------------

  setText(
    specialtyValue,

    data.suggested_specialty ||
      "General Medicine"
  );


  // ----------------------------------------------------------
  // Model stack
  // ----------------------------------------------------------

  const models =
    data.model_stack || {};


  const speechModelName =
    models.speech ||
    speechModel?.value ||
    "Browser Speech";

  const languageModelName =
    models.language ||
    languageModel?.value ||
    "Rule Hybrid";

  setText(
    modelValue,

    `${speechModelName} + ${languageModelName}`
  );


  // ----------------------------------------------------------
  // TRIAGE
  // ----------------------------------------------------------

  const assessment =
    data.assessment || {};


  const urgency =
    assessment.urgency ||
    "routine";


  if (urgencyBlock) {

    urgencyBlock.dataset.level =
      urgency;

    urgencyBlock.classList.remove(
      "routine",
      "urgent",
      "emergency"
    );

    urgencyBlock.classList.add(
      urgency
    );
  }


  setText(
    urgencyLabel,

    formatText(
      urgency
    )
  );


  setText(

    urgencyMessage,

    [
      assessment.message,

      data.recommended_next_action

    ]
      .filter(Boolean)
      .join(" ")
  );


  // ----------------------------------------------------------
  // Disclaimer
  // ----------------------------------------------------------

  setText(

    disclaimerText,

    data.disclaimer ||

      "SmartCareAI is not a medical diagnosis system."
  );


  // ----------------------------------------------------------
  // Spoken response
  // ----------------------------------------------------------

  latestSpokenResponse =
    data.spoken_response ||
    data.recommended_next_action ||
    "";


  // ----------------------------------------------------------
  // Explainable AI
  // ----------------------------------------------------------

  renderReasons(

    data.why_this_recommendation ||
      []
  );


  // ----------------------------------------------------------
  // Providers
  // ----------------------------------------------------------

  renderProviders(

    data.providers ||
      []
  );


  // ----------------------------------------------------------
  // Status
  // ----------------------------------------------------------

  setStatus(
    "AI analysis ready",
    false,
    "success"
  );

  if (analysisStatus) {

    analysisStatus.textContent =
      "Analysis complete. Review the AI recommendation and provider matches below.";
  }
}


// ============================================================
// AI EXPLANATION
// ============================================================

function renderReasons(
  reasons
) {

  if (!reasonList) {
    return;
  }


  if (
    !Array.isArray(reasons) ||
    reasons.length === 0
  ) {

    reasonList.innerHTML = `

      <p>
        No explanation available yet.
      </p>

    `;

    return;
  }


  reasonList.innerHTML =
    reasons
      .map(
        reason => `

          <div class="ai-reason">

            <span>
              ✓
            </span>

            <p>
              ${escapeHTML(reason)}
            </p>

          </div>

        `
      )
      .join("");
}


// ============================================================
// ANALYZE TRANSCRIPT
// ============================================================

async function analyzeTranscript() {

  const transcript =
    transcriptInput?.value.trim();


  if (!transcript) {

    setStatus(
      "Add symptoms first, then analyze.",
      false,
      "error"
    );

    if (analysisStatus) {

      analysisStatus.textContent =
        "Please speak or type the patient's problem first.";
    }

    transcriptInput?.focus();

    return;
  }


  // ----------------------------------------------------------
  // Disable analyze button
  // ----------------------------------------------------------

  if (analyzeButton) {

    analyzeButton.disabled =
      true;

    analyzeButton.textContent =
      "⏳ AI analyzing...";
  }


  setStatus(
    "Understanding patient message...",
    true
  );


  if (analysisStatus) {

    analysisStatus.textContent =
      "Detecting language, symptoms, care area and suitable providers...";
  }


  try {

    const response =
      await fetch(
        `${API}/voice/analyze`,
        {

          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({

            transcript:
              transcript,

            location:
              locationInput?.value.trim()
                || null,

            speech_model:
              speechModel?.value
                || "browser-web-speech",

            language_model:
              languageModel?.value
                || "rule-hybrid",

          }),
        }
      );


    // --------------------------------------------------------
    // Backend error
    // --------------------------------------------------------

    if (!response.ok) {

      let errorMessage =
        `Server error ${response.status}`;

      try {

        const errorData =
          await response.json();

        if (errorData.detail) {

          errorMessage =
            Array.isArray(
              errorData.detail
            )
              ? errorData.detail
                  .map(
                    item =>
                      item.msg
                  )
                  .join(", ")

              : String(
                  errorData.detail
                );
        }

      } catch {
        // Keep default error
      }


      throw new Error(
        errorMessage
      );
    }


    // --------------------------------------------------------
    // JSON
    // --------------------------------------------------------

    const data =
      await response.json();


    console.log(
      "SmartCareAI /api/voice/analyze:",
      data
    );


    renderAnalysis(
      data
    );


    // --------------------------------------------------------
    // Search section
    // --------------------------------------------------------

    if (
      locationInput?.value.trim()
    ) {

      searchInput.value =
        transcript;

    }


    // --------------------------------------------------------
    // Scroll to results
    // --------------------------------------------------------

    const resultsSection =
      document.querySelector(
        ".results-grid"
      );

    resultsSection?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });


  } catch (error) {

    console.error(
      "SmartCareAI analysis error:",
      error
    );


    setStatus(
      "AI analysis failed.",
      false,
      "error"
    );


    if (analysisStatus) {

      analysisStatus.textContent =
        `Error: ${error.message}`;
    }


    if (urgencyLabel) {

      urgencyLabel.textContent =
        "Analysis unavailable";
    }


    if (urgencyMessage) {

      urgencyMessage.textContent =
        "Check that FastAPI is running on http://127.0.0.1:8000 and try again.";
    }

  } finally {

    if (analyzeButton) {

      analyzeButton.disabled =
        false;

      analyzeButton.textContent =
        "🤖 Analyze with AI";
    }

  }
}


// ============================================================
// START VOICE
// ============================================================

function startListening() {

  if (!SpeechRecognition) {

    setStatus(
      "Chrome speech recognition is unavailable. Type symptoms instead.",
      false,
      "error"
    );

    if (analysisStatus) {

      analysisStatus.textContent =
        "Use Google Chrome or type the patient message manually.";
    }

    return;
  }


  if (isListening) {
    return;
  }


  recognition =
    new SpeechRecognition();


  // Hindi + English/Hinglish
  recognition.lang =
    "hi-IN";


  recognition.interimResults =
    true;


  recognition.continuous =
    false;


  // ----------------------------------------------------------
  // Voice started
  // ----------------------------------------------------------

  recognition.onstart = () => {

    isListening =
      true;


    if (speakButtonText) {

      speakButtonText.textContent =
        "Listening...";
    }


    setStatus(
      "Listening to patient...",
      true
    );


    if (analysisStatus) {

      analysisStatus.textContent =
        "Speak naturally. SmartCareAI is listening...";
    }
  };


  // ----------------------------------------------------------
  // Voice result
  // ----------------------------------------------------------

  recognition.onresult = (
    event
  ) => {

    let transcript = "";


    for (
      let index = event.resultIndex;

      index < event.results.length;

      index++
    ) {

      transcript +=

        event.results[index][0]
          .transcript;
    }


    if (transcriptInput) {

      transcriptInput.value =
        transcript.trim();
    }
  };


  // ----------------------------------------------------------
  // Voice error
  // ----------------------------------------------------------

  recognition.onerror = (
    event
  ) => {

    console.error(
      "Speech recognition error:",
      event.error
    );


    isListening =
      false;


    if (speakButtonText) {

      speakButtonText.textContent =
        "Start speaking";
    }


    let message =
      "Voice input failed.";


    if (
      event.error ===
      "not-allowed"
    ) {

      message =
        "Microphone permission was denied.";

    } else if (
      event.error ===
      "no-speech"
    ) {

      message =
        "No speech detected. Please try again.";

    } else if (
      event.error ===
      "network"
    ) {

      message =
        "Speech service network error.";

    }


    setStatus(
      message,
      false,
      "error"
    );
  };


  // ----------------------------------------------------------
  // Voice ended
  // ----------------------------------------------------------

  recognition.onend = () => {

    isListening =
      false;


    if (speakButtonText) {

      speakButtonText.textContent =
        "Start speaking";
    }


    const transcript =
      transcriptInput?.value.trim();


    if (transcript) {

      setStatus(
        "Voice captured. AI analysis starting...",
        false,
        "success"
      );


      // AUTOMATIC AI ANALYSIS
      analyzeTranscript();

    } else {

      setStatus(
        "No voice input detected.",
        false,
        "error"
      );
    }
  };


  try {

    recognition.start();

  } catch (error) {

    console.error(
      "Could not start recognition:",
      error
    );

    setStatus(
      "Could not start microphone.",
      false,
      "error"
    );
  }
}


// ============================================================
// STOP VOICE
// ============================================================

function stopListening() {

  if (
    recognition &&
    isListening
  ) {

    recognition.stop();
  }
}


// ============================================================
// HEAR AI RESULT
// ============================================================

function speakLatestResult() {

  if (!latestSpokenResponse) {

    setStatus(
      "Analyze symptoms first, then hear the result.",
      false,
      "error"
    );

    return;
  }


  if (
    !("speechSynthesis" in window)
  ) {

    setStatus(
      "Text-to-speech is unavailable in this browser.",
      false,
      "error"
    );

    return;
  }


  window.speechSynthesis.cancel();


  const utterance =
    new SpeechSynthesisUtterance(
      latestSpokenResponse
    );


  // Use Hindi voice when Hindi/Hinglish
  const detectedLanguage =
    latestAnalysis?.detected_language
      || "";


  if (
    detectedLanguage === "Hindi" ||
    detectedLanguage === "Hinglish"
  ) {

    utterance.lang =
      "hi-IN";

  } else {

    utterance.lang =
      "en-IN";
  }


  utterance.rate =
    0.9;


  utterance.pitch =
    1;


  utterance.onstart = () => {

    setStatus(
      "Speaking AI result..."
    );
  };


  utterance.onend = () => {

    setStatus(
      "AI result finished.",
      false,
      "success"
    );
  };


  window.speechSynthesis.speak(
    utterance
  );
}


// ============================================================
// LOAD PROVIDERS
// ============================================================

async function loadProviders() {

  try {

    const response =
      await fetch(
        `${API}/providers`
      );


    if (!response.ok) {

      throw new Error(
        `Provider API ${response.status}`
      );
    }


    const providers =
      await response.json();


    renderProviders(
      providers
    );


  } catch (error) {

    console.error(
      "Provider loading error:",
      error
    );


    if (searchStatus) {

      searchStatus.textContent =
        "Unable to load providers.";
    }
  }
}


// ============================================================
// LOAD DATA SOURCES
// ============================================================

async function loadSources() {

  if (!sourceList) {
    return;
  }


  try {

    const response =
      await fetch(
        `${API}/data-sources`
      );


    if (!response.ok) {

      return;
    }


    const sources =
      await response.json();


    if (
      !Array.isArray(sources)
    ) {

      return;
    }


    sourceList.innerHTML =
      sources
        .map(
          source => `

            <a
              class="source-card"
              href="${escapeHTML(
                source.url
              )}"
              target="_blank"
              rel="noopener noreferrer"
            >

              <strong>
                ${escapeHTML(
                  source.name
                )}
              </strong>

              <span>
                ${escapeHTML(
                  source.description ||
                  source.type ||
                  "Official data source"
                )}
              </span>

            </a>

          `
        )
        .join("");


  } catch (error) {

    console.error(
      "Source loading error:",
      error
    );
  }
}


// ============================================================
// SEARCH HEALTHCARE
// ============================================================

async function searchCare(
  event
) {

  event?.preventDefault();


  const query =
    searchInput?.value.trim()
      || "";


  const location =
    locationInput?.value.trim()
      || "";


  const ownership =
    ownershipFilter?.value
      || "";


  const specialty =
    specialtyFilter?.value
      || "";


  const budget =
    budgetInput?.value
      || "";


  const distance =
    distanceInput?.value
      || "";


  if (
    !query &&
    !location &&
    !ownership &&
    !specialty
  ) {

    setStatus(
      "Enter a doctor, hospital, specialty or location.",
      false,
      "error"
    );

    return;
  }


  if (searchStatus) {

    searchStatus.textContent =
      "🔎 Searching healthcare providers...";
  }


  providerList.innerHTML =
    "";


  const params =
    new URLSearchParams();


  // Query can be empty
  if (query) {

    params.set(
      "query",
      query
    );
  }


  if (location) {

    params.set(
      "location",
      location
    );
  }


  if (ownership) {

    params.set(
      "ownership",
      ownership
    );
  }


  if (specialty) {

    params.set(
      "specialty",
      specialty
    );
  }


  if (budget) {

    params.set(
      "budget_max_inr",
      budget
    );
  }


  if (distance) {

    params.set(
      "max_distance_km",
      distance
    );
  }


  params.set(
    "sort",
    "recommended"
  );


  try {

    const response =
      await fetch(
        `${API}/search?${params.toString()}`
      );


    if (!response.ok) {

      throw new Error(
        `Search API returned ${response.status}`
      );
    }


    const data =
      await response.json();


    console.log(
      "SmartCareAI search:",
      data
    );


    renderProviders(
      data.results || []
    );


    if (searchStatus) {

      searchStatus.textContent =
        `${data.total ?? 0} healthcare provider(s) found`;
    }


    setStatus(
      "Search results updated.",
      false,
      "success"
    );


    document
      .querySelector("#providers")
      ?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });


  } catch (error) {

    console.error(
      "Search error:",
      error
    );


    if (searchStatus) {

      searchStatus.textContent =
        "Search failed. Please check the backend.";
    }


    setStatus(
      "Healthcare search failed.",
      false,
      "error"
    );
  }
}


// ============================================================
// BUTTON EVENTS
// ============================================================

// ------------------------------------------------------------
// VOICE
// ------------------------------------------------------------

// Mouse:
// Hold button -> listen
// Release -> stop

if (speakButton) {

  speakButton.addEventListener(
    "mousedown",
    startListening
  );


  speakButton.addEventListener(
    "mouseup",
    stopListening
  );


  speakButton.addEventListener(
    "mouseleave",
    stopListening
  );


  // Touch devices

  speakButton.addEventListener(
    "touchstart",
    event => {

      event.preventDefault();

      startListening();
    }
  );


  speakButton.addEventListener(
    "touchend",
    event => {

      event.preventDefault();

      stopListening();
    }
  );
}


// ------------------------------------------------------------
// ANALYZE
// ------------------------------------------------------------

if (analyzeButton) {

  analyzeButton.addEventListener(
    "click",
    analyzeTranscript
  );
}


// ------------------------------------------------------------
// HEAR RESULT
// ------------------------------------------------------------

if (hearButton) {

  hearButton.addEventListener(
    "click",
    speakLatestResult
  );
}


// ------------------------------------------------------------
// SEARCH
// ------------------------------------------------------------

if (careSearch) {

  careSearch.addEventListener(
    "submit",
    searchCare
  );
}


// ============================================================
// KEYBOARD SHORTCUT
// ============================================================

// Ctrl + Enter -> Analyze

if (transcriptInput) {

  transcriptInput.addEventListener(
    "keydown",
    event => {

      if (
        event.ctrlKey &&
        event.key === "Enter"
      ) {

        event.preventDefault();

        analyzeTranscript();
      }
    }
  );
}


// ============================================================
// INITIALIZATION
// ============================================================

async function initializeApp() {

  console.log(
    "Initializing SmartCareAI..."
  );


  await checkBackend();


  await Promise.all([
    loadProviders(),
    loadSources()
  ]);


  console.log(
    "SmartCareAI initialized."
  );
}


initializeApp();


function detectTextLanguage(text) {

    if (!text) {
        return "en-IN";
    }

    // Devanagari characters
    const hindiCharacters =
        (text.match(
            /[\u0900-\u097F]/g
        ) || []).length;

    // English alphabet characters
    const englishCharacters =
        (text.match(
            /[A-Za-z]/g
        ) || []).length;

    if (
        hindiCharacters > englishCharacters
    ) {
        return "hi-IN";
    }

    return "en-IN";
}
