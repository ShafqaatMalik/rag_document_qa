// API Configuration
const API_BASE = '/api/v1';
// Frontend reference for similarity filtering (backend uses 0.3)
const SIMILARITY_THRESHOLD = 0.3;
const SESSIONS_KEY = 'rag_chat_sessions_v1';

// State
let documents = [];
let selectedDocIds = [];
let isLoading = false;
let currentChatId = null;
let sessions = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDocuments();
    setupEventListeners();
    loadSessions();
    renderSessionsList();
    startNewChatSession(false);
    // Confirm modal wiring (after DOM ready)
    const overlay = document.getElementById('confirmOverlay');
    const okBtn = document.getElementById('confirmOk');
    const cancelBtn = document.getElementById('confirmCancel');
    const closeBtn = document.getElementById('confirmClose');
    window.__confirmRefs = { overlay, okBtn, cancelBtn, closeBtn };
});

// Event Listeners
function setupEventListeners() {
    const fileInput = document.getElementById('fileInput');
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const newChatBtn = document.getElementById('newChatBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');

    fileInput.addEventListener('change', handleFileUpload);
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !isLoading) {
            sendQuestion();
        }
    });
    sendBtn.addEventListener('click', sendQuestion);

    // Chat management
    newChatBtn.addEventListener('click', () => startNewChatSession(true));
    clearChatBtn.addEventListener('click', clearCurrentChat);
}

// Promise-based themed confirm modal (returns true if confirmed)
function openConfirm(message, okLabel = 'OK') {
    return new Promise((resolve) => {
        const { overlay, okBtn, cancelBtn, closeBtn } = window.__confirmRefs || {};
        if (!overlay || !okBtn || !cancelBtn || !closeBtn) {
            resolve(window.confirm(message));
            return;
        }
        document.getElementById('confirmMessage').textContent = message;
        okBtn.textContent = okLabel;

        overlay.classList.remove('hidden');
        overlay.classList.add('show');
        overlay.setAttribute('aria-hidden', 'false');

        const cleanup = (result) => {
            overlay.classList.remove('show');
            overlay.classList.add('hidden');
            overlay.setAttribute('aria-hidden', 'true');
            okBtn.removeEventListener('click', onOk);
            cancelBtn.removeEventListener('click', onCancel);
            closeBtn.removeEventListener('click', onCancel);
            overlay.removeEventListener('click', onBackdrop);
            resolve(result);
        };

        const onOk = () => cleanup(true);
        const onCancel = () => cleanup(false);
        const onBackdrop = (e) => { if (e.target === overlay) cleanup(false); };

        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        closeBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onBackdrop);
    });
}

