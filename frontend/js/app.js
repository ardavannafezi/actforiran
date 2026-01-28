const API_BASE = 'https://back.actforiran.org';

const state = {
  step: 1,
  countries: [],
  recipients: [],
  topics: [],
  selectedCountry: '',
  selectedRecipients: new Set(),
  selectedTopics: new Set(),
  isResident: null,
  mailto: ''
};

const stepper = document.getElementById('stepper');
const campaignPanel = document.getElementById('campaignPanel');
const countrySelect = document.getElementById('countrySelect');
const recipientsList = document.getElementById('recipientsList');
const topicsList = document.getElementById('topicsList');
const emailSubject = document.getElementById('emailSubject');
const emailBody = document.getElementById('emailBody');
const generateEmail = document.getElementById('generateEmail');
const openGmail = document.getElementById('openGmail');

const startCampaigns = document.getElementById('startCampaigns');
const startCountry = document.getElementById('startCountry');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

// Persian number conversion
function toPersianNumber(num) {
  const persianDigits = '۰۱۲۳۴۵۶۷۸۹';
  return num.toString().replace(/[0-9]/g, (w) => persianDigits[+w]);
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

startCampaigns.addEventListener('click', () => {
  campaignPanel.classList.add('active');
  stepper.classList.remove('active');
  stepper.setAttribute('aria-hidden', 'true');
  campaignPanel.setAttribute('aria-hidden', 'false');
});

startCountry.addEventListener('click', () => {
  campaignPanel.classList.remove('active');
  stepper.classList.add('active');
  stepper.setAttribute('aria-hidden', 'false');
  campaignPanel.setAttribute('aria-hidden', 'true');
  setStep(1);
});

prevBtn.addEventListener('click', () => {
  if (state.step > 1) {
    setStep(state.step - 1);
  }
});

nextBtn.addEventListener('click', async () => {
  if (!validateCurrentStep()) {
    return;
  }

  if (state.step < 5) {
    setStep(state.step + 1);
  }
});

function validateCurrentStep() {
  switch (state.step) {
    case 1:
      if (!state.selectedCountry) {
        showNotification('لطفاً یک کشور انتخاب کنید.', 'error');
        return false;
      }
      break;
    case 2:
      if (state.selectedRecipients.size === 0) {
        showNotification('لطفاً حداقل یک گیرنده انتخاب کنید.', 'error');
        return false;
      }
      break;
    case 3:
      if (state.isResident === null) {
        showNotification('لطفاً وضعیت اقامت خود را مشخص کنید.', 'error');
        return false;
      }
      break;
    case 4:
      if (state.selectedTopics.size === 0) {
        showNotification('لطفاً حداقل یک موضوع انتخاب کنید.', 'error');
        return false;
      }
      break;
  }
  return true;
}

countrySelect.addEventListener('change', async (event) => {
  state.selectedCountry = event.target.value;
  if (!state.selectedCountry) return;
  
  setButtonLoading(nextBtn, true);
  try {
    await loadRecipients(state.selectedCountry);
    showNotification('گیرندگان با موفقیت بارگذاری شدند.', 'success');
  } catch (error) {
    showNotification('خطا در بارگذاری گیرندگان.', 'error');
  } finally {
    setButtonLoading(nextBtn, false);
  }
});

// Generate email button handler
generateEmail?.addEventListener('click', async () => {
  if (!validateCurrentStep()) {
    return;
  }
  
  setButtonLoading(generateEmail, true);
  try {
    await generateEmailContent();
    showNotification('ایمیل با موفقیت تولید شد!', 'success');
  } catch (error) {
    showNotification('خطا در تولید ایمیل. لطفاً دوباره تلاش کنید.', 'error');
  } finally {
    setButtonLoading(generateEmail, false);
  }
});

function setStep(step) {
  state.step = step;
  const progress = ((step - 1) / 4) * 100;
  document.documentElement.style.setProperty('--progress', `${progress}%`);

  // Update panels
  document.querySelectorAll('.panel').forEach(panel => {
    panel.classList.toggle('active', Number(panel.dataset.panel) === step);
  });
  
  // Update step indicators
  document.querySelectorAll('.step').forEach(stepEl => {
    const stepNum = Number(stepEl.dataset.step);
    stepEl.classList.toggle('active', stepNum === step);
    stepEl.classList.toggle('completed', stepNum < step);
  });
  
  // Update buttons
  prevBtn.disabled = step === 1;
  
  if (step === 5) {
    nextBtn.style.display = 'none';
    // Generate email button is already in the step 5 panel
  } else {
    nextBtn.style.display = 'flex';
    nextBtn.innerHTML = '<span>بعدی</span><span>→</span>';
  }
  
  // Add entrance animation to active panel
  const activePanel = document.querySelector('.panel.active');
  if (activePanel) {
    activePanel.style.animation = 'none';
    activePanel.offsetHeight; // Trigger reflow
    activePanel.style.animation = 'fadeInUp 0.5s ease forwards';
  }
}

function renderRecipients() {
  recipientsList.innerHTML = state.recipients.map(recipient => {
    const id = recipient.id;
    const isChecked = state.selectedRecipients.has(id) ? 'checked' : '';
    return `
      <label class="list-item">
        <input type="checkbox" data-id="${id}" ${isChecked}>
        <span>${recipient.full_name} — ${recipient.display_title || recipient.custom_title || recipient.role_name}</span>
      </label>
    `;
  }).join('');

  recipientsList.querySelectorAll('input[type="checkbox"]').forEach(box => {
    box.addEventListener('change', () => {
      const id = Number(box.dataset.id);
      if (box.checked) {
        state.selectedRecipients.add(id);
      } else {
        state.selectedRecipients.delete(id);
      }
      updateRecipientCount();
    });
  });
}

function renderTopics() {
  topicsList.innerHTML = state.topics.map(topic => {
    const id = topic.id;
    const isChecked = state.selectedTopics.has(id) ? 'checked' : '';
    return `
      <label class="list-item">
        <input type="checkbox" data-id="${id}" ${isChecked}>
        <span>${topic.display_title}</span>
      </label>
    `;
  }).join('');

  topicsList.querySelectorAll('input[type="checkbox"]').forEach(box => {
    box.addEventListener('change', () => {
      const id = Number(box.dataset.id);
      if (box.checked) {
        state.selectedTopics.add(id);
      } else {
        state.selectedTopics.delete(id);
      }
      updateTopicCount();
    });
  });
}

function updateRecipientCount() {
  const count = state.selectedRecipients.size;
  const countText = count > 0 ? ` (${toPersianNumber(count)} انتخاب شده)` : '';
  const header = document.querySelector('[data-panel="2"] .panel-header h3');
  if (header) {
    header.textContent = `انتخاب گیرندگان${countText}`;
  }
}

function updateTopicCount() {
  const count = state.selectedTopics.size;
  const countText = count > 0 ? ` (${toPersianNumber(count)} انتخاب شده)` : '';
  const header = document.querySelector('[data-panel="4"] .panel-header h3');
  if (header) {
    header.textContent = `انتخاب موضوعات${countText}`;
  }
}

async function loadCountries() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/countries`);
    if (!response.ok) throw new Error('Failed to load countries');
    
    const data = await response.json();
    state.countries = data.countries || [];
    countrySelect.innerHTML = '<option value="">یک کشور انتخاب کنید...</option>' +
      state.countries.map(c => `<option value="${c.code}">${c.name}</option>`).join('');
  } catch (error) {
    console.error('Error loading countries:', error);
    showNotification('خطا در بارگذاری کشورها.', 'error');
  }
}

async function loadRecipients(countryCode) {
  const response = await fetch(`${API_BASE}/api/v1/recipients?country_code=${countryCode}`);
  if (!response.ok) throw new Error('Failed to load recipients');
  
  const data = await response.json();
  state.recipients = data.recipients || [];
  state.selectedRecipients.clear();
  renderRecipients();
  updateRecipientCount();
}

async function loadTopics() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/topics`);
    if (!response.ok) throw new Error('Failed to load topics');
    
    const data = await response.json();
    state.topics = data.topics || [];
    renderTopics();
    updateTopicCount();
  } catch (error) {
    console.error('Error loading topics:', error);
    showNotification('خطا در بارگذاری موضوعات.', 'error');
  }
}

