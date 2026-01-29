/**
 * ActForIran - Admin Panel JavaScript
 * Persian RTL Admin Dashboard
 */

console.log('🚀 Admin.js loaded at:', new Date().toISOString());

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://back.actforiran.org';

console.log('📡 API Base configured:', API_BASE);

// State
let token = sessionStorage.getItem('adminToken');
let adminData = null;
let countries = [];
let roles = [];
let recipientsAdmin = [];

// DOM Elements (will be set in DOMContentLoaded)
let loginContainer;
let adminLayout;
let loginForm;
let logoutBtn;

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

// Global handler for inline onclick
window.handleLogin = async function() {
    const email = document.getElementById('loginEmail')?.value;
    const password = document.getElementById('loginPassword')?.value;

    if (!email || !password) {
        alert('لطفا ایمیل و رمز عبور را وارد کنید');
        return;
    }

    await attemptLogin(email, password);
};

async function attemptLogin(email, password) {
    const url = `${API_BASE}/api/v1/admin/auth/login`;
    const loginBtn = document.getElementById('loginBtn');
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.textContent = 'در حال ورود...';
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const responseData = await response.json();

        if (response.ok) {
            token = responseData.access_token;
            sessionStorage.setItem('adminToken', token);
            showNotification('✅ Login successful', 'success');
            await checkAuth();
        } else {
            showNotification('❌ Login failed. Check your credentials.', 'error');
        }
    } catch (error) {
        console.error('💥 Error:', error);
        showNotification('💥 Network error. Please try again.', 'error');
    } finally {
        if (loginBtn) {
            loginBtn.disabled = false;
            loginBtn.textContent = loginBtn.dataset.defaultText || 'ورود';
        }
    }
}

async function login(email, password) {
    console.log('🔐 Attempting login for:', email);
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        console.log('📡 Login response status:', response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error('❌ Login error:', error);
            throw new Error(error.detail || 'Login failed');
        }
        
        const data = await response.json();
        console.log('✅ Login successful, token received');
        token = data.access_token;
        sessionStorage.setItem('adminToken', token);
        
        showDashboard();
        showNotification('ورود موفقیت‌آمیز', 'success');
        
    } catch (error) {
        console.error('💥 Login error:', error);
        showNotification(error.message || 'ایمیل یا رمز عبور اشتباه است', 'error');
    }
}

function logout() {
    token = null;
    sessionStorage.removeItem('adminToken');
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
    console.log('📊 Showing dashboard');
    loginContainer.style.display = 'none';
    adminLayout.classList.add('active');
    
    if (adminData) {
        document.getElementById('adminEmail').textContent = adminData.email;
        
        // Hide admins tab for non-super-admins
        const adminsTab = document.querySelector('[data-tab="admins"]');
        if (adminsTab) {
            if (adminData.role === 'super_admin') {
                adminsTab.style.display = 'block';
            } else {
                adminsTab.style.display = 'none';
            }
        }
    }
    
    loadDashboardData();
}

