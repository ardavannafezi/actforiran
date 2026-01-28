/**
 * ActForIran - Main Application JavaScript
 * Persian RTL Frontend with 5-Step Stepper Form
 */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://back.actforiran.org';

// Application State
const state = {
    currentStep: 1,
    totalSteps: 5,
    countries: [],
    recipients: [],
    topics: [],
    campaigns: [],
    selectedCountry: null,
    selectedRecipients: new Set(),
    selectedTopics: new Set(),
    isResident: null,
    selectedCampaign: null,
    campaignMode: false, // Track if user started from campaign
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
    userName: document.getElementById('userName'),
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
    console.log('🚀 ActForIran App Loaded - Safari Compatible');
    
    // Load campaigns on page load
    loadCampaigns();
    
    // Choice buttons
    const campaignChoice = document.getElementById('campaignChoice');
    const customChoice = document.getElementById('customChoice');
    const campaignsSection = document.getElementById('campaignsSection');
    const stepsPreview = document.getElementById('stepsPreview');
    const choiceSection = document.getElementById('choiceSection');
    const backToChoiceCustom = document.getElementById('backToChoiceCustom');
    
    if (campaignChoice) {
        campaignChoice.onclick = function() {
            // Scroll to campaigns section
            document.getElementById('campaignsSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };
    }
    
    if (customChoice) {
        customChoice.onclick = function() {
            choiceSection.style.display = 'none';
            stepsPreview.style.display = 'block';
            // Scroll to form
            setTimeout(() => {
                document.getElementById('step1')?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        };
    }
    
    if (backToChoiceCustom) {
        backToChoiceCustom.onclick = function() {
            choiceSection.style.display = 'block';
            stepsPreview.style.display = 'none';
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
            stepsPreview.style.display = 'none';
        };
    }
    
    // Safari Fix: Use onclick instead of addEventListener
    if (elements.startBtn) {
        elements.startBtn.onclick = function(e) {
            e.preventDefault();
            console.log('🎯 Start button clicked (Custom Mode)');
            state.campaignMode = false;
            state.selectedCampaign = null;
            document.querySelector('.hero').style.display = 'none';
            elements.stepperContainer.classList.add('active');
            loadCountries();
            loadTopics();
        };
    }
    
    // Navigation buttons
    if (elements.prevBtn) {
        elements.prevBtn.onclick = function(e) {
            e.preventDefault();
            goToStep(state.currentStep - 1);
        };
    }
    
    if (elements.nextBtn) {
        elements.nextBtn.onclick = function(e) {
            e.preventDefault();
            handleNextStep();
        };
    }
    
    // Country select
    if (elements.countrySelect) {
        elements.countrySelect.onchange = handleCountryChange;
    }
    
    // Residency radio buttons
    document.querySelectorAll('input[name=\"resident\"]').forEach(radio => {
        radio.onclick = function(e) {
            state.isResident = e.target.value === 'yes';
        };
    });
    
    // Send email button
    if (elements.sendEmailBtn) {
        elements.sendEmailBtn.onclick = function(e) {
            e.preventDefault();
            sendEmail();
        };
    }
    
    console.log('✅ App initialized successfully');
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
            state.countries.map(c => `<option value="${c.code}">${c.flag || ''} ${c.name_persian || c.name}</option>`).join('');
        
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

async function loadCampaigns() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/campaigns`);
        if (!response.ok) throw new Error('Failed to load campaigns');
        
        const data = await response.json();
        state.campaigns = data.campaigns || [];
        
        renderCampaigns();
        
    } catch (error) {
        console.error('Error loading campaigns:', error);
        // Silently fail for campaigns - it's optional
    }
}

function renderCampaigns() {
    const campaignsSection = document.getElementById('campaignsSection');
    const campaignsList = document.getElementById('campaignsList');
    
    if (!state.campaigns || state.campaigns.length === 0) {
        return;
    }
    
    // Filter to show only top 5 hot campaigns
    const hotCampaigns = state.campaigns
        .filter(c => c.is_hot && c.is_active)
        .sort((a, b) => a.display_order - b.display_order)
        .slice(0, 5);
    
    if (hotCampaigns.length === 0) {
        return;
    }
    
    // Always show campaigns section
    campaignsSection.style.display = 'block';
    
    campaignsList.innerHTML = hotCampaigns.map(campaign => `
        <div class="campaign-card" onclick="selectCampaign(${campaign.id})" data-campaign-id="${campaign.id}">
            <div class="campaign-header">
                <div class="campaign-icon">${campaign.icon}</div>
                <div class="campaign-info">
                    <div class="campaign-title">${campaign.title}</div>
                    <div class="campaign-country">
                        <span>${campaign.country.flag}</span>
                        <span>${campaign.country.name_persian || campaign.country.name}</span>
                    </div>
                </div>
            </div>
            <div class="campaign-description">${campaign.description || ''}</div>
            <div class="campaign-meta">
                <div class="campaign-meta-item">
                    <span>👥</span>
                    <span>${campaign.recipient_ids.length} گیرنده</span>
                </div>
                <div class="campaign-meta-item">
                    <span>📝</span>
                    <span>${campaign.topic_ids.length} موضوع</span>
                </div>
            </div>
        </div>
    `).join('');
}

async function selectCampaign(campaignId) {
    const campaign = state.campaigns.find(c => c.id === campaignId);
    if (!campaign) return;
    
    console.log('🔥 Campaign selected:', campaign.title);
    
    // Set campaign mode
    state.campaignMode = true;
    state.selectedCampaign = campaign.id;
    
    // Pre-fill selections
    state.selectedCountry = campaign.country.code;
    state.selectedRecipients = new Set(campaign.recipient_ids);
    state.selectedTopics = new Set(campaign.topic_ids);
    
    // Hide hero, show stepper
    document.querySelector('.hero').style.display = 'none';
    elements.stepperContainer.classList.add('active');
    
    // Load data and move to step 3 (residency) since country/recipients/topics are pre-selected
    await loadCountries();
    await loadTopics();
    
    // Auto-load recipients for the campaign country
    await loadRecipients(campaign.country.code);
    
    // Jump to step 3 (residency/name step)
    goToStep(3);
    state.selectedCampaign = campaignId;
    
    // Start the stepper with pre-filled data
    document.querySelector('.hero').style.display = 'none';
    elements.stepperContainer.classList.add('active');
    
    // Load data
    loadCountries().then(() => {
        elements.countrySelect.value = state.selectedCountry;
        return handleCountryChange({ target: { value: state.selectedCountry } });
    });
    loadTopics();
    
    showNotification(`کمپین "${campaign.title}" انتخاب شد`, 'info');
}

async function generateEmail() {
    const userName = elements.userName ? elements.userName.value.trim() : '';
    
    const payload = {
        country_code: state.selectedCountry,
        recipient_ids: Array.from(state.selectedRecipients),
        topic_ids: Array.from(state.selectedTopics),
        is_resident: state.isResident,
        user_name: userName || null,
        campaign_id: state.selectedCampaign || null
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
    console.log('🚀 ActForIran App Loaded');
    console.log('📡 API Base:', API_BASE);
    
    // Check if all elements exist
    const missingElements = [];
    for (const [key, element] of Object.entries(elements)) {
        if (!element) {
            missingElements.push(key);
            console.error(`❌ Missing element: ${key}`);
        }
    }
    
    if (missingElements.length > 0) {
        console.error('⚠️ Some elements are missing:', missingElements);
        showNotification('خطا در بارگذاری صفحه', 'error');
    } else {
        console.log('✅ All elements found');
    }
    
    // Load campaigns on page load
    loadCampaigns();
    
    // Initialize stepper
    try {
        initStepper();
        console.log('✅ Stepper initialized');
    } catch (error) {
        console.error('❌ Error initializing stepper:', error);
        showNotification('خطا در راه‌اندازی', 'error');
    }
    
    // Test button click manually (Safari compatibility fallback)
    if (elements.startBtn) {
        console.log('✅ Start button found, adding listener...');
        elements.startBtn.onclick = function() {
            console.log('🎯 Start button clicked!');
            try {
                document.querySelector('.hero').style.display = 'none';
                elements.stepperContainer.classList.add('active');
                loadCountries();
                loadTopics();
                showNotification('خوش آمدید! لطفاً کشور را انتخاب کنید', 'success');
            } catch (error) {
                console.error('❌ Error in start button handler:', error);
                showNotification('خطا در شروع کمپین', 'error');
            }
        };
    } else {
        console.error('❌ Start button not found!');
    }
});

