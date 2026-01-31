# CRITICAL FIXES NEEDED FOR ADMIN.JS

## Architecture Summary
- **TOPICS**: Country → Topic → Recipients
- **CAMPAIGNS**: Campaigns → Recipients (NO topics, NO country)

## Backend Status: ✅ COMPLETE
- Models updated
- Schemas updated  
- API endpoints updated
- Database migrations added

## Frontend HTML Status: ✅ COMPLETE
- Topic modal has country selector + recipient checkboxes
- Campaign modal has recipient multi-select

## Frontend JavaScript Status: ❌ NEEDS FIXING

### Files to Update:
`/frontend/js/admin.js` - Lines 650-900

---

## JAVASCRIPT FIXES REQUIRED

### 1. Topic Functions (Lines ~600-700)

**Add Country Loading to Topic Modal:**
```javascript
// Add this function
async function loadCountriesForTopic() {
    const select = document.getElementById('topicCountry');
    if (!select) return;
    
    const response = await fetch(`${API_BASE}/api/v1/countries`);
    const data = await response.json();
    countries = data.countries || [];
    
    select.innerHTML = '<option value="">انتخاب کشور...</option>' +
        countries.map(c => `<option value="${c.code}">${c.flag || ''} ${c.name_persian || c.name}</option>`).join('');
}

// Add country change handler to filter recipients
document.getElementById('topicCountry')?.addEventListener('change', async (e) => {
    const countryCode = e.target.value;
    if (!countryCode) {
        document.getElementById('topicRecipientsSelector').innerHTML = 
            '<div style="color: var(--text-secondary);">ابتدا کشور را انتخاب کنید</div>';
        return;
    }
    
    // Load recipients for selected country
    const response = await fetch(`${API_BASE}/api/v1/recipients?country_code=${countryCode}`);
    const data = await response.json();
    const recipients = data.recipients || [];
    
    renderTopicRecipientsSelector([], recipients);
});
```

**Update renderTopicRecipientsSelector:**
```javascript
function renderTopicRecipientsSelector(selectedIds = [], recipients = []) {
    const container = document.getElementById('topicRecipientsSelector');
    if (!container) return;
    
    if (!recipients || recipients.length === 0) {
        container.innerHTML = '<div style="color: var(--text-secondary);">گیرنده‌ای برای این کشور یافت نشد</div>';
        return;
    }
    
    container.innerHTML = recipients.map(r => `
        <label style="display: flex; align-items: center; padding: 8px; cursor: pointer; border-radius: 4px; margin-bottom: 4px; background: var(--bg-surface);">
            <input type="checkbox" value="${r.id}" ${selectedIds.includes(r.id) ? 'checked' : ''} style="margin-left: 8px;">
            <span style="flex: 1;">${r.full_name} - ${r.custom_title || r.role_name}</span>
        </label>
    `).join('');
}
```

**Update Topic Submit Handler:**
```javascript
document.getElementById('topicForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('topicId').value;
    const countryCode = document.getElementById('topicCountry').value;
    
    if (!countryCode) {
        showNotification('کشور را انتخاب کنید', 'error');
        return;
    }
    
    const selectedRecipients = Array.from(
        document.querySelectorAll('#topicRecipientsSelector input[type="checkbox"]:checked')
    ).map(cb => parseInt(cb.value));
    
    const payload = {
        display_title: document.getElementById('topicTitle').value,
        slug: document.getElementById('topicSlug').value,
        description: document.getElementById('topicDescription').value || null,
        country_code: countryCode,
        recipient_ids: selectedRecipients
    };
    
    // Rest remains same...
});
```

**Update addTopicBtn handler:**
```javascript
document.getElementById('addTopicBtn').addEventListener('click', async () => {
    document.getElementById('topicModalTitle').textContent = 'افزودن موضوع';
    document.getElementById('topicForm').reset();
    document.getElementById('topicId').value = '';
    
    await loadCountriesForTopic();
    document.getElementById('topicRecipientsSelector').innerHTML = 
        '<div style="color: var(--text-secondary);">ابتدا کشور را انتخاب کنید</div>';
    
    openModal('topicModal');
});
```

---

### 2. Campaign Functions (Lines ~750-900)

**COMPLETELY REPLACE Campaign Functions:**