// Load Documents
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/documents`);
        const data = await response.json();
        
        documents = data.documents || [];
        renderDocuments();
        
        // Enable input if documents exist
        if (documents.length > 0) {
            document.getElementById('questionInput').disabled = false;
            document.getElementById('sendBtn').disabled = false;
            document.getElementById('newChatBtn').disabled = false;
            document.getElementById('clearChatBtn').disabled = false;
            updateInputHint('Type your question and press Enter');
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
        showError('Failed to load documents');
    }
}

// Render Documents
function renderDocuments() {
    const container = document.getElementById('documentsList');
    if (documents.length === 0) {
        container.innerHTML = '<div class="empty-state">No documents uploaded yet</div>';
        return;
    }
    
    container.innerHTML = documents.map(doc => `
        <div class="document-item ${selectedDocIds.includes(doc.doc_id) ? 'selected' : ''}" onclick="toggleDocumentSelection('${doc.doc_id}', event)">
            <div class="document-info">
                <div class="document-name" title="${doc.filename}">📄 ${doc.filename}</div>
                <div class="document-meta">
                    <span>${formatDate(doc.upload_date)}</span>
                </div>
            </div>
            <button class="document-menu" onclick="showContextMenu('${doc.doc_id}', event)">⋮</button>
        </div>
    `).join('');
}

// Toggle Document Selection
function toggleDocumentSelection(docId, event) {
    
    const index = selectedDocIds.indexOf(docId);
    if (index > -1) {
        selectedDocIds.splice(index, 1);
    } else {
        selectedDocIds.push(docId);
    }
    
    // Re-render to update selection state
    renderDocuments();
    updateInputHint();
}

// Show Context Menu
function showContextMenu(docId, event) {
    event.stopPropagation();
    event.preventDefault();
    
    // Remove existing context menu
    const existingMenu = document.querySelector('.context-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    const doc = documents.find(d => d.doc_id === docId);
    if (!doc) return;
    
    // Create context menu
    const menu = document.createElement('div');
    menu.className = 'context-menu show';
    menu.innerHTML = `
        <div class="context-menu-item danger" onclick="deleteDocument('${docId}', event)">
            🗑️ Delete Document
        </div>
    `;
    
    // Position menu
    const rect = event.target.getBoundingClientRect();
    menu.style.left = `${rect.left - 120}px`;
    menu.style.top = `${rect.bottom + 5}px`;
    
    document.body.appendChild(menu);
    
    // Close menu when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closeMenu() {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        });
    }, 0);
}

// Update Input Hint
function updateInputHint(text) {
    const hint = document.querySelector('.input-hint');
    const input = document.getElementById('questionInput');
    if (text) {
        hint.textContent = text;
    } else if (selectedDocIds.length > 0) {
        hint.textContent = `Querying ${selectedDocIds.length} selected document(s)`;
    } else {
        hint.textContent = 'Querying all documents';
    }

    // Also reflect selection in the input placeholder for clear context
    const names = getSelectedDocNames();
    if (names.length > 0) {
        const preview = names.slice(0, 2).join(', ');
        const more = names.length > 2 ? ` +${names.length - 2} more` : '';
        input.placeholder = `Ask about: ${preview}${more}`;
    } else {
        input.placeholder = 'Ask a question about your documents...';
    }
}

// Helper: get selected document filenames
function getSelectedDocNames() {
    const byId = new Map(documents.map(d => [d.doc_id, d.filename]));
    return selectedDocIds
        .map(id => byId.get(id))
        .filter(Boolean);
}

// Chat session management (simple)
function startNewChatSession(saveCurrent = true) {
    const container = document.getElementById('messagesContainer');
    if (saveCurrent && currentChatId) {
        // Persist current chat before starting a new one
        saveCurrentSession();
    }
    const now = Date.now();
    currentChatId = `chat_${now}`;
    container.innerHTML = '';
    // Optional: start with a subtle info message
    // showMessage('assistant', 'New chat started.');

    // Ensure controls enabled when documents exist
    if (documents.length > 0) {
        document.getElementById('questionInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
        document.getElementById('newChatBtn').disabled = false;
        document.getElementById('clearChatBtn').disabled = false;
    }

    // Immediately create a stub session so it appears in the sidebar
    // (it will be updated with title and content after first message)
    const exists = sessions.some(s => s.id === currentChatId);
    if (!exists) {
        sessions.unshift({ id: currentChatId, title: 'New Chat', html: '', createdAt: now, updatedAt: now });
        saveSessions();
    }

    // Scroll to top of new chat
    try {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (_) {
        window.scrollTo(0, 0);
    }
    renderSessionsList();
}

async function clearCurrentChat() {
    const container = document.getElementById('messagesContainer');
    if (!container.firstChild) return;
    const ok = await openConfirm('Delete this chat conversation?', 'Delete');
    if (!ok) return;
    container.innerHTML = '';
}

// --- Sessions (persisted in localStorage) ---
function loadSessions() {
    try {
        const raw = localStorage.getItem(SESSIONS_KEY);
        sessions = raw ? JSON.parse(raw) : [];
    } catch (e) {
        sessions = [];
    }
}

function saveSessions() {
    try {
        localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    } catch (e) {}
}

function sessionTitleFromMessages() {
    const container = document.getElementById('messagesContainer');
    const firstUser = container.querySelector('.user-message .message-text');
    if (!firstUser) return 'New Chat';
    const text = firstUser.textContent || firstUser.innerText || 'New Chat';
    return (text.trim().replace(/\s+/g, ' ').slice(0, 60)) || 'New Chat';
}

function saveCurrentSession() {
    const container = document.getElementById('messagesContainer');
    const html = container.innerHTML.trim();
    if (!currentChatId || html.length === 0) return; // don't save empty sessions
    const now = Date.now();
    const idx = sessions.findIndex(s => s.id === currentChatId);
    const payload = {
        id: currentChatId,
        title: sessionTitleFromMessages(),
        html,
        updatedAt: now,
        createdAt: idx >= 0 ? sessions[idx].createdAt : now
    };
    if (idx >= 0) {
        sessions[idx] = { ...sessions[idx], ...payload };
    } else {
        sessions.unshift(payload);
    }
    saveSessions();
    renderSessionsList();
}

function renderSessionsList() {
    const list = document.getElementById('sessionsList');
    if (!list) return;
    if (!sessions || sessions.length === 0) {
        list.innerHTML = '<div class="empty-state">No saved chats yet</div>';
        return;
    }
    list.innerHTML = sessions.map(s => `
        <div class="session-item ${s.id === currentChatId ? 'active' : ''}" onclick="switchSession('${s.id}', event)">
            <div class="session-info">
                <div class="session-title">${s.title || 'New Chat'}</div>
                <div class="session-meta">${new Date(s.updatedAt || s.createdAt).toLocaleString()}</div>
            </div>
            <button class="session-menu" title="More" onclick="sessionMenu('${s.id}', event)">⋮</button>
        </div>
    `).join('');
}

function switchSession(id, event) {
    if (event && event.target && event.target.closest && event.target.closest('.session-menu')) return;
    saveCurrentSession();
    const s = sessions.find(x => x.id === id);
    if (!s) return;
    const container = document.getElementById('messagesContainer');
    container.innerHTML = s.html || '';
    currentChatId = s.id;
    renderSessionsList();
    try {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    } catch (_) {
        window.scrollTo(0, document.body.scrollHeight);
    }
}

async function sessionMenu(id, event) {
    event.stopPropagation();
    const ok = await openConfirm('Delete this chat session?', 'Delete');
    if (!ok) return;
    sessions = sessions.filter(s => s.id !== id);
    saveSessions();
    if (currentChatId === id) {
        startNewChatSession(false);
    }
    renderSessionsList();
}

// Delete Document
async function deleteDocument(docId, event) {
    event.stopPropagation(); // Prevent selection toggle
    
    // Remove context menu
    const menu = document.querySelector('.context-menu');
    if (menu) {
        menu.remove();
    }
    
    const doc = documents.find(d => d.doc_id === docId);
    if (!doc) return;
    
    const ok = await openConfirm(`Are you sure you want to delete "${doc.filename}"?`, 'Delete');
    if (!ok) return;
    
    try {
        const response = await fetch(`${API_BASE}/documents/${docId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showMessage('assistant', `✅ Document "${doc.filename}" deleted successfully`);
            
            // Remove from selected list if it was selected
            const index = selectedDocIds.indexOf(docId);
            if (index > -1) {
                selectedDocIds.splice(index, 1);
            }
            
            // Reload documents list
            loadDocuments();
        } else {
            const data = await response.json();
            showMessage('assistant', `❌ Failed to delete: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        showMessage('assistant', `❌ Failed to delete: ${error.message}`);
    }
}

// Handle File Upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show uploading message
    showMessage('user', `Uploading: ${file.name}`);
    showLoadingMessage();
    
    try {
        const response = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            removeLoadingMessage();
            showMessage('assistant', `✅ Document uploaded successfully!\n\n📝 ${data.filename}\n📦 ${data.chunks_created} chunks created\n\nYou can now ask questions about this document.`);
            loadDocuments();
        } else {
            removeLoadingMessage();
            showMessage('assistant', `❌ Upload failed: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        removeLoadingMessage();
        showMessage('assistant', `❌ Upload failed: ${error.message}`);
    }
    
    // Reset file input
    event.target.value = '';
}

