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
const openGmail = document.getElementById('openGmail');

const startCampaigns = document.getElementById('startCampaigns');
const startCountry = document.getElementById('startCountry');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');

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
  if (state.step === 1 && !state.selectedCountry) {
    alert('لطفا کشور را انتخاب کنید.');
    return;
  }
  if (state.step === 2 && state.selectedRecipients.size === 0) {
    alert('حداقل یک مخاطب انتخاب کنید.');
    return;
  }
  if (state.step === 3 && state.isResident === null) {
    alert('لطفا وضعیت سکونت را انتخاب کنید.');
    return;
  }
  if (state.step === 4 && state.selectedTopics.size === 0) {
    alert('حداقل یک موضوع انتخاب کنید.');
    return;
  }

  if (state.step === 4) {
    await generateEmail();
  }

  if (state.step < 5) {
    setStep(state.step + 1);
  }
});

countrySelect.addEventListener('change', async (event) => {
  state.selectedCountry = event.target.value;
  if (!state.selectedCountry) return;
  await loadRecipients(state.selectedCountry);
});

function setStep(step) {
  state.step = step;
  document.querySelectorAll('.panel').forEach(panel => {
    panel.classList.toggle('active', Number(panel.dataset.panel) === step);
  });
  document.querySelectorAll('.step').forEach(stepEl => {
    const stepNum = Number(stepEl.dataset.step);
    stepEl.classList.toggle('active', stepNum === step);
    stepEl.classList.toggle('completed', stepNum < step);
  });
  prevBtn.disabled = step === 1;
  nextBtn.textContent = step === 5 ? 'پایان' : 'بعدی';
}

function renderRecipients() {
  recipientsList.innerHTML = state.recipients.map(recipient => {
    const id = recipient.id;
    return `
      <label class="list-item">
        <input type="checkbox" data-id="${id}">
        <span>${recipient.full_name} — ${recipient.display_title}</span>
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
    });
  });
}

function renderTopics() {
  topicsList.innerHTML = state.topics.map(topic => {
    const id = topic.id;
    return `
      <label class="list-item">
        <input type="checkbox" data-id="${id}">
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
    });
  });
}

async function loadCountries() {
  const response = await fetch(`${API_BASE}/api/v1/countries`);
  const data = await response.json();
  state.countries = data.countries || [];
  countrySelect.innerHTML = '<option value="">انتخاب کشور...</option>' +
    state.countries.map(c => `<option value="${c.code}">${c.name}</option>`).join('');
}

async function loadRecipients(countryCode) {
  const response = await fetch(`${API_BASE}/api/v1/recipients?country_code=${countryCode}`);
  const data = await response.json();
  state.recipients = data.recipients || [];
  state.selectedRecipients.clear();
  renderRecipients();
}

async function loadTopics() {
  const response = await fetch(`${API_BASE}/api/v1/topics`);
  const data = await response.json();
  state.topics = data.topics || [];
  renderTopics();
}

async function generateEmail() {
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
    alert('خطا در تولید ایمیل. لطفا دوباره تلاش کنید.');
    return;
  }

  const data = await response.json();
  emailSubject.value = data.subject || '';
  emailBody.value = data.body || '';
  state.mailto = data.mailto_link || '';
  openGmail.disabled = !state.mailto;
}

openGmail.addEventListener('click', () => {
  if (state.mailto) {
    window.location.href = state.mailto;
  }
});

document.querySelectorAll('input[name="resident"]').forEach(radio => {
  radio.addEventListener('change', () => {
    state.isResident = radio.value;
  });
});

(async function init() {
  await loadCountries();
  await loadTopics();
  setStep(1);
})();
