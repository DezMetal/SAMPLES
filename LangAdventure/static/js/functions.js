// --- Element Constants ---
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const messageList = document.getElementById('message-list');
const chatContainer = document.getElementById('chat-container');
const typingIndicator = document.getElementById('typing-indicator');

// Settings Panel Elements
const settingsButton = document.getElementById('settings-button');
const closeSettingsButton = document.getElementById('close-settings-button');
const settingsOverlay = document.getElementById('settings-overlay');
const settingsPanel = document.getElementById('settings-panel');
const journalNotes = document.getElementById('journal-notes');
const vocabList = document.getElementById('vocab-list');
const themeSwitcher = document.getElementById('theme-switcher');
const bubbleStyleSwitcher = document.getElementById('bubble-style-switcher');

// --- TEXT TO SPEECH SCRIPT ---
let synth = window.speechSynthesis;
let japaneseVoice = null;
let currentlySpeakingIcon = null;
const playIconSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"></path></svg>`;
const stopIconSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h12v12H6z"></path></svg>`;

function loadJapaneseVoice() {
    return new Promise(resolve => {
        let voices = synth.getVoices();
        if (voices.length) {
            japaneseVoice = voices.find(v => v.lang.startsWith('ja')) || voices.find(v => v.default && v.lang.startsWith('ja'));
            resolve();
            return;
        }
        synth.onvoiceschanged = () => {
            voices = synth.getVoices();
            japaneseVoice = voices.find(v => v.lang.startsWith('ja')) || voices.find(v => v.default && v.lang.startsWith('ja'));
            resolve();
        };
    });
}

function stripFurigana(text) {
    return text.replace(/\（[^）]+\）|\([^)]+\)/g, '').replace(/[*＊]/g, '').trim();
}

function toggleSpeech(iconElement, word = null) {
    if (!synth || !japaneseVoice) { console.warn("Speech synthesis not ready or Japanese voice not found."); return; }
    if (iconElement && iconElement === currentlySpeakingIcon && synth.speaking) { synth.cancel(); return; }
    if (synth.speaking) { synth.cancel(); }

    const textToSpeak = word ? word : stripFurigana(iconElement.closest('.bubble').querySelector('.japanese-text').textContent);
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.voice = japaneseVoice;
    utterance.lang = 'ja-JP';
    utterance.rate = 0.9;

    utterance.onstart = () => {
        document.querySelectorAll('.speech-icon.speaking').forEach(el => {
            el.innerHTML = playIconSVG;
            el.classList.remove('speaking');
        });
        if (iconElement) {
            currentlySpeakingIcon = iconElement;
            iconElement.innerHTML = stopIconSVG;
            iconElement.classList.add('speaking');
        }
    };
    utterance.onend = () => {
        if (iconElement && iconElement === currentlySpeakingIcon) {
            iconElement.innerHTML = playIconSVG;
            iconElement.classList.remove('speaking');
            currentlySpeakingIcon = null;
        }
    };
    utterance.onerror = (event) => {
        console.error('SpeechSynthesisUtterance.onerror', event);
        if (iconElement && iconElement === currentlySpeakingIcon) {
            iconElement.innerHTML = playIconSVG;
            iconElement.classList.remove('speaking');
            currentlySpeakingIcon = null;
        }
    };
    synth.speak(utterance);
}
// --- END OF TTS SCRIPT ---

// --- VOCABULARY LOGIC ---
let savedWords = JSON.parse(localStorage.getItem('savedWords')) || [];

function renderVocabList() {
    if (!vocabList) return;
    vocabList.innerHTML = '';
    const uniqueWords = savedWords.filter((v,i,a)=>a.findIndex(t=>(t.word === v.word))===i);
    if(uniqueWords.length === 0) {
        vocabList.innerHTML = `<li class="text-slate-400 text-center">No words saved yet.</li>`;
        return;
    }
    uniqueWords.sort((a,b) => a.word.localeCompare(b.word, 'ja')).forEach(wordObj => {
        const li = document.createElement('li');
        li.className = 'vocab-item';
        li.innerHTML = `
            <a href="https://jisho.org/search/${wordObj.word}" target="_blank" title="Look up on Jisho.org" class="flex-grow">
                <p class="font-semibold">${wordObj.word}</p>
                <p class="text-xs text-slate-500 italic">${wordObj.notes || 'No notes'}</p>
            </a>
            <div class="flex items-center gap-2">
                 <button class="speech-icon text-sm" onclick="toggleSpeech(null, '${wordObj.word}')">${playIconSVG}</button>
                 <button onclick="removeWord('${wordObj.word}')" class="text-red-500 text-2xl leading-none">&times;</button>
            </div>
        `;
        vocabList.appendChild(li);
    });
}

