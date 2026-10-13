/**
 * AURA Companion - Hitodama Desktop Island Client Controller
 * Renders 60 FPS Canvas Particle Orb, Agentic Pipeline Visualizer, and Real-Time Event Engine.
 */

// Global State
let currentOrbState = 'idle'; // idle | listening | thinking | speaking | error
let tasksList = [];
let remindersList = [];
let pendingConfirmationAction = null;

// Design Tokens (Parity with Tokens.cs)
const COLORS = {
  idle: { core: '#45F3FF', glow: 'rgba(102, 252, 241, 0.45)', particles: '#66FCF1' },
  listening: { core: '#FFFFFF', glow: 'rgba(69, 243, 255, 0.85)', particles: '#45F3FF' },
  thinking: { core: '#FFB84E', glow: 'rgba(255, 184, 78, 0.65)', particles: '#FFE34E' },
  speaking: { core: '#4EFF9B', glow: 'rgba(78, 255, 155, 0.75)', particles: '#8CFFC2' },
  error: { core: '#FF4E64', glow: 'rgba(255, 78, 100, 0.85)', particles: '#FF7B8C' }
};

// --------------------------------------------------------------------------
// 1. Hitodama Companion Orb 60 FPS Particle Canvas Simulation
// --------------------------------------------------------------------------
const canvas = document.getElementById('orbCanvas');
const ctx = canvas.getContext('2d');
const width = canvas.width;
const height = canvas.height;
const centerX = width / 2;
const centerY = height / 2;

// Particles definition
const PARTICLE_COUNT = 36;
const particles = [];
for (let i = 0; i < PARTICLE_COUNT; i++) {
  particles.push({
    angle: (i / PARTICLE_COUNT) * Math.PI * 2,
    radius: 45 + Math.random() * 30,
    speed: 0.015 + Math.random() * 0.02,
    size: 2 + Math.random() * 3,
    alpha: 0.3 + Math.random() * 0.7,
    oscFreq: 1 + Math.random() * 3,
  });
}

let tick = 0;

function renderOrb() {
  tick += 0.03;
  ctx.clearRect(0, 0, width, height);

  const theme = COLORS[currentOrbState] || COLORS.idle;

  // Outer ambient pulsing glow
  const pulseScale = 1 + Math.sin(tick * 1.5) * 0.08;
  const glowRadius = 80 * pulseScale;

  const glowGradient = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, glowRadius);
  glowGradient.addColorStop(0, theme.glow);
  glowGradient.addColorStop(0.5, theme.glow.replace(/[\d\.]+\)$/, '0.15)'));
  glowGradient.addColorStop(1, 'rgba(11, 12, 16, 0)');
  ctx.fillStyle = glowGradient;
  ctx.beginPath();
  ctx.arc(centerX, centerY, glowRadius, 0, Math.PI * 2);
  ctx.fill();

  // Swirling Particle Field
  for (let p of particles) {
    p.angle += p.speed * (currentOrbState === 'thinking' ? 2.5 : 1);
    const rOffset = Math.sin(tick * p.oscFreq) * 8;
    const currentRadius = (p.radius + rOffset) * (currentOrbState === 'listening' ? 1.2 : 1);

    const px = centerX + Math.cos(p.angle) * currentRadius;
    const py = centerY + Math.sin(p.angle) * currentRadius;

    ctx.fillStyle = theme.particles;
    ctx.globalAlpha = p.alpha;
    ctx.beginPath();
    ctx.arc(px, py, p.size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1.0;

  // Solid Core Particle
  const coreRadius = (32 + Math.sin(tick * 2) * 3) * (currentOrbState === 'listening' ? 1.15 : 1);
  const coreGrad = ctx.createRadialGradient(centerX - 8, centerY - 8, 4, centerX, centerY, coreRadius);
  coreGrad.addColorStop(0, '#FFFFFF');
  coreGrad.addColorStop(0.3, theme.core);
  coreGrad.addColorStop(1, theme.glow);

  ctx.fillStyle = coreGrad;
  ctx.beginPath();
  ctx.arc(centerX, centerY, coreRadius, 0, Math.PI * 2);
  ctx.fill();

  // Specular Highlight
  ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
  ctx.beginPath();
  ctx.arc(centerX - 8, centerY - 10, coreRadius * 0.28, 0, Math.PI * 2);
  ctx.fill();

  requestAnimationFrame(renderOrb);
}

renderOrb();

// State Switcher
function setOrbState(state) {
  currentOrbState = state;
  const badge = document.getElementById('orbStateBadge');
  badge.className = `badge badge-${state}`;
  badge.textContent = `STATE: ${state.toUpperCase()}`;

  document.querySelectorAll('.state-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.state === state);
  });
}

