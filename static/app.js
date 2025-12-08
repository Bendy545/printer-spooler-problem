const ws = new WebSocket("ws://" + window.location.host + "/ws/status");
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const currentTask = document.getElementById('current-task');
const queueCount = document.getElementById('queue-count');
const queueList = document.getElementById('queue-list');
const taskForm = document.getElementById('task-form');
const formResponse = document.getElementById('form-response');
const allowedExtensions = [".pdf"];

ws.onopen = () => {
    updateStatus('online', 'Connected');
    fetchSystemState();
};

ws.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (data.type === 'system_state') {
            updateSystemState(data.data);
        }
    } catch (e) {
        console.log('Server message:', event.data);
    }
};

ws.onclose = () => {
    updateStatus('offline', 'Disconnected from server');
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

/**
 * Form submission handler for adding a new task.
 */
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
            showFormResponse('Task added to queue!', 'success');
            taskForm.reset();
        } else {
            showFormResponse('Error: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showFormResponse('Error connecting to server', 'error');
    }

    setTimeout(() => {
        formResponse.textContent = '';
        formResponse.className = '';
    }, 3000);
});

/**
 * Checks if a filename has an allowed extension.
 * @param {string} filename
 * @returns {boolean} True if allowed, false otherwise
 */
function isAllowed(filename) {
    return allowedExtensions.some(ext => filename.toLowerCase().endsWith(ext));
}

/**
 * Fetches the current system state from the server and updates the UI.
 */
async function fetchSystemState() {
    try {
        const response = await fetch('/system-state/');
        const state = await response.json();
        updateSystemState(state);
    } catch (error) {
        console.error('Error fetching system state:', error);
    }
}

/**
 * Updates the queue and printer status UI based on server state.
 * @param {Object} state
 */
function updateSystemState(state) {
    console.log('Updating system state:', state);
    queueCount.textContent = state.queue_length;
    updatePrinterStatus(state);
    updateQueueList(state.queue_tasks);
}

/**
 * Updates the printer status display
 * @param {Object} state
 */
function updatePrinterStatus(state) {
    if (!state.printer_available) {
        updateStatus('offline', 'Printer disconnected');
        currentTask.textContent = 'Waiting for printer...';
        return;
    }

    if (state.printer_status === 'printing' && state.current_task) {
        updateStatus('printing', 'Printing');
        currentTask.textContent = `${state.current_task.name} (${state.current_task.pages} pages) - ${state.current_task.user}`;
    } else {
        updateStatus('online', 'Ready');
        currentTask.textContent = 'Nothing';
    }
}

/**
 * Updates the queue list display
 * @param {Array} tasks
 */
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
                <span class="queue-item-priority">Priority: ${task.priority}</span>
            </div>
            <div class="queue-item-details">
                User: ${task.user} | pages: ${task.pages}
            </div>
        </div>`
    ).join('');
}

/**
 * Updates the connection status indicator.
 * @param {string} status - e.g., 'online', 'offline', 'printing'
 * @param {string} text - Text to display
 */
function updateStatus(status, text) {
    statusIndicator.className = 'status-indicator';
    statusIndicator.classList.add(`status-${status}`);
    statusText.textContent = text;
}

/**
 * Displays a message in the form response area.
 * @param {string} message - Message text
 * @param {string} className - CSS class to apply (e.g., 'error', 'success')
 */
function showFormResponse(message, className) {
    formResponse.textContent = message;
    formResponse.className = className;
}