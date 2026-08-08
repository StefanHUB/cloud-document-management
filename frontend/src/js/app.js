/**
 * Cloud Document Management System - Frontend Application
 *
 * This JavaScript handles all frontend logic:
 * - Authentication and session management
 * - Document upload with region selection
 * - Document listing, filtering, download
 * - Review/approval workflow for administrators
 * - Region recommendation display
 *
 * The frontend communicates with the FastAPI backend via REST API calls.
 */

// API base URL - backend server
const API_URL = 'http://localhost:8000';

// Current user session
let currentUser = null;
let authToken = null;
let selectedRegionMode = 'cost';

// ===== PAGE NAVIGATION =====

function showPage(page) {
    document.getElementById('loginPage').style.display = page === 'login' ? '' : 'none';
    document.getElementById('dashboardPage').style.display = page === 'dashboard' ? '' : 'none';
}

// ===== AUTHENTICATION =====

/**
 * Fill demo credentials into the login form.
 * In production, Firebase Authentication would handle login.
 */
function fillDemoUser(role) {
    if (role === 'manager') {
        document.getElementById('loginUsername').value = 'manager_user';
        document.getElementById('loginPassword').value = 'manager123';
    } else {
        document.getElementById('loginUsername').value = 'admin_user';
        document.getElementById('loginPassword').value = 'admin123';
    }
}

/**
 * Handle login form submission.
 * Sends credentials to the backend and stores the auth token.
 */
async function login(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    errorDiv.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Login failed');
        }

        const data = await response.json();
        authToken = data.token;
        currentUser = data;

        // Update navbar
        document.getElementById('navUserInfo').style.display = '';
        document.getElementById('userBadge').innerHTML =
            `<i class="bi bi-person-circle"></i> ${data.name} <span class="badge bg-${data.role === 'admin' ? 'success' : 'primary'}">${data.role}</span>`;

        // Show dashboard
        showPage('dashboard');
        loadDashboard();
    } catch (err) {
        errorDiv.textContent = err.message;
        errorDiv.style.display = '';
    }
}

/**
 * Log out the current user.
 */
function logout() {
    authToken = null;
    currentUser = null;
    document.getElementById('navUserInfo').style.display = 'none';
    showPage('login');
}

// ===== DASHBOARD LOADING =====

/**
 * Load dashboard data: stats, documents, region recommendations.
 */
async function loadDashboard() {
    loadStats();
    loadDocuments();
    updateRegionPreview();

    // Show/hide upload section based on role
    const uploadSection = document.getElementById('uploadSection');
    uploadSection.style.display = currentUser.role === 'manager' ? '' : 'none';
}

/**
 * Load and display document statistics.
 */
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/documents`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        const docs = data.documents;

        const pending = docs.filter(d => d.status === 'pending').length;
        const approved = docs.filter(d => d.status === 'approved').length;
        const rejected = docs.filter(d => d.status === 'rejected').length;

        document.getElementById('statsRow').innerHTML = `
            <div class="col-md-3">
                <div class="stat-card bg-white shadow-sm">
                    <div class="stat-icon text-primary"><i class="bi bi-file-earmark-text"></i></div>
                    <div class="stat-number text-primary">${docs.length}</div>
                    <div class="stat-label">Total Documents</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card bg-white shadow-sm">
                    <div class="stat-icon text-warning"><i class="bi bi-clock"></i></div>
                    <div class="stat-number text-warning">${pending}</div>
                    <div class="stat-label">Pending Review</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card bg-white shadow-sm">
                    <div class="stat-icon text-success"><i class="bi bi-check-circle"></i></div>
                    <div class="stat-number text-success">${approved}</div>
                    <div class="stat-label">Approved</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card bg-white shadow-sm">
                    <div class="stat-icon text-danger"><i class="bi bi-x-circle"></i></div>
                    <div class="stat-number text-danger">${rejected}</div>
                    <div class="stat-label">Rejected</div>
                </div>
            </div>
        `;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ===== REGION SELECTION =====

/**
 * Select region mode (cost-aware or carbon-aware).
 * This is the key feature extending the research paper.
 *
 * ROUTING FLOW:
 * 1. User clicks "Cost-Aware" or "Carbon-Aware"
 * 2. This function sets the selectedRegionMode variable
 * 3. updateRegionPreview() calls the backend API:
 *    GET /regions/recommend?mode=cost  -> returns cheapest region
 *    GET /regions/recommend?mode=carbon -> returns greenest region
 * 4. When uploading, the region_mode is sent to the backend
 * 5. Backend (main.py) calls recommend_regions(region_mode)
 * 6. regions.py sorts regions by cost or sustainability score
 * 7. storage.py stores the file in the selected region directory
 */
function selectRegionMode(mode) {
    selectedRegionMode = mode;

    // Update radio buttons
    document.querySelector(`input[value="${mode}"]`).checked = true;

    // Visual feedback
    document.getElementById('costCard').classList.toggle('region-active', mode === 'cost');
    document.getElementById('carbonCard').classList.toggle('region-active', mode === 'carbon');

    updateRegionPreview();
}

/**
 * Update the region recommendation preview.
 * Fetches the recommended region from the backend and displays rationale.
 */
async function updateRegionPreview() {
    const mode = document.querySelector('input[name="regionMode"]:checked')?.value || 'cost';
    selectedRegionMode = mode;

    try {
        const response = await fetch(`${API_URL}/regions/recommend?mode=${mode}`);
        const data = await response.json();

        const badgeClass = mode === 'carbon' ? 'region-badge-carbon' : '';
        document.getElementById('regionRecommendation').innerHTML = `
            <div class="alert ${mode === 'carbon' ? 'alert-success' : 'alert-primary'}">
                <div class="d-flex align-items-center">
                    <i class="bi ${mode === 'carbon' ? 'bi-globe2' : 'bi-currency-exchange'} me-2"></i>
                    <div>
                        <strong>${data.mode_label} Region Selected:</strong>
                        <span class="region-badge ${badgeClass} ms-2">${data.recommended_region.name}</span>
                        <span class="region-badge ${badgeClass}">${data.recommended_region.region_id}</span>
                        <p class="mb-0 mt-1 small">${data.rationale}</p>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        console.error('Failed to load region recommendation:', err);
    }
}