// ============================================
// DASHBOARD DATA
// ============================================
async function loadDashboardData() {
    console.log('📥 Loading dashboard data');
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
        const token = sessionStorage.getItem('adminToken');
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
        
        if (token) {
            const overviewRes = await fetch(`${API_BASE}/api/v1/admin/analytics/overview`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (overviewRes.ok) {
                const overview = await overviewRes.json();
                document.getElementById('statEmails').textContent = toPersian(overview.total_emails || 0);
            } else {
                document.getElementById('statEmails').textContent = '۰';
            }
        } else {
            document.getElementById('statEmails').textContent = '۰';
        }
        
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
            countries.map(c => `<option value="${c.code}">${c.flag || ''} ${c.name_persian || c.name}</option>`).join('');
        
        // Render countries table
        const tbody = document.getElementById('countriesTableBody');
        tbody.innerHTML = countries.map(c => `
            <tr>
                <td>${c.code}</td>
                <td>${c.name}</td>
                <td>${c.name_persian || '-'}</td>
                <td>${c.flag || '-'}</td>
                <td><span class="badge ${c.is_active ? 'badge-success' : 'badge-error'}">${c.is_active ? 'فعال' : 'غیرفعال'}</span></td>
                <td>
                    <button class="btn-icon" onclick="editCountry('${c.code}', '${c.name}', '${c.name_persian || ''}', '${c.flag || ''}', ${c.is_active})" title="ویرایش">✏️</button>
                    <button class="btn-icon" onclick="deleteCountry('${c.code}')" title="حذف">🗑️</button>
                </td>
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
        const response = await fetch(`${API_BASE}/api/v1/admin/recipients`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const recipients = await response.json();
        recipientsAdmin = Array.isArray(recipients) ? recipients : [];
        
        const tbody = document.getElementById('recipientsTableBody');
        
        if (recipientsAdmin.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">گیرنده‌ای یافت نشد</td></tr>';
            return;
        }
        
        tbody.innerHTML = recipientsAdmin.map(r => `
            <tr>
                <td>${r.full_name}</td>
                <td>${r.email_address}</td>
                <td>${r.custom_title || r.role_name || '-'}</td>
                <td>${r.media_outlets || '-'}</td>
                <td>${r.country_name}</td>
                <td>
                    <span class="badge ${r.approval_status === 'approved' ? 'badge-success' : 'badge-warning'}">
                        ${r.approval_status === 'approved' ? 'تایید شده' : 'در انتظار'}
                    </span>
                </td>
                <td class="actions">
                    <button class="btn btn-secondary btn-sm" onclick="editRecipient(${r.id})">ویرایش</button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteRecipient(${r.id})">حذف</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading recipients:', error);
        document.getElementById('recipientsTableBody').innerHTML = 
            '<tr><td colspan="7" class="loading">خطا در بارگذاری</td></tr>';
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
        custom_title: document.getElementById('recipientTitle').value || null,
        media_outlets: document.getElementById('recipientMedia').value || null
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
    const recipient = recipientsAdmin.find(r => r.id === id);
    document.getElementById('recipientModalTitle').textContent = 'ویرایش گیرنده';
    document.getElementById('recipientId').value = id;
    if (recipient) {
        document.getElementById('recipientName').value = recipient.full_name || '';
        document.getElementById('recipientEmail').value = recipient.email_address || '';
        document.getElementById('recipientRole').value = recipient.role_id || '';
        document.getElementById('recipientCountry').value = recipient.country_code || '';
        document.getElementById('recipientTitle').value = recipient.custom_title || '';
        document.getElementById('recipientMedia').value = recipient.media_outlets || '';
    }
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
        
        // Load data for the tab
        if (tabName === 'admins') {
            loadAdmins();
        } else if (tabName === 'pending') {
            loadPendingCampaigns();
        } else if (tabName === 'analytics') {
            loadAnalytics();
        }
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
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔐 Admin Panel Loaded');
    console.log('📡 API Base:', API_BASE);
    
    // Set DOM elements
    loginContainer = document.getElementById('loginContainer');
    adminLayout = document.getElementById('adminLayout');
    loginForm = document.getElementById('loginForm');
    logoutBtn = document.getElementById('logoutBtn');
    
    // Setup event listeners
    const loginFormElement = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtnElement = document.getElementById('logoutBtn');
    
    if (loginBtn) {
        console.log('✅ Login button found');
        loginBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('📝 Login button clicked');
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            
            if (!email || !password) {
                showNotification('لطفا ایمیل و رمز عبور را وارد کنید', 'error');
                return;
            }
            
            await attemptLogin(email, password);
        });
    } else {
        console.error('❌ Login button not found');
    }
    
    if (logoutBtnElement) {
        console.log('✅ Logout button found');
        logoutBtnElement.addEventListener('click', () => {
            console.log('🚪 Logout clicked');
            logout();
        });
    }
    
    // Close modals on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Check auth
    checkAuth();
});
// ============================================
// CAMPAIGN MANAGEMENT
// ============================================
let campaigns = [];
let campaignTopics = [];
let campaignRecipients = [];
let filteredCampaignRecipients = [];

