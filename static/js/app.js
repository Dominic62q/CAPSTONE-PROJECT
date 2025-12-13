const API_BASE = "/api";

let auth = {
  token: null,
  username: null,
};

document.addEventListener("DOMContentLoaded", () => {
  loadAuthFromStorage();
  setupThemeToggle();
  setupNav();
  setupAuthForms();
  setupGroupForms();
  setupResourceForms();
  setActiveView("dashboard");
  refreshAllData();
});

/* -------------------- Helpers -------------------- */

function apiHeaders(extra = {}) {
  const headers = { "Content-Type": "application/json", ...extra };
  if (auth.token) {
    headers["Authorization"] = `Token ${auth.token}`;
  }
  return headers;
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: apiHeaders(options.headers || {}),
  });

  let data = null;
  const text = await res.text();
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const error = new Error("API error");
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

function showAlert(type, message) {
  const box = document.getElementById("alert-box");
  const inner = document.getElementById("alert-inner");

  if (!message) {
    box.classList.add("hidden");
    return;
  }

  const base =
    "rounded-lg px-4 py-3 text-sm border " +
    (type === "error"
      ? "bg-red-50 border-red-200 text-red-800 dark:bg-red-950 dark:border-red-900 dark:text-red-100"
      : "bg-green-50 border-green-200 text-green-800 dark:bg-green-950 dark:border-green-900 dark:text-green-100");

  inner.className = base;
  inner.textContent = message;
  box.classList.remove("hidden");

  setTimeout(() => {
    box.classList.add("hidden");
  }, 4000);
}

function setActiveView(view) {
  const panels = document.querySelectorAll(".view-panel");
  panels.forEach((p) => p.classList.add("hidden"));

  const active = document.getElementById(`view-${view}`);
  if (active) active.classList.remove("hidden");

  const navButtons = document.querySelectorAll(".nav-btn");
  navButtons.forEach((btn) => {
    if (btn.dataset.view === view) {
      btn.classList.add("bg-blue-600", "text-white");
      btn.classList.remove(
        "hover:bg-gray-100",
        "dark:hover:bg-gray-800",
        "text-gray-900",
        "dark:text-gray-100"
      );
    } else {
      btn.classList.remove("bg-blue-600", "text-white");
      btn.classList.add(
        "hover:bg-gray-100",
        "dark:hover:bg-gray-800",
        "text-gray-900",
        "dark:text-gray-100"
      );
    }
  });

  const title = document.getElementById("view-title");
  const subtitle = document.getElementById("view-subtitle");

  switch (view) {
    case "dashboard":
      title.textContent = "Dashboard";
      subtitle.textContent = "Overview of your subjects and activity.";
      break;
    case "groups":
      title.textContent = "Study Groups";
      subtitle.textContent = "Join or create groups to collaborate.";
      break;
    case "resources":
      title.textContent = "Resources";
      subtitle.textContent = "Links and materials shared in your groups.";
      break;
    case "matches":
      title.textContent = "Study Matches";
      subtitle.textContent =
        "Users who share subjects of interest with you.";
      break;
    case "auth":
      title.textContent = "Login / Register";
      subtitle.textContent = "Manage your StudyHub account.";
      break;
    default:
      break;
  }
}

/* -------------------- Theme -------------------- */

function setupThemeToggle() {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const html = document.documentElement;
    const isDark = html.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
  });
}

/* -------------------- Auth state -------------------- */

function loadAuthFromStorage() {
  const token = localStorage.getItem("token");
  const username = localStorage.getItem("username");
  if (token && username) {
    auth.token = token;
    auth.username = username;
  }
  updateAuthUI();
}

