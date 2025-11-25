// WebSocket connection for real-time updates
const ws = new WebSocket("ws://" + window.location.host + "/ws/status");

// DOM elements
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const currentTask = document.getElementById('current-task');
const queueCount = document.getElementById('queue-count');
const queueList = document.getElementById('queue-list');
const log = document.getElementById('log');
const taskForm = document.getElementById('task-form');
const formResponse = document.getElementById('form-response');

// WebSocket events
ws.onopen = () => {
    updateStatus('online', 'Disconnected');
    addLogMessage("INFO: Connected to server", 'info');
    fetchSystemState(); // Load initial state
};

ws.onmessage = (event) => {
    try {
        // Try to parse as JSON first (for system state)
        const data = JSON.parse(event.data);
        if (data.type === 'system_state') {
            updateSystemState(data.data);
        }
    } catch (e) {
        // If not JSON, treat as plain text message
        addLogMessage(event.data, getMessageClass(event.data));

        // Refresh system state when important events happen
        if (event.data.startsWith('NEW:') || event.data.startsWith('START:') ||
            event.data.startsWith('END:') || event.data.startsWith('STOP:')) {
            fetchSystemState();
        }
    }
};

ws.onclose = () => {
    updateStatus('offline', 'Disconnected');
    addLogMessage("INFO: Disconnected from server", 'info');
};

ws.onerror = (error) => {
    addLogMessage("CHYBA: Error connecting", 'stop');
};

// Form submission
taskForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const taskData = {
        username: document.getElementById('username').value,
        name: document.getElementById('name').value,
        pages: parseInt(document.getElementById('pages').value),
        priority: parseInt(document.getElementById('priority').value)
    };

    showFormResponse('Sending...', '');

    try {
        const response = await fetch('/tasks/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(taskData)
        });

        const result = await response.json();
        if (response.ok) {
            showFormResponse('Task added!', 'success');
            taskForm.reset();
            fetchSystemState(); // Refresh the display
        } else {
            showFormResponse('Error: ' + (result.error || 'Neznámá chyba'), 'error');
        }
    } catch (error) {
        showFormResponse('Error connecting', 'error');
    }

    setTimeout(() => {
        formResponse.textContent = '';
        formResponse.className = '';
    }, 3000);
});

async function fetchSystemState() {
    try {
        const response = await fetch('/system-state/');
        const state = await response.json();
        updateSystemState(state);
    } catch (error) {
        console.error('Error fetching system state:', error);
    }
}

function updateSystemState(state) {
    console.log('Updating system state:', state); // Debug log

    queueCount.textContent = state.queue_length;

    updatePrinterStatus(state);

    updateQueueList(state.queue_tasks);
}

function updatePrinterStatus(state) {
    if (state.printer_status === 'printing' && state.current_task) {
        updateStatus('printing', 'printing');
        currentTask.textContent = `${state.current_task.name} (${state.current_task.pages} pages)`;
    } else {
        updateStatus('online', 'Ready');
        currentTask.textContent = 'Nic';
    }
}

function updateQueueList(tasks) {
    console.log('Updating queue with tasks:', tasks); // Debug log

    if (tasks.length === 0) {
        queueList.innerHTML = '<p class="empty">Queue is empty/p>';
        return;
    }

    queueList.innerHTML = tasks.map(task => `
        <div class="queue-item">
            <div class="queue-item-header">
                <span class="queue-item-name">${task.name}</span>
                <span class="queue-item-priority">Priorita: ${task.priority}</span>
            </div>
            <div class="queue-item-details">
                Uživatel: ${task.user} | Stran: ${task.pages}
            </div>
        </div>
    `).join('');
}

function updateStatus(status, text) {
    statusIndicator.className = 'status-indicator';
    statusIndicator.classList.add(`status-${status}`);
    statusText.textContent = text;
}

function addLogMessage(message, className) {
    const li = document.createElement('li');
    li.textContent = message;
    li.className = className;
    log.appendChild(li);
    log.scrollTop = log.scrollHeight;
}

function getMessageClass(message) {
    if (message.startsWith('INFO:')) return 'info';
    if (message.startsWith('NEW:')) return 'new';
    if (message.startsWith('START:')) return 'start';
    if (message.startsWith('END:')) return 'end';
    if (message.startsWith('STOP:')) return 'stop';
    return 'info';
}

function showFormResponse(message, className) {
    formResponse.textContent = message;
    formResponse.className = className;
}

setInterval(fetchSystemState, 3000);