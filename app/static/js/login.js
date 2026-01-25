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

    // Hide/show username icon based on validation
    const usernameIcon = formGroup.querySelector('.username-icon');
    if (usernameIcon && field.id === 'username') {
        if (!value) {
            usernameIcon.style.opacity = '0';
            usernameIcon.style.visibility = 'hidden';
        } else {
            usernameIcon.style.opacity = '1';
            usernameIcon.style.visibility = 'visible';
        }
    }

    if (!value) {
        // Show error
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = errorMessage;
        formGroup.appendChild(errorDiv);
        
        // Hide username icon when error is shown
        if (usernameIcon && field.id === 'username') {
            usernameIcon.style.opacity = '0';
            usernameIcon.style.visibility = 'hidden';
        }
        
        return false;
    } else {
        // Show valid
        field.classList.add('is-valid');
        
        // Show username icon when valid
        if (usernameIcon && field.id === 'username') {
            usernameIcon.style.opacity = '1';
            usernameIcon.style.visibility = 'visible';
        }
        
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
    addPasswordToggle();
    addUsernameIcon();
}

function addUsernameIcon() {
    const usernameInput = document.getElementById('username');
    if (!usernameInput) return;

    // Check if icon already exists
    if (usernameInput.parentElement.querySelector('.username-icon')) {
        return;
    }

    // Ensure parent container has relative positioning
    const usernameContainer = usernameInput.parentElement;
    usernameContainer.style.position = 'relative';

    // Add padding-right to username input to make room for icon
    usernameInput.style.paddingRight = '45px';

    // Create icon element
    const iconElement = document.createElement('i');
    iconElement.className = 'fas fa-user-shield username-icon';
    iconElement.setAttribute('aria-hidden', 'true');
    
    // Style the icon
    iconElement.style.cssText = `
        position: absolute;
        right: 12px;
        top: 70%;
        transform: translateY(-50%);
        color: #055194;
        font-size: 1.1rem;
        z-index: 10;
        pointer-events: none;
        transition: opacity 0.3s ease;
    `;

    // Append icon to container
    usernameContainer.appendChild(iconElement);

    // Function to toggle icon visibility based on error state
    function toggleIconVisibility() {
        const hasError = usernameInput.classList.contains('is-invalid');
        const invalidFeedback = usernameContainer.querySelector('.invalid-feedback');
        const hasInvalidFeedback = invalidFeedback && invalidFeedback.style.display !== 'none';
        
        if (hasError || hasInvalidFeedback) {
            iconElement.style.opacity = '0';
            iconElement.style.visibility = 'hidden';
        } else {
            iconElement.style.opacity = '1';
            iconElement.style.visibility = 'visible';
        }
    }

    // Watch for validation changes
    usernameInput.addEventListener('blur', toggleIconVisibility);
    usernameInput.addEventListener('input', toggleIconVisibility);
    
    // Initial check
    toggleIconVisibility();

    // Watch for DOM changes (for dynamically added error messages)
    const observer = new MutationObserver(toggleIconVisibility);
    observer.observe(usernameContainer, {
        childList: true,
        attributes: true,
        attributeFilter: ['class']
    });
}

function addPasswordToggle() {
    const passwordInput = document.getElementById('password');
    if (!passwordInput) return;

    // Check if toggle button already exists
    if (passwordInput.parentElement.querySelector('.password-toggle-btn')) {
        return;
    }

    // Ensure parent container has relative positioning
    const passwordContainer = passwordInput.parentElement;
    passwordContainer.style.position = 'relative';

    // Add padding-right to password input to make room for button
    passwordInput.style.paddingRight = '45px';

    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'password-toggle-btn';
    toggleButton.setAttribute('aria-label', 'Toggle password visibility');
    toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
    
    // Style the toggle button
    toggleButton.style.cssText = `
        position: absolute;
        right: 12px;
        top: 70%;
        transform: translateY(-50%);
        border: none;
        background: transparent;
        color: #666;
        cursor: pointer;
        padding: 5px 8px;
        z-index: 10;
        outline: none;
        transition: color 0.3s ease;
    `;

    // Add hover effect
    toggleButton.addEventListener('mouseenter', function() {
        this.style.color = '#055194';
    });
    toggleButton.addEventListener('mouseleave', function() {
        this.style.color = '#666';
    });

    // Append button to container
    passwordContainer.appendChild(toggleButton);

    function togglePasswordVisibility() {
        const hasError = passwordInput.classList.contains('is-invalid');
        const invalidFeedback = passwordContainer.querySelector('.invalid-feedback');
        const hasInvalidFeedback = invalidFeedback && invalidFeedback.style.display !== 'none';
        
        if (hasError || hasInvalidFeedback) {
            toggleButton.style.opacity = '0';
            toggleButton.style.display = 'none';
        } else {
            toggleButton.style.opacity = '1';
            toggleButton.style.display = 'block';
        }
    }

    // Watch for validation changes
    passwordInput.addEventListener('blur', togglePasswordVisibility);
    passwordInput.addEventListener('input', togglePasswordVisibility);
    
    // Initial check
    togglePasswordVisibility();

    // Watch for DOM changes (for dynamically added error messages)
    // Toggle password visibility
    toggleButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        
        // Update icon
        const icon = this.querySelector('i');
        if (icon) {
            icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
        } else {
            this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
        }
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

    .password-toggle-btn {
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        border: none;
        background: transparent;
        color: #666;
        cursor: pointer;
        padding: 5px 8px;
        z-index: 10;
        outline: none;
        transition: color 0.3s ease;
    }

    .password-toggle-btn:hover {
        color: #055194;
    }

    .password-toggle-btn:focus {
        outline: 2px solid #055194;
        outline-offset: 2px;
        border-radius: 4px;
    }

    .mb-4 {
        position: relative;
    }

    .username-icon {
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: #055194;
        font-size: 1.1rem;
        z-index: 10;
        pointer-events: none;
        transition: opacity 0.3s ease, visibility 0.3s ease;
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