function updateAuthUI() {
  const authInfo = document.getElementById("auth-info");
  const authButtons = document.getElementById("auth-buttons");
  const userPill = document.getElementById("user-pill");

  if (!authInfo || !authButtons) return;

  authButtons.innerHTML = "";

  if (auth.token && auth.username) {
    authInfo.textContent = "You are logged in.";
    const span = document.createElement("span");
    span.textContent = `Hi, ${auth.username}`;
    userPill.textContent = `Hi, ${auth.username}`;

    const logoutBtn = document.createElement("button");
    logoutBtn.textContent = "Logout";
    logoutBtn.className =
      "px-3 py-1.5 rounded-lg text-xs border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800";
    logoutBtn.addEventListener("click", handleLogout);

    authButtons.appendChild(logoutBtn);

    const createGroupBtn = document.getElementById("btn-open-create-group");
    const createResBtn = document.getElementById("btn-open-create-resource");
    if (createGroupBtn) createGroupBtn.classList.remove("hidden");
    if (createResBtn) createResBtn.classList.remove("hidden");
  } else {
    authInfo.textContent = "You are not logged in.";
    userPill.textContent = "";

    const loginBtn = document.createElement("button");
    loginBtn.textContent = "Login";
    loginBtn.className =
      "px-3 py-1.5 rounded-lg text-xs border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800";
    loginBtn.addEventListener("click", () => {
      setActiveView("auth");
    });

    const regBtn = document.createElement("button");
    regBtn.textContent = "Register";
    regBtn.className =
      "px-3 py-1.5 rounded-lg text-xs bg-blue-600 text-white hover:bg-blue-700";
    regBtn.addEventListener("click", () => {
      setActiveView("auth");
    });

    authButtons.appendChild(loginBtn);
    authButtons.appendChild(regBtn);

    const createGroupBtn = document.getElementById("btn-open-create-group");
    const createResBtn = document.getElementById("btn-open-create-resource");
    if (createGroupBtn) createGroupBtn.classList.add("hidden");
    if (createResBtn) createResBtn.classList.add("hidden");
  }
}

/* -------------------- Navigation -------------------- */

function setupNav() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const view = btn.dataset.view;
      setActiveView(view);
      if (view === "dashboard") {
        loadSubjects();
      } else if (view === "groups") {
        loadGroups();
      } else if (view === "resources") {
        loadResources();
      } else if (view === "matches") {
        loadMatches();
      }
    });
  });
}

/* -------------------- Auth Forms -------------------- */

function setupAuthForms() {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("login-username").value.trim();
      const password = document.getElementById("login-password").value.trim();
      if (!username || !password) {
        showAlert("error", "Please fill in username and password.");
        return;
      }
      try {
        const data = await apiFetch("/login/", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        auth.token = data.token;
        auth.username = data.username;
        localStorage.setItem("token", data.token);
        localStorage.setItem("username", data.username);
        updateAuthUI();
        showAlert("success", "Logged in successfully.");
        setActiveView("dashboard");
        refreshAllData();
      } catch (err) {
        showAlert(
          "error",
          (err.data && (err.data.error || err.data.detail)) ||
            "Invalid credentials."
        );
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("reg-username").value.trim();
      const email = document.getElementById("reg-email").value.trim();
      const password = document.getElementById("reg-password").value.trim();
      const password2 = document
        .getElementById("reg-password2")
        .value.trim();

      if (!username || !email || !password || !password2) {
        showAlert("error", "Please fill in all registration fields.");
        return;
      }

      try {
        await apiFetch("/register/", {
          method: "POST",
          body: JSON.stringify({ username, email, password, password2 }),
        });
        showAlert(
          "success",
          "Registration successful. You can now log in."
        );
        setActiveView("auth");
      } catch (err) {
        const data = err.data || {};
        showAlert("error", JSON.stringify(data));
      }
    });
  }
}

async function handleLogout() {
  try {
    if (auth.token) {
      await apiFetch("/logout/", { method: "POST" });
    }
  } catch (err) {
    // ignore logout errors
  } finally {
    auth.token = null;
    auth.username = null;
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    updateAuthUI();
    showAlert("success", "Logged out.");
    setActiveView("dashboard");
    refreshAllData();
  }
}

/* -------------------- Groups -------------------- */

