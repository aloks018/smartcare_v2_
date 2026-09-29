const API = window.SMARTCARE_API_URL || window.SMARTCARE_API || "/api";
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const $ = (selector) => document.querySelector(selector);

const elements = {
  analyzeButton: $("#analyzeButton"),
  assistantStatusDot: $("#assistantStatusDot"),
  assistantStatusText: $("#assistantStatusText"),
  catalogCount: $("#catalogCount"),
  disclaimer: $("#disclaimerText"),
  distance: $("#distanceInput"),
  hearButton: $("#hearButton"),
  languageModel: $("#languageModel"),
  languageValue: $("#languageValue"),
  location: $("#locationInput"),
  medicalMatchList: $("#medicalMatchList"),
  medicalMatchStatus: $("#medicalMatchStatus"),
  menuToggle: $("#menuToggle"),
  mobileMenu: $("#mobileMenu"),
  modelValue: $("#modelValue"),
  ownership: $("#ownershipFilter"),
  patientLanguage: $("#patientLanguage"),
  providerList: $("#providerList"),
  reasonList: $("#reasonList"),
  searchForm: $("#careSearch"),
  searchInput: $("#searchInput"),
  searchStatus: $("#searchStatus"),
  sourceList: $("#sourceList"),
  speakButton: $("#speakButton"),
  speakButtonText: $("#speakButtonText"),
  speechModel: $("#speechModel"),
  specialty: $("#specialtyFilter"),
  specialtyValue: $("#specialtyValue"),
  statusDot: $("#statusDot"),
  statusText: $("#statusText"),
  symptomsValue: $("#symptomsValue"),
  transcript: $("#manualTranscript"),
  urgencyBlock: $("#urgencyBlock"),
  urgencyLabel: $("#urgencyLabel"),
  urgencyMessage: $("#urgencyMessage"),
  analysisStatus: $("#analysisStatus"),
};

let recognition = null;
let isListening = false;
let latestAnalysis = null;
let latestSpokenResponse = "";
let providerCount = 0;
let capturedTranscript = "";
let recognitionError = false;
let analysisStartedFromVoice = false;

function setText(element, value) {
  if (element) element.textContent = value ?? "-";
}

