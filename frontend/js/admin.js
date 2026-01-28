/**
 * ActForIran - Admin Panel JavaScript
 * Persian RTL Admin Dashboard
 */

const API_BASE = 'http://localhost:8000';

// State
let token = localStorage.getItem('adminToken');
let adminData = null;
let countries = [];
let roles = [];

// DOM Elements
const loginContainer = document.getElementById('loginContainer');
const adminLayout = document.getElementById('adminLayout');
const loginForm = document.getElementById('loginForm');
const logoutBtn = document.getElementById('logoutBtn');

// ============================================
// NOTIFICATION SYSTEM
// ============================================
function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// AUTHENTICATION
// ============================================
async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('adminToken', token);
        
        showDashboard();
        showNotification('ورود موفقیت‌آمیز', 'success');
        
    } catch (error) {
        console.error('Login error:', error);
        showNotification('ایمیل یا رمز عبور اشتباه است', 'error');
    }
}

function logout() {
    token = null;
    localStorage.removeItem('adminToken');
    showLogin();
    showNotification('خروج موفقیت‌آمیز', 'success');
}

async function checkAuth() {
    if (!token) {
        showLogin();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Invalid token');
        
        adminData = await response.json();
        showDashboard();
        
    } catch (error) {
        console.error('Auth check failed:', error);
        logout();
    }
}

function showLogin() {
    loginContainer.style.display = 'flex';
    adminLayout.classList.remove('active');
}

function showDashboard() {
    loginContainer.style.display = 'none';
    adminLayout.classList.add('active');
    
    if (adminData) {
        document.getElementById('adminEmail').textContent = adminData.email;
    }
    
    loadDashboardData();
}

// ============================================
// DASHBOARD DATA
// ============================================
async function loadDashboardData() {
    await Promise.all([
        loadStats(),
        loadCountries(),
        loadRoles(),
        loadRecipients(),
        loadTopics()
    ]);
}