function setupGroupForms() {
  const btnOpen = document.getElementById("btn-open-create-group");
  const btnCancel = document.getElementById("btn-cancel-create-group");
  const btnCancel2 = document.getElementById("btn-cancel-create-group-2");
  const form = document.getElementById("create-group-form");

  if (btnOpen && form) {
    btnOpen.addEventListener("click", () => {
      form.classList.remove("hidden");
    });
  }

  const closeForm = () => form && form.classList.add("hidden");

  if (btnCancel) btnCancel.addEventListener("click", closeForm);
  if (btnCancel2) btnCancel2.addEventListener("click", closeForm);

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = document.getElementById("group-name").value.trim();
      const description = document
        .getElementById("group-description")
        .value.trim();
      if (!auth.token) {
        showAlert("error", "You must be logged in to create a group.");
        return;
      }
      if (!name) {
        showAlert("error", "Group name is required.");
        return;
      }
      try {
        await apiFetch("/groups/", {
          method: "POST",
          body: JSON.stringify({ name, description }),
        });
        showAlert("success", "Group created successfully.");
        form.reset();
        form.classList.add("hidden");
        loadGroups();
      } catch (err) {
        showAlert("error", JSON.stringify(err.data || {}));
      }
    });
  }
}

async function loadGroups() {
  try {
    const data = await apiFetch("/groups/");
    const groups = Array.isArray(data) ? data : data.results || [];
    renderGroups(groups);
    populateGroupsForResourceForm(groups);
  } catch (err) {
    showAlert("error", "Could not load groups.");
  }
}

function renderGroups(groups) {
  const container = document.getElementById("groups-list");
  const detail = document.getElementById("group-detail-content");
  if (!container) return;

  container.innerHTML = "";
  if (detail) {
    detail.innerHTML =
      "<p class='text-sm text-gray-500 dark:text-gray-400'>Select a group from the list to see details here.</p>";
  }

  if (!groups.length) {
    container.innerHTML =
      "<p class='text-sm text-gray-500 dark:text-gray-400'>No groups yet. Create one to get started.</p>";
    return;
  }

  groups.forEach((g) => {
    const card = document.createElement("div");
    card.className =
      "p-4 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl flex justify-between gap-3";
    card.innerHTML = `
      <div class="text-sm">
        <h4 class="font-semibold">${escapeHtml(g.name)}</h4>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          ${escapeHtml(g.description || "No description")}
        </p>
        <p class="text-[11px] text-gray-400 dark:text-gray-500 mt-1">
          Owner: ${escapeHtml(g.created_by_username || "-")}
        </p>
      </div>
      <div class="flex flex-col gap-2 items-end text-xs">
        <button data-id="${g.id}" class="btn-group-view px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800">
          View
        </button>
        ${
          auth.token
            ? `<button data-id="${g.id}" class="btn-group-join px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700">
                 Join
               </button>`
            : ""
        }
      </div>
    `;
    container.appendChild(card);
  });

  container.addEventListener("click", (e) => {
    const viewBtn = e.target.closest(".btn-group-view");
    const joinBtn = e.target.closest(".btn-group-join");
    const leaveBtn = e.target.closest(".btn-group-leave");

    if (viewBtn) {
      const id = viewBtn.dataset.id;
      loadGroupDetail(id);
    } else if (joinBtn) {
      const id = joinBtn.dataset.id;
      joinGroup(id);
    } else if (leaveBtn) {
      const id = leaveBtn.dataset.id;
      leaveGroup(id);
    }
  });
}

