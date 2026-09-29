"use strict";

const API_BASE = "/api/auth";

const loginTab = document.getElementById(
  "loginTab"
);

const registerTab = document.getElementById(
  "registerTab"
);

const loginForm = document.getElementById(
  "loginForm"
);

const registerForm = document.getElementById(
  "registerForm"
);

const authForms = document.getElementById(
  "authForms"
);

const accountPanel = document.getElementById(
  "accountPanel"
);

const authMessage = document.getElementById(
  "authMessage"
);

const accountName = document.getElementById(
  "accountName"
);

const accountEmail = document.getElementById(
  "accountEmail"
);

const logoutButton = document.getElementById(
  "logoutButton"
);


// ============================================================
// TOKEN
// ============================================================

function getToken() {

  return localStorage.getItem(
    "smartcare_access_token"
  );
}


function saveToken(token) {

  localStorage.setItem(
    "smartcare_access_token",
    token
  );
}


function clearToken() {

  localStorage.removeItem(
    "smartcare_access_token"
  );
}


// ============================================================
// MESSAGE
// ============================================================

function showMessage(
  message,
  type = ""
) {

  authMessage.textContent = message;

  authMessage.className =
    `auth-message ${type}`;
}


// ============================================================
// API
// ============================================================

async function apiRequest(
  endpoint,
  options = {}
) {

  const response = await fetch(
    `${API_BASE}${endpoint}`,
    {
      ...options,

      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    }
  );


  let data = null;

  try {

    data = await response.json();

  } catch {

    data = null;

  }


  if (!response.ok) {

    const message =
      data?.detail ||
      "Something went wrong.";

    throw new Error(message);
  }


  return data;
}


// ============================================================
// TABS
// ============================================================

function showLogin() {

  loginTab.classList.add("active");
  registerTab.classList.remove("active");

  loginForm.classList.add("active");
  registerForm.classList.remove("active");

  showMessage("");
}


function showRegister() {

  registerTab.classList.add("active");
  loginTab.classList.remove("active");

  registerForm.classList.add("active");
  loginForm.classList.remove("active");

  showMessage("");
}


loginTab.addEventListener(
  "click",
  showLogin
);


registerTab.addEventListener(
  "click",
  showRegister
);


// ============================================================
// SHOW ACCOUNT
// ============================================================

function showAccount(user) {

  authForms.style.display = "none";

  accountPanel.classList.add(
    "active"
  );

  accountName.textContent =
    user.full_name;

  accountEmail.textContent =
    user.email;

  showMessage(
    "You are logged in.",
    "success"
  );
}


// ============================================================
// REGISTER
// ============================================================

registerForm.addEventListener(
  "submit",
  async (event) => {

    event.preventDefault();

    showMessage(
      "Creating your account..."
    );


    const payload = {

      full_name:
        document.getElementById(
          "registerName"
        ).value.trim(),

      email:
        document.getElementById(
          "registerEmail"
        ).value.trim(),

      phone:
        document.getElementById(
          "registerPhone"
        ).value.trim() || null,

      password:
        document.getElementById(
          "registerPassword"
        ).value,
    };


    try {

      const data = await apiRequest(
        "/register",
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );


      saveToken(
        data.access_token
      );


      showAccount(
        data.user
      );

    } catch (error) {

      console.error(
        "Registration failed:",
        error
      );

      showMessage(
        error.message,
        "error"
      );
    }

  }
);


// ============================================================
// LOGIN
// ============================================================

loginForm.addEventListener(
  "submit",
  async (event) => {

    event.preventDefault();

    showMessage(
      "Signing you in..."
    );


    const payload = {

      email:
        document.getElementById(
          "loginEmail"
        ).value.trim(),

      password:
        document.getElementById(
          "loginPassword"
        ).value,
    };


    try {

      const data = await apiRequest(
        "/login",
        {
          method: "POST",
          body: JSON.stringify(payload),
        }
      );


      saveToken(
        data.access_token
      );


      showAccount(
        data.user
      );

    } catch (error) {

      console.error(
        "Login failed:",
        error
      );

      showMessage(
        error.message,
        "error"
      );
    }

  }
);


// ============================================================
// CHECK EXISTING LOGIN
// ============================================================

async function loadCurrentUser() {

  const token = getToken();

  if (!token) {
    return;
  }


  try {

    const response =
      await fetch(
        `${API_BASE}/me`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );


    if (!response.ok) {

      clearToken();

      return;
    }


    const user =
      await response.json();


    showAccount(user);

  } catch (error) {

    console.error(
      "Could not load current user:",
      error
    );

    clearToken();
  }
}


// ============================================================
// LOGOUT
// ============================================================

logoutButton.addEventListener(
  "click",
  () => {

    clearToken();

    accountPanel.classList.remove(
      "active"
    );

    authForms.style.display =
      "block";

    showLogin();

    showMessage(
      "You have been logged out.",
      "success"
    );
  }
);


// ============================================================
// START
// ============================================================

loadCurrentUser();