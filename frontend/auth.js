
const API_BASE_URL = "http://127.0.0.1:8000";

// ---------- GET HTML ELEMENTS ----------

const customerTab = document.getElementById("customer-tab");
const ownerTab = document.getElementById("owner-tab");

const customerSection = document.getElementById("customer-section");
const ownerSection = document.getElementById("owner-section");

const customerForm = document.getElementById("customer-form");
const ownerForm = document.getElementById("owner-form");

const loginMode = document.getElementById("login-mode");
const signupMode = document.getElementById("signup-mode");

const nameGroup = document.getElementById("name-group");
const nameInput = document.getElementById("customer-name");

const formTitle = document.getElementById("form-title");
const formSubtitle = document.getElementById("form-subtitle");
const customerSubmit = document.getElementById("customer-submit");

const messageBox = document.getElementById("message");

let currentMode = "login";
let currentAccountType = "customer";

// ---------- MESSAGE ----------

function showMessage(message, type = "error") {
    messageBox.textContent = message;
    messageBox.className = `message ${type}`;
}

function clearMessage() {
    messageBox.textContent = "";
    messageBox.className = "message";
}

// ---------- ADD PHONE FIELD FOR SIGNUP ----------

const phoneGroup = document.createElement("div");
phoneGroup.className = "form-group";
phoneGroup.hidden = true;

phoneGroup.innerHTML = `
    <label for="customer-phone">Phone Number</label>
    <input
        type="tel"
        id="customer-phone"
        name="phone"
        placeholder="Enter your phone number"
        autocomplete="tel"
        inputmode="tel"
        maxlength="15"
    >
`;

nameGroup.after(phoneGroup);

const phoneInput = document.getElementById("customer-phone");

// ---------- CUSTOMER LOGIN / SIGNUP MODE ----------

function setCustomerMode(mode) {
    currentMode = mode;
    clearMessage();

    const isSignup = mode === "signup";

    nameGroup.hidden = !isSignup;
    phoneGroup.hidden = !isSignup;

    nameInput.required = isSignup;
    phoneInput.required = isSignup;

    loginMode.classList.toggle("active", !isSignup);
    signupMode.classList.toggle("active", isSignup);

    formTitle.textContent = isSignup
        ? "Create Your Account"
        : "Welcome Back!";

    formSubtitle.textContent = isSignup
        ? "Sign up to start ordering fresh chicken."
        : "Login to order your favourite cuts.";

    customerSubmit.textContent = isSignup
        ? "Create Account"
        : "Login as Customer";

    const passwordInput = document.getElementById("customer-password");

    passwordInput.autocomplete = isSignup
        ? "new-password"
        : "current-password";
}

loginMode.addEventListener("click", () => {
    setCustomerMode("login");
});

signupMode.addEventListener("click", () => {
    setCustomerMode("signup");
});

// ---------- SWITCH CUSTOMER / OWNER ----------

function setAccountType(type) {
    currentAccountType = type;
    clearMessage();

    const isCustomer = type === "customer";

    customerSection.hidden = !isCustomer;
    ownerSection.hidden = isCustomer;

    customerTab.classList.toggle("active", isCustomer);
    ownerTab.classList.toggle("active", !isCustomer);
}

customerTab.addEventListener("click", () => {
    setAccountType("customer");
});

ownerTab.addEventListener("click", () => {
    setAccountType("owner");
});

// ---------- API ERROR HANDLING ----------

async function getErrorMessage(response) {
    try {
        const data = await response.json();

        if (Array.isArray(data.detail)) {
            return data.detail
                .map((item) => item.msg || "Invalid input")
                .join(", ");
        }

        return data.detail || data.message || "Something went wrong.";
    } catch {
        return `Request failed (${response.status}).`;
    }
}

// ---------- SAVE LOGIN SESSION ----------

function saveSession(data) {
    if (!data.access_token || !data.user) {
        throw new Error("The server returned an unexpected login response.");
    }

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("current_user", JSON.stringify(data.user));
}

// ---------- CUSTOMER FORM ----------

customerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage();

    const email = document
        .getElementById("customer-email")
        .value.trim();

    const password = document
        .getElementById("customer-password")
        .value;

    const isSignup = currentMode === "signup";

    const payload = {
        email,
        password
    };

    if (isSignup) {
        const name = nameInput.value.trim();
        const phone = phoneInput.value.trim();

        if (!name || !phone) {
            showMessage("Please enter your name and phone number.");
            return;
        }

        payload.name = name;
        payload.phone = phone;
    }

    customerSubmit.disabled = true;
    customerSubmit.textContent = isSignup
        ? "Creating account..."
        : "Logging in...";

    try {
        const endpoint = isSignup
            ? "/auth/register"
            : "/auth/login";

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(await getErrorMessage(response));
        }

        // Signup creates the account; login is a separate step.
        if (isSignup) {
            showMessage(
                "Account created successfully! Please log in.",
                "success"
            );

            customerForm.reset();
            setCustomerMode("login");
            return;
        }

        const data = await response.json();

        if (!data.user || data.user.role !== "customer") {
            showMessage(
                "This account is not a customer account. Please use the correct login option."
            );
            return;
        }

        saveSession(data);

        showMessage("Login successful! Opening the homepage...", "success");

        setTimeout(() => {
           window.location.href = "/index.html";
        }, 900);

    } catch (error) {
        showMessage(
            error.message ||
            "Could not connect to the server. Check that your backend is running."
        );
    } finally {
        customerSubmit.disabled = false;
        customerSubmit.textContent = currentMode === "signup"
            ? "Create Account"
            : "Login as Customer";
    }
});

// ---------- OWNER LOGIN ----------

ownerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage();

    const email = document.getElementById("owner-email").value.trim();
    const password = document.getElementById("owner-password").value;

    const submitButton = ownerForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;
    submitButton.textContent = "Verifying...";

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        if (!response.ok) {
            throw new Error(await getErrorMessage(response));
        }

        const data = await response.json();

        if (!data.user || data.user.role !== "owner") {
            showMessage(
                "Access denied. Please use the registered owner account."
            );
            return;
        }

        saveSession(data);

        showMessage(
            "Owner login successful! Your session is saved. The owner dashboard is our next step.",
            "success"
        );

    } catch (error) {
        showMessage(
            error.message ||
            "Could not connect to the server. Check that your backend is running."
        );
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Login to Dashboard";
    }
});

// ---------- INITIAL STATE ----------

setAccountType("customer");
setCustomerMode("login");


/* Redirect users who already have a saved session */
const savedToken = localStorage.getItem("access_token");
const savedUser = localStorage.getItem("current_user");

if (savedToken && savedUser) {
    try {
        const user = JSON.parse(savedUser);

        if (user.role === "customer") {
            window.location.replace("/index.html");
        }
    } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("current_user");
    }
}