async function loadGroupDetail(id) {
  try {
    const g = await apiFetch(`/groups/${id}/`);
    const detail = document.getElementById("group-detail-content");
    if (!detail) return;

    const members = (g.members || []).map((m) => `<span class="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs">${escapeHtml(m)}</span>`).join(" ");
    const subjects = (g.subjects || [])
      .map(
        (s) =>
          `<span class="px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950 text-[11px] text-blue-700 dark:text-blue-200">${escapeHtml(
            s.name
          )}</span>`
      )
      .join(" ");
    const resources = (g.resources || [])
      .map(
        (r) =>
          `<li class="text-xs">
             <a href="${escapeAttr(r.link)}" target="_blank" class="text-blue-600 dark:text-blue-300 underline">${escapeHtml(
            r.title
          )}</a>
             <span class="text-gray-400 dark:text-gray-500"> · by ${escapeHtml(
               r.uploaded_by_username || "-"
             )}</span>
           </li>`
      )
      .join("");

    detail.innerHTML = `
      <div class="space-y-3 text-sm">
        <div>
          <h4 class="font-semibold text-base">${escapeHtml(g.name)}</h4>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${escapeHtml(
            g.description || "No description"
          )}</p>
        </div>
        <div>
          <p class="text-[11px] text-gray-400 dark:text-gray-500 mb-1">Subjects</p>
          <div class="flex flex-wrap gap-1">${subjects || "<span class='text-xs text-gray-400'>None</span>"}</div>
        </div>
        <div>
          <p class="text-[11px] text-gray-400 dark:text-gray-500 mb-1">Members</p>
          <div class="flex flex-wrap gap-1">${members || "<span class='text-xs text-gray-400'>No members yet</span>"}</div>
        </div>
        <div>
          <p class="text-[11px] text-gray-400 dark:text-gray-500 mb-1">Resources</p>
          <ul class="space-y-1">
            ${resources || "<li class='text-xs text-gray-400'>No resources yet</li>"}
          </ul>
        </div>
        ${
          auth.token
            ? `<div class="pt-2">
                 <button data-id="${g.id}" class="btn-group-join px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 text-xs mr-2">
                   Join
                 </button>
                 <button data-id="${g.id}" class="btn-group-leave px-3 py-1.5 rounded-lg border border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-950 text-xs">
                   Leave
                 </button>
               </div>`
            : ""
        }
      </div>
    `;
  } catch (err) {
    showAlert("error", "Could not load group details.");
  }
}

async function joinGroup(id) {
  if (!auth.token) {
    showAlert("error", "You must be logged in to join a group.");
    return;
  }
  try {
    await apiFetch(`/groups/${id}/join/`, { method: "POST" });
    showAlert("success", "Joined group.");
    loadGroupDetail(id);
    loadGroups();
  } catch (err) {
    showAlert(
      "error",
      (err.data && (err.data.error || err.data.detail)) ||
        "Could not join group."
    );
  }
}

async function leaveGroup(id) {
  if (!auth.token) {
    showAlert("error", "You must be logged in to leave a group.");
    return;
  }
  try {
    await apiFetch(`/groups/${id}/leave/`, { method: "POST" });
    showAlert("success", "Left group.");
    loadGroupDetail(id);
    loadGroups();
  } catch (err) {
    showAlert(
      "error",
      (err.data && (err.data.error || err.data.detail)) ||
        "Could not leave group."
    );
  }
}

/* -------------------- Subjects (Dashboard) -------------------- */

