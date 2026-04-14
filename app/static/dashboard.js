const tasksEl = document.getElementById('tasks');
const detailEl = document.getElementById('detail');

async function fetchTasks() {
  const res = await fetch('/api/tasks');
  const tasks = await res.json();
  tasksEl.innerHTML = '';
  tasks.forEach((t) => {
    const li = document.createElement('li');
    li.innerHTML = `<b>#${t.id}</b> [${t.status}] ${t.goal} <button data-id="${t.id}">Detay</button>`;
    tasksEl.appendChild(li);
  });
}

async function fetchDetail(id) {
  const res = await fetch(`/api/tasks/${id}`);
  const data = await res.json();
  detailEl.textContent = JSON.stringify(data, null, 2);
}

document.getElementById('task-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const goal = document.getElementById('goal').value.trim();
  if (!goal) return;
  await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal })
  });
  document.getElementById('goal').value = '';
  fetchTasks();
});

document.getElementById('refresh').addEventListener('click', fetchTasks);

tasksEl.addEventListener('click', (e) => {
  if (e.target.tagName === 'BUTTON') {
    fetchDetail(e.target.dataset.id);
  }
});

fetchTasks();
setInterval(fetchTasks, 5000);
