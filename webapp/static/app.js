/**
 * reAlIty Web — Frontend
 * Handles drag-and-drop upload, preview, API calls, and result display.
 */

// ─── DOM refs ───
const uploadZone = document.getElementById('uploadZone');
const fileInput  = document.getElementById('fileInput');
const previewArea = document.getElementById('previewArea');
const previewMedia = document.getElementById('previewMedia');
const previewFilename = document.getElementById('previewFilename');
const previewBadge = document.getElementById('previewBadge');
const verifyBtn = document.getElementById('verifyBtn');
const progressArea = document.getElementById('progressArea');
const progressBar = document.getElementById('progressBar');
const progressStatus = document.getElementById('progressStatus');
const resultArea = document.getElementById('resultArea');
const verdictText = document.getElementById('verdictText');
const aiBar = document.getElementById('aiBar');
const humanBar = document.getElementById('humanBar');
const aiScore = document.getElementById('aiScore');
const humanScore = document.getElementById('humanScore');
const warningBox = document.getElementById('warningBox');
const warningText = document.getElementById('warningText');
const clearBtn = document.getElementById('clearBtn');
const errorToast = document.getElementById('errorToast');
const errorText = document.getElementById('errorText');

// ─── State ───
let currentFile = null;
let currentMediaType = null;

// ─── Event listeners ───
uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

verifyBtn.addEventListener('click', runDetection);
clearBtn.addEventListener('click', clearAll);

// ─── Handle file selection ───
function handleFile(file) {
    currentFile = file;

    // Determine media type from MIME type
    if (file.type.startsWith('video/')) {
        currentMediaType = 'video';
    } else if (file.type.startsWith('image/')) {
        currentMediaType = 'image';
    } else {
        // Fallback: try to infer from extension
        const ext = file.name.split('.').pop().toLowerCase();
        if (['mp4','avi','mov','mkv','webm'].includes(ext)) {
            currentMediaType = 'video';
        } else {
            currentMediaType = 'image';
        }
    }

    showPreview(file, currentMediaType);

    // UI transitions
    uploadZone.style.display = 'none';
    previewArea.style.display = 'block';
    resultArea.style.display = 'none';
    clearBtn.style.display = 'block';
    progressArea.style.display = 'none';
}

// ─── Show preview ───
function showPreview(file, type) {
    previewMedia.innerHTML = '';
    previewFilename.textContent = file.name;

    if (type === 'video') {
        previewBadge.textContent = 'Video';
        previewBadge.classList.add('video');

        // Show video placeholder (don't preload large videos)
        previewMedia.classList.add('video-placeholder');
        previewMedia.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="2" width="20" height="20" rx="2.5"/>
                <polygon points="10 8 16 12 10 16" fill="currentColor"/>
            </svg>
            <span>${file.name}</span>
        `;
    } else {
        previewBadge.textContent = 'Image';
        previewBadge.classList.remove('video');
        previewMedia.classList.remove('video-placeholder');

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.alt = file.name;
        img.onload = () => URL.revokeObjectURL(img.src);
        previewMedia.appendChild(img);
    }
}

// ─── Run detection ───
async function runDetection() {
    if (!currentFile) return;

    verifyBtn.disabled = true;
    previewArea.style.display = 'none';
    progressArea.style.display = 'block';
    progressBar.classList.add('indeterminate');
    progressStatus.textContent = currentMediaType === 'video'
        ? 'Loading model & extracting frames...'
        : 'Loading model...';

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/detect', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.detail || data.error || 'Detection failed');
        }

        showResult(data);

    } catch (err) {
        showError(err.message || 'Something went wrong. Please try again.');
        verifyBtn.disabled = false;
        progressArea.style.display = 'none';
        previewArea.style.display = 'block';
    }
}

// ─── Show result ───
function showResult(data) {
    progressArea.style.display = 'none';
    resultArea.style.display = 'block';
    verifyBtn.disabled = false;

    const ai = data.ai || 0;
    const hum = data.hum || 0;

    // Verdict
    if (ai > hum) {
        verdictText.textContent = 'Likely AI-Generated';
        verdictText.className = 'verdict-text ai';
    } else {
        verdictText.textContent = 'Likely Human-Made';
        verdictText.className = 'verdict-text human';
    }

    // Scores with animation delay
    aiBar.style.width = '0%';
    humanBar.style.width = '0%';
    aiScore.textContent = '--%';
    humanScore.textContent = '--%';

    requestAnimationFrame(() => {
        setTimeout(() => {
            aiBar.style.width = `${ai}%`;
            humanBar.style.width = `${hum}%`;
            aiScore.textContent = `${ai}%`;
            humanScore.textContent = `${hum}%`;
        }, 50);
    });

    // Overlay warning
    if (data.overlay_detected) {
        warningBox.style.display = 'flex';
        warningText.textContent =
            'Heavy text, arrows, circles, or graphic overlays detected on this file — ' +
            'that tends to reduce detection accuracy, so treat this result with extra caution.';
    } else {
        warningBox.style.display = 'none';
    }
}

// ─── Clear everything ───
function clearAll() {
    currentFile = null;
    currentMediaType = null;
    fileInput.value = '';

    uploadZone.style.display = 'block';
    previewArea.style.display = 'none';
    progressArea.style.display = 'none';
    resultArea.style.display = 'none';
    clearBtn.style.display = 'none';

    // Reset result fields
    verdictText.textContent = 'Awaiting analysis';
    verdictText.className = 'verdict-text';
    aiBar.style.width = '0%';
    humanBar.style.width = '0%';
    aiScore.textContent = '--%';
    humanScore.textContent = '--%';
    warningBox.style.display = 'none';
    verifyBtn.disabled = false;
}

// ─── Error toast ───
function showError(msg) {
    errorText.textContent = msg;
    errorToast.style.display = 'block';
    setTimeout(() => {
        errorToast.style.display = 'none';
    }, 5000);
}