// Send Question
async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (!question || isLoading) return;
    
    isLoading = true;
    input.value = '';
    
    // Show user message
    showMessage('user', question);
    showLoadingMessage();
    
    try {
        const requestBody = {
            question: question,
            top_k: 5
        };
        
        // Add doc_ids filter if documents are selected
        if (selectedDocIds.length > 0) {
            requestBody.doc_ids = selectedDocIds;
        }
        
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        removeLoadingMessage();
        
        if (response.ok) {
            showMessage('assistant', data.answer, data.sources, data.latency_seconds);
        } else {
            showMessage('assistant', `❌ Error: ${data.error || 'Failed to get answer'}`);
        }
    } catch (error) {
        removeLoadingMessage();
        showMessage('assistant', `❌ Error: ${error.message}`);
    } finally {
        isLoading = false;
    }
}

// Show Message
function showMessage(role, text, sources = null, latency = null) {
    const container = document.getElementById('messagesContainer');
    
    // Remove welcome message if exists
    const welcome = container.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = role === 'user' ? '👤' : 'AI';
    const avatarClass = role === 'user' ? 'user-avatar' : 'assistant-avatar';
    
    // Format text based on role
    let formattedText;
    if (role === 'user') {
        // Keep user messages as-is with line breaks
        formattedText = text.replace(/\n/g, '<br>');
    } else {
        // For assistant, format as paragraphs for better readability
        formattedText = formatAssistantMessage(text);
    }
    
    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = `
            <div class="message-sources">
                <div class="sources-header">Sources (${sources.length})</div>
                ${sources.map((source, index) => `
                    <div class="source-item">
                        <div class="source-header">
                            <span class="source-file">📄 ${source.filename}</span>
                            <span class="source-score">${Math.round(source.score * 100)}%</span>
                        </div>
                        <div class="source-snippet">${source.text_snippet}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    let latencyHTML = '';
    if (latency) {
        latencyHTML = `<div style="font-size: 16px; color: var(--text-muted); margin-top: 8px;">⚡ Answered in ${latency}s</div>`;
    }
    
    const actionsHTML = role === 'assistant' ? `
            <div class="message-actions">
                <button class="action-btn" onclick="copyMessage(this)" title="Copy to clipboard">Copy</button>
                <button class="action-btn" onclick="saveMessage(this)" title="Download as .txt">Save</button>
            </div>
        ` : '';

    messageDiv.innerHTML = `
        <div class="message-avatar ${avatarClass}">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${formattedText}</div>
            ${sourcesHTML}
            ${latencyHTML}
            ${actionsHTML}
        </div>
    `;
    
    container.appendChild(messageDiv);
    // Scroll inner container (if scrollable) and also window to ensure visibility
    container.scrollTop = container.scrollHeight;
    try {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    } catch (e) {
        window.scrollTo(0, document.body.scrollHeight);
    }
    // Persist session after each new message
    saveCurrentSession();
}

