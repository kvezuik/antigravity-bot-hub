// Antigravity 2.0 • Grok Bot Studio Frontend Application

let currentBot = null;
let botsList = [];
let currentEffort = 'high';
let isGenerating = false;
let authStatus = { authenticated: false, email: null, subscription: 'none' };

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  await checkStatus();
  await loadBots();
});

// Check Google Auth & Subscription Status
async function checkStatus(forceRefresh = false) {
  try {
    const url = forceRefresh ? '/api/status?refresh=1' : '/api/status';
    const res = await fetch(url);
    const data = await res.json();
    authStatus = data;

    const emailEl = document.getElementById('account-email');
    const avatarEl = document.getElementById('account-avatar');
    const statusTextEl = document.getElementById('status-text');
    const statusDot = document.querySelector('.status-dot');

    if (!data.authenticated) {
      emailEl.textContent = 'Вход не выполнен';
      avatarEl.textContent = '?';
      statusTextEl.textContent = 'Требуется Google вход';
      statusDot.className = 'status-dot no-sub';
      showAuthModal(data);
    } else if (data.subscription === 'none') {
      emailEl.textContent = data.email || 'Google User';
      avatarEl.textContent = (data.email || 'G')[0].toUpperCase();
      statusTextEl.textContent = 'Нет подписки Antigravity';
      statusDot.className = 'status-dot no-sub';
      showAuthModal(data);
    } else {
      emailEl.textContent = data.email || 'Google User';
      avatarEl.textContent = (data.email || 'G')[0].toUpperCase();
      statusTextEl.textContent = 'Antigravity Pro Active';
      statusDot.className = 'status-dot';
    }
  } catch (err) {
    console.error('Failed to check status:', err);
  }
}

// Show Google Auth / Subscription Modal
function showAuthModal(data) {
  const modal = document.getElementById('auth-modal');
  const body = document.getElementById('auth-modal-body');
  const actionBtn = document.getElementById('modal-action-btn');

  if (!data.authenticated) {
    body.innerHTML = `
      <div class="alert-banner error">
        <strong>⚠️ Требуется авторизация Google:</strong><br>
        Для работы ядра Antigravity 2.0 необходим аккаунт Google с активной подпиской.
      </div>
      <p style="font-size: 13px; color: var(--text-secondary);">
        Нажмите кнопку ниже, чтобы открыть официальную страницу входа в Google Аккаунт.
      </p>
    `;
    actionBtn.textContent = 'Войти через Google';
    actionBtn.onclick = () => window.open(data.login_url || 'https://accounts.google.com/o/oauth2/auth', '_blank');
  } else if (data.subscription === 'none') {
    body.innerHTML = `
      <div class="alert-banner error">
        <strong>❌ Отсутствует активная подписка:</strong><br>
        Аккаунт <b>${data.email}</b> подключен, но не имеет активной подписки Google Antigravity (Gemini Advanced).
      </div>
      <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
        Использование моделей временно заблокировано до активации подписки.<br>
        Оформить подписку можно в панели Google One.
      </p>
    `;
    actionBtn.textContent = 'Оформить подписку';
    actionBtn.onclick = () => window.open('https://one.google.com/explore-plan/gemini-advanced', '_blank');
  } else {
    body.innerHTML = `
      <div class="alert-banner success">
        <strong>✓ Статус в норме:</strong><br>
        Аккаунт <b>${data.email}</b> успешно авторизован.<br>
        Подписка Google Antigravity 2.0 активна.
      </div>
      <p style="font-size: 13px; color: var(--text-secondary);">
        Ядро готово к генерации ответов и выполнению кода.
      </p>
    `;
    actionBtn.textContent = 'Обновить статус';
    actionBtn.onclick = () => checkStatus(true);
  }

  modal.style.display = 'flex';
}

function openAuthModal() {
  showAuthModal(authStatus);
}

function closeAuthModal() {
  document.getElementById('auth-modal').style.display = 'none';
}

// Load Bots list from API
async function loadBots() {
  try {
    const res = await fetch('/api/bots');
    botsList = await res.json();
    renderPersonas();

    if (botsList.length > 0 && !currentBot) {
      selectBot(botsList[0].id);
    }
  } catch (err) {
    console.error('Failed to load bots:', err);
  }
}

