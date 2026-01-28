const API_BASE = 'http://localhost:8000';
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

// Persian translations
const persianTexts = {
  'admin': 'مدیر',
  'super_admin': 'مدیر ارشد',
  'approved': 'تأیید شده',
  'pending': 'در انتظار تأیید',
  'rejected': 'رد شده',
  'connected': 'متصل',
  'edit': 'ویرایش',
  'delete': 'حذف',
  'approve': 'تأیید',
  'reject': 'رد'
};

function translateText(text) {
  return persianTexts[text] || text;
}

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: ${type === 'error' ? 'var(--error)' : type === 'success' ? 'var(--success)' : 'var(--accent)'};
    color: white;
    border-radius: 12px;
    font-weight: 600;
    z-index: 1000;
    animation: slideInLeft 0.3s ease;
    box-shadow: var(--shadow);
  `;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease forwards';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Add loading state to buttons
function setButtonLoading(button, isLoading) {
  if (isLoading) {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = '<span>در حال پردازش...</span>';
  } else {
    button.disabled = false;
    button.innerHTML = button.dataset.originalText || button.innerHTML;
  }
}

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

  try {
    const response = await fetch(`${API_BASE}/api/v1/admin/auth/me`, {
      headers: authHeaders()
    });

    if (!response.ok) {
      return null;
    }
    return response.json();
  } catch (error) {
    console.error('Error fetching user info:', error);
    return null;
  }
}

async function apiRequest(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
        ...(options.headers || {})
      }
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }
    if (response.status === 204) return null;
    return response.json();
  } catch (error) {
    console.error('API Request error:', error);
    throw error;
  }
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
  recipientRole.innerHTML = roles.map(role => 
    `<option value="${role.id}">${translateText(role.name)}</option>`
  ).join('');
  recipientCountry.innerHTML = countries.map(country => 
    `<option value="${country.code}">${country.name}</option>`
  ).join('');
}

function renderRecipientsTable() {
  recipientsTable.innerHTML = recipients.map(recipient => {
    const statusClass = `status ${recipient.approval_status}`;
    const approveActions = currentRole === 'super_admin'
      ? `<button data-action="approve" data-id="${recipient.id}">${translateText('approve')}</button>
         <button data-action="reject" data-id="${recipient.id}">${translateText('reject')}</button>`
      : '';
    return `
      <tr>
        <td>${recipient.full_name}</td>
        <td>${recipient.email_address}</td>
        <td>${recipient.custom_title || translateText(recipient.role_name)}</td>
        <td>${recipient.country_name}</td>
        <td><span class="${statusClass}">${translateText(recipient.approval_status)}</span></td>
        <td>
          <button data-action="edit" data-id="${recipient.id}">${translateText('edit')}</button>
          <button data-action="delete" data-id="${recipient.id}">${translateText('delete')}</button>
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
      ? `<button data-action="approve" data-id="${topic.id}">${translateText('approve')}</button>
         <button data-action="reject" data-id="${topic.id}">${translateText('reject')}</button>`
      : '';
    return `
      <tr>
        <td>${topic.display_title}</td>
        <td>${topic.slug}</td>
        <td><span class="${statusClass}">${translateText(topic.approval_status)}</span></td>
        <td>
          <button data-action="edit" data-id="${topic.id}">${translateText('edit')}</button>
          <button data-action="delete" data-id="${topic.id}">${translateText('delete')}</button>
          ${approveActions}
        </td>
      </tr>
    `;
  }).join('');
}