function saveWord(word) {
    // Strip any lingering furigana before saving
    const cleanWord = word.replace(/\（.*\）/, '');
    const existingEntry = savedWords.find(w => w.word === cleanWord);
    if (existingEntry) {
        showCustomAlert(`'${cleanWord}' is already in your vocabulary list.`); // Changed from alert to custom alert
        return;
    }

    // Using a custom modal instead of prompt for better UI/UX
    showCustomPrompt(`Add a note for "${cleanWord}":`, (notes) => {
        if (notes !== null) { // User didn't cancel
            const wordObj = { word: cleanWord, notes: notes };
            savedWords.push(wordObj);
            localStorage.setItem('savedWords', JSON.stringify(savedWords));
            renderVocabList();
        }
    });
}

// Custom prompt/alert implementation
function showCustomPrompt(message, callback) {
    const modalHtml = `
        <div id="custom-prompt-overlay" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center">
            <div class="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full">
                <p class="text-lg font-semibold mb-4">${message}</p>
                <input type="text" id="custom-prompt-input" class="w-full p-2 border rounded-md mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <div class="flex justify-end gap-3">
                    <button id="custom-prompt-cancel" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">Cancel</button>
                    <button id="custom-prompt-ok" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition">OK</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const overlay = document.getElementById('custom-prompt-overlay');
    const input = document.getElementById('custom-prompt-input');
    const okButton = document.getElementById('custom-prompt-ok');
    const cancelButton = document.getElementById('custom-prompt-cancel');

    input.focus();

    const cleanup = () => {
        overlay.remove();
    };

    okButton.onclick = () => {
        callback(input.value);
        cleanup();
    };
    cancelButton.onclick = () => {
        callback(null);
        cleanup();
    };
    overlay.onclick = (e) => {
        if (e.target === overlay) {
            callback(null);
            cleanup();
        }
    };
    input.onkeydown = (e) => {
        if (e.key === 'Enter') {
            okButton.click();
        } else if (e.key === 'Escape') {
            cancelButton.click();
        }
    };
}


function removeWord(wordToRemove) {
    savedWords = savedWords.filter(w => w.word !== wordToRemove);
    localStorage.setItem('savedWords', JSON.stringify(savedWords));
    renderVocabList();
}


// --- Core App Functions ---
const scrollToBottom = () => { if(chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight; };

function createBubbleHtml(part) {
    // Check part.has_japanese directly
    const playIconHtml = part.has_japanese ? `<div class="speech-icon" onclick="toggleSpeech(this)">${playIconSVG}</div>` : '';

    // Wrap Japanese words/phrases for saving, stripping furigana for the saved word
    const japaneseHtml = part.japanese.replace(/([一-龠ぁ-ゔァ-ヴー]+(?:（[^）]+）)?)/g, (match) => {
        const rootWord = stripFurigana(match);
        return `<span class="savable-word" onclick="saveWord('${rootWord}')">${match}</span>`;
    });

    const bubbleTextHtml = part.english
        ? `<p class="japanese-text">${japaneseHtml}</p><p class="english-translation">${part.english}</p>`
        : `<p class="japanese-text">${japaneseHtml}</p>`;

    return `<div class="flex items-start gap-3"><div class="avatar-companion">A</div><div class="bubble bubble-companion flex-1"><div class="flex-grow">${bubbleTextHtml}</div>${playIconHtml}</div></div>`;
}


function appendUserTurn(message) {
    const turnWrapper = document.createElement('div');
    turnWrapper.classList.add('message-turn');
    turnWrapper.innerHTML = `
        <p class="font-semibold text-slate-600 text-sm text-right mr-12 mb-1">${userName}</p>
        <div class="flex items-start gap-3 justify-end">
            <div class="bubble bubble-user max-w-4xl">
                <p class="user-text">${message}</p>
            </div>
            <div class="avatar-user">Y</div>
        </div>
    `;
    messageList.insertBefore(turnWrapper, typingIndicator);
};

function appendAiTurn(parts, role = 'model') { // Added role parameter
    if (!parts || parts.length === 0) return;
    const turnWrapper = document.createElement('div');
    turnWrapper.classList.add('message-turn');

    if (role === 'model') {
        const bubblesContainer = document.createElement('div');
        bubblesContainer.className = 'space-y-2';
        parts.forEach(part => {
            const bubbleHtml = createBubbleHtml(part);
            bubblesContainer.innerHTML += bubbleHtml;
        });
        turnWrapper.innerHTML = `<p class="font-semibold text-slate-600 text-sm ml-12 mb-1">${characterName}</p>`;
        turnWrapper.appendChild(bubblesContainer);
    } else if (role === 'user') {
        turnWrapper.innerHTML = `
            <p class="font-semibold text-slate-600 text-sm text-right mr-12 mb-1">${userName}</p>
            <div class="flex items-start gap-3 justify-end">
                <div class="bubble bubble-user max-w-4xl">
                    <p class="user-text">${parts[0].japanese}</p>
                </div>
                <div class="avatar-user">Y</div>
            </div>
        `;
    } else if (role === 'system') {
        // Do not append system messages to the chat display
        return;
    }

    messageList.insertBefore(turnWrapper, typingIndicator);
};

async function handleFormSubmit(e) {
    e.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;
    appendUserTurn(message);
    messageInput.value = '';
    sendButton.disabled = true;
    scrollToBottom();
    typingIndicator.classList.remove('hidden');
    scrollToBottom();
    try {
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message }),
        });
        typingIndicator.classList.add('hidden');
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'An unknown error occurred.');
        }
        const aiParts = await response.json();
        appendAiTurn(aiParts, 'model'); // Ensure role is 'model' for AI responses
    } catch (error) {
        console.error('Error:', error);
        typingIndicator.classList.add('hidden');
        const errorParts = [{ japanese: 'エラーが発生しました。', english: `An error occurred: ${error.message}` }];
        appendAiTurn(errorParts, 'model'); // Display error as a model message
    } finally {
        sendButton.disabled = false;
        messageInput.focus();
        scrollToBottom();
    }
}

// --- SETTINGS PANEL LOGIC ---
function openSettings() {
    settingsOverlay.classList.add('open');
    settingsPanel.classList.add('open');
}
function closeSettings() {
    settingsOverlay.classList.remove('open');
    settingsPanel.classList.remove('open');
}
function handleTabClick(e) {
    const clickedTab = e.currentTarget;
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    clickedTab.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`tab-${clickedTab.dataset.tab}`).classList.remove('hidden');
}
function applyCssVariable(cssVar, value, unit = '') {
    document.documentElement.style.setProperty(cssVar, value + unit);
    localStorage.setItem(cssVar, value);
}
function applyBubbleStyle(style) {
    const radius = style === 'sharp' ? '0.125rem' : '0.75rem';
    applyCssVariable('--bubble-radius', radius);
    localStorage.setItem('bubbleStyle', style);
    document.querySelectorAll('#bubble-style-switcher button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.style === style);
    });
}
function applyTheme(theme) {
    document.body.dataset.theme = theme;
    localStorage.setItem('theme', theme);
    document.querySelectorAll('#theme-switcher button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });
}
function loadSettings() {
    settingsPanel.querySelectorAll('input[data-css-var]').forEach(input => {
        const cssVar = input.dataset.cssVar;
        const savedValue = localStorage.getItem(cssVar);
        const defaultValue = getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
        const valueToApply = savedValue || defaultValue;
        if (input.type === 'color') { input.value = valueToApply.startsWith('#') ? valueToApply : '#ffffff'; }
        else { input.value = parseFloat(valueToApply); }
        applyCssVariable(cssVar, valueToApply, input.dataset.unit || '');
    });
    journalNotes.value = localStorage.getItem('journalNotes') || '';
    applyTheme(localStorage.getItem('theme') || 'light');
    applyBubbleStyle(localStorage.getItem('bubbleStyle') || 'rounded');
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    loadJapaneseVoice();

    if (messageForm) {
        // Loop through the 'messages' array passed from Flask and append them
        const messagesFromFlask = JSON.parse(document.getElementById('flask-messages-data').textContent);
        messagesFromFlask.forEach(msg => {
            appendAiTurn(msg.parsed_content, msg.role); // Use the new role parameter
        });

        messageForm.addEventListener('submit', handleFormSubmit);
        settingsButton.addEventListener('click', openSettings);
        closeSettingsButton.addEventListener('click', closeSettings);
        settingsOverlay.addEventListener('click', closeSettings);

        document.querySelectorAll('.tab-button').forEach(btn => btn.addEventListener('click', handleTabClick));
        if (themeSwitcher) {
            themeSwitcher.querySelectorAll('.theme-button').forEach(btn => btn.addEventListener('click', (e) => applyTheme(e.currentTarget.dataset.theme)));
        }
        if (bubbleStyleSwitcher) {
            bubbleStyleSwitcher.querySelectorAll('.theme-button').forEach(btn => btn.addEventListener('click', (e) => applyBubbleStyle(e.currentTarget.dataset.style)));
        }

        settingsPanel.querySelectorAll('input[data-css-var]').forEach(input => {
            input.addEventListener('input', (e) => applyCssVariable(e.target.dataset.cssVar, e.target.value, e.target.dataset.unit || ''));
        });

        journalNotes.addEventListener('input', (e) => localStorage.setItem('journalNotes', e.target.value));

        loadSettings();
        renderVocabList();
        scrollToBottom();
    }
});

// Implement a custom alert/prompt for saveWord
function showCustomAlert(message) {
    const modalHtml = `
        <div id="custom-alert-overlay" class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center">
            <div class="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full text-center">
                <p class="text-lg font-semibold mb-4">${message}</p>
                <button id="custom-alert-ok" class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition">OK</button>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const overlay = document.getElementById('custom-alert-overlay');
    const okButton = document.getElementById('custom-alert-ok');

    okButton.focus();

    const cleanup = () => {
        overlay.remove();
    };

    okButton.onclick = cleanup;
    overlay.onclick = (e) => {
        if (e.target === overlay) {
            cleanup();
        }
    };
    document.onkeydown = (e) => {
        if (e.key === 'Escape' || e.key === 'Enter') {
            cleanup();
        }
    };
}
