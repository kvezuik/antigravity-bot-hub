// Antigravity 2.0 • Desktop Studio Application Controller

let projects = [];
let currentProjectId = null;
let currentChatId = null;
let currentChat = null;
let currentEffort = 'high';
let isGenerating = false;
let authStatus = { authenticated: false, email: null, subscription: 'none' };
let editingChatId = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuthStatus();
  await loadProjects();
});

// ================= GOOGLE AUTH & SUBSCRIPTION =================

async function checkAuthStatus(forceRefresh = false) {
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
      statusTextEl.textContent = 'Требуется вход Google';
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
    console.error('Failed to check auth status:', err);
  }
}

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
      <p style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.5;">
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
      <p style="font-size: 12.5px; color: var(--text-secondary); line-height: 1.5;">
        Использование моделей заблокировано до активации подписки.<br>
        Оформить подписку можно в панели Google One / Antigravity.
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
      <p style="font-size: 12.5px; color: var(--text-secondary);">
        Ядро готово к генерации ответов и выполнению кода.
      </p>
    `;
    actionBtn.textContent = 'Обновить статус';
    actionBtn.onclick = () => checkAuthStatus(true);
  }

  modal.style.display = 'flex';
}

function openAuthModal() {
  showAuthModal(authStatus);
}

function closeAuthModal() {
  document.getElementById('auth-modal').style.display = 'none';
}

// ================= PROJECTS MANAGEMENT =================

async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    const data = await res.json();
    projects = data.projects || [];
    currentProjectId = data.active_id || (projects[0] ? projects[0].id : null);

    renderProjectsMenu();
    updateProjectHeader();
    await loadChats();
  } catch (err) {
    console.error('Failed to load projects:', err);
  }
}

function renderProjectsMenu() {
  const listEl = document.getElementById('projects-list');
  listEl.innerHTML = '';

  projects.forEach(p => {
    const item = document.createElement('button');
    item.className = `dropdown-item ${p.id === currentProjectId ? 'active' : ''}`;
    item.innerHTML = `<span>${p.icon || '📁'}</span> <span>${escapeHtml(p.name)}</span>`;
    item.onclick = () => selectProject(p.id);
    listEl.appendChild(item);
  });
}

function updateProjectHeader() {
  const current = projects.find(p => p.id === currentProjectId) || projects[0];
  if (current) {
    document.getElementById('current-proj-icon').textContent = current.icon || '📁';
    document.getElementById('current-proj-name').textContent = current.name;
    document.getElementById('header-project-pill').textContent = `${current.icon || '📁'} ${current.name}`;
  }
}

function toggleProjectMenu() {
  const menu = document.getElementById('project-dropdown-menu');
  menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

// Close dropdown on outside click
document.addEventListener('click', (e) => {
  const container = document.querySelector('.project-selector-container');
  if (container && !container.contains(e.target)) {
    document.getElementById('project-dropdown-menu').style.display = 'none';
  }
});

async function selectProject(pid) {
  document.getElementById('project-dropdown-menu').style.display = 'none';
  if (pid === currentProjectId) return;

  try {
    await fetch('/api/projects/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: pid })
    });
    currentProjectId = pid;
    renderProjectsMenu();
    updateProjectHeader();
    await loadChats();
  } catch (err) {
    console.error('Failed to select project:', err);
  }
}

function openNewProjectModal() {
  document.getElementById('project-dropdown-menu').style.display = 'none';
  document.getElementById('project-name-input').value = '';
  document.getElementById('project-icon-input').value = '📁';
  document.getElementById('project-modal').style.display = 'flex';
  document.getElementById('project-name-input').focus();
}

function closeProjectModal() {
  document.getElementById('project-modal').style.display = 'none';
}

function setProjectEmoji(emoji) {
  document.getElementById('project-icon-input').value = emoji;
}

async function submitProject() {
  const name = document.getElementById('project-name-input').value.trim();
  const icon = document.getElementById('project-icon-input').value.trim() || '📁';

  if (!name) {
    alert('Пожалуйста, введите название проекта.');
    return;
  }

  try {
    const res = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, icon })
    });
    const newProj = await res.json();
    closeProjectModal();
    await loadProjects();
    await selectProject(newProj.id);
  } catch (err) {
    alert('Ошибка при создании проекта: ' + err.message);
  }
}

// ================= CHATS MANAGEMENT =================

async function loadChats() {
  try {
    const res = await fetch(`/api/chats?project_id=${currentProjectId || ''}`);
    const data = await res.json();
    const chats = data.chats || [];
    currentChatId = data.active_id || (chats[0] ? chats[0].id : null);

    document.getElementById('chats-count').textContent = chats.length;
    renderChatsList(chats);

    if (currentChatId) {
      await loadChatMessages(currentChatId);
    } else if (chats.length > 0) {
      await selectChat(chats[0].id);
    } else {
      // If no chats in this project, open empty state
      document.getElementById('messages-container').innerHTML = '';
      document.getElementById('header-chat-name').textContent = 'Нет диалогов';
      document.getElementById('header-chat-icon').textContent = '💬';
    }
  } catch (err) {
    console.error('Failed to load chats:', err);
  }
}

function renderChatsList(chats) {
  const container = document.getElementById('chats-list');
  container.innerHTML = '';

  chats.forEach(chat => {
    const item = document.createElement('div');
    item.className = `chat-item ${chat.id === currentChatId ? 'active' : ''}`;
    item.onclick = (e) => {
      if (!e.target.closest('.chat-item-actions')) {
        selectChat(chat.id);
      }
    };

    item.innerHTML = `
      <span class="chat-item-icon">${chat.icon || '💬'}</span>
      <span class="chat-item-name">${escapeHtml(chat.name || 'Новый диалог')}</span>
      <div class="chat-item-actions">
        <button class="btn-item-action" onclick="openEditChatModal('${chat.id}')" title="Переименовать диалог">✏️</button>
        <button class="btn-item-action" onclick="confirmDeleteChat('${chat.id}', event)" title="Удалить диалог">✕</button>
      </div>
    `;
    container.appendChild(item);
  });
}

async function selectChat(chatId) {
  if (chatId === currentChatId && currentChat) return;

  try {
    await fetch('/api/chats/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: chatId })
    });
    currentChatId = chatId;
    await loadChats();
  } catch (err) {
    console.error('Failed to select chat:', err);
  }
}

async function loadChatMessages(chatId) {
  try {
    const res = await fetch(`/api/chats/messages?id=${chatId}`);
    if (!res.ok) return;

    const chat = await res.json();
    currentChat = chat;

    // Update Header
    document.getElementById('header-chat-icon').textContent = chat.icon || '💬';
    document.getElementById('header-chat-name').textContent = chat.name || 'Новый диалог';
    document.getElementById('header-model-pill').textContent = formatModelName(chat.model);
    document.getElementById('header-effort-pill').textContent = `⚡ ${capitalize(chat.effort || 'high')} Reasoning`;

    // Update Sidebar inputs
    if (chat.model) {
      document.getElementById('sidebar-model-select').value = chat.model;
    }
    if (chat.effort) {
      setEffort(chat.effort, false);
    }

    // Render Messages
    renderMessages(chat.messages || []);
  } catch (err) {
    console.error('Failed to load chat messages:', err);
  }
}

function renderMessages(messages) {
  const container = document.getElementById('messages-container');
  container.innerHTML = '';

  messages.forEach(msg => {
    appendMessage(msg.role, msg.content, msg.thoughts, false);
  });

  scrollToBottom();
}

function openNewChatModal() {
  editingChatId = null;
  document.getElementById('chat-modal-title').textContent = '💬 Новый диалог';
  document.getElementById('chat-name-input').value = '';
  document.getElementById('chat-icon-input').value = '💬';
  document.getElementById('chat-modal').style.display = 'flex';
  document.getElementById('chat-name-input').focus();
}

function openEditChatModal(chatId = null) {
  editingChatId = chatId || currentChatId;
  const chat = currentChat;
  document.getElementById('chat-modal-title').textContent = '✏️ Редактирование диалога';
  document.getElementById('chat-name-input').value = (chat && chat.name) ? chat.name : '';
  document.getElementById('chat-icon-input').value = (chat && chat.icon) ? chat.icon : '💬';
  document.getElementById('chat-modal').style.display = 'flex';
  document.getElementById('chat-name-input').focus();
}

function closeChatModal() {
  document.getElementById('chat-modal').style.display = 'none';
  editingChatId = null;
}

function setChatEmoji(emoji) {
  document.getElementById('chat-icon-input').value = emoji;
}

async function submitChatModal() {
  const name = document.getElementById('chat-name-input').value.trim();
  const icon = document.getElementById('chat-icon-input').value.trim() || '💬';

  if (!name) {
    alert('Пожалуйста, введите название диалога.');
    return;
  }

  try {
    if (editingChatId) {
      // Update existing chat
      await fetch('/api/chats/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: editingChatId, name, icon })
      });
      closeChatModal();
      await loadChats();
    } else {
      // Create new chat
      const model = document.getElementById('sidebar-model-select').value;
      const res = await fetch('/api/chats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: currentProjectId,
          name,
          icon,
          model
        })
      });
      const newChat = await res.json();
      closeChatModal();
      await loadChats();
      await selectChat(newChat.id);
    }
  } catch (err) {
    alert('Ошибка при сохранении диалога: ' + err.message);
  }
}

async function confirmDeleteChat(chatId, event) {
  if (event) event.stopPropagation();
  if (confirm('Вы уверены, что хотите удалить этот диалог?')) {
    try {
      await fetch('/api/chats/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: chatId })
      });
      await loadChats();
    } catch (err) {
      alert('Ошибка при удалении диалога: ' + err.message);
    }
  }
}

async function clearCurrentChat() {
  if (!currentChatId) return;
  if (confirm('Очистить все сообщения в текущем диалоге?')) {
    try {
      await fetch('/api/chats/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: currentChatId })
      });
      await loadChatMessages(currentChatId);
    } catch (err) {
      alert('Ошибка при очистке диалога: ' + err.message);
    }
  }
}

async function exportCurrentChat() {
  if (!currentChatId) return;
  try {
    const res = await fetch(`/api/chats/export?id=${currentChatId}`);
    const data = await res.json();
    alert('Диалог сохранен в файл:\n' + data.path);
  } catch (err) {
    alert('Ошибка сохранения: ' + err.message);
  }
}

// ================= MODEL & EFFORT SETTINGS =================

async function onSidebarModelChange() {
  const model = document.getElementById('sidebar-model-select').value;
  if (currentChatId) {
    await fetch('/api/chats/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentChatId, model })
    });
    document.getElementById('header-model-pill').textContent = formatModelName(model);
  }
}

async function setEffort(level, saveToBackend = true) {
  currentEffort = level;
  document.querySelectorAll('.effort-pill').forEach(pill => {
    pill.classList.toggle('active', pill.dataset.effort === level);
  });
  document.getElementById('header-effort-pill').textContent = `⚡ ${capitalize(level)} Reasoning`;

  if (saveToBackend && currentChatId) {
    await fetch('/api/chats/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentChatId, effort: level })
    });
  }
}

// ================= CHAT MESSAGING =================

async function sendMessage() {
  if (isGenerating) return;

  const textarea = document.getElementById('chat-textarea');
  const text = textarea.value.trim();
  if (!text) return;

  if (!currentChatId) {
    openNewChatModal();
    return;
  }

  // Append user message immediately
  appendMessage('user', text);
  textarea.value = '';
  autoResizeTextarea(textarea);

  // Set thinking state
  isGenerating = true;
  const indicator = document.getElementById('thinking-indicator');
  indicator.style.display = 'flex';
  scrollToBottom();

  const model = document.getElementById('sidebar-model-select').value;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: currentChatId,
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
      appendMessage('assistant', data.reply || data.message || 'Ошибка доступа к модели.');
    } else if (data.reply) {
      appendMessage('assistant', data.reply, data.thoughts);
    } else {
      appendMessage('assistant', `❌ Ошибка: ${data.message || 'Не удалось получить ответ'}`);
    }
  } catch (err) {
    indicator.style.display = 'none';
    isGenerating = false;
    appendMessage('assistant', `❌ Ошибка соединения с сервером: ${err.message}`);
  }
}

function appendMessage(role, content, thoughts = '', scroll = true) {
  const container = document.getElementById('messages-container');
  const card = document.createElement('div');
  card.className = `message-card ${role}`;

  const avatar = role === 'user' ? '👤' : '✦';
  const author = role === 'user' ? 'Вы' : 'Antigravity 2.0';

  let bodyHtml = '';

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
  if (scroll) scrollToBottom();
}

function toggleThought(headerEl) {
  const body = headerEl.nextElementSibling;
  if (body) {
    body.style.display = body.style.display === 'none' ? 'block' : 'none';
  }
}

// Markdown Formatter
function formatMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Fenced Code Blocks with Copy button
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
  html = html.replace(/^### (.*$)/gim, '<h4 style="margin: 8px 0 4px; color: var(--accent-primary);">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="margin: 10px 0 6px; color: var(--text-main);">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 style="margin: 12px 0 8px; color: var(--accent-indigo);">$1</h2>');

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

function formatModelName(model) {
  if (!model) return 'Gemini 3.8 Flash';
  if (model.includes('3.8-flash')) return 'Gemini 3.8 Flash';
  if (model.includes('3.1-pro')) return 'Gemini 3.1 Pro';
  if (model.includes('sonnet')) return 'Claude Sonnet';
  return model;
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}
