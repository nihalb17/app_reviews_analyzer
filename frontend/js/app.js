// ============================================
// Constants & Configuration
// ============================================
// Use window.API_BASE_URL if defined (for production), otherwise default to localhost
const API_BASE = window.API_BASE_URL || "http://localhost:8001/api";
const STATUS_STAGES = [
    "Started",
    "Data Fetched",
    "Themes Created",
    "Reviews Classified",
    "Insight Generation",
    "Report Generated",
    "Mail Sent"
];

const STATUS_PRIORITY = {
    "Started": 0,
    "Data Fetched": 1,
    "Themes Created": 2,
    "Reviews Classified": 3,
    "Insight Generation": 4,
    "Report Generated": 5,
    "Mail Sent": 6
};

const ROLES = ["Product", "Support", "UI/UX", "Leadership"];

// ============================================
// State Management
// ============================================
let HISTORY = [];
let currentTheme = localStorage.getItem('theme') || 'dark';
let isSendFormOpen = false;
let isDeleteModalOpen = false;
let deleteTargetId = null;

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initApp();
    fetchHistory();
});

function initTheme() {
    document.documentElement.setAttribute('data-theme', currentTheme);
}

function initApp() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div id="header-container"></div>
        <div id="main-content"></div>
        <div id="modal-container"></div>
    `;
    renderHeader();
}

// ============================================
// Theme Toggle
// ============================================
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    renderHeader();
}

// ============================================
// API Functions
// ============================================
async function fetchHistory() {
    try {
        const res = await fetch(`${API_BASE}/history`);
        if (!res.ok) throw new Error('Failed to fetch history');
        HISTORY = await res.json();
    } catch (err) {
        console.error("Failed to fetch history:", err);
        // Keep HISTORY as empty array on error
        HISTORY = [];
    }
    // Always update the UI, even on error (will show empty state)
    updateMainContent();
}

async function deleteHistoryItem(id) {
    try {
        const res = await fetch(`${API_BASE}/history/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete');
        fetchHistory();
        showNotification('Trigger deleted successfully', 'success');
    } catch (err) {
        console.error("Failed to delete:", err);
        showNotification('Failed to delete trigger', 'error');
    }
}