async function generateEmailContent() {
  const payload = {
    country_code: state.selectedCountry,
    recipient_ids: Array.from(state.selectedRecipients),
    topic_ids: Array.from(state.selectedTopics),
    is_resident: state.isResident === 'yes'
  };

  const response = await fetch(`${API_BASE}/api/v1/generate-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error('Failed to generate email');
  }

  const data = await response.json();
  emailSubject.value = data.subject || '';
  emailBody.value = data.body || '';
  state.mailto = data.mailto_link || '';
  
  // Enable the Gmail button
  openGmail.disabled = !state.mailto;
  
  // Add some visual feedback
  emailSubject.style.animation = 'fadeInUp 0.5s ease';
  emailBody.style.animation = 'fadeInUp 0.5s ease 0.1s both';
}

openGmail.addEventListener('click', () => {
  if (state.mailto) {
    window.location.href = state.mailto;
    showNotification('در حال باز کردن کلاینت ایمیل...', 'success');
  }
});

// Radio button handler for residency
document.querySelectorAll('input[name="resident"]').forEach(radio => {
  radio.addEventListener('change', () => {
    state.isResident = radio.value;
  });
});

// Add some visual enhancements
document.addEventListener('DOMContentLoaded', () => {
  // Add scroll animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
      }
    });
  }, observerOptions);
  
  // Observe elements for scroll animations
  document.querySelectorAll('.info-card, .stat-card').forEach(card => {
    observer.observe(card);
  });
});

// Initialize the application
(async function init() {
  try {
    await Promise.all([
      loadCountries(),
      loadTopics()
    ]);
    setStep(1);
    showNotification('سیستم آماده و فعال است.', 'success');
  } catch (error) {
    console.error('Initialization error:', error);
    showNotification('خطا در راه‌اندازی سیستم.', 'error');
  }
})();

