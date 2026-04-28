(function () {
    const STORAGE_KEYS = {
      apiBase: "sales_api_base_url",
      authToken: "sales_auth_token",
      user: "sales_user",
      legacyLogin: "isLoggedIn",
      legacyEmail: "userEmail",
      legacyRole: "userRole",
      demoUsers: "sales_demo_users"
    };
  
    const fileOrigin = window.location.protocol === "file:";
    // Always use port 8000 for FastAPI — the frontend may be served from a different port (e.g. 3000)
    const DEFAULT_API_BASE = fileOrigin ? "http://localhost:8000" : window.location.origin;
  
    function safeJsonParse(value, fallback) {
      if (!value) {
        return fallback;
      }
  
      try {
        return JSON.parse(value);
      } catch (error) {
        return fallback;
      }
    }
  
    function getApiBase() {
      return (localStorage.getItem(STORAGE_KEYS.apiBase) || DEFAULT_API_BASE).trim();
    }
  
    function setApiBase(url) {
      const clean = (url || "").trim().replace(/\/+$/, "");
  
      if (!clean) {
        localStorage.removeItem(STORAGE_KEYS.apiBase);
        return "";
      }
  
      localStorage.setItem(STORAGE_KEYS.apiBase, clean);
      return clean;
    }
  
    function hasConfiguredBackend() {
      const base = getApiBase();
      // Connected if a valid base URL is set (not the placeholder)
      return Boolean(base) && !base.includes("your-fastapi-server.example.com");
    }
  
    function buildApiUrl(path, params) {
      const base = getApiBase().replace(/\/+$/, "");
      const cleanedPath = String(path || "").replace(/^\/+/, "");
      const url = new URL(cleanedPath, `${base}/`);
  
      if (params && typeof params === "object") {
        Object.entries(params).forEach(([key, value]) => {
          if (value === undefined || value === null || value === "" || value === "All") {
            return;
          }
  
          url.searchParams.set(key, value);
        });
      }
  
      return url.toString();
    }
  
    async function request(path, options) {
      const config = options || {};
      const headers = new Headers(config.headers || {});
      const token = localStorage.getItem(STORAGE_KEYS.authToken);
  
      if (!headers.has("Accept")) {
        headers.set("Accept", "application/json");
      }
  
      if (token && config.auth !== false) {
        headers.set("Authorization", `Bearer ${token}`);
      }
  
      let body = config.body;
  
      if (body && !(body instanceof FormData) && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
  
      if (headers.get("Content-Type") === "application/json" && body && typeof body !== "string") {
        body = JSON.stringify(body);
      }
  
      let response;
  
      try {
        response = await fetch(buildApiUrl(path, config.params), {
          method: config.method || "GET",
          headers,
          body
        });
      } catch (error) {
        throw new Error("Could not reach the backend server.");
      }
  
      const contentType = response.headers.get("content-type") || "";
      let payload = null;
  
      if (response.status !== 204) {
        if (contentType.includes("application/json")) {
          payload = await response.json();
        } else {
          payload = await response.text();
        }
      }
  
      if (!response.ok) {
        const message =
          (payload && payload.detail) ||
          (payload && payload.message) ||
          (typeof payload === "string" && payload) ||
          `Request failed with status ${response.status}.`;
        const error = new Error(message);
        error.status = response.status;
        error.payload = payload;
        throw error;
      }
  
      return payload;
    }
  
    function deriveUserFromLegacyState() {
      if (localStorage.getItem(STORAGE_KEYS.legacyLogin) !== "true") {
        return null;
      }
  
      const email = localStorage.getItem(STORAGE_KEYS.legacyEmail) || "admin@sales.com";
      const role = localStorage.getItem(STORAGE_KEYS.legacyRole) || "Admin";
      return {
        email,
        role,
        name: email.split("@")[0].replace(/[._-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
      };
    }
  
    function getUser() {
      return safeJsonParse(localStorage.getItem(STORAGE_KEYS.user), deriveUserFromLegacyState());
    }
  
    function setSession(payload) {
      const token = payload.accessToken || payload.access_token || payload.token || "demo-session";
      const user = payload.user || {};
      localStorage.setItem(STORAGE_KEYS.authToken, token);
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user));
      localStorage.setItem(STORAGE_KEYS.legacyLogin, "true");
      localStorage.setItem(STORAGE_KEYS.legacyEmail, user.email || "");
      localStorage.setItem(STORAGE_KEYS.legacyRole, user.role || "Viewer");
    }
  
    function clearSession() {
      localStorage.removeItem(STORAGE_KEYS.authToken);
      localStorage.removeItem(STORAGE_KEYS.user);
      localStorage.removeItem(STORAGE_KEYS.legacyLogin);
      localStorage.removeItem(STORAGE_KEYS.legacyEmail);
      localStorage.removeItem(STORAGE_KEYS.legacyRole);
    }
  
    function isAuthenticated() {
      return Boolean(localStorage.getItem(STORAGE_KEYS.authToken) || deriveUserFromLegacyState());
    }
  
    function signOut() {
      clearSession();
      window.location.href = "login.html";
    }
  
    function getDemoUsers() {
      const stored = safeJsonParse(localStorage.getItem(STORAGE_KEYS.demoUsers), []);
      const seeded = [
        {
          name: "Sales Admin",
          email: "admin@sales.com",
          password: "Admin@1234",
          role: "Admin"
        }
      ];
  
      const merged = [...seeded];
      stored.forEach((user) => {
        if (!merged.find((entry) => entry.email.toLowerCase() === user.email.toLowerCase())) {
          merged.push(user);
        }
      });
      return merged;
    }
  
    function saveDemoUsers(users) {
      localStorage.setItem(STORAGE_KEYS.demoUsers, JSON.stringify(users));
    }
  
    function formatCurrency(value) {
      const number = Number(value || 0);
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
      }).format(number);
    }
  
    function formatCompactCurrency(value) {
      const number = Number(value || 0);
      return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        notation: "compact",
        maximumFractionDigits: 1
      }).format(number);
    }
  
    function formatPercent(value) {
      return `${Number(value || 0).toFixed(1)}%`;
    }
  
    function formatDateTime(value) {
      if (!value) {
        return "Not available";
      }
  
      const date = new Date(value);
  
      if (Number.isNaN(date.getTime())) {
        return String(value);
      }
  
      return new Intl.DateTimeFormat("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit"
      }).format(date);
    }
  
    function escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }
  
    function showToast(message, type) {
      const kind = type || "info";
      let stack = document.getElementById("toastStack");
  
      if (!stack) {
        stack = document.createElement("div");
        stack.id = "toastStack";
        stack.className = "toast-stack";
        document.body.appendChild(stack);
      }
  
      const toast = document.createElement("div");
      toast.className = `toast ${kind}`;
      toast.textContent = message;
      stack.appendChild(toast);
  
      window.setTimeout(() => {
        toast.remove();
      }, 4200);
    }
  
    /* ═══════════════════════════════════════════════════════════════
       THEME TOGGLE — Dark (default) ↔ Light
    ═══════════════════════════════════════════════════════════════ */
    const THEME_KEY = "zc_theme";
  
    function getTheme() {
      return localStorage.getItem(THEME_KEY) || "dark";
    }
  
    function applyTheme(theme) {
      if (theme === "light") {
        document.documentElement.setAttribute("data-theme", "light");
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
      // update toggle label if it exists
      const label = document.getElementById("themeToggleLabel");
      if (label) label.textContent = theme === "light" ? "Light" : "Dark";
    }
  
    function toggleTheme() {
      const next = getTheme() === "dark" ? "light" : "dark";
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
    }
  
    function injectThemeToggle() {
      // Only inject once and only when a .nav-links exists
      const navLinks = document.querySelector(".nav-links");
      if (!navLinks || document.getElementById("themeToggleBtn")) return;
  
      const btn = document.createElement("button");
      btn.id = "themeToggleBtn";
      btn.title = "Toggle light / dark theme";
      btn.setAttribute("aria-label", "Toggle theme");
      btn.className = "theme-toggle-wrap";
      btn.onclick = toggleTheme;
  
      btn.innerHTML = `
        <span class="theme-toggle-label" id="themeToggleLabel">Dark</span>
        <div class="theme-toggle-track">
          <div class="theme-toggle-knob">
            <!-- moon icon (dark mode) -->
            <svg class="theme-icon-moon" xmlns="http://www.w3.org/2000/svg"
                 width="8" height="8" viewBox="0 0 24 24" fill="white"
                 stroke="none">
              <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/>
            </svg>
            <!-- sun icon (light mode) -->
            <svg class="theme-icon-sun" xmlns="http://www.w3.org/2000/svg"
                 width="8" height="8" viewBox="0 0 24 24" fill="none"
                 stroke="white" stroke-width="2.5"
                 stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          </div>
        </div>`;
  
      // Insert before the first child of nav-links (leftmost position inside it)
      navLinks.insertBefore(btn, navLinks.firstChild);
  
      // Update label to match current theme
      applyTheme(getTheme());
    }
  
    // Apply theme immediately (before paint) to avoid flash
    applyTheme(getTheme());
  
    // Inject toggle after DOM is ready
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", injectThemeToggle);
    } else {
      injectThemeToggle();
    }
  
    window.App = {
      STORAGE_KEYS,
      DEFAULT_API_BASE,
      buildApiUrl,
      clearSession,
      escapeHtml,
      formatCompactCurrency,
      formatCurrency,
      formatDateTime,
      formatPercent,
      getApiBase,
      getDemoUsers,
      getTheme,
      getUser,
      hasConfiguredBackend,
      isAuthenticated,
      request,
      saveDemoUsers,
      setApiBase,
      setSession,
      showToast,
      signOut,
      toggleTheme
    };
  })();