async function retryTrigger(id) {
    try {
        const res = await fetch(`${API_BASE}/actions/retry/${id}`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to retry');
        showNotification('Retry initiated', 'success');
        fetchHistory();
    } catch (err) {
        console.error("Failed to retry:", err);
        showNotification('Failed to retry trigger', 'error');
    }
}

// ============================================
// Render Functions
// ============================================
function renderHeader() {
    const container = document.getElementById('header-container');
    const themeIcon = currentTheme === 'light' ? 'moon' : 'sun';
    
    container.innerHTML = `
        <header class="header fade-in">
            <div class="header-left">
                <h1>Reviews Analyser</h1>
                <p>Send your app review insights</p>
            </div>
            <div class="header-right">
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Theme">
                    <i data-lucide="${themeIcon}" size="20"></i>
                </button>
                <button class="btn btn-primary" onclick="toggleSendForm(true)">
                    <i data-lucide="send" size="18"></i> Send Insights
                </button>
            </div>
        </header>
    `;
    initIcons();
}

function updateMainContent() {
    const container = document.getElementById('main-content');
    if (HISTORY.length === 0) {
        container.innerHTML = renderEmptyState();
    } else {
        container.innerHTML = renderHistoryTable();
    }
    initIcons();
}

function renderEmptyState() {
    return `
        <div class="history-section fade-in">
            <div class="history-header">
                <h2>Mail Trigger History</h2>
                <button class="refresh-btn" onclick="fetchHistory()" title="Refresh">
                    <i data-lucide="refresh-cw" size="18"></i>
                </button>
            </div>
            <div class="empty-state" style="margin-top: 0; border-radius: 16px;">
                <div class="empty-icon">
                    <i data-lucide="inbox" size="40"></i>
                </div>
                <h3>No triggers yet</h3>
                <p>Start by triggering a new review analysis for your stakeholders.</p>
                <button class="btn btn-primary" onclick="toggleSendForm(true)">
                    <i data-lucide="send" size="18"></i> Send Insights
                </button>
            </div>
        </div>
    `;
}

function renderHistoryTable() {
    return `
        <div class="history-section fade-in">
            <div class="history-header">
                <h2>Mail Trigger History</h2>
                <button class="refresh-btn" onclick="fetchHistory()" title="Refresh">
                    <i data-lucide="refresh-cw" size="18"></i>
                </button>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Trigger Time</th>
                            <th>Type</th>
                            <th>Role</th>
                            <th>Reviews</th>
                            <th>Time Period</th>
                            <th>Receiver Name</th>
                            <th>Receiver Email</th>
                            <th>Status</th>
                            <th>Actionables</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${HISTORY.map((row, index) => renderHistoryRow(row, index)).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function renderHistoryRow(row, index) {
    const isMostRecent = index === 0;
    const isFailed = row.status && row.status.includes('Failed');
    const isMailSent = row.status === 'Mail Sent';
    const statusClass = getStatusBadgeClass(row.status);
    
    return `
        <tr>
            <td>${row.trigger_time || row.date || '-'}</td>
            <td>${row.type || 'Manual'}</td>
            <td>${row.role || '-'}</td>
            <td>${row.reviews || '-'}</td>
            <td>${row.time_period || row.period || '-'}</td>
            <td>${row.receiver_name || row.receiverName || '-'}</td>
            <td>${row.receiver_email || row.recipient_email || '-'}</td>
            <td>
                <span class="badge ${statusClass}">${row.status || 'Unknown'}</span>
            </td>
            <td>
                <div class="action-btn-group">
                    ${renderActionButtons(row, isMostRecent, isFailed, isMailSent)}
                </div>
            </td>
        </tr>
    `;
}

function renderActionButtons(row, isMostRecent, isFailed, isMailSent) {
    // Most recent trigger with Mail Sent or Report Generated status - View PDF
    const isReportReady = isMailSent || row.status === 'Report Generated';
    if (isMostRecent && isReportReady) {
        return `
            <button class="action-btn view" onclick="handleViewPDF('${row.id}')">
                <i data-lucide="file-text" size="14"></i> View PDF
            </button>
        `;
    }
    
    // Most recent trigger with Failed status - Retry only
    if (isMostRecent && isFailed) {
        return `
            <button class="action-btn retry" onclick="handleRetry('${row.id}')">
                <i data-lucide="refresh-cw" size="14"></i> Retry
            </button>
        `;
    }
    
    // Other triggers - Delete only
    return `
        <button class="action-btn delete" onclick="openDeleteModal('${row.id}')">
            <i data-lucide="trash-2" size="14"></i> Delete
        </button>
    `;
}

function getStatusBadgeClass(status) {
    if (!status) return 'badge-info';
    if (status === 'Mail Sent') return 'badge-success';
    if (status.includes('Failed')) return 'badge-error';
    return 'badge-info';
}

// ============================================
// Modal Functions
// ============================================
function toggleSendForm(show) {
    isSendFormOpen = show;
    const modalContainer = document.getElementById('modal-container');
    
    if (show) {
        modalContainer.innerHTML = renderSendFormModal();
        initIcons();
    } else {
        modalContainer.innerHTML = '';
    }
}



function openDeleteModal(id) {
    deleteTargetId = id;
    isDeleteModalOpen = true;
    const modalContainer = document.getElementById('modal-container');
    modalContainer.innerHTML = renderDeleteModal();
    initIcons();
}

function closeDeleteModal() {
    deleteTargetId = null;
    isDeleteModalOpen = false;
    const modalContainer = document.getElementById('modal-container');
    if (!isSendFormOpen) {
        modalContainer.innerHTML = '';
    }
}

// ============================================
// Modal Renderers
// ============================================
function renderSendFormModal() {
    return `
        <div class="modal-overlay" onclick="if(event.target===this) toggleSendForm(false)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2>Send Insights</h2>
                    <button class="modal-close" onclick="toggleSendForm(false)">
                        <i data-lucide="x" size="20"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Number of Reviews <span class="required">*</span></label>
                        <input type="number" id="send-review-count" class="form-control" 
                               value="1000" min="0" max="2000" step="100" required>
                        <div class="form-hint">Default: 1000, Max: 2000</div>
                        <div class="form-error" id="send-review-count-error">Please enter a value between 10 and 2000</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Time Period <span class="required">*</span></label>
                        <select id="send-time-period" class="form-control" required>
                            ${Array.from({ length: 12 }, (_, i) => 
                                `<option value="${i + 1}" ${i + 1 === 7 ? 'selected' : ''}>Last ${i + 1} Week${i + 1 > 1 ? 's' : ''}</option>`
                            ).join('')}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Role <span class="required">*</span></label>
                        <select id="send-role" class="form-control" required>
                            ${ROLES.map(role => `<option value="${role}">${role}</option>`).join('')}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Receiver Name <span class="required">*</span></label>
                        <input type="text" id="send-receiver-name" class="form-control" 
                               placeholder="Enter receiver's name" required>
                        <div class="form-error" id="send-receiver-name-error">Receiver name is required</div>
                    </div>
                    
                    <div class="form-group">
                        <label>Receiver Email <span class="required">*</span></label>
                        <input type="email" id="send-receiver-email" class="form-control" 
                               placeholder="Enter receiver's email" required>
                        <div class="form-error" id="send-receiver-email-error">Please enter a valid email address</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="toggleSendForm(false)">Cancel</button>
                    <button class="btn btn-primary" onclick="handleSendSubmit()">
                        <i data-lucide="send" size="16"></i> Send Mail
                    </button>
                </div>
            </div>
        </div>
    `;
}





function renderDeleteModal() {
    return `
        <div class="modal-overlay confirm-modal" onclick="if(event.target===this) closeDeleteModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-body">
                    <div class="confirm-icon">
                        <i data-lucide="alert-triangle" size="28"></i>
                    </div>
                    <h3>Are you sure?</h3>
                    <p>This action cannot be undone. The trigger will be permanently deleted.</p>
                    <div style="display: flex; gap: 1rem; justify-content: center;">
                        <button class="btn btn-secondary" onclick="closeDeleteModal()">Cancel</button>
                        <button class="btn btn-danger" onclick="confirmDelete()">
                            <i data-lucide="trash-2" size="16"></i> Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// Form Validation
// ============================================
function validateSendForm() {
    let isValid = true;
    
    // Validate review count
    const reviewCount = parseInt(document.getElementById('send-review-count').value);
    const reviewCountError = document.getElementById('send-review-count-error');
    const reviewCountInput = document.getElementById('send-review-count');
    
    if (isNaN(reviewCount) || reviewCount < 10 || reviewCount > 2000) {
        reviewCountError.classList.add('visible');
        reviewCountInput.classList.add('error');
        isValid = false;
    } else {
        reviewCountError.classList.remove('visible');
        reviewCountInput.classList.remove('error');
    }
    
    // Validate receiver name
    const receiverName = document.getElementById('send-receiver-name').value.trim();
    const receiverNameError = document.getElementById('send-receiver-name-error');
    const receiverNameInput = document.getElementById('send-receiver-name');
    
    if (!receiverName) {
        receiverNameError.classList.add('visible');
        receiverNameInput.classList.add('error');
        isValid = false;
    } else {
        receiverNameError.classList.remove('visible');
        receiverNameInput.classList.remove('error');
    }
    
    // Validate receiver email
    const receiverEmail = document.getElementById('send-receiver-email').value.trim();
    const receiverEmailError = document.getElementById('send-receiver-email-error');
    const receiverEmailInput = document.getElementById('send-receiver-email');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!receiverEmail || !emailRegex.test(receiverEmail)) {
        receiverEmailError.classList.add('visible');
        receiverEmailInput.classList.add('error');
        isValid = false;
    } else {
        receiverEmailError.classList.remove('visible');
        receiverEmailInput.classList.remove('error');
    }
    
    return isValid;
}

// ============================================
// Form Submission
// ============================================
async function handleSendSubmit() {
    if (!validateSendForm()) return;
    
    const btn = document.querySelector('.modal-footer .btn-primary');
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" size="16" class="spin"></i> Sending...';
    
    const payload = {
        reviews_count: parseInt(document.getElementById('send-review-count').value),
        weeks: parseInt(document.getElementById('send-time-period').value),
        role: document.getElementById('send-role').value,
        recipient_name: document.getElementById('send-receiver-name').value.trim(),
        recipient_email: document.getElementById('send-receiver-email').value.trim(),
        mode: 'email',
        type: 'Manual'
    };
    
    try {
        const res = await fetch(`${API_BASE}/trigger`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            toggleSendForm(false);
            showNotification('Mail trigger initiated successfully', 'success');
            fetchHistory();
        } else {
            const errorData = await res.json().catch(() => ({}));
            showNotification(`Failed: ${errorData.detail || 'Unknown error'}`, 'error');
        }
    } catch (err) {
        showNotification('Error connecting to server', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="send" size="16"></i> Send Mail';
    }
}

// ============================================
// Action Handlers
// ============================================
function handleViewPDF(id) {
    window.open(`${API_BASE}/view-pdf/${id}`, '_blank');
}

function handleRetry(id) {
    retryTrigger(id);
}

function confirmDelete() {
    if (deleteTargetId) {
        deleteHistoryItem(deleteTargetId);
    }
    closeDeleteModal();
}

// ============================================
// Notification System
// ============================================
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-weight: 500;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        max-width: 400px;
        word-wrap: break-word;
    `;
    
    // Set colors based on type
    switch (type) {
        case 'success':
            notification.style.background = 'var(--success-bg)';
            notification.style.color = 'var(--success-color)';
            notification.style.border = '1px solid var(--success-color)';
            break;
        case 'error':
            notification.style.background = 'var(--error-bg)';
            notification.style.color = 'var(--error-color)';
            notification.style.border = '1px solid var(--error-color)';
            break;
        case 'warning':
            notification.style.background = 'var(--warning-bg)';
            notification.style.color = 'var(--warning-color)';
            notification.style.border = '1px solid var(--warning-color)';
            break;
        default:
            notification.style.background = 'var(--info-bg)';
            notification.style.color = 'var(--info-color)';
            notification.style.border = '1px solid var(--info-color)';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// Utility Functions
// ============================================
function initIcons() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// Add spin animation for loader
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spin {
        animation: spin 1s linear infinite;
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(style);
