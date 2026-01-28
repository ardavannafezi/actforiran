/**
 * ActForIran - Main Application JavaScript
 * Persian RTL Frontend with 5-Step Stepper Form
 */

const API_BASE = 'http://localhost:8000';

// Application State
const state = {
    currentStep: 1,
    totalSteps: 5,
    countries: [],
    recipients: [],
    topics: [],
    selectedCountry: null,
    selectedRecipients: new Set(),
    selectedTopics: new Set(),
    isResident: null,
    generatedEmail: {
        subject: '',
        body: '',
        mailto: ''
    }
};

// DOM Elements
const elements = {
    startBtn: document.getElementById('startBtn'),
    stepperContainer: document.getElementById('stepperContainer'),
    progressFill: document.getElementById('progressFill'),
    prevBtn: document.getElementById('prevBtn'),
    nextBtn: document.getElementById('nextBtn'),
    countrySelect: document.getElementById('countrySelect'),
    recipientsList: document.getElementById('recipientsList'),
    topicsList: document.getElementById('topicsList'),
    emailSubject: document.getElementById('emailSubject'),
    emailBody: document.getElementById('emailBody'),
    sendEmailBtn: document.getElementById('sendEmailBtn')
};

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
// STEPPER NAVIGATION
// ============================================
function initStepper() {
    // Start button
    elements.startBtn.addEventListener('click', () => {
        document.querySelector('.hero').style.display = 'none';
        elements.stepperContainer.classList.add('active');
        loadCountries();
        loadTopics();
    });
    
    // Navigation buttons
    elements.prevBtn.addEventListener('click', () => goToStep(state.currentStep - 1));
    elements.nextBtn.addEventListener('click', handleNextStep);
    
    // Country select
    elements.countrySelect.addEventListener('change', handleCountryChange);
    
    // Residency radio buttons
    document.querySelectorAll('input[name="resident"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            state.isResident = e.target.value === 'yes';
        });
    });
    
    // Send email button
    elements.sendEmailBtn.addEventListener('click', sendEmail);
}

function goToStep(step) {
    if (step < 1 || step > state.totalSteps) return;
    
    state.currentStep = step;
    
    // Update progress bar
    const progress = ((step - 1) / (state.totalSteps - 1)) * 100;
    elements.progressFill.style.width = `${progress}%`;
    
    // Update step indicators
    document.querySelectorAll('.step-indicator').forEach(indicator => {
        const indicatorStep = parseInt(indicator.dataset.step);
        indicator.classList.remove('active', 'completed');
        if (indicatorStep === step) {
            indicator.classList.add('active');
        } else if (indicatorStep < step) {
            indicator.classList.add('completed');
        }
    });
    
    // Update panels
    document.querySelectorAll('.step-panel').forEach(panel => {
        const panelStep = parseInt(panel.dataset.step);
        panel.classList.toggle('active', panelStep === step);
    });
    
    // Update navigation buttons
    elements.prevBtn.disabled = step === 1;
    
    if (step === state.totalSteps) {
        elements.nextBtn.style.display = 'none';
    } else {
        elements.nextBtn.style.display = 'flex';
        elements.nextBtn.innerHTML = 'بعدی <span class="btn-icon">←</span>';
    }
}

function handleNextStep() {
    // Validate current step
    if (!validateCurrentStep()) return;
    
    // Special handling for step 4 -> 5 (generate email)
    if (state.currentStep === 4) {
        generateEmail();
    }
    
    goToStep(state.currentStep + 1);
}

function validateCurrentStep() {
    switch (state.currentStep) {
        case 1:
            if (!state.selectedCountry) {
                showNotification('لطفاً یک کشور انتخاب کنید', 'error');
                return false;
            }
            break;
        case 2:
            if (state.selectedRecipients.size === 0) {
                showNotification('لطفاً حداقل یک گیرنده انتخاب کنید', 'error');
                return false;
            }
            break;
        case 3:
            if (state.isResident === null) {
                showNotification('لطفاً وضعیت اقامت خود را مشخص کنید', 'error');
                return false;
            }
            break;
        case 4:
            if (state.selectedTopics.size === 0) {
                showNotification('لطفاً حداقل یک موضوع انتخاب کنید', 'error');
                return false;
            }
            break;
    }
    return true;
}

// ============================================
// API CALLS
// ============================================
async function loadCountries() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/countries`);
        if (!response.ok) throw new Error('Failed to load countries');
        
        const data = await response.json();
        state.countries = data.countries || [];
        
        elements.countrySelect.innerHTML = '<option value="">یک کشور انتخاب کنید...</option>' +
            state.countries.map(c => `<option value="${c.code}">${c.name}</option>`).join('');
        
    } catch (error) {
        console.error('Error loading countries:', error);
        showNotification('خطا در بارگذاری کشورها', 'error');
        elements.countrySelect.innerHTML = '<option value="">خطا در بارگذاری</option>';
    }
}

async function handleCountryChange(e) {
    const countryCode = e.target.value;
    if (!countryCode) {
        state.selectedCountry = null;
        return;
    }
    
    state.selectedCountry = countryCode;
    state.selectedRecipients.clear();
    
    try {
        elements.recipientsList.innerHTML = '<div class="loading">در حال بارگذاری گیرندگان...</div>';
        
        const response = await fetch(`${API_BASE}/api/v1/recipients?country_code=${countryCode}`);
        if (!response.ok) throw new Error('Failed to load recipients');
        
        const data = await response.json();
        state.recipients = data.recipients || [];
        
        renderRecipients();
        
    } catch (error) {
        console.error('Error loading recipients:', error);
        showNotification('خطا در بارگذاری گیرندگان', 'error');
        elements.recipientsList.innerHTML = '<div class="loading">خطا در بارگذاری</div>';
    }
}

async function loadTopics() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/topics`);
        if (!response.ok) throw new Error('Failed to load topics');
        
        const data = await response.json();
        state.topics = data.topics || [];
        
        renderTopics();
        
    } catch (error) {
        console.error('Error loading topics:', error);
        showNotification('خطا در بارگذاری موضوعات', 'error');
        elements.topicsList.innerHTML = '<div class="loading">خطا در بارگذاری</div>';
    }
}