async function loadSubjects() {
  try {
    const data = await apiFetch("/subjects/");
    const subs = Array.isArray(data) ? data : data.results || [];
    const container = document.getElementById("subjects-list");
    if (!container) return;
    container.innerHTML = "";

    if (!subs.length) {
      container.innerHTML =
        "<p class='text-sm text-gray-500 dark:text-gray-400'>No subjects found.</p>";
      return;
    }

    subs.forEach((s) => {
      const card = document.createElement("div");
      card.className =
        "p-3 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl text-sm";
      card.innerHTML = `
        <p class="font-semibold">${escapeHtml(s.name)}</p>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    showAlert("error", "Could not load subjects.");
  }
}

/* -------------------- Resources -------------------- */

function setupResourceForms() {
  const btnOpen = document.getElementById("btn-open-create-resource");
  const btnCancel = document.getElementById("btn-cancel-create-resource");
  const btnCancel2 = document.getElementById("btn-cancel-create-resource-2");
  const form = document.getElementById("create-resource-form");

  if (btnOpen && form) {
    btnOpen.addEventListener("click", () => {
      form.classList.remove("hidden");
    });
  }

  const closeForm = () => form && form.classList.add("hidden");
  if (btnCancel) btnCancel.addEventListener("click", closeForm);
  if (btnCancel2) btnCancel2.addEventListener("click", closeForm);

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!auth.token) {
        showAlert("error", "You must be logged in to share a resource.");
        return;
      }
      const title = document.getElementById("res-title").value.trim();
      const link = document.getElementById("res-link").value.trim();
      const group = document.getElementById("res-group").value;

      if (!title || !link || !group) {
        showAlert("error", "Please fill in all fields.");
        return;
      }

      try {
        await apiFetch("/resources/", {
          method: "POST",
          body: JSON.stringify({ title, link, group }),
        });
        showAlert("success", "Resource shared.");
        form.reset();
        form.classList.add("hidden");
        loadResources();
      } catch (err) {
        showAlert("error", JSON.stringify(err.data || {}));
      }
    });
  }
}

function populateGroupsForResourceForm(groups) {
  const select = document.getElementById("res-group");
  if (!select) return;
  select.innerHTML = "";
  groups.forEach((g) => {
    const opt = document.createElement("option");
    opt.value = g.id;
    opt.textContent = g.name;
    select.appendChild(opt);
  });
}

async function loadResources() {
  try {
    const data = await apiFetch("/resources/");
    const resources = Array.isArray(data) ? data : data.results || [];
    const container = document.getElementById("resources-list");
    if (!container) return;

    container.innerHTML = "";

    if (!resources.length) {
      container.innerHTML =
        "<p class='text-sm text-gray-500 dark:text-gray-400'>No resources yet.</p>";
      return;
    }

    resources.forEach((r) => {
      const card = document.createElement("div");
      card.className =
        "p-3 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl text-sm flex justify-between gap-3";
      card.innerHTML = `
        <div>
          <a href="${escapeAttr(r.link)}" target="_blank"
             class="text-blue-600 dark:text-blue-300 underline font-medium">
            ${escapeHtml(r.title)}
          </a>
          <p class="text-[11px] text-gray-500 dark:text-gray-400 mt-1">
            Group ID: ${r.group} · By ${escapeHtml(
        r.uploaded_by_username || "-"
      )}
          </p>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    showAlert("error", "Could not load resources.");
  }
}

/* -------------------- Matches -------------------- */

async function loadMatches() {
  if (!auth.token) {
    const container = document.getElementById("matches-list");
    if (container) {
      container.innerHTML =
        "<p class='text-sm text-gray-500 dark:text-gray-400'>You must be logged in to see matches.</p>";
    }
    return;
  }

  try {
    const data = await apiFetch("/matches/");
    const matches = Array.isArray(data) ? data : data.results || [];
    const container = document.getElementById("matches-list");
    if (!container) return;

    container.innerHTML = "";

    if (!matches.length) {
      container.innerHTML =
        "<p class='text-sm text-gray-500 dark:text-gray-400'>No matches yet. Add subjects to your profile first.</p>";
      return;
    }

    matches.forEach((m) => {
      const subjects = (m.subjects || [])
        .map(
          (s) =>
            `<span class="px-2 py-0.5 rounded-full bg-purple-50 dark:bg-purple-950 text-[11px] text-purple-700 dark:text-purple-200">${escapeHtml(
              s.name
            )}</span>`
        )
        .join(" ");

      const card = document.createElement("div");
      card.className =
        "p-3 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-xl text-sm flex justify-between gap-3";
      card.innerHTML = `
        <div>
          <p class="font-semibold">${escapeHtml(m.username)}</p>
          <div class="mt-1 flex flex-wrap gap-1">
            ${subjects}
          </div>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    showAlert("error", "Could not load matches.");
  }
}

/* -------------------- Refresh helpers -------------------- */

function refreshAllData() {
  loadSubjects();
  loadGroups();
  loadResources();
  if (auth.token) {
    loadMatches();
  }
}

/* -------------------- Small utils -------------------- */

function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(str) {
  if (str == null) return "";
  return String(str).replace(/"/g, "&quot;");
}