function escapeHTML(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function formatText(value) {
  return String(value ?? "").replace(/[_-]+/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function setStatus(message, state = "normal") {
  setText(elements.statusText, message);
  if (elements.statusDot) elements.statusDot.className = `status-dot ${state}`;
  setText(elements.assistantStatusText, message);
  if (elements.assistantStatusDot) elements.assistantStatusDot.className = `status-dot ${state}`;
}

function setProcessing(active) {
  document.body.classList.toggle("ai-processing", active);
  if (!elements.analyzeButton) return;
  elements.analyzeButton.disabled = active;
  elements.analyzeButton.innerHTML = active
    ? 'Working <span class="loading-mark" aria-hidden="true"></span>'
    : 'Analyze with AI <span class="arrow" aria-hidden="true">→</span>';
}

async function apiError(response) {
  try {
    const payload = await response.json();
    if (Array.isArray(payload.detail)) return payload.detail.map((item) => item.msg).join(", ");
    return payload.detail || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

async function getJSON(path) {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(await apiError(response));
  return response.json();
}

function providerCard(provider) {
  const address = provider.address || [provider.city, provider.state].filter(Boolean).join(", ") || "Address not listed";
  const fee = provider.consultation_fee_inr != null ? `From Rs. ${Number(provider.consultation_fee_inr).toLocaleString("en-IN")}` : "Fee on request";
  const distance = provider.distance_km != null ? `${Number(provider.distance_km).toFixed(1)} km away` : "Distance not listed";
  const score = provider.match_score != null ? `${Math.round(provider.match_score)}% match` : "Directory match";
  const source = provider.verified_source || (provider.verified ? "Verified public source" : "Directory listing");
  const reasons = Array.isArray(provider.match_reasons) ? provider.match_reasons.slice(0, 2) : [];
  const actions = [
    provider.phone ? `<a class="provider-action" href="tel:${escapeHTML(provider.phone)}">Call</a>` : "",
    provider.website ? `<a class="provider-action primary-action" href="${escapeHTML(provider.website)}" target="_blank" rel="noopener noreferrer">Visit source <span aria-hidden="true">↗</span></a>` : "",
  ].filter(Boolean).join("");
  return `<article class="provider-card">
    <div class="provider-card-top"><span class="provider-kind">${escapeHTML(provider.provider_type || "Healthcare")}</span><span class="match-score">${escapeHTML(score)}</span></div>
    <h3>${escapeHTML(provider.name || "Healthcare provider")}</h3>
    <div class="provider-tags"><span>${escapeHTML(provider.ownership || "Public")}</span><span>${escapeHTML(provider.specialty || "General Medicine")}</span>${provider.emergency_available ? '<span class="emergency-tag">Emergency</span>' : ""}</div>
    <p class="provider-address">${escapeHTML(address)}</p>
    <div class="provider-meta"><span>${escapeHTML(fee)}</span><span>${escapeHTML(distance)}</span></div>
    ${provider.availability ? `<p class="availability">${escapeHTML(provider.availability)}</p>` : ""}
    ${reasons.length ? `<div class="match-reasons">${reasons.map((reason) => `<span>${escapeHTML(reason)}</span>`).join("")}</div>` : ""}
    <div class="provider-footer"><span class="source-stamp"><i></i>${escapeHTML(source)}</span><div class="provider-actions">${actions}</div></div>
  </article>`;
}

function renderProviders(providers) {
  if (!elements.providerList) return;
  if (!Array.isArray(providers) || providers.length === 0) {
    elements.providerList.innerHTML = '<div class="empty-state"><strong>No matching care providers found.</strong><span>Try a different care need, specialty, or location.</span></div>';
    return;
  }
  elements.providerList.innerHTML = providers.map(providerCard).join("");
}

function renderReasons(reasons) {
  if (!elements.reasonList) return;
  if (!Array.isArray(reasons) || reasons.length === 0) {
    elements.reasonList.innerHTML = "<p>AI insights will be shown after analysis.</p>";
    return;
  }
  elements.reasonList.innerHTML = reasons.slice(0, 4).map((reason) => `<div class="ai-reason"><i aria-hidden="true">✓</i><p>${escapeHTML(reason)}</p></div>`).join("");
}

function medicalMatchCard(match) {
  const signalTerms = [...(match.matching_symptoms || []), ...(match.matching_conditions || []), ...(match.matching_keywords || [])].slice(0, 5);
  const subspecialties = (match.related_subspecialties || []).slice(0, 3);
  return `<article class="medical-match-card">
    <div class="medical-card-top"><span>${escapeHTML(match.parent_category)}</span><strong>${escapeHTML(match.relevance)}% relevant</strong></div>
    <h4>${escapeHTML(match.specialty_name)}</h4>
    <p>${escapeHTML(match.description)}</p>
    ${signalTerms.length ? `<div class="match-chip-row">${signalTerms.map((term) => `<span>${escapeHTML(term)}</span>`).join("")}</div>` : ""}
    ${subspecialties.length ? `<p class="subspecialty-line"><b>Related:</b> ${escapeHTML(subspecialties.join(" · "))}</p>` : ""}
    <p class="consult-line"><b>When to consult:</b> ${escapeHTML(match.when_to_consult)}</p>
  </article>`;
}

function renderMedicalMatches(matches, message) {
  if (elements.medicalMatchStatus) setText(elements.medicalMatchStatus, message);
  if (!elements.medicalMatchList) return;
  if (!Array.isArray(matches) || matches.length === 0) {
    elements.medicalMatchList.innerHTML = '<div class="catalog-empty">No clear specialty match was found. Try a symptom, condition, treatment, or specialty name.</div>';
    return;
  }
  elements.medicalMatchList.innerHTML = matches.map(medicalMatchCard).join("");
}

function renderAnalysis(data) {
  latestAnalysis = data;
  const symptoms = Array.isArray(data.symptoms) ? data.symptoms : [];
  const assessment = data.assessment || {};
  const stack = data.model_stack || {};
  const urgency = assessment.urgency || "routine";
  setText(elements.languageValue, data.detected_language || "Language detected");
  setText(elements.symptomsValue, symptoms.length ? symptoms.map((item) => item.name).join(", ") : "No clear symptom detected");
  setText(elements.specialtyValue, data.suggested_specialty || "General Medicine");
  setText(elements.modelValue, `${stack.speech || elements.speechModel?.value || "Web Speech"} + ${stack.language || elements.languageModel?.value || "Smart hybrid"}`);
  setText(elements.urgencyLabel, formatText(urgency));
  setText(elements.urgencyMessage, [assessment.message, data.recommended_next_action].filter(Boolean).join(" "));
  setText(elements.disclaimer, data.disclaimer || "SmartCare AI supports care navigation and does not replace a medical diagnosis.");
  if (elements.urgencyBlock) elements.urgencyBlock.dataset.level = urgency;
  latestSpokenResponse = data.spoken_response || data.recommended_next_action || "";
  renderReasons(data.why_this_recommendation);
  renderMedicalMatches(data.medical_matches, "Matches are based on symptoms, conditions, treatments, and specialty keywords in the local catalog.");
  renderProviders(data.providers);
  setText(elements.analysisStatus, "Your AI care brief is ready. Review the care priority, specialty matches, and local provider options below.");
  setStatus("AI care brief ready", "success");
}

async function analyzeTranscript() {
  const transcript = elements.transcript?.value.trim();
  if (!transcript) {
    setStatus("Add a patient message before analysis.", "error");
    setText(elements.analysisStatus, "Enter or speak a health concern to create an AI care brief.");
    elements.transcript?.focus();
    return;
  }
  setProcessing(true);
  setStatus("Understanding your message", "listening");
  setText(elements.analysisStatus, "Detecting language, symptoms, care area, and suitable providers.");
  try {
    const response = await fetch(`${API}/voice/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript, location: elements.location?.value.trim() || null, speech_model: elements.speechModel?.value || "browser-web-speech", language_model: elements.languageModel?.value || "rule-hybrid" }),
    });
    if (!response.ok) throw new Error(await apiError(response));
    const data = await response.json();
    renderAnalysis(data);
    if (elements.searchInput && !elements.searchInput.value.trim()) elements.searchInput.value = transcript;
    $(".analysis-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    console.error("Voice analysis failed:", error);
    setStatus("AI analysis is unavailable right now.", "error");
    setText(elements.analysisStatus, error.message || "Please check the SmartCare service and try again.");
  } finally {
    setProcessing(false);
  }
}

function startListening() {
  if (!SpeechRecognition) {
    setStatus("Voice recognition is not available in this browser.", "error");
    setText(elements.analysisStatus, "Use the latest Chrome version, allow microphone access, or type your message instead.");
    return;
  }
  if (isListening) return;
  capturedTranscript = "";
  recognitionError = false;
  analysisStartedFromVoice = false;
  if (elements.transcript) elements.transcript.value = "";
  recognition = new SpeechRecognition();
  recognition.lang = elements.patientLanguage?.value || "en-IN";
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;
  recognition.onstart = () => { isListening = true; document.body.classList.add("is-listening"); setText(elements.speakButtonText, "Listening now"); setStatus("Listening to your message", "listening"); setText(elements.analysisStatus, "Speak clearly, then pause when you are finished."); };
  recognition.onresult = (event) => {
    let interimTranscript = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const phrase = event.results[index][0].transcript.trim();
      if (event.results[index].isFinal) capturedTranscript = `${capturedTranscript} ${phrase}`.trim();
      else interimTranscript = `${interimTranscript} ${phrase}`.trim();
    }
    if (elements.transcript) elements.transcript.value = `${capturedTranscript} ${interimTranscript}`.trim();
    if (capturedTranscript || interimTranscript) setText(elements.analysisStatus, "I heard you. Keep speaking or pause to create your care brief.");
  };
  recognition.onerror = (event) => {
    recognitionError = true;
    console.error("Speech recognition error:", event.error);
    const messages = { "not-allowed": "Microphone permission was denied. Allow it in Chrome site settings and try again.", "service-not-allowed": "Chrome blocked the speech service. Check your browser permissions and internet connection.", "no-speech": "No speech was detected. Tap the microphone and speak after the listening tone.", network: "Voice service network error. Check your internet connection and try again.", aborted: "Voice capture stopped. Tap the microphone to try again." };
    setStatus(messages[event.error] || "Voice input did not complete. Please try again.", "error");
    setText(elements.analysisStatus, messages[event.error] || "Voice input did not complete. Please try again.");
  };
  recognition.onend = () => {
    isListening = false;
    document.body.classList.remove("is-listening");
    setText(elements.speakButtonText, "Tap to speak");
    const transcript = capturedTranscript.trim();
    if (!recognitionError && transcript && !analysisStartedFromVoice) {
      analysisStartedFromVoice = true;
      if (elements.transcript) elements.transcript.value = transcript;
      setStatus("Voice captured. Creating your care brief", "listening");
      analyzeTranscript();
    } else if (!recognitionError && !transcript) {
      setStatus("No speech was captured. Tap the microphone and try again.", "error");
      setText(elements.analysisStatus, "No speech was captured. Speak after the listening state appears.");
    }
  };
  try { recognition.start(); } catch (error) { recognitionError = true; setStatus("Microphone could not start. Check Chrome permissions and try again.", "error"); console.error("Could not start voice recognition:", error); }
}

function stopListening() {
  if (recognition && isListening) recognition.stop();
}

function speakLatestResult() {
  if (!latestSpokenResponse) { setStatus("Create an AI care brief before listening to it.", "error"); return; }
  if (!("speechSynthesis" in window)) { setStatus("Text-to-speech is unavailable in this browser.", "error"); return; }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(latestSpokenResponse);
  utterance.lang = elements.patientLanguage?.value || (["Hindi", "Hinglish"].includes(latestAnalysis?.detected_language) ? "hi-IN" : "en-IN");
  utterance.rate = 0.92;
  utterance.onstart = () => setStatus("Reading your AI care brief");
  utterance.onend = () => setStatus("AI care brief finished", "success");
  window.speechSynthesis.speak(utterance);
}

async function searchMedicalMatches(query) {
  if (!query) { renderMedicalMatches([], "Enter a healthcare enquiry to search the specialty catalog."); return; }
  try {
    const data = await getJSON(`/medical/search?${new URLSearchParams({ query, limit: "3" })}`);
    renderMedicalMatches(data.results, data.total ? `${data.total} relevant care area${data.total === 1 ? "" : "s"} found in the specialty catalog.` : "No direct specialty match was found.");
  } catch (error) {
    console.error("Medical catalog search failed:", error);
    renderMedicalMatches([], "The specialty catalog is temporarily unavailable.");
  }
}

async function searchCare(event) {
  event?.preventDefault();
  const query = elements.searchInput?.value.trim() || "";
  const location = elements.location?.value.trim() || "";
  const ownership = elements.ownership?.value || "";
  const specialty = elements.specialty?.value || "";
  if (!query && !location && !ownership && !specialty) { setStatus("Enter a care need, location, ownership, or specialty.", "error"); return; }
  const fallbackQuery = [query, specialty, ownership, location].filter(Boolean).join(" ") || "healthcare";
  const params = new URLSearchParams({ query: fallbackQuery, sort: "recommended" });
  if (location) params.set("location", location);
  if (ownership) params.set("ownership", ownership);
  if (specialty) params.set("specialty", specialty);
  if (elements.distance?.value) params.set("max_distance_km", elements.distance.value);
  setText(elements.searchStatus, "Searching SmartCare’s care directory...");
  if (elements.providerList) elements.providerList.innerHTML = '<div class="directory-loading"><i></i><span>Finding suitable care options</span></div>';
  try {
    const [providerResponse] = await Promise.all([getJSON(`/search?${params}`), searchMedicalMatches(fallbackQuery)]);
    renderProviders(providerResponse.results || []);
    setText(elements.searchStatus, `${providerResponse.total ?? 0} provider${providerResponse.total === 1 ? "" : "s"} found`);
    setStatus("Directory results updated", "success");
  } catch (error) {
    console.error("Directory search failed:", error);
    setText(elements.searchStatus, "Directory search is unavailable right now.");
    setStatus("Healthcare search failed.", "error");
  }
}

async function loadProviders() {
  try {
    const providers = await getJSON("/providers");
    providerCount = Array.isArray(providers) ? providers.length : 0;
    renderProviders(providers);
    setText(elements.searchStatus, `${providerCount} providers in the directory`);
  } catch (error) {
    console.error("Provider loading failed:", error);
    setText(elements.searchStatus, "Unable to load the provider directory.");
  }
}

async function loadSources() {
  if (!elements.sourceList) return;
  try {
    const sources = await getJSON("/data-sources");
    elements.sourceList.innerHTML = sources.map((source) => `<a class="source-card" href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer"><span class="source-number">${escapeHTML(source.type || "Official")}</span><strong>${escapeHTML(source.name)}</strong><p>${escapeHTML(source.description || "Public healthcare data source")}</p><span class="source-link">Open source <b aria-hidden="true">↗</b></span></a>`).join("");
  } catch (error) {
    console.error("Data source loading failed:", error);
  }
}

async function loadSpecialties() {
  try {
    const [specialties, stats] = await Promise.all([getJSON("/medical/specialties"), getJSON("/medical/catalog/stats")]);
    if (elements.specialty) {
      const existing = new Set([...elements.specialty.options].map((option) => option.value));
      specialties.forEach((specialty) => { if (!existing.has(specialty.name)) elements.specialty.add(new Option(specialty.name, specialty.name)); });
    }
    setText(elements.catalogCount, stats.specialties || specialties.length);
  } catch (error) {
    console.error("Specialty loading failed:", error);
  }
}

async function checkBackend() {
  try {
    const data = await getJSON("/health");
    setStatus(`${data.service || "SmartCare AI"} is ready`, "success");
  } catch (error) {
    console.error("Backend health check failed:", error);
    setStatus("SmartCare service is not connected.", "error");
  }
}

function setupRevealAnimations() {
  if (!("IntersectionObserver" in window)) { document.querySelectorAll(".reveal").forEach((element) => element.classList.add("is-visible")); return; }
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => { if (entry.isIntersecting) { entry.target.classList.add("is-visible"); observer.unobserve(entry.target); } }), { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
}

function setupMobileMenu() {
  elements.menuToggle?.addEventListener("click", () => {
    const open = elements.mobileMenu?.classList.toggle("is-open") || false;
    elements.menuToggle.setAttribute("aria-expanded", String(open));
  });
  elements.mobileMenu?.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => { elements.mobileMenu.classList.remove("is-open"); elements.menuToggle?.setAttribute("aria-expanded", "false"); }));
}

elements.speakButton?.addEventListener("click", () => (isListening ? stopListening() : startListening()));
elements.analyzeButton?.addEventListener("click", analyzeTranscript);
elements.hearButton?.addEventListener("click", speakLatestResult);
elements.searchForm?.addEventListener("submit", searchCare);
elements.transcript?.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") analyzeTranscript(); });

async function initializeApp() {
  setupRevealAnimations();
  setupMobileMenu();
  await checkBackend();
  await Promise.all([loadProviders(), loadSources(), loadSpecialties()]);
  if (providerCount) setStatus(`SmartCare AI is ready with ${providerCount} providers`, "success");
}

initializeApp();

function showToast(message) {
  const toast = document.querySelector("#toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => toast.classList.remove("show"), 3200);
}

function routeToView() {
  const requestedView = window.location.hash.replace(/^#/, "") || "dashboard";
  const view = document.querySelector(`[data-view="${requestedView}"]`) ? requestedView : "dashboard";
  document.querySelectorAll(".app-view").forEach((section) => section.classList.toggle("active-view", section.dataset.view === view));
  document.querySelectorAll("[data-route]").forEach((link) => link.classList.toggle("active", link.dataset.route === view));
  elements.mobileMenu?.classList.remove("is-open");
  elements.menuToggle?.setAttribute("aria-expanded", "false");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-route]").forEach((link) => link.addEventListener("click", routeToView));
window.addEventListener("hashchange", routeToView);
window.addEventListener("load", routeToView);
document.querySelectorAll("[data-demo-action]").forEach((button) => button.addEventListener("click", () => {
  const messages = {
    appointment: "Appointment booking will open when provider scheduling is connected.",
    details: "Appointment details are ready for your next connected care session.",
    question: "Your question draft is ready to review.",
    upload: "Record upload is ready for the connected patient account.",
    read: "All notifications are marked as read.",
  };
  showToast(messages[button.dataset.demoAction] || "SmartCare action ready.");
}));
routeToView();
window.setTimeout(routeToView, 0);
