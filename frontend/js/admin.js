const API_BASE = 'https://back.actforiran.org';
const TOKEN_KEY = 'actforiran_admin_token';

const loginView = document.getElementById('loginView');
const dashboardView = document.getElementById('dashboardView');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const adminMeta = document.getElementById('adminMeta');
const adminRole = document.getElementById('adminRole');
const logoutBtn = document.getElementById('logoutBtn');

function setView(isLoggedIn) {
  if (isLoggedIn) {
    loginView.style.display = 'none';
    dashboardView.style.display = 'grid';
    dashboardView.setAttribute('aria-hidden', 'false');
  } else {
    loginView.style.display = 'grid';
    dashboardView.style.display = 'none';
    dashboardView.setAttribute('aria-hidden', 'true');
  }
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function fetchMe() {
  const token = getToken();
  if (!token) return null;

  const response = await fetch(`${API_BASE}/api/v1/admin/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (!response.ok) {
    return null;
  }
  return response.json();
}

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  loginError.textContent = '';

  const email = document.getElementById('adminEmail').value.trim();
  const password = document.getElementById('adminPassword').value;

  const response = await fetch(`${API_BASE}/api/v1/admin/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    loginError.textContent = 'ورود نامعتبر است. ایمیل یا رمز عبور درست نیست.';
    return;
  }

  const data = await response.json();
  setToken(data.access_token);
  await hydrateDashboard();
});

logoutBtn.addEventListener('click', () => {
  clearToken();
  setView(false);
});

async function hydrateDashboard() {
  const me = await fetchMe();
  if (!me) {
    clearToken();
    setView(false);
    return;
  }

  adminMeta.textContent = `خوش آمدید، ${me.email}`;
  adminRole.textContent = me.role === 'super_admin' ? 'مدیر ارشد' : 'مدیر';
  setView(true);
}

(async function init() {
  await hydrateDashboard();
})();