document.querySelectorAll('.state-btn').forEach(btn => {
  btn.addEventListener('click', () => setOrbState(btn.dataset.state));
});

canvas.addEventListener('click', () => {
  const states = ['idle', 'listening', 'thinking', 'speaking', 'error'];
  const nextIdx = (states.indexOf(currentOrbState) + 1) % states.length;
  setOrbState(states[nextIdx]);
});

// --------------------------------------------------------------------------
// 2. FSM Pipeline State Machine Highlighting
// --------------------------------------------------------------------------
function resetFsmNodes() {
  document.querySelectorAll('.fsm-node').forEach(node => {
    node.className = 'fsm-node';
  });
  document.getElementById('activeStateText').textContent = 'READY';
}

async function animateFsmPipeline(states) {
  resetFsmNodes();
  for (let s of states) {
    const el = document.querySelector(`.fsm-node[data-fsm="${s}"]`);
    if (el) {
      document.querySelectorAll('.fsm-node.active').forEach(n => {
        n.classList.remove('active');
        n.classList.add('completed');
      });
      el.classList.add('active');
      document.getElementById('activeStateText').textContent = s;
      await new Promise(r => setTimeout(r, 120));
    }
  }
}

// --------------------------------------------------------------------------
// 3. Island Tabs
// --------------------------------------------------------------------------
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    btn.classList.add('active');
    const target = btn.dataset.tab;
    const pane = document.getElementById(`tab${target.charAt(0).toUpperCase() + target.slice(1)}`);
    if (pane) pane.classList.add('active');

    if (target === 'tasks') loadTasks();
    if (target === 'reminders') loadReminders();
    if (target === 'telemetry') loadTelemetry();
  });
});

// --------------------------------------------------------------------------
// 4. Chat & Agentic Request Execution
// --------------------------------------------------------------------------
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const chatHistory = document.getElementById('chatHistory');

function addChatMessage(sender, text, isAssistant = false) {
  const msg = document.createElement('div');
  msg.className = `chat-message ${isAssistant ? 'assistant' : 'user'}`;
  msg.innerHTML = `
    <div class="avatar">${isAssistant ? 'A' : 'U'}</div>
    <div class="message-body">
      <div class="author-name">${isAssistant ? 'AURA Companion' : 'You'}</div>
      <p>${escapeHtml(text)}</p>
    </div>
  `;
  chatHistory.appendChild(msg);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  addChatMessage('user', text, false);
  userInput.value = '';

  setOrbState('thinking');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, user_confirmed: false })
    });
    const data = await res.json();

    if (data.execution_states) {
      await animateFsmPipeline(data.execution_states);
    }

    if (data.error_code === 'CONFIRMATION_REQUIRED') {
      setOrbState('error');
      openConfirmationModal(
        'Confirm Destructive Operation',
        `AURA blocked execution: ${data.reply}\nDo you wish to confirm?`,
        async () => {
          // Re-send with user_confirmed: true
          const confirmRes = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, user_confirmed: true })
          });
          const confirmData = await confirmRes.json();
          addChatMessage('assistant', confirmData.reply, true);
          setOrbState('speaking');
          setTimeout(() => setOrbState('idle'), 2000);
          loadTasks();
        }
      );
    } else {
      setOrbState('speaking');
      addChatMessage('assistant', data.reply, true);
      setTimeout(() => setOrbState('idle'), 2200);
    }

    loadTasks();
    loadReminders();
  } catch (err) {
    setOrbState('error');
    addChatMessage('assistant', 'Error connecting to AURA local runtime: ' + err.message, true);
  }
});

// Chips click handler
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('chip')) {
    userInput.value = e.target.textContent;
    chatForm.dispatchEvent(new Event('submit'));
  }
});

// --------------------------------------------------------------------------
// 5. Tasks Management
// --------------------------------------------------------------------------
async function loadTasks() {
  try {
    const res = await fetch('/api/tasks');
    tasksList = await res.json();
    renderTasks();
    document.getElementById('taskCountBadge').textContent = tasksList.filter(t => t.status === 'open').length;
  } catch (e) {
    console.error('Failed to load tasks', e);
  }
}