// Event handlers and initialization
loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  loginError.textContent = '';
  
  const button = event.target.querySelector('button[type="submit"]');
  setButtonLoading(button, true);

  try {
    const email = document.getElementById('adminEmail').value.trim();
    const password = document.getElementById('adminPassword').value;

    const response = await fetch(`${API_BASE}/api/v1/admin/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      loginError.textContent = 'اطلاعات ورود نامعتبر است. لطفاً اطلاعات خود را بررسی کنید.';
      return;
    }

    const data = await response.json();
    setToken(data.access_token);
    await hydrateDashboard();
    showNotification('با موفقیت وارد شدید.', 'success');
  } catch (error) {
    console.error('Login error:', error);
    loginError.textContent = 'خطا در ورود. لطفاً دوباره تلاش کنید.';
  } finally {
    setButtonLoading(button, false);
  }
});

logoutBtn.addEventListener('click', () => {
  clearToken();
  setView(false);
  showNotification('با موفقیت خارج شدید.', 'success');
});

// Navigation handlers
document.querySelectorAll('.nav-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    const view = pill.dataset.view;
    setActiveView(view);
    
    // Load data based on view
    switch(view) {
      case 'recipients':
        loadRecipients();
        break;
      case 'topics':
        loadTopics();
        break;
    }
  });
});

// Reset form handlers
recipientReset.addEventListener('click', resetRecipientForm);
topicReset.addEventListener('click', resetTopicForm);

// Form submission handlers
recipientForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  
  const button = recipientSubmit;
  setButtonLoading(button, true);
  
  try {
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
      showNotification('گیرنده با موفقیت بروزرسانی شد.', 'success');
    } else {
      await apiRequest('/api/v1/admin/recipients', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      showNotification('گیرنده جدید با موفقیت اضافه شد.', 'success');
    }

    resetRecipientForm();
    await loadRecipients();
  } catch (error) {
    console.error('Recipient form error:', error);
    showNotification('خطا در ذخیره گیرنده.', 'error');
  } finally {
    setButtonLoading(button, false);
  }
});

topicForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  
  const button = topicSubmit;
  setButtonLoading(button, true);
  
  try {
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
      showNotification('موضوع با موفقیت بروزرسانی شد.', 'success');
    } else {
      await apiRequest('/api/v1/admin/topics', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      showNotification('موضوع جدید با موفقیت اضافه شد.', 'success');
    }

    resetTopicForm();
    await loadTopics();
  } catch (error) {
    console.error('Topic form error:', error);
    showNotification('خطا در ذخیره موضوع.', 'error');
  } finally {
    setButtonLoading(button, false);
  }
});

// Table action handlers
recipientsTable.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  
  const id = button.dataset.id;
  const action = button.dataset.action;
  const recipient = recipients.find(item => String(item.id) === id);
  if (!recipient) return;

  setButtonLoading(button, true);
  
  try {
    switch(action) {
      case 'edit':
        recipientId.value = recipient.id;
        recipientName.value = recipient.full_name;
        recipientEmail.value = recipient.email_address;
        recipientRole.value = recipient.role_id;
        recipientTitle.value = recipient.custom_title || '';
        recipientCountry.value = recipient.country_code;
        recipientSubmit.innerHTML = '<span>بروزرسانی گیرنده</span>';
        // Scroll to form
        recipientForm.scrollIntoView({ behavior: 'smooth' });
        break;
        
      case 'delete':
        if (confirm('آیا از حذف این گیرنده اطمینان دارید؟')) {
          await apiRequest(`/api/v1/admin/recipients/${id}`, { method: 'DELETE' });
          await loadRecipients();
          showNotification('گیرنده با موفقیت حذف شد.', 'success');
        }
        break;
        
      case 'approve':
        await apiRequest(`/api/v1/admin/recipients/${id}/approve`, { method: 'POST' });
        await loadRecipients();
        showNotification('گیرنده تأیید شد.', 'success');
        break;
        
      case 'reject':
        await apiRequest(`/api/v1/admin/recipients/${id}/reject`, {
          method: 'POST',
          body: JSON.stringify({ reason: 'رد شده توسط مدیر' })
        });
        await loadRecipients();
        showNotification('گیرنده رد شد.', 'success');
        break;
    }
  } catch (error) {
    console.error('Recipient action error:', error);
    showNotification('خطا در انجام عملیات.', 'error');
  } finally {
    setButtonLoading(button, false);
  }
});

topicsTable.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  
  const id = button.dataset.id;
  const action = button.dataset.action;
  const topic = topics.find(item => String(item.id) === id);
  if (!topic) return;

  setButtonLoading(button, true);
  
  try {
    switch(action) {
      case 'edit':
        topicId.value = topic.id;
        topicSlug.value = topic.slug;
        topicTitle.value = topic.display_title;
        topicDescription.value = topic.description || '';
        topicSubmit.innerHTML = '<span>بروزرسانی موضوع</span>';
        // Scroll to form
        topicForm.scrollIntoView({ behavior: 'smooth' });
        break;
        
      case 'delete':
        if (confirm('آیا از حذف این موضوع اطمینان دارید؟')) {
          await apiRequest(`/api/v1/admin/topics/${id}`, { method: 'DELETE' });
          await loadTopics();
          showNotification('موضوع با موفقیت حذف شد.', 'success');
        }
        break;
        
      case 'approve':
        await apiRequest(`/api/v1/admin/topics/${id}/approve`, { method: 'POST' });
        await loadTopics();
        showNotification('موضوع تأیید شد.', 'success');
        break;
        
      case 'reject':
        await apiRequest(`/api/v1/admin/topics/${id}/reject`, {
          method: 'POST',
          body: JSON.stringify({ reason: 'رد شده توسط مدیر' })
        });
        await loadTopics();
        showNotification('موضوع رد شد.', 'success');
        break;
    }
  } catch (error) {
    console.error('Topic action error:', error);
    showNotification('خطا در انجام عملیات.', 'error');
  } finally {
    setButtonLoading(button, false);
  }
});

// Helper functions
function resetRecipientForm() {
  recipientId.value = '';
  recipientName.value = '';
  recipientEmail.value = '';
  recipientTitle.value = '';
  recipientRole.selectedIndex = 0;
  recipientCountry.selectedIndex = 0;
  recipientSubmit.innerHTML = '<span>ذخیره گیرنده</span>';
}

function resetTopicForm() {
  topicId.value = '';
  topicSlug.value = '';
  topicTitle.value = '';
  topicDescription.value = '';
  topicSubmit.innerHTML = '<span>ذخیره موضوع</span>';
}

// Data loading functions
async function loadRoles() {
  try {
    const data = await apiRequest('/api/v1/admin/roles');
    roles = data.roles || [];
  } catch (error) {
    console.error('Error loading roles:', error);
    showNotification('خطا در بارگذاری نقش‌ها.', 'error');
  }
}

async function loadCountries() {
  try {
    const data = await apiRequest('/api/v1/countries');
    countries = data.countries || [];
  } catch (error) {
    console.error('Error loading countries:', error);
    showNotification('خطا در بارگذاری کشورها.', 'error');
  }
}

async function loadRecipients() {
  try {
    const data = await apiRequest('/api/v1/admin/recipients');
    recipients = data.recipients || [];
    renderRecipientsTable();
  } catch (error) {
    console.error('Error loading recipients:', error);
    showNotification('خطا در بارگذاری گیرندگان.', 'error');
  }
}

async function loadTopics() {
  try {
    const data = await apiRequest('/api/v1/admin/topics');
    topics = data.topics || [];
    renderTopicsTable();
  } catch (error) {
    console.error('Error loading topics:', error);
    showNotification('خطا در بارگذاری موضوعات.', 'error');
  }
}

async function hydrateDashboard() {
  try {
    const user = await fetchMe();
    if (!user) {
      clearToken();
      setView(false);
      return;
    }

    currentRole = user.role;
    adminRole.textContent = translateText(user.role);
    adminMeta.textContent = `${user.email} - آخرین ورود: الان`;
    
    setView(true);
    
    // Load initial data
    await Promise.all([
      loadRoles(),
      loadCountries()
    ]);
    
    renderRecipientOptions();
    
    // Set default view
    setActiveView('overview');
    
  } catch (error) {
    console.error('Dashboard hydration error:', error);
    clearToken();
    setView(false);
    showNotification('خطا در بارگذاری داشبورد.', 'error');
  }
}

// Initialize the application
(async function init() {
  try {
    const token = getToken();
    if (token) {
      await hydrateDashboard();
    } else {
      setView(false);
    }
  } catch (error) {
    console.error('Initialization error:', error);
    setView(false);
  }
})();
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
