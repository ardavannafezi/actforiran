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
    citizenshipStatus: null,
    citizenshipCountry: null,
    recipientsPage: 1,
    recipientsPageSize: 30,
    recipientsHasMore: true,
    selectedCampaign: null,
    campaignMode: false, // Track if user started from campaign
    generatedEmail: {
        groups: []
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
    emailGroups: document.getElementById('emailGroups'),
    citizenshipCountryGroup: document.getElementById('citizenshipCountryGroup'),
    citizenshipCountrySelect: document.getElementById('citizenshipCountrySelect')
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
            updateCitizenshipCountryVisibility();
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
    
    // Citizenship status radio buttons
    document.querySelectorAll('input[name=\"citizenship_status\"]').forEach(radio => {
        radio.onclick = function(e) {
            state.citizenshipStatus = e.target.value;
            updateCitizenshipCountryVisibility();
        };
    });

    if (elements.citizenshipCountrySelect) {
        elements.citizenshipCountrySelect.onchange = function(e) {
            state.citizenshipCountry = e.target.value || null;
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
    
    // Scroll to top of stepper container to keep form in view
    const stepperContainer = document.querySelector('.stepper-container');
    if (stepperContainer) {
        stepperContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
            if (!state.citizenshipStatus) {
                showNotification('لطفاً وضعیت شهروندی خود را مشخص کنید', 'error');
                return false;
            }
            if (state.campaignMode && state.citizenshipStatus === 'selected_country_citizen' && !state.citizenshipCountry) {
                showNotification('لطفاً کشور شهروندی/اقامت خود را انتخاب کنید', 'error');
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
        // Fetch suggested country based on IP
        let suggestedCountry = null;
        try {
            const suggestResponse = await fetch(`${API_BASE}/api/v1/suggest-country`);
            if (suggestResponse.ok) {
                const suggestData = await suggestResponse.json();
                if (suggestData.suggested_country) {
                    suggestedCountry = suggestData.suggested_country;
                }
            }
        } catch (err) {
            console.log('Could not fetch suggested country:', err);
        }
        
        const response = await fetch(`${API_BASE}/api/v1/countries`);
        if (!response.ok) throw new Error('Failed to load countries');
        
        const data = await response.json();
        state.countries = data.countries || [];
        
        elements.countrySelect.innerHTML = '<option value="">یک کشور انتخاب کنید...</option>' +
            state.countries.map(c => `<option value="${c.code}">${c.flag || ''} ${c.name_persian || c.name}</option>`).join('');

        // Show suggested country hint
        const hintElement = document.getElementById('suggestedCountryHint');
        if (suggestedCountry && hintElement) {
            hintElement.textContent = `(پیشنهاد: ${suggestedCountry.flag} ${suggestedCountry.name})`;
            // Auto-select suggested country
            elements.countrySelect.value = suggestedCountry.code;
            handleCountryChange({ target: { value: suggestedCountry.code } });
        }

        if (state.selectedCountry) {
            updateSelectedCountryLabels(state.selectedCountry);
        }

        if (elements.citizenshipCountrySelect) {
            elements.citizenshipCountrySelect.innerHTML = '<option value="">انتخاب کنید...</option>' +
                state.countries.map(c => `<option value="${c.code}">${c.flag || ''} ${c.name_persian || c.name}</option>`).join('');
            if (state.citizenshipCountry) {
                elements.citizenshipCountrySelect.value = state.citizenshipCountry;
            }
        }
        
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
        updateSelectedCountryLabels(null);
        return;
    }
    
    state.selectedCountry = countryCode;
    state.selectedRecipients.clear();
    state.recipientsPage = 1;
    state.recipientsHasMore = true;
    updateSelectedCountryLabels(countryCode);
    
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

function updateSelectedCountryLabels(countryCode) {
    const country = state.countries.find(c => c.code === countryCode);
    const countryName = country?.name_persian || country?.name || 'این کشور';

    if (elements.selectedCountryLabel) {
        elements.selectedCountryLabel.textContent = countryName;
    }
    if (elements.selectedCountryInline) {
        elements.selectedCountryInline.textContent = countryName;
    }
}

function updateCitizenshipCountryVisibility() {
    if (!elements.citizenshipCountryGroup) return;
    const shouldShow = state.campaignMode && state.citizenshipStatus === 'selected_country_citizen';
    elements.citizenshipCountryGroup.style.display = shouldShow ? 'block' : 'none';
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
    
    // Prefer hot campaigns, fallback to any active campaigns
    let hotCampaigns = state.campaigns
        .filter(c => (c.is_hot !== false) && (c.is_active !== false))
        .sort((a, b) => a.display_order - b.display_order)
        .slice(0, 5);

    if (hotCampaigns.length === 0) {
        hotCampaigns = state.campaigns
            .filter(c => c.is_active !== false)
            .sort((a, b) => a.display_order - b.display_order)
            .slice(0, 5);
    }

    if (hotCampaigns.length === 0) {
        campaignsSection.style.display = 'block';
        campaignsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 24px;">فعلاً کمپین فعالی ثبت نشده است</p>';
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
                    <div class="campaign-country"></div>
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
    state.selectedCountry = campaign.country?.code || campaign.country_code || '';
    state.selectedRecipients = new Set(campaign.recipient_ids);
    state.selectedTopics = new Set(campaign.topic_ids);
    state.citizenshipCountry = null;
    
    // Hide hero, show stepper
    document.querySelector('.hero').style.display = 'none';
    elements.stepperContainer.classList.add('active');
    
    // Load data and move to step 3 (residency) since country/recipients/topics are pre-selected
    await loadCountries();
    await loadTopics();
    
    // Auto-load recipients for the campaign country
    
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
    updateCitizenshipCountryVisibility();
    
    showNotification(`کمپین "${campaign.title}" انتخاب شد`, 'info');
}

async function generateEmail() {
    const userName = elements.userName ? elements.userName.value.trim() : '';
    if (!state.citizenshipStatus) {
        showNotification('لطفاً وضعیت شهروندی خود را مشخص کنید', 'error');
        return;
    }
    if (state.campaignMode && state.citizenshipStatus === 'selected_country_citizen' && !state.citizenshipCountry) {
        showNotification('لطفاً کشور شهروندی/اقامت خود را انتخاب کنید', 'error');
        return;
    }
    
    const payload = {
        country_code: state.selectedCountry,
        recipient_ids: Array.from(state.selectedRecipients),
        topic_ids: Array.from(state.selectedTopics),
        sender_citizenship_status: state.citizenshipStatus,
        user_name: userName || null,
        campaign_id: state.selectedCampaign || null
    };
    if (state.citizenshipCountry) {
        payload.sender_citizenship_country_code = state.citizenshipCountry;
    }
    
    try {
        if (elements.emailGroups) {
            elements.emailGroups.innerHTML = '<div class="loading">در حال تولید ایمیل...</div>';
        }
        
        const response = await fetch(`${API_BASE}/api/v1/generate-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
        let errorDetail = 'Failed to generate email';
        try {
            const error = await response.json();
            if (error && error.detail) {
                errorDetail = typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail);
            }
        } catch (e) {
            // ignore JSON parse errors
        }
        throw new Error(errorDetail);
        }
        
        const data = await response.json();
        
        state.generatedEmail.groups = data.groups || [];
        renderEmailGroups();
        showNotification('ایمیل‌ها با موفقیت تولید شد!', 'success');
        
    } catch (error) {
        console.error('Error generating email:', error);
        showNotification('خطا در تولید ایمیل با هوش مصنوعی', 'error');
    }
}

async function sendEmailGroup(index) {
    const group = state.generatedEmail.groups?.[index];
    if (!group) return;

    const subjectInput = document.getElementById(`emailSubject_${index}`);
    const bodyInput = document.getElementById(`emailBody_${index}`);
    const subject = subjectInput ? subjectInput.value : group.subject;
    const body = bodyInput ? bodyInput.value : group.body;

    const emails = group.recipients.map(r => r.email).join(',');
    const mailto = `mailto:?bcc=${encodeURIComponent(emails)}&subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;

    // Log analytics only on send click
    try {
        const logPayload = {
            country_code: state.selectedCountry,
            recipient_ids: group.recipient_ids,
            topic_ids: Array.from(state.selectedTopics),
            sender_citizenship_status: state.citizenshipStatus,
            user_name: elements.userName ? elements.userName.value.trim() : null,
            campaign_id: state.selectedCampaign || null,
            subject,
            body
        };
        if (state.citizenshipCountry) {
            logPayload.sender_citizenship_country_code = state.citizenshipCountry;
        }

        await fetch(`${API_BASE}/api/v1/log-email-send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(logPayload)
        });
    } catch (error) {
        console.error('Error logging email send:', error);
    }

    window.location.href = mailto;
    showNotification('در حال باز کردن برنامه ایمیل...', 'success');
}

window.sendEmailGroup = sendEmailGroup;

function renderEmailGroups() {
    if (!elements.emailGroups) return;
    if (!state.generatedEmail.groups || state.generatedEmail.groups.length === 0) {
        elements.emailGroups.innerHTML = '<div class="loading">ایمیلی تولید نشد</div>';
        return;
    }

    elements.emailGroups.innerHTML = state.generatedEmail.groups.map((group, idx) => `
        <div class="email-group-card">
            <div class="email-group-header">
                <div>گروه ${idx + 1} — ${group.recipients.length} گیرنده</div>
                <div class="email-group-meta">${group.recipients.map(r => r.name).join('، ')}</div>
            </div>
            <div class="form-group">
                <label>موضوع ایمیل</label>
                <input type="text" id="emailSubject_${idx}" class="form-input" value="${group.subject || ''}">
            </div>
            <div class="form-group">
                <label>متن ایمیل</label>
                <textarea id="emailBody_${idx}" class="form-textarea" rows="8">${group.body || ''}</textarea>
            </div>
            <button class="btn btn-primary btn-large" onclick="sendEmailGroup(${idx})">
                <span class="btn-icon">✉️</span>
                ارسال ایمیل گروه ${idx + 1}
            </button>
        </div>
    `).join('');
}

// ============================================
// RENDER FUNCTIONS
// ============================================
function renderRecipients() {
    if (state.recipients.length === 0) {
        elements.recipientsList.innerHTML = '<div class="loading">گیرنده‌ای برای این کشور یافت نشد</div>';
        return;
    }

    const allSelected = state.selectedRecipients.size === state.recipients.length;

    elements.recipientsList.innerHTML = `
        <label class="checkbox-item select-all ${allSelected ? 'selected' : ''}" data-id="all">
            <input type="checkbox" ${allSelected ? 'checked' : ''}>
            <div class="item-content">
                <div class="item-title">انتخاب همه گیرندگان</div>
                <div class="item-subtitle">همه افراد این کشور انتخاب شوند</div>
            </div>
        </label>
    `;
    
    state.recipientsPage = 1;
    state.recipientsHasMore = true;
    appendRecipientsPage();
    bindRecipientSelectionHandlers();
    setupRecipientsInfiniteScroll();
}

function appendRecipientsPage() {
    if (!state.recipientsHasMore) return;
    const start = (state.recipientsPage - 1) * state.recipientsPageSize;
    const end = start + state.recipientsPageSize;
    const slice = state.recipients.slice(start, end);
    if (slice.length === 0) {
        state.recipientsHasMore = false;
        return;
    }

    const fragment = document.createElement('div');
    fragment.innerHTML = slice.map(recipient => `
        <label class="checkbox-item ${state.selectedRecipients.has(recipient.id) ? 'selected' : ''}" data-id="${recipient.id}">
            <input type="checkbox" ${state.selectedRecipients.has(recipient.id) ? 'checked' : ''}>
            <div class="item-content">
                <div class="item-title">${recipient.full_name}</div>
                <div class="item-subtitle">${recipient.display_title} — ${recipient.country_name}</div>
            </div>
        </label>
    `).join('');

    elements.recipientsList.appendChild(fragment);
    state.recipientsPage += 1;
    if (end >= state.recipients.length) {
        state.recipientsHasMore = false;
    }
}

function bindRecipientSelectionHandlers() {
    // Add event listeners (iOS-friendly)
    elements.recipientsList.querySelectorAll('.checkbox-item').forEach(item => {
        if (item.dataset.bound === 'true') return;
        item.dataset.bound = 'true';
        const checkbox = item.querySelector('input[type="checkbox"]');

        const applySelection = () => {
            if (item.dataset.id === 'all') {
                if (checkbox.checked) {
                    state.recipients.forEach(r => state.selectedRecipients.add(r.id));
                } else {
                    state.selectedRecipients.clear();
                }
                renderRecipients();
                return;
            }

            const id = parseInt(item.dataset.id);
            if (checkbox.checked) {
                state.selectedRecipients.add(id);
                item.classList.add('selected');
            } else {
                state.selectedRecipients.delete(id);
                item.classList.remove('selected');
            }
        };

        checkbox.addEventListener('change', applySelection);

        const toggleFromCard = (e) => {
            if (e.target === checkbox) return;
            e.preventDefault();
            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        };

        item.addEventListener('click', toggleFromCard);
        item.addEventListener('touchend', toggleFromCard, { passive: false });
    });
}

function setupRecipientsInfiniteScroll() {
    if (!elements.recipientsList || elements.recipientsList.dataset.scrollBound === 'true') return;
    elements.recipientsList.dataset.scrollBound = 'true';
    elements.recipientsList.addEventListener('scroll', () => {
        const el = elements.recipientsList;
        if (!state.recipientsHasMore) return;
        if (el.scrollTop + el.clientHeight >= el.scrollHeight - 80) {
            appendRecipientsPage();
            bindRecipientSelectionHandlers();
        }
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
    
    // Add event listeners (iOS-friendly)
    elements.topicsList.querySelectorAll('.checkbox-item').forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        const id = parseInt(item.dataset.id);

        const applySelection = () => {
            if (checkbox.checked) {
                state.selectedTopics.add(id);
                item.classList.add('selected');
            } else {
                state.selectedTopics.delete(id);
                item.classList.remove('selected');
            }
        };

        checkbox.addEventListener('change', applySelection);

        const toggleFromCard = (e) => {
            if (e.target === checkbox) return;
            e.preventDefault();
            checkbox.checked = !checkbox.checked;
            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
        };

        item.addEventListener('click', toggleFromCard);
        item.addEventListener('touchend', toggleFromCard, { passive: false });
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

// ============================================
// TICKER SLIDER
// ============================================
let tickerMessages = [];
let currentTickerIndex = 0;

async function loadTickerMessages() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/ticker-messages`);
        if (response.ok) {
            const data = await response.json();
            tickerMessages = data.messages || [];
            if (tickerMessages.length > 0) {
                // Display first message
                const tickerText = document.getElementById('tickerText');
                if (tickerText) {
                    tickerText.textContent = tickerMessages[0];
                }
                // Start slider if multiple messages
                if (tickerMessages.length > 1) {
                    startTickerSlider();
                }
            } else {
                const tickerText = document.getElementById('tickerText');
                if (tickerText) {
                    tickerText.textContent = 'مرکز رسمی حمایت بین‌المللی — صدای شما به گوش جهان می‌رسد';
                }
            }
        }
    } catch (error) {
        console.error('Error loading ticker messages:', error);
        // Keep default message in HTML if API fails
    }
}

function startTickerSlider() {
    if (tickerMessages.length <= 1) return;
    
    setInterval(() => {
        const tickerText = document.getElementById('tickerText');
        if (!tickerText) return;
        
        // Fade out
        tickerText.style.opacity = '0';
        
        setTimeout(() => {
            currentTickerIndex = (currentTickerIndex + 1) % tickerMessages.length;
            tickerText.textContent = tickerMessages[currentTickerIndex];
            // Fade in
            tickerText.style.opacity = '1';
        }, 500);
    }, 5000); // Change every 5 seconds
}
// Load ticker on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadTickerMessages);
} else {
    loadTickerMessages();
}