// Render Personas in sidebar
function renderPersonas() {
  const container = document.getElementById('personas-list');
  container.innerHTML = '';

  botsList.forEach(bot => {
    const item = document.createElement('div');
    item.className = `persona-item ${currentBot && currentBot.id === bot.id ? 'active' : ''}`;
    item.onclick = () => selectBot(bot.id);

    item.innerHTML = `
      <span class="persona-emoji">${bot.emoji || '🤖'}</span>
      <div class="persona-meta">
        <span class="persona-name">${escapeHtml(bot.name)}</span>
        <span class="persona-tagline">${escapeHtml(bot.tagline || '')}</span>
      </div>
    `;
    container.appendChild(item);
  });
}

// Select Active Bot
function selectBot(botId) {
  const bot = botsList.find(b => b.id === botId);
  if (!bot) return;

  currentBot = bot;
  renderPersonas();

  // Update header
  document.getElementById('header-bot-avatar').textContent = bot.emoji || '🤖';
  document.getElementById('header-bot-name').textContent = bot.name;
  document.getElementById('header-bot-archetype').textContent = (bot.archetype || 'bot').toUpperCase();
  document.getElementById('header-bot-tagline').textContent = bot.tagline || '';

  // Set default model for this bot
  if (bot.model) {
    document.getElementById('model-select').value = bot.model;
  }

  // Clear or render welcome message
  const container = document.getElementById('messages-container');
  container.innerHTML = '';
  
  let greeting = `${bot.emoji} Привет! Я на связи. Чем займемся сегодня?`;
  if (bot.archetype && bot.archetype.includes('rebel')) {
    greeting = `${bot.emoji} Ну что, готов к порции чистой правды и бодрого кода? Выкладывай вопрос, разберем без корпоративной цензуры! 🏴‍☠️`;
  } else if (bot.archetype && bot.archetype.includes('thinker')) {
    greeting = `${bot.emoji} Приветствую. Сформулируй задачу или гипотезу, разберем ее по первым принципам и пошаговой логике. 🧠`;
  } else if (bot.archetype && bot.archetype.includes('coder')) {
    greeting = `${bot.emoji} Терминал готов. Жду код, архитектурную дилемму или лог ошибки. 💻⚡`;
  }

  appendMessage('bot', greeting);
}

// Start New Chat
function startNewChat() {
  if (currentBot) {
    selectBot(currentBot.id);
  }
}

// Model & Effort settings
function updateModelSelection() {
  const model = document.getElementById('model-select').value;
  if (currentBot) {
    currentBot.model = model;
  }
}

function setEffort(level) {
  currentEffort = level;
  document.querySelectorAll('.effort-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.effort === level);
  });
}

// Handle User Input & Sending
async function sendMessage() {
  if (isGenerating) return;

  const textarea = document.getElementById('chat-textarea');
  const text = textarea.value.trim();
  if (!text) return;

  // Append user message to UI
  appendMessage('user', text);
  textarea.value = '';
  autoResizeTextarea(textarea);

  // Set thinking state
  isGenerating = true;
  const indicator = document.getElementById('thinking-indicator');
  const thinkingText = document.getElementById('thinking-text');
  thinkingText.textContent = `${currentBot ? currentBot.name : 'Грок'} размышляет над ответом...`;
  indicator.style.display = 'flex';
  scrollToBottom();

  const model = document.getElementById('model-select').value;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        bot_id: currentBot ? currentBot.id : 'grok_fun',
        message: text,
        model: model,
        effort: currentEffort
      })
    });

    const data = await res.json();
    indicator.style.display = 'none';
    isGenerating = false;

    if (data.error === 'subscription_required' || data.error === 'auth_required') {
      showAuthModal(data);
      appendMessage('bot', data.reply || data.message || 'Ошибка подписки.');
    } else if (data.reply) {
      appendMessage('bot', data.reply, data.thoughts);
    } else {
      appendMessage('bot', `❌ Ошибка: ${data.message || 'Не удалось получить ответ'}`);
    }
  } catch (err) {
    indicator.style.display = 'none';
    isGenerating = false;
    appendMessage('bot', `❌ Ошибка соединения с сервером: ${err.message}`);
  }
}