```javascript
// DELETE these old functions:
// - loadAllTopics()
// - openCampaignModal() (old version)
// - saveCampaign() (old version)

// REPLACE WITH THESE NEW FUNCTIONS:

async function loadRecipientsForCampaign() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/admin/recipients`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load recipients');
        
        const data = await response.json();
        campaignRecipients = Array.isArray(data) ? data : (data.recipients || []);
        
    } catch (error) {
        console.error('Error loading recipients:', error);
    }
}

async function openCampaignModal(campaignId = null) {
    const modal = document.getElementById('campaignModal');
    const title = document.getElementById('campaignModalTitle');
    const form = document.getElementById('campaignForm');
    
    // Load all recipients
    await loadRecipientsForCampaign();
    
    // Populate recipients select (grouped by country)
    const recipientsSelect = document.getElementById('campaignRecipients');
    const grouped = campaignRecipients.reduce((acc, r) => {
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
        Array.from(recipientsSelect.options).forEach(opt => {
            opt.selected = campaign.recipient_ids.includes(parseInt(opt.value));
        });
    } else {
        // Add mode
        title.textContent = 'افزودن کمپین';
        form.reset();
        document.getElementById('campaignId').value = '';
    }
    
    modal.classList.add('active');
}

async function saveCampaign(e) {
    e.preventDefault();
    
    const campaignId = document.getElementById('campaignId').value;
    const recipientIds = Array.from(document.getElementById('campaignRecipients').selectedOptions)
        .map(opt => parseInt(opt.value));
    
    if (recipientIds.length === 0) {
        showNotification('حداقل یک گیرنده انتخاب کنید', 'error');
        return;
    }
    
    const payload = {
        title: document.getElementById('campaignTitle').value,
        slug: document.getElementById('campaignSlug').value,
        description: document.getElementById('campaignDescription').value || '',
        icon: document.getElementById('campaignIcon').value || '🔥',
        recipient_ids: recipientIds,
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
```

**Update renderCampaigns (remove topic_ids):**
```javascript
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
                </div>
            </div>
            <div class="campaign-admin-description">${campaign.description || ''}</div>
            <div class="campaign-admin-stats">
                <span>👥 ${toPersian(campaign.recipient_ids.length)} گیرنده</span>
                ${campaign.is_hot ? '<span style="color: var(--accent-red);">🔥 داغ</span>' : ''}
            </div>
            <div class="campaign-admin-actions">
                <button class="btn btn-secondary" onclick="editCampaign(${campaign.id})">ویرایش</button>
                <button class="btn btn-error" onclick="deleteCampaign(${campaign.id})">حذف</button>
            </div>
        </div>
    `).join('');
}
```

---

### 3. Wire up addCampaignBtn

```javascript
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
```

---

## QUICK FIX CHECKLIST

- [ ] Add `loadCountriesForTopic()` function
- [ ] Add country change handler to topic modal
- [ ] Update `renderTopicRecipientsSelector()` to accept recipients parameter
- [ ] Update topic form submit to include country_code
- [ ] Delete old campaign functions (loadAllTopics that loads topics)
- [ ] Add `loadRecipientsForCampaign()` function
- [ ] Replace `openCampaignModal()` with recipient-based version
- [ ] Replace `saveCampaign()` with recipient-based version
- [ ] Update `renderCampaigns()` to remove topic_ids display
- [ ] Wire up `addCampaignBtn` click handler

---

## TESTING CHECKLIST

After making changes, test:

1. **Topics:**
   - [ ] Click "افزودن موضوع" button - modal opens
   - [ ] Select country - recipients load for that country
   - [ ] Select recipients and save - topic created with country_code + recipient_ids
   - [ ] Edit topic - country and recipients pre-selected
   - [ ] Topics table shows country name

2. **Campaigns:**
   - [ ] Click "افزودن کمپین" button - modal opens
   - [ ] Recipients grouped by country in multi-select
   - [ ] Select recipients and save - campaign created with recipient_ids only
   - [ ] Edit campaign - recipients pre-selected
   - [ ] Campaigns list shows recipient count (no topic count)

3. **Database:**
   - [ ] Check advocacy_topics table has country_code column
   - [ ] Check advocacy_topics table has recipient_ids column
   - [ ] Check campaigns table does NOT have topic_ids column
   - [ ] Check campaigns table does NOT have country_code column

---

## STATUS

**Backend:** ✅ 100% Complete
**Frontend HTML:** ✅ 100% Complete
**Frontend JS:** ❌ 0% Complete - needs all fixes above

**Estimated Time:** 15-20 minutes to apply all JavaScript changes.