// ===== DOCUMENT MANAGEMENT =====

/**
 * Upload a document to cloud storage with region selection.
 */
async function uploadDocument(event) {
    event.preventDefault();

    const title = document.getElementById('docTitle').value;
    const description = document.getElementById('docDescription').value;
    const fileInput = document.getElementById('docFile');
    const regionMode = document.querySelector('input[name="regionMode"]:checked').value;

    if (!fileInput.files[0]) {
        alert('Please select a file to upload.');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('region_mode', regionMode);

    try {
        const response = await fetch(`${API_URL}/documents/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Upload failed');
        }

        const data = await response.json();
        alert(`Document uploaded to ${data.storage_region} (${data.region_mode} mode)`);

        // Reset form
        document.getElementById('docTitle').value = '';
        document.getElementById('docDescription').value = '';
        fileInput.value = '';

        // Reload dashboard
        loadDashboard();
    } catch (err) {
        alert('Upload error: ' + err.message);
    }
}

/**
 * Load and display documents in the table.
 * @param {string} statusFilter - Optional filter by status
 */
async function loadDocuments(statusFilter) {
    try {
        let url = `${API_URL}/documents`;
        if (statusFilter) {
            url += `?status=${statusFilter}`;
        }

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        const docs = data.documents;

        if (docs.length === 0) {
            document.getElementById('documentsTable').innerHTML =
                '<div class="text-center text-muted py-4"><i class="bi bi-inbox" style="font-size: 2rem;"></i><p class="mt-2">No documents found</p></div>';
            return;
        }

        let tableHTML = `
            <table class="table table-hover doc-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>File</th>
                        <th>Region</th>
                        <th>Status</th>
                        <th>Uploaded By</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        docs.forEach(doc => {
            const statusClass = `doc-status-${doc.status}`;
            const regionBadge = doc.region_mode === 'carbon' ? 'region-badge-carbon' : '';
            const date = new Date(doc.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });

            let actions = `
                <button class="btn btn-sm btn-outline-primary" onclick="downloadDocument(${doc.id})">
                    <i class="bi bi-download"></i>
                </button>
            `;

            // Admin can review pending documents
            if (currentUser.role === 'admin' && doc.status === 'pending') {
                actions += `
                    <button class="btn btn-sm btn-outline-success" onclick="reviewDocument(${doc.id}, 'approved')">
                        <i class="bi bi-check-lg"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="reviewDocument(${doc.id}, 'rejected')">
                        <i class="bi bi-x-lg"></i>
                    </button>
                `;
            }

            tableHTML += `
                <tr>
                    <td><strong>${doc.title}</strong><br><small class="text-muted">${doc.description || ''}</small></td>
                    <td><i class="bi bi-file-earmark"></i> ${doc.file_name}<br><small class="text-muted">${formatFileSize(doc.file_size)}</small></td>
                    <td><span class="region-badge ${regionBadge}">${doc.storage_region}</span><br><small class="text-muted">${doc.region_mode}</small></td>
                    <td class="${statusClass}"><i class="bi bi-${doc.status === 'approved' ? 'check-circle' : doc.status === 'rejected' ? 'x-circle' : 'clock'}"></i> ${doc.status}</td>
                    <td>${doc.uploaded_by}</td>
                    <td>${date}</td>
                    <td>${actions}</td>
                </tr>
            `;
        });

        tableHTML += '</tbody></table>';
        document.getElementById('documentsTable').innerHTML = tableHTML;
    } catch (err) {
        document.getElementById('documentsTable').innerHTML =
            `<div class="alert alert-danger">Failed to load documents: ${err.message}</div>`;
    }
}

/**
 * Download a document from cloud storage.
 */
async function downloadDocument(docId) {
    try {
        const response = await fetch(`${API_URL}/documents/${docId}/download`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('Download failed');

        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'document';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);
            if (match) filename = match[1];
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert('Download error: ' + err.message);
    }
}

/**
 * Review a document (approve or reject).
 * Only administrators can perform this action.
 */
async function reviewDocument(docId, status) {
    const comment = status === 'approved' ? 'Document approved by administrator' : 'Document rejected by administrator';

    try {
        const response = await fetch(`${API_URL}/documents/${docId}/review`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status, comment })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Review failed');
        }

        alert(`Document ${status} successfully`);
        loadDashboard();
    } catch (err) {
        alert('Review error: ' + err.message);
    }
}

// ===== UTILITY FUNCTIONS =====

/**
 * Format file size in human-readable format.
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
