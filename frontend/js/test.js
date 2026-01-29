/**
 * ActForIran - API Test Suite
 * Comprehensive testing of all backend endpoints
 */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://back.actforiran.org';
let adminToken = null;
let testStats = {
    passed: 0,
    failed: 0,
    pending: 0,
    total: 0
};

// Persian number converter
function toPersian(num) {
    const persianDigits = '۰۱۲۳۴۵۶۷۸۹';
    return num.toString().replace(/[0-9]/g, w => persianDigits[+w]);
}

// Update statistics
function updateStats() {
    document.getElementById('passedCount').textContent = toPersian(testStats.passed);
    document.getElementById('failedCount').textContent = toPersian(testStats.failed);
    document.getElementById('pendingCount').textContent = toPersian(testStats.pending);
    document.getElementById('totalCount').textContent = toPersian(testStats.total);
}

// Show test result
function showResult(elementId, success, data, statusCode = null) {
    const resultDiv = document.getElementById(`result-${elementId}`);
    resultDiv.style.display = 'block';
    
    const statusText = statusCode ? `HTTP ${statusCode}` : '';
    const statusClass = success ? 'text-success' : 'text-error';
    
    resultDiv.innerHTML = `
        <pre style="color: ${success ? 'var(--success)' : 'var(--error)'};">
${statusText ? `Status: ${statusText}\n` : ''}${success ? '✓ SUCCESS' : '✗ FAILED'}
${typeof data === 'string' ? data : JSON.stringify(data, null, 2)}</pre>
    `;
    
    // Update stats
    if (success) {
        testStats.passed++;
    } else {
        testStats.failed++;
    }
    testStats.total++;
    updateStats();
}

// Update section status
function updateSectionStatus(sectionId, status) {
    const dot = document.getElementById(`status-${sectionId}`);
    if (dot) {
        dot.className = 'status-dot';
        if (status === 'success') dot.classList.add('status-success');
        else if (status === 'error') dot.classList.add('status-error');
        else if (status === 'pending') dot.classList.add('status-pending');
    }
}

