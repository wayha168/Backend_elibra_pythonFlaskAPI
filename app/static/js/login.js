// Login page JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize login form
    initializeLoginForm();

    // Add form validation
    addFormValidation();

    // Add visual effects
    addVisualEffects();
});

function initializeLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // Add loading state to button
            const submitButton = loginForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';

                // Re-enable after 3 seconds if no redirect happens
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Login';
                }, 3000);
            }
        });
    }
}

function addFormValidation() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    // Real-time validation
    if (usernameInput) {
        usernameInput.addEventListener('blur', function() {
            validateField(this, 'Username is required');
        });
    }

    if (passwordInput) {
        passwordInput.addEventListener('blur', function() {
            validateField(this, 'Password is required');
        });
    }
}

function validateField(field, errorMessage) {
    const value = field.value.trim();
    const formGroup = field.closest('.mb-4');

    // Remove existing error message
    const existingError = formGroup.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }

    // Remove existing valid styling
    field.classList.remove('is-valid', 'is-invalid');

    if (!value) {
        // Show error
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = errorMessage;
        formGroup.appendChild(errorDiv);
        return false;
    } else {
        // Show valid
        field.classList.add('is-valid');
        return true;
    }
}

function addVisualEffects() {
    // Add ripple effect to login button
    const loginButton = document.querySelector('.login-card .btn');
    if (loginButton) {
        loginButton.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.left = (e.offsetX - 10) + 'px';
            ripple.style.top = (e.offsetY - 10) + 'px';
            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }

    // Add focus effects to inputs
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });

    // Add password visibility toggle
    addPasswordToggle();
}

function addPasswordToggle() {
    const passwordInput = document.getElementById('password');
    if (!passwordInput) return;

    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'btn btn-sm position-absolute';
    toggleButton.innerHTML = '👁️';
    toggleButton.style.cssText = 'right: 10px; top: 50%; transform: translateY(-50%); border: none; background: transparent; color: #666;';

    // Position the toggle button
    const passwordContainer = passwordInput.parentElement;
    passwordContainer.style.position = 'relative';
    passwordContainer.appendChild(toggleButton);

    // Toggle password visibility
    toggleButton.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        this.innerHTML = type === 'password' ? '👁️' : '🙈';
    });
}

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    .ripple-effect {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    }

    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    .mb-4.focused label {
        color: #055194 !important;
        font-weight: 600;
    }

    .form-control:focus {
        border-color: #055194 !important;
        box-shadow: 0 0 0 0.2rem rgba(5, 81, 148, 0.25) !important;
    }

    .invalid-feedback {
        display: block;
        color: #dc3545;
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
`;
document.head.appendChild(style);

// Handle form submission errors (if any)
window.addEventListener('load', function() {
    // Check for flash messages or errors
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        });
    }
});