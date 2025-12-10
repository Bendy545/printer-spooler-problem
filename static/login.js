document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const loginButton = document.getElementById('login-button');
    const errorMessage = document.getElementById('error-message');

    fetch('/api/check-auth')
        .then(res => res.json())
        .then(data => {
            if (data.authenticated) {
                window.location.href = '/';
            }
        })
        .catch(err => console.error('Auth check failed:', err));

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(loginForm);
            loginButton.disabled = true;
            loginButton.textContent = 'Logging in...';
            errorMessage.classList.remove('show');

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    window.location.href = '/';
                } else {
                    const error = await response.json();
                    showError(error.detail || 'Login failed');
                    loginButton.disabled = false;
                    loginButton.textContent = 'Login';
                }
            } catch (error) {
                showError('Connection error. Please try again.');
                loginButton.disabled = false;
                loginButton.textContent = 'Login';
            }
        });
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.add('show');
    }
});