// Generic API test function
async function testEndpoint(name, url, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${url}`, options);
        const data = await response.json();
        
        showResult(name, response.ok, data, response.status);
        return response.ok;
    } catch (error) {
        showResult(name, false, error.message);
        return false;
    }
}

// ============================================
// HEALTH TESTS
// ============================================
async function testHealth() {
    updateSectionStatus('health', 'pending');
    const success = await testEndpoint('health', '/health');
    updateSectionStatus('health', success ? 'success' : 'error');
}

async function testRoot() {
    updateSectionStatus('health', 'pending');
    const success = await testEndpoint('root', '/');
    updateSectionStatus('health', success ? 'success' : 'error');
}

// ============================================
// PUBLIC API TESTS
// ============================================
async function testCountries() {
    updateSectionStatus('public', 'pending');
    const success = await testEndpoint('countries', '/api/v1/countries');
    updateSectionStatus('public', success ? 'success' : 'error');
}

async function testRecipients() {
    updateSectionStatus('public', 'pending');
    const success = await testEndpoint('recipients', '/api/v1/recipients');
    updateSectionStatus('public', success ? 'success' : 'error');
}

async function testRecipientsFiltered() {
    const countryCode = document.getElementById('recipientCountryCode').value;
    if (!countryCode) {
        alert('لطفاً کد کشور را وارد کنید');
        return;
    }
    
    updateSectionStatus('public', 'pending');
    const success = await testEndpoint('recipients', `/api/v1/recipients?country_code=${countryCode}`);
    updateSectionStatus('public', success ? 'success' : 'error');
}

async function testTopics() {
    updateSectionStatus('public', 'pending');
    const success = await testEndpoint('topics', '/api/v1/topics');
    updateSectionStatus('public', success ? 'success' : 'error');
}

async function testCampaigns() {
    updateSectionStatus('public', 'pending');
    const success = await testEndpoint('campaigns', '/api/v1/campaigns');
    updateSectionStatus('public', success ? 'success' : 'error');
}

async function testGenerateEmail() {
    updateSectionStatus('public', 'pending');
    
    // First, get some data to use
    try {
        const countriesRes = await fetch(`${API_BASE}/api/v1/countries`);
        const countriesData = await countriesRes.json();
        const country = countriesData.countries?.[0];
        
        if (!country) {
            showResult('generate-email', false, 'No countries available');
            updateSectionStatus('public', 'error');
            return;
        }
        
        const recipientsRes = await fetch(`${API_BASE}/api/v1/recipients?country_code=${country.code}`);
        const recipientsData = await recipientsRes.json();
        const recipient = recipientsData.recipients?.[0];
        
        const topicsRes = await fetch(`${API_BASE}/api/v1/topics`);
        const topicsData = await topicsRes.json();
        const topic = topicsData.topics?.[0];
        
        if (!recipient || !topic) {
            showResult('generate-email', false, 'No recipients or topics available');
            updateSectionStatus('public', 'error');
            return;
        }
        
        const payload = {
            country_code: country.code,
            recipient_ids: [recipient.id],
            topic_ids: [topic.id],
            sender_citizenship_status: "international_supporter"
        };
        
        const success = await testEndpoint('generate-email', '/api/v1/generate-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        updateSectionStatus('public', success ? 'success' : 'error');
        
    } catch (error) {
        showResult('generate-email', false, error.message);
        updateSectionStatus('public', 'error');
    }
}

// ============================================
// ADMIN API TESTS
// ============================================
async function testAdminLogin() {
    updateSectionStatus('admin', 'pending');
    
    const email = document.getElementById('adminEmail').value;
    const password = document.getElementById('adminPassword').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            adminToken = data.access_token;
            localStorage.setItem('testAdminToken', adminToken);
        }
        
        showResult('admin-login', response.ok, data, response.status);
        updateSectionStatus('admin', response.ok ? 'success' : 'error');
        
    } catch (error) {
        showResult('admin-login', false, error.message);
        updateSectionStatus('admin', 'error');
    }
}

async function testAdminMe() {
    updateSectionStatus('admin', 'pending');
    
    if (!adminToken) {
        adminToken = localStorage.getItem('testAdminToken');
    }
    
    if (!adminToken) {
        showResult('admin-me', false, 'لطفاً ابتدا لاگین کنید');
        updateSectionStatus('admin', 'error');
        return;
    }
    
    const success = await testEndpoint('admin-me', '/api/v1/admin/auth/me', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    
    updateSectionStatus('admin', success ? 'success' : 'error');
}

async function testAdminRoles() {
    updateSectionStatus('admin', 'pending');
    
    if (!adminToken) {
        adminToken = localStorage.getItem('testAdminToken');
    }
    
    if (!adminToken) {
        showResult('admin-roles', false, 'لطفاً ابتدا لاگین کنید');
        updateSectionStatus('admin', 'error');
        return;
    }
    
    const success = await testEndpoint('admin-roles', '/api/v1/admin/roles', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    
    updateSectionStatus('admin', success ? 'success' : 'error');
}

async function testAnalyticsOverview() {
    updateSectionStatus('admin', 'pending');
    
    if (!adminToken) {
        adminToken = localStorage.getItem('testAdminToken');
    }
    
    if (!adminToken) {
        showResult('analytics-overview', false, 'لطفاً ابتدا لاگین کنید');
        updateSectionStatus('admin', 'error');
        return;
    }
    
    const success = await testEndpoint('analytics-overview', '/api/v1/admin/analytics/overview', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    
    updateSectionStatus('admin', success ? 'success' : 'error');
}

async function testTopCountries() {
    updateSectionStatus('admin', 'pending');
    
    if (!adminToken) {
        adminToken = localStorage.getItem('testAdminToken');
    }
    
    if (!adminToken) {
        showResult('top-countries', false, 'لطفاً ابتدا لاگین کنید');
        updateSectionStatus('admin', 'error');
        return;
    }
    
    const success = await testEndpoint('top-countries', '/api/v1/admin/analytics/top-countries', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    
    updateSectionStatus('admin', success ? 'success' : 'error');
}

async function testTopTopics() {
    updateSectionStatus('admin', 'pending');
    
    if (!adminToken) {
        adminToken = localStorage.getItem('testAdminToken');
    }
    
    if (!adminToken) {
        showResult('top-topics', false, 'لطفاً ابتدا لاگین کنید');
        updateSectionStatus('admin', 'error');
        return;
    }
    
    const success = await testEndpoint('top-topics', '/api/v1/admin/analytics/top-topics', {
        headers: { 'Authorization': `Bearer ${adminToken}` }
    });
    
    updateSectionStatus('admin', success ? 'success' : 'error');
}

// ============================================
// TEST API TESTS
// ============================================
async function testConnectivity() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('connectivity', '/api/test/connectivity');
    updateSectionStatus('test', success ? 'success' : 'error');
}

async function testDatabase() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('database', '/api/test/database');
    updateSectionStatus('test', success ? 'success' : 'error');
}

async function testSampleData() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('sample-data', '/api/test/sample-data');
    updateSectionStatus('test', success ? 'success' : 'error');
}

async function testAdminAuth() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('admin-auth', '/api/test/admin-auth');
    updateSectionStatus('test', success ? 'success' : 'error');
}

async function testPublicEndpoints() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('public-endpoints', '/api/test/public-endpoints');
    updateSectionStatus('test', success ? 'success' : 'error');
}

async function testEmailGeneration() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('email-generation', '/api/test/email-generation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    updateSectionStatus('test', success ? 'success' : 'error');
}

async function testAdminLoginTest() {
    updateSectionStatus('test', 'pending');
    const success = await testEndpoint('admin-login-test', '/api/test/admin-login-test');
    updateSectionStatus('test', success ? 'success' : 'error');
}

// ============================================
// TEST SUITES
// ============================================
async function runAllTests() {
    clearResults();
    
    console.log('🧪 Running all tests...');
    
    // Health tests
    await testHealth();
    await testRoot();
    await sleep(500);
    
    // Public API tests
    await testCountries();
    await sleep(500);
    await testRecipients();
    await sleep(500);
    await testTopics();
    await sleep(500);
    
    // Test API tests
    await testConnectivity();
    await sleep(500);
    await testDatabase();
    await sleep(500);
    await testSampleData();
    await sleep(500);
    await testAdminAuth();
    await sleep(500);
    await testPublicEndpoints();
    await sleep(500);
    await testEmailGeneration();
    await sleep(500);
    await testAdminLoginTest();
    await sleep(500);
    
    // Admin tests (require login first)
    await testAdminLogin();
    await sleep(500);
    await testAdminMe();
    await sleep(500);
    await testAdminRoles();
    
    console.log('✅ All tests completed!');
    
    // Show summary notification
    const successRate = ((testStats.passed / testStats.total) * 100).toFixed(0);
    alert(`تست‌ها تمام شدند!\n\nموفق: ${testStats.passed}\nناموفق: ${testStats.failed}\nکل: ${testStats.total}\n\nنرخ موفقیت: ${successRate}%`);
}

async function runPublicTests() {
    clearResults();
    
    console.log('🌍 Running public API tests...');
    
    await testHealth();
    await sleep(500);
    await testCountries();
    await sleep(500);
    await testRecipients();
    await sleep(500);
    await testTopics();
    
    console.log('✅ Public tests completed!');
}

async function runAdminTests() {
    clearResults();
    
    console.log('🔐 Running admin API tests...');
    
    await testAdminLogin();
    await sleep(500);
    await testAdminMe();
    await sleep(500);
    await testAdminRoles();
    
    console.log('✅ Admin tests completed!');
}

function clearResults() {
    // Clear all result divs
    document.querySelectorAll('.test-result').forEach(div => {
        div.style.display = 'none';
        div.innerHTML = '';
    });
    
    // Reset stats
    testStats = {
        passed: 0,
        failed: 0,
        pending: 0,
        total: 0
    };
    updateStats();
    
    // Reset status dots
    document.querySelectorAll('.status-dot').forEach(dot => {
        dot.className = 'status-dot';
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================
// AUTO-RUN ON LOAD
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🧪 Test suite ready!');
    console.log('API Base:', API_BASE);
    
    // Check if admin token exists
    adminToken = localStorage.getItem('testAdminToken');
    if (adminToken) {
        console.log('✓ Admin token found in localStorage');
    }
    
    // Auto-run basic connectivity test
    setTimeout(() => {
        console.log('Running automatic connectivity check...');
        testHealth();
    }, 500);
});