async function loadCampaigns() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/campaigns`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load campaigns');
        
        const data = await response.json();
        campaigns = Array.isArray(data) ? data : (data.campaigns || []);
        renderCampaigns();
        
    } catch (error) {
        console.error('Error loading campaigns:', error);
        showNotification('خطا در بارگذاری کمپین‌ها', 'error');
    }
}

function renderCampaigns() {
    const list = document.getElementById('campaignsAdminList');
    if (!list) return;
    
    if (campaigns.length === 0) {
        list.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">هیچ کمپینی یافت نشد</p>';
        return;
    }
    
    list.innerHTML = campaigns.map(campaign => `
        <div class="campaign-admin-card ${campaign.is_hot ? 'is-hot' : ''}">
            <div class="campaign-admin-header">
                <div class="campaign-admin-icon">${campaign.icon}</div>
            <div class="campaign-admin-info">
                <div class="campaign-admin-title">${campaign.title}</div>
                <div class="campaign-admin-country">
                    <span>Recipients: ${campaign.recipient_ids.length}</span>
                </div>
            </div>
            </div>
            <div class="campaign-admin-description">${campaign.description || ''}</div>
            <div class="campaign-admin-stats">
                <span>📧 ${campaign.email_count || 0} ایمیل</span>
                <span>👥 ${campaign.recipient_ids.length} گیرنده</span>
                <span>📝 ${campaign.topic_ids.length} موضوع</span>
                ${campaign.is_hot ? '<span style="color: var(--accent-red);">🔥 داغ</span>' : ''}
            </div>
            <div class="campaign-admin-actions">
                <button class="btn btn-secondary" onclick="editCampaign(${campaign.id})">ویرایش</button>
                <button class="btn btn-error" onclick="deleteCampaign(${campaign.id})">حذف</button>
            </div>
        </div>
    `).join('');
}

async function openCampaignModal(campaignId = null) {
    const modal = document.getElementById('campaignModal');
    const title = document.getElementById('campaignModalTitle');
    const form = document.getElementById('campaignForm');
    
    // Load recipients and topics for selects
    await loadAllTopics();
    await loadRecipientsForCountry();
    
    // Populate topics select
    const topicsSelect = document.getElementById('campaignTopics');
    topicsSelect.innerHTML = campaignTopics.map(t => 
        `<option value="${t.id}">${t.display_title}</option>`
    ).join('');
    
    if (campaignId) {
        // Edit mode
        const campaign = campaigns.find(c => c.id === campaignId);
        if (!campaign) return;
        
        title.textContent = 'ویرایش کمپین';
        document.getElementById('campaignId').value = campaign.id;
        document.getElementById('campaignTitle').value = campaign.title;
        document.getElementById('campaignSlug').value = campaign.slug;
        document.getElementById('campaignDescription').value = campaign.description || '';
        document.getElementById('campaignIcon').value = campaign.icon || '';
        document.getElementById('campaignIsHot').checked = campaign.is_hot;
        document.getElementById('campaignDisplayOrder').value = campaign.display_order || 0;
        
        // Select recipients
        Array.from(document.getElementById('campaignRecipients').options).forEach(opt => {
            opt.selected = campaign.recipient_ids.includes(parseInt(opt.value));
        });
        
        // Select topics
        Array.from(document.getElementById('campaignTopics').options).forEach(opt => {
            opt.selected = campaign.topic_ids.includes(parseInt(opt.value));
        });
    } else {
        // Add mode
        title.textContent = 'افزودن کمپین';
        form.reset();
        document.getElementById('campaignId').value = '';
        document.getElementById('campaignRecipients').innerHTML = '';
    }
    
    modal.classList.add('active');
}

async function loadAllTopics() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/topics`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load topics');
        
        const data = await response.json();
        campaignTopics = Array.isArray(data) ? data : (data.topics || []);
        
    } catch (error) {
        console.error('Error loading topics:', error);
    }
}