async function generateEmail() {
    const payload = {
        country_code: state.selectedCountry,
        recipient_ids: Array.from(state.selectedRecipients),
        topic_ids: Array.from(state.selectedTopics),
        is_resident: state.isResident
    };
    
    try {
        elements.emailSubject.value = 'در حال تولید ایمیل...';
        elements.emailBody.value = 'لطفاً صبر کنید...';
        
        const response = await fetch(`${API_BASE}/api/v1/generate-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate email');
        }
        
        const data = await response.json();
        
        state.generatedEmail.subject = data.subject || '';
        state.generatedEmail.body = data.body || '';
        state.generatedEmail.mailto = data.mailto_link || '';
        
        elements.emailSubject.value = state.generatedEmail.subject;
        elements.emailBody.value = state.generatedEmail.body;
        
        showNotification('ایمیل با موفقیت تولید شد!', 'success');
        
    } catch (error) {
        console.error('Error generating email:', error);
        
        // Fallback: Generate sample email locally
        const country = state.countries.find(c => c.code === state.selectedCountry);
        const selectedRecipients = state.recipients.filter(r => state.selectedRecipients.has(r.id));
        const selectedTopics = state.topics.filter(t => state.selectedTopics.has(t.id));
        
        const subject = 'فراخوان فوری: حمایت از حقوق بشر در ایران';
        const body = `به عنوان یک شهروند نگران، از شما درخواست می‌کنم که به وضعیت حقوق بشر در ایران توجه کنید.

موضوعات مورد نظر:
${selectedTopics.map(t => `• ${t.display_title}`).join('\n')}

مردم ایران به حمایت بین‌المللی شما نیاز دارند.

با احترام`;
        
        const emails = selectedRecipients.map(r => r.email_address).join(',');
        
        state.generatedEmail.subject = subject;
        state.generatedEmail.body = body;
        state.generatedEmail.mailto = `mailto:${emails}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        
        elements.emailSubject.value = subject;
        elements.emailBody.value = body;
        
        showNotification('ایمیل نمونه تولید شد (بدون AI)', 'info');
    }
}

function sendEmail() {
    // Update mailto with current values (in case user edited)
    const emails = state.recipients
        .filter(r => state.selectedRecipients.has(r.id))
        .map(r => r.email_address)
        .join(',');
    
    const subject = elements.emailSubject.value;
    const body = elements.emailBody.value;
    
    const mailto = `mailto:${emails}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    window.location.href = mailto;
    showNotification('در حال باز کردن برنامه ایمیل...', 'success');
}

// ============================================
// RENDER FUNCTIONS
// ============================================
function renderRecipients() {
    if (state.recipients.length === 0) {
        elements.recipientsList.innerHTML = '<div class="loading">گیرنده‌ای برای این کشور یافت نشد</div>';
        return;
    }
    
    elements.recipientsList.innerHTML = state.recipients.map(recipient => `
        <label class="checkbox-item ${state.selectedRecipients.has(recipient.id) ? 'selected' : ''}" data-id="${recipient.id}">
            <input type="checkbox" ${state.selectedRecipients.has(recipient.id) ? 'checked' : ''}>
            <div class="item-content">
                <div class="item-title">${recipient.full_name}</div>
                <div class="item-subtitle">${recipient.display_title} — ${recipient.country_name}</div>
            </div>
        </label>
    `).join('');
    
    // Add event listeners
    elements.recipientsList.querySelectorAll('.checkbox-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const id = parseInt(item.dataset.id);
            const checkbox = item.querySelector('input[type="checkbox"]');
            
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            
            if (checkbox.checked) {
                state.selectedRecipients.add(id);
                item.classList.add('selected');
            } else {
                state.selectedRecipients.delete(id);
                item.classList.remove('selected');
            }
        });
    });
}

function renderTopics() {
    if (state.topics.length === 0) {
        elements.topicsList.innerHTML = '<div class="loading">موضوعی یافت نشد</div>';
        return;
    }
    
    elements.topicsList.innerHTML = state.topics.map(topic => `
        <label class="checkbox-item ${state.selectedTopics.has(topic.id) ? 'selected' : ''}" data-id="${topic.id}">
            <input type="checkbox" ${state.selectedTopics.has(topic.id) ? 'checked' : ''}>
            <div class="item-content">
                <div class="item-title">${topic.display_title}</div>
                ${topic.description ? `<div class="item-subtitle">${topic.description}</div>` : ''}
            </div>
        </label>
    `).join('');
    
    // Add event listeners
    elements.topicsList.querySelectorAll('.checkbox-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const id = parseInt(item.dataset.id);
            const checkbox = item.querySelector('input[type="checkbox"]');
            
            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
            }
            
            if (checkbox.checked) {
                state.selectedTopics.add(id);
                item.classList.add('selected');
            } else {
                state.selectedTopics.delete(id);
                item.classList.remove('selected');
            }
        });
    });
}

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initStepper();
});