// Append message card to UI
function appendMessage(role, content, thoughts = '') {
  const container = document.getElementById('messages-container');
  const card = document.createElement('div');
  card.className = `message-card ${role}`;

  const avatar = role === 'user' ? '👤' : (currentBot ? currentBot.emoji : '🤖');
  const author = role === 'user' ? 'Вы' : (currentBot ? currentBot.name : 'Бот');

  let bodyHtml = '';

  // If there are reasoning thoughts, show expandable block
  if (thoughts && thoughts.trim()) {
    bodyHtml += `
      <div class="thought-box">
        <div class="thought-header" onclick="toggleThought(this)">
          <span>💭 Размышления модели (Reasoning Process)</span>
          <span style="font-size: 10px; margin-left: auto;">▼</span>
        </div>
        <div class="thought-body">${escapeHtml(thoughts)}</div>
      </div>
    `;
  }

  bodyHtml += `<div class="text-content">${formatMarkdown(content)}</div>`;

  card.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-body">
      <div class="message-author">${escapeHtml(author)}</div>
      <div class="message-content">${bodyHtml}</div>
    </div>
  `;

  container.appendChild(card);
  scrollToBottom();
}

function toggleThought(headerEl) {
  const body = headerEl.nextElementSibling;
  if (body) {
    body.style.display = body.style.display === 'none' ? 'block' : 'none';
  }
}

// Simple Markdown Formatter
function formatMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Fenced Code Blocks with copy button
  html = html.replace(/```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const id = 'code-' + Math.random().toString(36).substring(2, 9);
    return `
      <pre>
        <button class="code-copy-btn" onclick="copyCode('${id}')">📋 Копировать</button>
        <code id="${id}" class="language-${lang}">${code.trim()}</code>
      </pre>
    `;
  });

  // Inline Code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4 style="margin: 8px 0 4px; color: var(--accent-blue);">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="margin: 10px 0 6px; color: var(--text-primary);">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 style="margin: 12px 0 8px; color: var(--accent-purple);">$1</h2>');

  // Line breaks
  html = html.replace(/\n/g, '<br>');

  return html;
}

function copyCode(id) {
  const el = document.getElementById(id);
  if (!el) return;
  navigator.clipboard.writeText(el.innerText).then(() => {
    alert('Код скопирован в буфер обмена!');
  });
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Auto resize textarea
function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

function handleTextareaKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function insertPrompt(promptText) {
  const textarea = document.getElementById('chat-textarea');
  textarea.value = promptText;
  textarea.focus();
  autoResizeTextarea(textarea);
}

function scrollToBottom() {
  const container = document.getElementById('messages-container');
  container.scrollTop = container.scrollHeight;
}

// Custom Bot Modal Functions
function openCreateBotModal() {
  document.getElementById('create-bot-modal').style.display = 'flex';
}

function closeCreateBotModal() {
  document.getElementById('create-bot-modal').style.display = 'none';
}

async function submitCreateBot() {
  const name = document.getElementById('new-bot-name').value.trim();
  const emoji = document.getElementById('new-bot-emoji').value.trim() || '🤖';
  const tagline = document.getElementById('new-bot-tagline').value.trim();
  const archetype = document.getElementById('new-bot-archetype').value;
  const humor = parseInt(document.getElementById('new-bot-humor').value, 10);
  const prompt = document.getElementById('new-bot-prompt').value.trim();

  if (!name) {
    alert('Пожалуйста, введите имя бота.');
    return;
  }

  try {
    const res = await fetch('/api/bots', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name, emoji, tagline, archetype,
        humor_level: humor,
        system_prompt: prompt || 'Ты умный персональный ИИ-ассистент в стиле Grok.'
      })
    });

    const newBot = await res.json();
    closeCreateBotModal();
    await loadBots();
    selectBot(newBot.id);
  } catch (err) {
    alert('Ошибка при создании бота: ' + err.message);
  }
}

// Clear Chat
function clearCurrentChat() {
  if (confirm('Очистить историю текущего диалога?')) {
    startNewChat();
  }
}

// Export Chat Markdown
async function saveChatMarkdown() {
  if (!currentBot) return;
  try {
    const res = await fetch(`/api/export-chat?bot_id=${currentBot.id}`);
    const data = await res.json();
    alert('Диалог сохранен в файл:\n' + data.path);
  } catch (err) {
    alert('Ошибка сохранения: ' + err.message);
  }
}

// Export Bot to Antigravity Rules
async function exportCurrentToRules() {
  if (!currentBot) return;
  try {
    const res = await fetch('/api/export-rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bot_id: currentBot.id })
    });
    const data = await res.json();
    alert('Правило успешно создано в Antigravity:\n' + data.path);
  } catch (err) {
    alert('Ошибка экспорта: ' + err.message);
  }
}