// Copy the assistant message text to clipboard
async function copyMessage(el) {
    try {
        const message = el.closest('.message');
        const textEl = message.querySelector('.message-text');
        const text = textEl ? textEl.innerText.trim() : '';
        if (!text) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
        } else {
            // Fallback
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
        }
        // Feedback
        const original = el.textContent;
        el.textContent = 'Copied';
        el.disabled = true;
        setTimeout(() => { el.textContent = original; el.disabled = false; }, 1200);
    } catch (err) {
        console.error('Copy failed', err);
    }
}

// Save the assistant message text to a .txt file
function saveMessage(el) {
    const message = el.closest('.message');
    const textEl = message.querySelector('.message-text');
    const text = textEl ? textEl.innerText.trim() : '';
    if (!text) return;
    const blob = new Blob([text + '\n'], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const ts = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const filename = `answer-${ts.getFullYear()}${pad(ts.getMonth()+1)}${pad(ts.getDate())}-${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}.txt`;
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Feedback
    const original = el.textContent;
    el.textContent = 'Saved';
    el.disabled = true;
    setTimeout(() => { el.textContent = original; el.disabled = false; }, 1200);
}

// Format assistant message with proper paragraphs
function formatAssistantMessage(text) {
    // Split by double newlines for paragraphs
    const paragraphs = text.split(/\n\n+/);
    
    // Wrap each paragraph in <p> tags
    const formatted = paragraphs
        .map(p => p.trim())
        .filter(p => p.length > 0)
        .map(p => `<p>${p.replace(/\n/g, ' ')}</p>`)
        .join('');
    
    return formatted || `<p>${text}</p>`;
}

// Show Loading Message
function showLoadingMessage() {
    const container = document.getElementById('messagesContainer');
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.id = 'loadingMessage';
    
    loadingDiv.innerHTML = `
        <div class="message-avatar assistant-avatar">AI</div>
        <div class="message-content">
            <div class="loading-message">
                <span>Thinking</span>
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;
    try {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    } catch (e) {
        window.scrollTo(0, document.body.scrollHeight);
    }
}

// Remove Loading Message
function removeLoadingMessage() {
    const loading = document.getElementById('loadingMessage');
    if (loading) {
        loading.remove();
    }
}

// Show Error
function showError(message) {
    showMessage('assistant', `❌ ${message}`);
}

// Format Date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString();
}
