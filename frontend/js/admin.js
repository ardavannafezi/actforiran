const API_BASE = 'https://back.actforiran.org';
const TOKEN_KEY = 'actforiran_admin_token';

const loginView = document.getElementById('loginView');
const dashboardView = document.getElementById('dashboardView');
const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const adminMeta = document.getElementById('adminMeta');
const adminRole = document.getElementById('adminRole');
const logoutBtn = document.getElementById('logoutBtn');

const recipientForm = document.getElementById('recipientForm');
const recipientId = document.getElementById('recipientId');
const recipientName = document.getElementById('recipientName');
const recipientEmail = document.getElementById('recipientEmail');
const recipientRole = document.getElementById('recipientRole');
const recipientTitle = document.getElementById('recipientTitle');
const recipientCountry = document.getElementById('recipientCountry');
const recipientSubmit = document.getElementById('recipientSubmit');
const recipientReset = document.getElementById('recipientReset');
const recipientsTable = document.getElementById('recipientsTable').querySelector('tbody');

const topicForm = document.getElementById('topicForm');
const topicId = document.getElementById('topicId');
const topicSlug = document.getElementById('topicSlug');
const topicTitle = document.getElementById('topicTitle');
const topicDescription = document.getElementById('topicDescription');
const topicSubmit = document.getElementById('topicSubmit');
const topicReset = document.getElementById('topicReset');
const topicsTable = document.getElementById('topicsTable').querySelector('tbody');

let currentRole = 'admin';
let roles = [];
let countries = [];
let recipients = [];
let topics = [];

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

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` };
}

async function fetchMe() {
  const token = getToken();
  if (!token) return null;

  const response = await fetch(`${API_BASE}/api/v1/admin/auth/me`, {
    headers: authHeaders()
  });

  if (!response.ok) {
    return null;
  }
  return response.json();
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    throw new Error('Request failed');
  }
  if (response.status === 204) return null;
  return response.json();
}

function setActiveView(view) {
  document.querySelectorAll('.nav-pill').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
  document.querySelectorAll('.dashboard-view').forEach(section => {
    section.classList.toggle('active', section.id === `view-${view}`);
  });
}

function renderRecipientOptions() {
  recipientRole.innerHTML = roles.map(role => `<option value="${role.id}">${role.name}</option>`).join('');
  recipientCountry.innerHTML = countries.map(country => `<option value="${country.code}">${country.name}</option>`).join('');
}

function renderRecipientsTable() {
  recipientsTable.innerHTML = recipients.map(recipient => {
    const statusClass = `status ${recipient.approval_status}`;
    const approveActions = currentRole === 'super_admin'
      ? `<button data-action="approve" data-id="${recipient.id}">Approve</button>
         <button data-action="reject" data-id="${recipient.id}">Reject</button>`
      : '';
    return `
      <tr>
        <td>${recipient.full_name}</td>
        <td>${recipient.email_address}</td>
        <td>${recipient.custom_title || recipient.role_name}</td>
        <td>${recipient.country_name}</td>
        <td><span class="${statusClass}">${recipient.approval_status}</span></td>
        <td>
          <button data-action="edit" data-id="${recipient.id}">Edit</button>
          <button data-action="delete" data-id="${recipient.id}">Delete</button>
          ${approveActions}
        </td>
      </tr>
    `;
  }).join('');
}

function renderTopicsTable() {
  topicsTable.innerHTML = topics.map(topic => {
    const statusClass = `status ${topic.approval_status}`;
    const approveActions = currentRole === 'super_admin'
      ? `<button data-action="approve" data-id="${topic.id}">Approve</button>
         <button data-action="reject" data-id="${topic.id}">Reject</button>`
      : '';
    return `
      <tr>
        <td>${topic.display_title}</td>
        <td>${topic.slug}</td>
        <td><span class="${statusClass}">${topic.approval_status}</span></td>
        <td>
          <button data-action="edit" data-id="${topic.id}">Edit</button>
          <button data-action="delete" data-id="${topic.id}">Delete</button>
          ${approveActions}
        </td>
      </tr>
    `;
  }).join('');
}

function resetRecipientForm() {
  recipientId.value = '';
  recipientName.value = '';
  recipientEmail.value = '';
  recipientTitle.value = '';
  recipientSubmit.textContent = 'Save recipient';
}

function resetTopicForm() {
  topicId.value = '';
  topicSlug.value = '';
  topicTitle.value = '';
  topicDescription.value = '';
  topicSubmit.textContent = 'Save topic';
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
    loginError.textContent = 'Invalid login. Please check your credentials.';
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

recipientReset.addEventListener('click', resetRecipientForm);

topicReset.addEventListener('click', resetTopicForm);

recipientForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    full_name: recipientName.value.trim(),
    email_address: recipientEmail.value.trim(),
    role_id: Number(recipientRole.value),
    custom_title: recipientTitle.value.trim() || null,
    country_code: recipientCountry.value
  };

  if (recipientId.value) {
    await apiRequest(`/api/v1/admin/recipients/${recipientId.value}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  } else {
    await apiRequest('/api/v1/admin/recipients', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  resetRecipientForm();
  await loadRecipients();
});

topicForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    slug: topicSlug.value.trim(),
    display_title: topicTitle.value.trim(),
    description: topicDescription.value.trim() || null
  };

  if (topicId.value) {
    await apiRequest(`/api/v1/admin/topics/${topicId.value}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  } else {
    await apiRequest('/api/v1/admin/topics', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  resetTopicForm();
  await loadTopics();
});

recipientsTable.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  const id = button.dataset.id;
  const action = button.dataset.action;
  const recipient = recipients.find(item => String(item.id) === id);
  if (!recipient) return;

  if (action === 'edit') {
    recipientId.value = recipient.id;
    recipientName.value = recipient.full_name;
    recipientEmail.value = recipient.email_address;
    recipientRole.value = recipient.role_id;
    recipientTitle.value = recipient.custom_title || '';
    recipientCountry.value = recipient.country_code;
    recipientSubmit.textContent = 'Update recipient';
  }
  if (action === 'delete') {
    await apiRequest(`/api/v1/admin/recipients/${id}`, { method: 'DELETE' });
    await loadRecipients();
  }
  if (action === 'approve') {
    await apiRequest(`/api/v1/admin/recipients/${id}/approve`, { method: 'POST' });
    await loadRecipients();
  }
  if (action === 'reject') {
    await apiRequest(`/api/v1/admin/recipients/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason: 'Rejected by admin' })
    });
    await loadRecipients();
  }
});

topicsTable.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  const id = button.dataset.id;
  const action = button.dataset.action;
  const topic = topics.find(item => String(item.id) === id);
  if (!topic) return;

  if (action === 'edit') {
    topicId.value = topic.id;
    topicSlug.value = topic.slug;
    topicTitle.value = topic.display_title;
    topicDescription.value = topic.description || '';
    topicSubmit.textContent = 'Update topic';
  }
  if (action === 'delete') {
    await apiRequest(`/api/v1/admin/topics/${id}`, { method: 'DELETE' });
    await loadTopics();
  }
  if (action === 'approve') {
    await apiRequest(`/api/v1/admin/topics/${id}/approve`, { method: 'POST' });
    await loadTopics();
  }
  if (action === 'reject') {
    await apiRequest(`/api/v1/admin/topics/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason: 'Rejected by admin' })
    });
    await loadTopics();
  }
});

async function loadRoles() {
  roles = await apiRequest('/api/v1/admin/roles');
}

async function loadCountries() {
  const response = await fetch(`${API_BASE}/api/v1/countries`);
  const data = await response.json();
  countries = data.countries || [];
}

async function loadRecipients() {
  recipients = await apiRequest('/api/v1/admin/recipients');
  renderRecipientsTable();
}

async function loadTopics() {
  topics = await apiRequest('/api/v1/admin/topics');
  renderTopicsTable();
}

async function hydrateDashboard() {
  const me = await fetchMe();
  if (!me) {
    clearToken();
    setView(false);
    return;
  }

  adminMeta.textContent = `Welcome, ${me.email}`;
  adminRole.textContent = me.role === 'super_admin' ? 'Super Admin' : 'Admin';
  currentRole = me.role;
  setView(true);

  await Promise.all([loadRoles(), loadCountries()]);
  renderRecipientOptions();
  await Promise.all([loadRecipients(), loadTopics()]);
}

function initTabs() {
  document.querySelectorAll('.nav-pill').forEach(btn => {
    btn.addEventListener('click', () => setActiveView(btn.dataset.view));
  });
}

(async function init() {
  initTabs();
  await hydrateDashboard();
})();