async function loadRecipientsForCountry() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/recipients`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load recipients');
        
        const data = await response.json();
        campaignRecipients = Array.isArray(data) ? data : (data.recipients || []);
        filteredCampaignRecipients = [...campaignRecipients];
        renderCampaignRecipients('');
        
    } catch (error) {
        console.error('Error loading recipients:', error);
    }
}

function renderCampaignRecipients(query) {
    const recipientsSelect = document.getElementById('campaignRecipients');
    const search = (query || '').trim().toLowerCase();

    filteredCampaignRecipients = campaignRecipients.filter(r => {
        const name = (r.full_name || '').toLowerCase();
        const title = (r.custom_title || r.role_name || '').toLowerCase();
        const country = (r.country_name || r.country_code || '').toLowerCase();
        return name.includes(search) || title.includes(search) || country.includes(search);
    });

    const grouped = filteredCampaignRecipients.reduce((acc, r) => {
        const key = r.country_name || r.country_code || 'Other';
        acc[key] = acc[key] || [];
        acc[key].push(r);
        return acc;
    }, {});

    recipientsSelect.innerHTML = Object.keys(grouped).sort().map(country => {
        const options = grouped[country].map(r =>
            `<option value="${r.id}">${r.full_name} - ${r.custom_title || r.role_name}</option>`
        ).join('');
        return `<optgroup label="${country}">${options}</optgroup>`;
    }).join('');
}

// Load recipients without country filter
document.addEventListener('DOMContentLoaded', () => {
    loadRecipientsForCountry();
    const recipientsSearch = document.getElementById('campaignRecipientsSearch');
    if (recipientsSearch) {
        recipientsSearch.addEventListener('input', (e) => renderCampaignRecipients(e.target.value));
    }
});

async function saveCampaign(e) {
    e.preventDefault();
    
    const campaignId = document.getElementById('campaignId').value;
    const recipientIds = Array.from(document.getElementById('campaignRecipients').selectedOptions).map(opt => parseInt(opt.value));
    const topicIds = Array.from(document.getElementById('campaignTopics').selectedOptions).map(opt => parseInt(opt.value));
    
    if (recipientIds.length === 0) {
        showNotification('حداقل یک گیرنده انتخاب کنید', 'error');
        return;
    }
    
    if (topicIds.length === 0) {
        showNotification('حداقل یک موضوع انتخاب کنید', 'error');
        return;
    }
    
    const payload = {
        title: document.getElementById('campaignTitle').value,
        slug: document.getElementById('campaignSlug').value,
        description: document.getElementById('campaignDescription').value || '',
        icon: document.getElementById('campaignIcon').value || '🔥',
        recipient_ids: recipientIds,
        topic_ids: topicIds,
        is_hot: document.getElementById('campaignIsHot').checked,
        display_order: parseInt(document.getElementById('campaignDisplayOrder').value) || 0,
        is_active: true
    };
    
    try {
        const url = campaignId 
            ? `${API_BASE}/api/v1/admin/campaigns/${campaignId}`
            : `${API_BASE}/api/v1/admin/campaigns`;
        const method = campaignId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save campaign');
        }
        
        closeModal('campaignModal');
        await loadCampaigns();
        if (!campaignId && adminData && adminData.role !== 'super_admin') {
            showNotification('کمپین ایجاد شد، منتظر تایید بمانید', 'info');
        } else {
            showNotification(campaignId ? 'کمپین ویرایش شد' : 'کمپین ایجاد شد', 'success');
        }
        
    } catch (error) {
        console.error('Error saving campaign:', error);
        showNotification('خطا در ذخیره کمپین', 'error');
    }
}

async function editCampaign(campaignId) {
    await openCampaignModal(campaignId);
}

async function deleteCampaign(campaignId) {
    if (!confirm('آیا از حذف این کمپین اطمینان دارید?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/campaigns/${campaignId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to delete campaign');
        
        await loadCampaigns();
        showNotification('کمپین حذف شد', 'success');
        
    } catch (error) {
        console.error('Error deleting campaign:', error);
        showNotification('خطا در حذف کمپین', 'error');
    }
}

// Setup campaign form
document.addEventListener('DOMContentLoaded', () => {
    const addCampaignBtn = document.getElementById('addCampaignBtn');
    if (addCampaignBtn) {
        addCampaignBtn.addEventListener('click', () => openCampaignModal());
    }
    
    const campaignForm = document.getElementById('campaignForm');
    if (campaignForm) {
        campaignForm.addEventListener('submit', saveCampaign);
    }
});

// Load campaigns analytics
async function loadCampaignAnalytics() {
    try {
        const [overview, campaignStats] = await Promise.all([
            fetch(`${API_BASE}/api/v1/admin/analytics/overview`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json()),
            fetch(`${API_BASE}/api/v1/admin/analytics/campaigns`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(r => r.json())
        ]);
        
        // Update overview stats
        document.getElementById('analyticsTotal').textContent = toPersian(overview.total_emails || overview.total_emails_generated || 0);
        document.getElementById('analyticsSuccess').textContent = overview.success_rate || '0%';
        document.getElementById('analyticsUnique').textContent = toPersian(overview.unique_users || 0);
        document.getElementById('analyticsCampaigns').textContent = toPersian(overview.active_campaigns || 0);
        
        // Render campaign analytics with enhanced styling
        const list = document.getElementById('campaignAnalyticsList');
        if (list && campaignStats.campaign_analytics) {
            list.innerHTML = campaignStats.campaign_analytics.map((ca, index) => `
                <div class="stat-card" style="margin-bottom: 12px; border-left: 4px solid hsl(${index * 30}, 70%, 60%); background: linear-gradient(90deg, hsla(${index * 30}, 70%, 60%, 0.1) 0%, transparent 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="stat-label" style="font-weight: 500;">${ca.campaign_title}</div>
                        <div class="stat-value" style="font-size: 1.2rem; color: hsl(${index * 30}, 70%, 50%);">${toPersian(ca.email_count)}</div>
                    </div>
                </div>
            `).join('');
        }
        
        // Load top countries
        const topCountries = await fetch(`${API_BASE}/api/v1/admin/analytics/top-countries`, {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(r => r.json());
        
        const topCountriesList = document.getElementById('topCountriesList');
        if (topCountriesList && topCountries.top_countries) {
            topCountriesList.innerHTML = topCountries.top_countries.slice(0, 10).map(tc => `
                <tr>
                    <td style="font-weight: 500;">${tc.country}</td>
                    <td><span style="background: linear-gradient(90deg, var(--primary-color), transparent); padding: 4px 12px; border-radius: 6px; color: white; font-weight: 600;">${toPersian(tc.email_count)}</span></td>
                </tr>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// Load analytics when tab is clicked
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            if (tab.dataset.tab === 'analytics') {
                loadCampaignAnalytics();
            }
            if (tab.dataset.tab === 'campaigns') {
                loadCampaigns();
            }
        });
    });

    // ==================== ADMIN MANAGEMENT ====================
    
    window.loadAdmins = async function() {
        const token = sessionStorage.getItem('adminToken');
        const tbody = document.getElementById('adminsTableBody');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/admins`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) throw new Error('Failed to load admins');
            
            const data = await response.json();
            const admins = data.admins || [];
            
            tbody.innerHTML = admins.length ? admins.map(admin => `
                <tr>
                    <td>${admin.email}</td>
                    <td><span class="badge ${admin.role === 'super_admin' ? 'badge-hot' : ''}">${admin.role}</span></td>
                    <td><span class="badge ${admin.is_active ? 'badge-success' : 'badge-error'}">${admin.is_active ? 'فعال' : 'غیرفعال'}</span></td>
                    <td>${admin.created_at ? new Date(admin.created_at).toLocaleDateString('fa-IR') : '-'}</td>
                    <td>${admin.last_login ? new Date(admin.last_login).toLocaleDateString('fa-IR') : '-'}</td>
                    <td>
                        <button class="btn-icon" onclick="editAdmin(${admin.id})" title="ویرایش">✏️</button>
                        <button class="btn-icon" onclick="deleteAdmin(${admin.id})" title="حذف">🗑️</button>
                    </td>
                </tr>
            `).join('') : '<tr><td colspan="6" class="no-data">مدیری یافت نشد</td></tr>';
        } catch (error) {
            console.error('Failed to load admins:', error);
            tbody.innerHTML = '<tr><td colspan="6" class="error">خطا در بارگذاری</td></tr>';
        }
    };

    document.getElementById('addAdminBtn')?.addEventListener('click', () => {
        document.getElementById('adminModalTitle').textContent = 'افزودن مدیر';
        document.getElementById('adminForm').reset();
        document.getElementById('adminId').value = '';
        document.getElementById('adminPassword').required = true;
        openModal('adminModal');
    });

    document.getElementById('adminForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const id = document.getElementById('adminId').value;
        const payload = {
            email: document.getElementById('adminEmail').value,
            role: document.getElementById('adminRole').value,
            is_active: document.getElementById('adminIsActive').checked
        };
        
        const password = document.getElementById('adminPassword').value;
        if (password) payload.password = password;
        
        const token = sessionStorage.getItem('adminToken');
        const url = id ? `${API_BASE}/api/v1/admin/admins/${id}` : `${API_BASE}/api/v1/admin/admins`;
        const method = id ? 'PUT' : 'POST';
        
        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save admin');
            }
            
            closeModal('adminModal');
            loadAdmins();
            showNotification(id ? 'مدیر ویرایش شد' : 'مدیر جدید اضافه شد', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    });

    window.editAdmin = async function(id) {
        const token = sessionStorage.getItem('adminToken');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/admins`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) throw new Error('Failed to load admin');
            
            const data = await response.json();
            const admin = data.admins.find(a => a.id === id);
            
            if (!admin) throw new Error('Admin not found');
            
            document.getElementById('adminModalTitle').textContent = 'ویرایش مدیر';
            document.getElementById('adminId').value = admin.id;
            document.getElementById('adminEmail').value = admin.email;
            document.getElementById('adminRole').value = admin.role;
            document.getElementById('adminIsActive').checked = admin.is_active;
            document.getElementById('adminPassword').value = '';
            document.getElementById('adminPassword').required = false;
            
            openModal('adminModal');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    };

    window.deleteAdmin = async function(id) {
        if (!confirm('آیا از حذف این مدیر اطمینان دارید؟')) return;
        
        const token = sessionStorage.getItem('adminToken');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/admins/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete admin');
            }
            
            loadAdmins();
            showNotification('مدیر حذف شد', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    };

    // ==================== COUNTRY MANAGEMENT ====================
    
    document.getElementById('addCountryBtn')?.addEventListener('click', () => {
        document.getElementById('countryModalTitle').textContent = 'افزودن کشور';
        document.getElementById('countryForm').reset();
        document.getElementById('countryOriginalCode').value = '';
        document.getElementById('countryIsActive').checked = true;
        openModal('countryModal');
    });

    document.getElementById('countryForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const originalCode = document.getElementById('countryOriginalCode').value;
        const code = document.getElementById('countryCode').value.toUpperCase();
        const payload = {
            code: code,
            name: document.getElementById('countryName').value,
            name_persian: document.getElementById('countryNamePersian').value,
            flag: document.getElementById('countryFlag').value,
            is_active: document.getElementById('countryIsActive').checked
        };
        
        const token = sessionStorage.getItem('adminToken');
        const url = originalCode ? `${API_BASE}/api/v1/admin/countries/${originalCode}` : `${API_BASE}/api/v1/admin/countries`;
        const method = originalCode ? 'PUT' : 'POST';
        
        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save country');
            }
            
            closeModal('countryModal');
            loadCountries();
            showNotification(originalCode ? 'کشور ویرایش شد' : 'کشور جدید اضافه شد', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    });

    window.editCountry = function(code, name, namePersian, flag, isActive) {
        document.getElementById('countryModalTitle').textContent = 'ویرایش کشور';
        document.getElementById('countryOriginalCode').value = code;
        document.getElementById('countryCode').value = code;
        document.getElementById('countryName').value = name;
        document.getElementById('countryNamePersian').value = namePersian;
        document.getElementById('countryFlag').value = flag;
        document.getElementById('countryIsActive').checked = isActive;
        openModal('countryModal');
    };

    window.deleteCountry = async function(code) {
        if (!confirm(`آیا از حذف کشور ${code} اطمینان دارید؟`)) return;
        
        const token = sessionStorage.getItem('adminToken');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/countries/${code}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete country');
            }
            
            loadCountries();
            showNotification('کشور حذف شد', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    };

    // ==================== PENDING CAMPAIGNS ====================
    
    window.loadPendingCampaigns = async function() {
        const token = sessionStorage.getItem('adminToken');
        const container = document.getElementById('pendingCampaignsList');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/campaigns/pending`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) throw new Error('Failed to load pending campaigns');
            
            const data = await response.json();
            const campaigns = Array.isArray(data) ? data : (data.pending_campaigns || []);
            
            if (campaigns.length === 0) {
                container.innerHTML = '<div class="no-data">کمپینی در انتظار تایید نیست</div>';
                return;
            }
            
            container.innerHTML = campaigns.map(campaign => `
                <div class="campaign-admin-card">
                    <div class="campaign-admin-header">
                        <span class="campaign-icon">${campaign.icon || '📧'}</span>
                        <h3>${campaign.title}</h3>
                    </div>
                    <p class="campaign-admin-description">${campaign.description || ''}</p>
                    <div class="campaign-admin-meta">
                        <span>👥 ${campaign.recipient_ids.length} گیرنده</span>
                        <span>📋 ${campaign.topic_ids.length} موضوع</span>
                    </div>
                    <div class="campaign-admin-actions" style="margin-top: 16px;">
                        <button class="btn btn-success" onclick="approveCampaign(${campaign.id})" style="flex: 1;">✅ تایید</button>
                        <button class="btn btn-danger" onclick="rejectCampaign(${campaign.id})" style="flex: 1;">❌ رد</button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load pending campaigns:', error);
            container.innerHTML = '<div class="error">خطا در بارگذاری</div>';
        }
    };

    window.approveCampaign = async function(id) {
        const token = sessionStorage.getItem('adminToken');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/campaigns/${id}/approve`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('اجازه ندارید. فقط سوپرادمین می‌تواند تایید کند');
                }
                throw new Error('خطا در تایید کمپین');
            }
            
            loadPendingCampaigns();
            loadCampaigns();
            showNotification('کمپین تایید شد', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    };

    window.rejectCampaign = async function(id) {
        const reason = prompt('دلیل رد کمپین (اختیاری):');
        
        const token = sessionStorage.getItem('adminToken');
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/campaigns/${id}/reject`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ reason: reason || '' })
            });
            
            if (!response.ok) {
                if (response.status === 403) {
                    throw new Error('اجازه ندارید. فقط سوپرادمین می‌تواند رد کند');
                }
                throw new Error('خطا در رد کمپین');
            }
            
            loadPendingCampaigns();
            showNotification('کمپین رد شد', 'error');
        } catch (error) {
            showNotification(error.message, 'error');
        }
    };

    // ==================== CHARTS ====================
    
    let campaignChart, countryChart, userCountryChart;
    
    window.renderCharts = function(analytics) {
        // Campaign Distribution Chart
        const campaignCtx = document.getElementById('campaignChart');
        if (campaignCtx && analytics.campaign_analytics) {
            if (campaignChart) campaignChart.destroy();
            
            const campaigns = analytics.campaign_analytics.slice(0, 10);
            campaignChart = new Chart(campaignCtx, {
                type: 'bar',
                data: {
                    labels: campaigns.map(c => c.campaign_title),
                    datasets: [{
                        label: 'تعداد ایمیل',
                        data: campaigns.map(c => c.email_count),
                        backgroundColor: 'rgba(99, 102, 241, 0.8)',
                        borderColor: 'rgb(99, 102, 241)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
        
        // Country Distribution Chart
        const countryCtx = document.getElementById('countryChart');
        if (countryCtx && analytics.top_countries) {
            if (countryChart) countryChart.destroy();
            
            const countries = analytics.top_countries.slice(0, 10);
            countryChart = new Chart(countryCtx, {
                type: 'doughnut',
                data: {
                    labels: countries.map(c => c.country),
                    datasets: [{
                        data: countries.map(c => c.email_count),
                        backgroundColor: [
                            'rgba(99, 102, 241, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(34, 197, 94, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(168, 85, 247, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(14, 165, 233, 0.8)',
                            'rgba(251, 146, 60, 0.8)',
                            'rgba(132, 204, 22, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                font: { size: 11 }
                            }
                        }
                    }
                }
            });
        }

        // User Countries Chart
        const userCountryCtx = document.getElementById('userCountryChart');
        if (userCountryCtx && analytics.user_countries) {
            if (userCountryChart) userCountryChart.destroy();

            const users = analytics.user_countries.slice(0, 10);
            userCountryChart = new Chart(userCountryCtx, {
                type: 'bar',
                data: {
                    labels: users.map(u => u.country),
                    datasets: [{
                        label: 'کاربر',
                        data: users.map(u => u.user_count),
                        backgroundColor: 'rgba(34, 197, 94, 0.8)',
                        borderColor: 'rgb(34, 197, 94)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    };

    // Load analytics and render charts
    window.loadAnalytics = async function() {
        await loadCampaignAnalytics();
        
        const token = sessionStorage.getItem('adminToken');
        try {
            const response = await fetch(`${API_BASE}/api/v1/admin/analytics`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const analytics = await response.json();
                renderCharts(analytics);
            }
        } catch (error) {
            console.error('Failed to load analytics for charts:', error);
        }
    };
});