function renderTasks() {
  const container = document.getElementById('taskListContainer');
  const query = (document.getElementById('taskSearchInput').value || '').toLowerCase();
  const filtered = tasksList.filter(t => t.title.toLowerCase().includes(query));

  if (!filtered.length) {
    container.innerHTML = '<div class="empty-state">No tasks matching search criteria.</div>';
    return;
  }

  container.innerHTML = filtered.map(t => `
    <div class="task-item">
      <div class="item-left">
        <div class="checkbox-custom ${t.status === 'completed' ? 'checked' : ''}" onclick="toggleTaskStatus('${t.id}', '${t.status}')">
          ${t.status === 'completed' ? '✓' : ''}
        </div>
        <div>
          <div class="item-title ${t.status === 'completed' ? 'completed' : ''}">${escapeHtml(t.title)}</div>
          ${t.due_date ? `<span style="font-size: 11px; color: var(--color-text-secondary);">Due: ${t.due_date}</span>` : ''}
        </div>
      </div>
      <div class="item-actions">
        <span class="priority-pill prio-${t.priority}">${t.priority}</span>
        <button class="icon-action-btn" onclick="requestDeleteTask('${t.id}', '${escapeHtml(t.title)}')">✕</button>
      </div>
    </div>
  `).join('');
}

document.getElementById('taskSearchInput').addEventListener('input', renderTasks);

async function toggleTaskStatus(id, currentStatus) {
  const endpoint = currentStatus === 'completed' ? `/api/tasks/${id}/reopen` : `/api/tasks/${id}/complete`;
  await fetch(endpoint, { method: 'POST' });
  loadTasks();
}

function requestDeleteTask(id, title) {
  openConfirmationModal(
    'Delete Task',
    `Are you sure you want to permanently delete task "${title}"?`,
    async () => {
      await fetch(`/api/tasks/${id}?confirmed=true`, { method: 'DELETE' });
      loadTasks();
    }
  );
}

// Create Task Modal
const taskModal = document.getElementById('taskModal');
document.getElementById('openNewTaskModalBtn').onclick = () => taskModal.classList.add('show');
document.getElementById('closeTaskModalBtn').onclick = () => taskModal.classList.remove('show');
document.getElementById('cancelTaskModalBtn').onclick = () => taskModal.classList.remove('show');

document.getElementById('createTaskForm').onsubmit = async (e) => {
  e.preventDefault();
  const title = document.getElementById('newTaskTitle').value;
  const description = document.getElementById('newTaskDesc').value;
  const priority = document.getElementById('newTaskPriority').value;
  const due_date = document.getElementById('newTaskDueDate').value;

  await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description, priority, due_date })
  });

  taskModal.classList.remove('show');
  document.getElementById('createTaskForm').reset();
  loadTasks();
};

// --------------------------------------------------------------------------
// 6. Reminders Management
// --------------------------------------------------------------------------
async function loadReminders() {
  try {
    const res = await fetch('/api/reminders');
    remindersList = await res.json();
    renderReminders();
    document.getElementById('reminderCountBadge').textContent = remindersList.filter(r => r.status === 'scheduled').length;
  } catch (e) {
    console.error('Failed to load reminders', e);
  }
}

function renderReminders() {
  const container = document.getElementById('reminderListContainer');
  if (!remindersList.length) {
    container.innerHTML = '<div class="empty-state">No scheduled reminders in SQLite database.</div>';
    return;
  }

  container.innerHTML = remindersList.map(r => `
    <div class="reminder-item">
      <div class="item-left">
        <span style="font-size: 16px;">⏰</span>
        <div>
          <div class="item-title">${escapeHtml(r.message)}</div>
          <div style="font-size: 11px; color: var(--color-accent-cyan);">
            Trigger: ${new Date(r.trigger_time_utc).toLocaleString()} 
            ${r.recurrence_rule ? `· Recurrence: ${r.recurrence_rule}` : ''}
          </div>
        </div>
      </div>
      <div class="item-actions">
        <button class="icon-action-btn" onclick="snoozeReminder('${r.id}')">+10m Snooze</button>
        <button class="icon-action-btn" onclick="cancelReminder('${r.id}')">Cancel</button>
      </div>
    </div>
  `).join('');
}

document.getElementById('nlScheduleBtn').onclick = async () => {
  const text = document.getElementById('nlReminderInput').value.trim();
  if (!text) return;

  userInput.value = text;
  document.querySelector('.tab-btn[data-tab="conversation"]').click();
  chatForm.dispatchEvent(new Event('submit'));
  document.getElementById('nlReminderInput').value = '';
};

async function snoozeReminder(id) {
  await fetch(`/api/reminders/${id}/snooze?minutes=10`, { method: 'POST' });
  loadReminders();
}

async function cancelReminder(id) {
  await fetch(`/api/reminders/${id}/cancel`, { method: 'POST' });
  loadReminders();
}

