// Global variables
let isFileUploaded = false;
let isJobSubmitted = false;
let isChatVisible = false;
let isInputCollapsed = false;
let sessionId = "";
let ws = null; // web socket
let isAgentResponseLoading = false;
let callbackOnWsConnected = () => { }

const ERROR_MSG_TYPE = 'error';
const SUCCESS_MSG_TYPE = 'success';

const AGENT_ROLE = 'agent';
const USER_ROLE = 'user';

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
});

// Initialize all event listeners
function initializeEventListeners() {
    // Collapse/expand functionality
    const sectionsHeader = document.getElementById('sections-header');
    const collapseToggle = document.getElementById('collapse-toggle');

    sectionsHeader.addEventListener('click', toggleInputSections);
    collapseToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleInputSections();
    });

    // File upload functionality
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    const uploadBox = document.getElementById('upload-box');

    const triggerFileUpload = (e) => {
        e?.stopPropagation();
        fileInput.click();
    }

    uploadBtn.addEventListener('click', triggerFileUpload);
    uploadBox.addEventListener('click', triggerFileUpload);
    fileInput.addEventListener('change', handleFileUpload);

    // Job description functionality
    const submitJobBtn = document.getElementById('submit-job-btn');
    submitJobBtn.addEventListener('click', handleJobSubmission);

    // Generate resume functionality
    const generateBtn = document.getElementById('generate-btn');
    generateBtn.addEventListener('click', handleGenerateResume);

    // Export functionality
    const exportBtn = document.getElementById('export-btn');

    async function loadHtml2PdfLibrary() {
        if (typeof window.html2pdf === 'undefined') {
            await new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
                script.onload = resolve;
                document.body.appendChild(script);
            });
        }
    }

    async function generateResumePdfWithHtml2Pdf() {
        await loadHtml2PdfLibrary();
        const el = document.getElementById('resume-preview');
        if (!el) {
            console.error('No #resume-preview element found!');
            return;
        }
        window.html2pdf().set({
            margin: 0.5,
            filename: 'resume.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        }).from(el).save();
    }

    exportBtn.addEventListener('click', generateResumePdfWithHtml2Pdf);

    // Chat functionality
    const collapseChatBtn = document.getElementById('collapse-chat-btn');
    const expandChatBtn = document.getElementById('expand-chat-btn');
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    const chatOverlay = document.getElementById('chat-overlay');

    collapseChatBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        collapseChat();
    });
    expandChatBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        expandChat();
    });

    sendBtn.addEventListener('click', sendMessage);
    chatOverlay.addEventListener('click', (e) => {
        e.stopPropagation();
        collapseChat()
    });

    chatInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

function openInputSections() {
    const inputSections = document.getElementById('input-sections');
    const collapseText = document.querySelector('.collapse-text');
    inputSections.classList.remove('collapsed');
    collapseText.textContent = 'Collapse';
    isInputCollapsed = false;
}

function closeInputSections() {
    const inputSections = document.getElementById('input-sections');
    const collapseText = document.querySelector('.collapse-text');
    inputSections.classList.add('collapsed');
    collapseText.textContent = 'Expand';
    isInputCollapsed = true;
}

// Toggle input sections collapse/expand
function toggleInputSections() {
    if (isInputCollapsed) {
        openInputSections();
    } else {
        closeInputSections();
    }
}

