const ws = new WebSocket("ws://" + window.location.host + "/ws/status");
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const currentTask = document.getElementById('current-task');
const queueCount = document.getElementById('queue-count');
const queueList = document.getElementById('queue-list');
const taskForm = document.getElementById('task-form');
const formResponse = document.getElementById('form-response');
const allowedExtensions = [".pdf", ".docx", ".jpg", ".jpeg", ".png"];

ws.onopen = () => {
    updateStatus('online', 'Disconnected');
    fetchSystemState();
};

ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (data.type === 'system_state') {
            updateSystemState(data.data);
        }
    } catch (e) {

    }
};

ws.onclose = () => {
    updateStatus('offline', 'Disconnected');
};

ws.onerror = (error) => {
};

taskForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData();
    formData.append("username", document.getElementById('username').value);
    formData.append("priority", parseInt(document.getElementById('priority').value));

    const fileInput = document.getElementById('file');
    if (fileInput.files.length === 0) {
    showFormResponse('Error: You have not selected a file', 'error');
    return;
    }

    const file = fileInput.files[0];

    if (!isAllowed(file.name)) {
    showFormResponse(
        'Invalid file type! Allowed types: ' + allowedExtensions.join(', '),
        'error'
    );
    return;
    }

    formData.append("file", file);

    showFormResponse('Sending...', '');

    try {
        const response = await fetch('/tasks/', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showFormResponse('Task added!', 'success');
            taskForm.reset();
        } else {
            showFormResponse('Error: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showFormResponse('Error connecting', 'l', 'error');
    }

    setTimeout(() => {
        formResponse.textContent = '';
        formResponse.className = '';
    }, 3000);
});

function isAllowed(filename) {
    return allowedExtensions.some(ext => filename.toLowerCase().endsWith(ext));
}

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
    console.log('Updating system state:', state);
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
        currentTask.textContent = 'Nothing';
    }
}

function updateQueueList(tasks) {
    console.log('Updating queue with tasks:', tasks);
    if (tasks.length === 0) {
        queueList.innerHTML = '<p class="empty">Queue is empty</p>';
        return;
    }

    queueList.innerHTML = tasks.map(task =>
        `<div class="queue-item">
            <div class="queue-item-header">
                <span class="queue-item-name">${task.name}</span>
                <span class="queue-item-priority">Priorita: ${task.priority}</span>
            </div>
            <div class="queue-item-details">
                Uživatel: ${task.user} | Stran: ${task.pages}
            </div>
        </div>`
    ).join('');
}

function updateStatus(status, text) {
    statusIndicator.className = 'status-indicator';
    statusIndicator.classList.add(`status-${status}`);
    statusText.textContent = text;
}

function showFormResponse(message, className) {
    formResponse.textContent = message;
    formResponse.className = className;
}