// --------------------------------------------------------------------------
// 7. Privacy, Clipboard & Nuclear Wipe
// --------------------------------------------------------------------------
document.getElementById('testClipboardBtn').onclick = async () => {
  const text = document.getElementById('clipboardTestInput').value;
  const res = await fetch('/api/clipboard_check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  const data = await res.json();
  const box = document.getElementById('clipboardResultBox');
  if (data.is_sensitive) {
    box.style.borderColor = 'var(--color-error)';
    box.innerHTML = `<span style="color: var(--color-error);">⚠️ SENSITIVE CONTENT DETECTED!</span><br>${data.reason}<br><strong>Sanitized for history:</strong><br>${escapeHtml(data.sanitized)}`;
  } else {
    box.style.borderColor = 'var(--color-success)';
    box.innerHTML = `<span style="color: var(--color-success);">✓ Safe Content:</span> No API keys or credentials detected.`;
  }
};

document.getElementById('exportDataBtn').onclick = async () => {
  const [tasksRes, remsRes] = await Promise.all([fetch('/api/tasks'), fetch('/api/reminders')]);
  const data = {
    exported_at: new Date().toISOString(),
    tasks: await tasksRes.json(),
    reminders: await remsRes.json()
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `aura_companion_backup_${Date.now()}.json`;
  a.click();
};

document.getElementById('nuclearWipeBtn').onclick = () => {
  openConfirmationModal(
    'Nuclear Data Wipe',
    'DANGER: This will permanently purge all tasks, reminders, and persistent memory records from SQLite. Proceed?',
    async () => {
      await fetch('/api/nuclear_wipe?confirm=true', { method: 'DELETE' });
      loadTasks();
      loadReminders();
      alert('All local data wiped successfully.');
    }
  );
};

// --------------------------------------------------------------------------
// 8. Hardware Telemetry Polling
// --------------------------------------------------------------------------
async function loadTelemetry() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('telBackend').textContent = data.npu_status.includes('Active') ? 'QUALCOMM_HEXAGON_NPU' : 'CPU_LOCAL';
    document.getElementById('telBackendDesc').textContent = data.npu_status;
    document.getElementById('telDbVer').textContent = `Schema Migration V${data.database_version} Active (WAL)`;
  } catch (e) {
    console.error('Failed to load telemetry', e);
  }
}

// --------------------------------------------------------------------------
// 9. Voice PTT Simulator
// --------------------------------------------------------------------------
const pttBtn = document.getElementById('voicePttBtn');
let isPttActive = false;

pttBtn.onclick = async () => {
  isPttActive = !isPttActive;
  pttBtn.classList.toggle('active', isPttActive);

  if (isPttActive) {
    setOrbState('listening');
    document.getElementById('voiceBtnLabel').textContent = 'Listening...';
  } else {
    document.getElementById('voiceBtnLabel').textContent = 'Win + Space';
    setOrbState('thinking');

    // Simulate speech dictation with spoken correction
    const testSpeech = "Remind me in 30 minutes to review code scratch that 15 minutes to review code";
    const res = await fetch(`/api/voice_simulate?raw_text=${encodeURIComponent(testSpeech)}`, { method: 'POST' });
    const data = await res.json();

    addChatMessage('user', `🎙️ [Spoken]: "${data.raw_text}"`, false);
    addChatMessage('assistant', `Corrected dictation: "${data.corrected_text}"`, true);

    userInput.value = data.corrected_text;
    chatForm.dispatchEvent(new Event('submit'));
  }
};

// --------------------------------------------------------------------------
// 10. Confirmation Modal Engine
// --------------------------------------------------------------------------
const confirmModal = document.getElementById('confirmModal');
const confirmTitle = document.getElementById('confirmModalTitle');
const confirmText = document.getElementById('confirmModalText');
const confirmProceedBtn = document.getElementById('confirmProceedBtn');
const confirmCancelBtn = document.getElementById('confirmCancelBtn');

function openConfirmationModal(title, message, onProceed) {
  confirmTitle.textContent = title;
  confirmText.textContent = message;
  pendingConfirmationAction = onProceed;
  confirmModal.classList.add('show');
}

confirmCancelBtn.onclick = () => {
  confirmModal.classList.remove('show');
  pendingConfirmationAction = null;
};

confirmProceedBtn.onclick = async () => {
  confirmModal.classList.remove('show');
  if (pendingConfirmationAction) {
    await pendingConfirmationAction();
    pendingConfirmationAction = null;
  }
};

// Initial Load
loadTasks();
loadReminders();
loadTelemetry();