// Toast notification system
function showToast(message, type = SUCCESS_MSG_TYPE) {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Auto remove toast after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

async function uploadUserProfile(formData) {
    const response = await fetch('/api/user-profile/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return await response.json();
}

// File upload handler
async function handleFileUpload(event) {
    try {
        event.stopPropagation();
        const file = event.target.files[0];
        if (!file) return;

        // Validate file size (5MB limit)
        if (file.size > 5 * 1024 * 1024) {
            showToast('File size exceeds 5MB limit', ERROR_MSG_TYPE);
            return;
        }

        // Validate file type
        const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        if (!allowedTypes.includes(fileExtension)) {
            showToast('Invalid file type. Please upload PDF, DOC, DOCX, or TXT files', ERROR_MSG_TYPE);
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const result = await uploadUserProfile(formData);
        sessionId = result.session_id;
        isFileUploaded = true;

        document.getElementById('upload-btn').textContent = 'Update file';
        document.getElementById('upload-success').classList.add('show');
        showToast('File uploaded successfully!', SUCCESS_MSG_TYPE);
    } catch (err) {
        console.error('Error uploading user profile:', err);
        showToast('Could not upload the file. Please try again', ERROR_MSG_TYPE)
    }
}

async function submitJobDescription(jobDescription) {
    const response = await fetch('/api/job-description', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ description: jobDescription }),
        credentials: 'include'
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to submit job description');
    }

    return await response.json();
}

// Job description submission handler
async function handleJobSubmission() {
    try {
        const jobDescription = document.getElementById('job-description').value.trim();

        if (!jobDescription) {
            showToast('Please enter a job description', ERROR_MSG_TYPE);
            return;
        }

        const result = await submitJobDescription(jobDescription);
        sessionId = result.session_id;
        isJobSubmitted = true;

        // Simulate successful submission
        setTimeout(() => {
            document.getElementById('submit-job-btn').textContent = 'Update Job Description'
            showToast('Job description submitted successfully!', SUCCESS_MSG_TYPE);
        }, 500);
    } catch (err) {
        showToast('Could not submit the job description. Please try again', ERROR_MSG_TYPE);
    }
}

function connectWebSocket() {
    if (!sessionId) {
        // Session ID is not set, so we can't connect to the WebSocket
        console.warn('No session id found to establish websocket connection');
        return;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        // Socket connection already established and open
        callbackOnWsConnected?.();
        return;
    }

    // Dynamically determine ws/wss and host
    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const wsHost = window.location.host;
    const wsPath = `/ws/${sessionId}`;
    const wsUrl = `${wsProtocol}://${wsHost}${wsPath}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        // Send initial connection message with session ID
        ws.send(JSON.stringify({
            type: 'connect',
            session_id: sessionId
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
            case 'connected':
                sessionId = data.session_id;
                callbackOnWsConnected?.();
                break;

            case 'agent_response':
                addAgentMessage(data.message);
                break;

            case 'resume_updated':
                updateResumePreview(data.data);
                break;
            
            case 'agent_response_in_progress':
                handleAgentResponseLoading();
                break;
            
            case 'agent_response_completed':
                handleAgentResponseCompleted();
                break;

            case 'error':
                showToast(data.message, ERROR_MSG_TYPE);
                break;
        }
    };

    ws.onclose = () => {
        ws = null;
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function sendSocketMessage(payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload));
    } else {
        console.warn('WebSocket not connected to send message');
    }
}

function sendGenerateResumeMessage() {
    sendSocketMessage({
        type: 'generate',
        session_id: sessionId
    });
}

function sendUserMessage(message) {
    sendSocketMessage({
        type: 'user_message',
        session_id: sessionId,
        message: message
    });
}

function generateResume() {
    callbackOnWsConnected = sendGenerateResumeMessage;
    connectWebSocket();
}

// Resume generation handler
function handleGenerateResume() {
    if (!isFileUploaded) {
        showToast('Please upload your profile', ERROR_MSG_TYPE);
        return;
    }

    if (!isJobSubmitted) {
        showToast('Please submit a job description', ERROR_MSG_TYPE);
        return;
    }

    generateResume();
    showChat();

}

function showChat() {
    isChatVisible = true;
    closeInputSections();
    expandChat();
}

function collapseChat() {
    if (!isChatVisible) return;

    const chatSidebar = document.getElementById('chat-sidebar');
    const chatOverlay = document.getElementById('chat-overlay');
    const mainContainer = document.querySelector('.main-container');
    const previewSection = document.querySelector('.preview-section');
    const expandChatBtn = document.getElementById('expand-chat-btn');

    chatSidebar.classList.add('collapsed');
    chatSidebar.classList.remove('show');
    chatOverlay.classList.remove('show');
    mainContainer.classList.remove('chat-open');
    previewSection.classList.remove('chat-active');
    expandChatBtn.classList.remove('hidden');
}

function expandChat() {
    if (!isChatVisible) return;

    const chatSidebar = document.getElementById('chat-sidebar');
    const chatOverlay = document.getElementById('chat-overlay');
    const mainContainer = document.querySelector('.main-container');
    const previewSection = document.querySelector('.preview-section');
    const expandChatBtn = document.getElementById('expand-chat-btn');

    chatSidebar.classList.remove('collapsed');
    chatSidebar.classList.add('show');
    chatOverlay.classList.add('show');
    mainContainer.classList.add('chat-open');
    previewSection.classList.add('chat-active');
    expandChatBtn.classList.add('hidden');
}

function addChatMessage(userType, message, classNames="") {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${userType}-message ${classNames}`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = message;

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);

    // Scroll to the bottom of the chat
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addAgentMessage(message) {
    addChatMessage(AGENT_ROLE, message);
    if (isAgentResponseLoading)
        addAgentResponseLoader();
}

function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();

    if (!message) return;

    sendUserMessage(message);
    addChatMessage(USER_ROLE, message);

    // Clear input field
    chatInput.value = '';
}

function updateResumePreview(content) {
    document.getElementById('resume-preview').innerHTML = content;
}

function addAgentResponseLoader() {
    removeAgentResponseLoader();
    addChatMessage(AGENT_ROLE, '', 'agent-loading-text loading-message');
}

function removeAgentResponseLoader() {
    document.querySelectorAll(".agent-loading-text").forEach(e => e.remove());
}

function handleAgentResponseLoading() {
    isAgentResponseLoading = true;
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = true;
    sendBtn.classList.add('disabled');
    addAgentResponseLoader();
}

function handleAgentResponseCompleted() {
    isAgentResponseLoading = false;
    removeAgentResponseLoader();
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = false;
    sendBtn.classList.remove('disabled');
}