async function loadStats() {
    try {
        // Load countries count
        const countriesRes = await fetch(`${API_BASE}/api/v1/countries`);
        const countriesData = await countriesRes.json();
        document.getElementById('statCountries').textContent = toPersian(countriesData.countries?.length || 0);
        
        // Load recipients count
        const recipientsRes = await fetch(`${API_BASE}/api/v1/recipients`);
        const recipientsData = await recipientsRes.json();
        document.getElementById('statRecipients').textContent = toPersian(recipientsData.recipients?.length || 0);
        
        // Load topics count
        const topicsRes = await fetch(`${API_BASE}/api/v1/topics`);
        const topicsData = await topicsRes.json();
        document.getElementById('statTopics').textContent = toPersian(topicsData.topics?.length || 0);
        
        // Emails count (placeholder)
        document.getElementById('statEmails').textContent = '۰';
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadCountries() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/countries`);
        const data = await response.json();
        countries = data.countries || [];
        
        // Populate country select in modal
        const select = document.getElementById('recipientCountry');
        select.innerHTML = '<option value="">انتخاب کنید...</option>' +
            countries.map(c => `<option value="${c.code}">${c.name}</option>`).join('');
        
        // Render countries table
        const tbody = document.getElementById('countriesTableBody');
        tbody.innerHTML = countries.map(c => `
            <tr>
                <td>${c.code}</td>
                <td>${c.name}</td>
                <td><span class="badge badge-success">فعال</span></td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

async function loadRoles() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/roles`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            // Fallback roles
            roles = [
                { id: 1, name: 'President' },
                { id: 2, name: 'Prime Minister' },
                { id: 3, name: 'Foreign Minister' },
                { id: 4, name: 'Ambassador' }
            ];
        } else {
            const data = await response.json();
            roles = data || [];
        }
        
        const select = document.getElementById('recipientRole');
        select.innerHTML = '<option value="">انتخاب کنید...</option>' +
            roles.map(r => `<option value="${r.id}">${r.name}</option>`).join('');
        
    } catch (error) {
        console.error('Error loading roles:', error);
    }
}

async function loadRecipients() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/recipients`);
        const data = await response.json();
        const recipients = data.recipients || [];
        
        const tbody = document.getElementById('recipientsTableBody');
        
        if (recipients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">گیرنده‌ای یافت نشد</td></tr>';
            return;
        }
        
        tbody.innerHTML = recipients.map(r => `
            <tr>
                <td>${r.full_name}</td>
                <td>${r.email_address}</td>
                <td>${r.display_title || '-'}</td>
                <td>${r.country_name}</td>
                <td><span class="badge badge-success">فعال</span></td>
                <td class="actions">
                    <button class="btn btn-secondary btn-sm" onclick="editRecipient(${r.id})">ویرایش</button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteRecipient(${r.id})">حذف</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading recipients:', error);
        document.getElementById('recipientsTableBody').innerHTML = 
            '<tr><td colspan="6" class="loading">خطا در بارگذاری</td></tr>';
    }
}

async function loadTopics() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/topics`);
        const data = await response.json();
        const topics = data.topics || [];
        
        const tbody = document.getElementById('topicsTableBody');
        
        if (topics.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">موضوعی یافت نشد</td></tr>';
            return;
        }
        
        tbody.innerHTML = topics.map(t => `
            <tr>
                <td>${t.display_title}</td>
                <td><code>${t.slug}</code></td>
                <td>${t.description || '-'}</td>
                <td><span class="badge badge-success">فعال</span></td>
                <td class="actions">
                    <button class="btn btn-secondary btn-sm" onclick="editTopic(${t.id})">ویرایش</button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteTopic(${t.id})">حذف</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading topics:', error);
        document.getElementById('topicsTableBody').innerHTML = 
            '<tr><td colspan="5" class="loading">خطا در بارگذاری</td></tr>';
    }
}

// ============================================
// MODAL FUNCTIONS
// ============================================
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Recipient Modal
document.getElementById('addRecipientBtn').addEventListener('click', () => {
    document.getElementById('recipientModalTitle').textContent = 'افزودن گیرنده';
    document.getElementById('recipientForm').reset();
    document.getElementById('recipientId').value = '';
    openModal('recipientModal');
});

document.getElementById('recipientForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('recipientId').value;
    const payload = {
        full_name: document.getElementById('recipientName').value,
        email_address: document.getElementById('recipientEmail').value,
        role_id: parseInt(document.getElementById('recipientRole').value),
        country_code: document.getElementById('recipientCountry').value,
        custom_title: document.getElementById('recipientTitle').value || null
    };
    
    try {
        const url = id 
            ? `${API_BASE}/api/v1/admin/recipients/${id}`
            : `${API_BASE}/api/v1/admin/recipients`;
        
        const response = await fetch(url, {
            method: id ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Operation failed');
        }
        
        closeModal('recipientModal');
        showNotification(id ? 'گیرنده ویرایش شد' : 'گیرنده اضافه شد', 'success');
        loadRecipients();
        loadStats();
        
    } catch (error) {
        console.error('Error saving recipient:', error);
        showNotification('خطا در ذخیره گیرنده', 'error');
    }
});

async function editRecipient(id) {
    // In a real app, fetch recipient data by ID
    document.getElementById('recipientModalTitle').textContent = 'ویرایش گیرنده';
    document.getElementById('recipientId').value = id;
    openModal('recipientModal');
}

async function deleteRecipient(id) {
    if (!confirm('آیا از حذف این گیرنده اطمینان دارید؟')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/recipients/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Delete failed');
        
        showNotification('گیرنده حذف شد', 'success');
        loadRecipients();
        loadStats();
        
    } catch (error) {
        console.error('Error deleting recipient:', error);
        showNotification('خطا در حذف گیرنده', 'error');
    }
}

// Topic Modal
document.getElementById('addTopicBtn').addEventListener('click', () => {
    document.getElementById('topicModalTitle').textContent = 'افزودن موضوع';
    document.getElementById('topicForm').reset();
    document.getElementById('topicId').value = '';
    openModal('topicModal');
});

document.getElementById('topicForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('topicId').value;
    const payload = {
        display_title: document.getElementById('topicTitle').value,
        slug: document.getElementById('topicSlug').value,
        description: document.getElementById('topicDescription').value || null
    };
    
    try {
        const url = id 
            ? `${API_BASE}/api/v1/admin/topics/${id}`
            : `${API_BASE}/api/v1/admin/topics`;
        
        const response = await fetch(url, {
            method: id ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Operation failed');
        }
        
        closeModal('topicModal');
        showNotification(id ? 'موضوع ویرایش شد' : 'موضوع اضافه شد', 'success');
        loadTopics();
        loadStats();
        
    } catch (error) {
        console.error('Error saving topic:', error);
        showNotification('خطا در ذخیره موضوع', 'error');
    }
});

async function editTopic(id) {
    document.getElementById('topicModalTitle').textContent = 'ویرایش موضوع';
    document.getElementById('topicId').value = id;
    openModal('topicModal');
}

async function deleteTopic(id) {
    if (!confirm('آیا از حذف این موضوع اطمینان دارید؟')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/topics/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Delete failed');
        
        showNotification('موضوع حذف شد', 'success');
        loadTopics();
        loadStats();
        
    } catch (error) {
        console.error('Error deleting topic:', error);
        showNotification('خطا در حذف موضوع', 'error');
    }
}

// ============================================
// TABS
// ============================================
document.querySelectorAll('.admin-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Update active tab
        document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Show corresponding content
        const tabName = tab.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}Tab`).classList.add('active');
    });
});

// ============================================
// UTILITY FUNCTIONS
// ============================================
function toPersian(num) {
    const persianDigits = '۰۱۲۳۴۵۶۷۸۹';
    return num.toString().replace(/[0-9]/g, w => persianDigits[+w]);
}

// ============================================
// EVENT LISTENERS
// ============================================
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    login(email, password);
});

logoutBtn.addEventListener('click', logout);

// Close modals on outside click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});
