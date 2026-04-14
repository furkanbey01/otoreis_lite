let selectedTaskId = null;

const tasksEl = document.getElementById('tasks');
const detailEl = document.getElementById('detail');
const settingsView = document.getElementById('settings-view');

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${txt}`);
  }
  return res.json();
}

function parseIntOrNull(v) {
  const trimmed = String(v || '').trim();
  if (!trimmed) return null;
  const n = Number(trimmed);
  return Number.isFinite(n) ? n : null;
}

async function loadSettings() {
  const s = await api('/api/settings');
  document.getElementById('default_timeout_sec').value = s.default_timeout_sec;
  document.getElementById('max_steps').value = s.max_steps;
  document.getElementById('max_retries').value = s.max_retries;
  document.getElementById('require_approval').checked = s.require_approval;
  settingsView.textContent = JSON.stringify(s, null, 2);
}

async function saveSettings(event) {
  event.preventDefault();
  const payload = {
    default_timeout_sec: parseIntOrNull(document.getElementById('default_timeout_sec').value),
    max_steps: parseIntOrNull(document.getElementById('max_steps').value),
    max_retries: parseIntOrNull(document.getElementById('max_retries').value),
    require_approval: document.getElementById('require_approval').checked,
  };
  const s = await api('/api/settings', { method: 'PUT', body: JSON.stringify(payload) });
  settingsView.textContent = JSON.stringify(s, null, 2);
}

async function fetchTasks() {
  const tasks = await api('/api/tasks');
  tasksEl.innerHTML = '';
  tasks.forEach((t) => {
    const li = document.createElement('li');
    li.innerHTML = `<b>#${t.id}</b> [${t.status}] ${t.goal} (${t.current_step}/${t.total_steps}) <button data-id="${t.id}">Detay</button>`;
    tasksEl.appendChild(li);
  });
}

async function fetchDetail(id) {
  selectedTaskId = Number(id);
  const data = await api(`/api/tasks/${id}`);
  detailEl.textContent = JSON.stringify(data, null, 2);
}

function parseSteps(raw) {
  const txt = (raw || '').trim();
  if (!txt) return null;
  return JSON.parse(txt);
}

async function createTask(event) {
  event.preventDefault();
  const payload = {
    goal: document.getElementById('goal').value.trim(),
    steps: parseSteps(document.getElementById('steps_json').value),
    require_approval: document.getElementById('task_require_approval').checked,
    timeout_sec: parseIntOrNull(document.getElementById('task_timeout').value),
    max_steps: parseIntOrNull(document.getElementById('task_max_steps').value),
    max_retries: parseIntOrNull(document.getElementById('task_retries').value),
  };
  if (!payload.goal) {
    alert('Goal zorunlu');
    return;
  }
  const res = await api('/api/tasks', { method: 'POST', body: JSON.stringify(payload) });
  await fetchTasks();
  await fetchDetail(res.id);
}

async function approveCurrent(approve) {
  if (!selectedTaskId) return alert('Önce bir görev seçin');
  await api(`/api/tasks/${selectedTaskId}/approval`, {
    method: 'POST',
    body: JSON.stringify({ approve, note: approve ? 'approved from dashboard' : 'denied from dashboard' })
  });
  await fetchDetail(selectedTaskId);
  await fetchTasks();
}

async function cancelCurrent() {
  if (!selectedTaskId) return alert('Önce bir görev seçin');
  await api(`/api/tasks/${selectedTaskId}/cancel`, { method: 'POST', body: '{}' });
  await fetchDetail(selectedTaskId);
  await fetchTasks();
}

document.getElementById('settings-form').addEventListener('submit', (e) => {
  saveSettings(e).catch((err) => alert(err.message));
});
document.getElementById('task-form').addEventListener('submit', (e) => {
  createTask(e).catch((err) => alert(err.message));
});
document.getElementById('refresh-all').addEventListener('click', () => {
  Promise.all([loadSettings(), fetchTasks()]).catch((err) => alert(err.message));
});
document.getElementById('approve-btn').addEventListener('click', () => {
  approveCurrent(true).catch((err) => alert(err.message));
});
document.getElementById('deny-btn').addEventListener('click', () => {
  approveCurrent(false).catch((err) => alert(err.message));
});
document.getElementById('cancel-btn').addEventListener('click', () => {
  cancelCurrent().catch((err) => alert(err.message));
});

tasksEl.addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON') {
    fetchDetail(e.target.dataset.id).catch((err) => alert(err.message));
  }
});

Promise.all([loadSettings(), fetchTasks()]).catch((err) => {
  alert(err.message);
});
setInterval(() => {
  fetchTasks().catch(() => {});
  if (selectedTaskId) fetchDetail(selectedTaskId).catch(() => {});
}, 4000);
