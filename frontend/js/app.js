const apiBase = document.body.dataset.apiBase || "https://back.actforiran.org";

const state = {
  countries: [],
  recipients: [],
  topics: [],
  selectedCountry: null,
};

const ui = {
  countrySelect: document.getElementById("countrySelect"),
  recipientsList: document.getElementById("recipientsList"),
  topicsList: document.getElementById("topicsList"),
  generateButton: document.getElementById("generateButton"),
  notice: document.getElementById("notice"),
  preview: document.getElementById("preview"),
  subjectOutput: document.getElementById("subjectOutput"),
  bodyOutput: document.getElementById("bodyOutput"),
  gmailButton: document.getElementById("gmailButton"),
};

function showNotice(message) {
  ui.notice.textContent = message;
  ui.notice.style.display = "block";
}

function clearNotice() {
  ui.notice.style.display = "none";
  ui.notice.textContent = "";
}

async function fetchJSON(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json();
}

function renderCountryOptions() {
  ui.countrySelect.innerHTML = `<option value="">Select a country</option>`;
  state.countries.forEach((country) => {
    const option = document.createElement("option");
    option.value = country.code;
    option.textContent = country.name;
    ui.countrySelect.appendChild(option);
  });
}

function renderRecipients() {
  ui.recipientsList.innerHTML = "";

  if (!state.recipients.length) {
    ui.recipientsList.innerHTML = `<p class="helper">No recipients available yet for this country.</p>`;
    return;
  }

  state.recipients.forEach((recipient) => {
    const wrapper = document.createElement("label");
    wrapper.className = "checkbox-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = recipient.id;

    const text = document.createElement("span");
    text.innerHTML = `<strong>${recipient.full_name}</strong><br>${recipient.display_title}`;

    wrapper.appendChild(checkbox);
    wrapper.appendChild(text);
    ui.recipientsList.appendChild(wrapper);
  });
}

function renderTopics() {
  ui.topicsList.innerHTML = "";

  if (!state.topics.length) {
    ui.topicsList.innerHTML = `<p class="helper">No topics have been approved yet.</p>`;
    return;
  }

  state.topics.forEach((topic) => {
    const wrapper = document.createElement("label");
    wrapper.className = "checkbox-item";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = topic.id;

    const text = document.createElement("span");
    text.innerHTML = `<strong>${topic.display_title}</strong><br>${topic.description || ""}`;

    wrapper.appendChild(checkbox);
    wrapper.appendChild(text);
    ui.topicsList.appendChild(wrapper);
  });
}

function getSelectedValues(container) {
  return Array.from(container.querySelectorAll("input[type='checkbox']:checked")).map((el) =>
    Number(el.value)
  );
}

function getResidency() {
  const selected = document.querySelector("input[name='residency']:checked");
  if (!selected) {
    return null;
  }
  return selected.value === "yes";
}

async function loadCountries() {
  const data = await fetchJSON("/api/v1/countries");
  state.countries = data.countries || [];
  renderCountryOptions();
}

async function loadTopics() {
  const data = await fetchJSON("/api/v1/topics");
  state.topics = data.topics || [];
  renderTopics();
}

async function loadRecipients(countryCode) {
  const data = await fetchJSON(`/api/v1/recipients?country_code=${countryCode}`);
  state.recipients = data.recipients || [];
  renderRecipients();
}

async function handleGenerate() {
  clearNotice();
  ui.preview.style.display = "none";
  ui.gmailButton.disabled = true;

  const countryCode = ui.countrySelect.value;
  if (!countryCode) {
    showNotice("Please select a country.");
    return;
  }

  const recipientIds = getSelectedValues(ui.recipientsList);
  if (!recipientIds.length) {
    showNotice("Please choose at least one recipient.");
    return;
  }

  const topicIds = getSelectedValues(ui.topicsList);
  if (!topicIds.length) {
    showNotice("Please choose at least one topic.");
    return;
  }

  const isResident = getResidency();
  if (isResident === null) {
    showNotice("Please tell us if you are a resident of the selected country.");
    return;
  }

  ui.generateButton.disabled = true;
  ui.generateButton.textContent = "Generating...";

  try {
    const data = await fetchJSON("/api/v1/generate-email", {
      method: "POST",
      body: JSON.stringify({
        country_code: countryCode,
        recipient_ids: recipientIds,
        topic_ids: topicIds,
        is_resident: isResident,
      }),
    });

    ui.subjectOutput.textContent = data.subject || "";
    ui.bodyOutput.textContent = data.body || "";

    ui.gmailButton.onclick = () => {
      if (data.mailto_link) {
        window.location.href = data.mailto_link;
      }
    };
    ui.gmailButton.disabled = !data.mailto_link;

    ui.preview.style.display = "block";
  } catch (error) {
    showNotice(`Failed to generate email: ${error.message}`);
    ui.gmailButton.disabled = true;
  } finally {
    ui.generateButton.disabled = false;
    ui.generateButton.textContent = "Generate Email";
  }
}

ui.countrySelect.addEventListener("change", async (event) => {
  clearNotice();
  const code = event.target.value;
  if (!code) {
    state.recipients = [];
    renderRecipients();
    return;
  }
  try {
    await loadRecipients(code);
  } catch (error) {
    showNotice(`Failed to load recipients: ${error.message}`);
  }
});

ui.generateButton.addEventListener("click", handleGenerate);

(async function init() {
  try {
    await Promise.all([loadCountries(), loadTopics()]);
  } catch (error) {
    showNotice(`Failed to load initial data: ${error.message}`);
  }
})();
