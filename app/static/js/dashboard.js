/**
 * Dashboard WebSocket and Real-time Updates
 */
(function() {
    'use strict';

    // Store initial values from template
    let initialStats = {
        totalUsers: 0,
        totalBooks: 0,
        totalPayments: 0,
        totalRevenue: 0
    };

    // Initialize stats from data attributes or global variables
    function initializeStats() {
        const statsContainer = document.querySelector('[data-stats]');
        if (statsContainer) {
            try {
                initialStats = JSON.parse(statsContainer.getAttribute('data-stats'));
            } catch (e) {
                console.warn('Could not parse stats from data attribute');
            }
        }
    }

    // Wait for Socket.IO to be available
    function initializeDashboard() {
        // Check if Socket.IO is loaded
        if (typeof io === 'undefined') {
            console.warn('Socket.IO not loaded yet, retrying...');
            setTimeout(initializeDashboard, 100);
            return;
        }

        // Initialize Socket.IO connection
        const socket = io({
            transports: ['websocket', 'polling'],
            withCredentials: true
        });
        
        initializeSocketHandlers(socket);
    }

    function initializeSocketHandlers(socket) {
        // Connection event handlers
        socket.on('connect', function() {
            console.log('Connected to websocket server');
        });

        socket.on('connected', function(data) {
        });

        socket.on('disconnect', function() {
            console.log('Disconnected from websocket server');
        });

        // Handle new activity notifications
        socket.on('new_activity', function(data) {
            
            const activity = data.data;
            const activityType = data.activity_type;
            
            // Show notification toast
            showNotification(activity, activityType);
            
            // Update dashboard based on activity type
            if (activityType === 'payment') {
                updatePaymentActivity(activity);
                updateDashboardStats();
            } else if (activityType === 'book') {
                updateBookActivity(activity);
                updateDashboardStats();
            } else if (activityType === 'user') {
                updateUserActivity(activity);
                updateDashboardStats();
            }
        });

        // Handle dashboard stats update
        socket.on('dashboard_update', function(data) {
            updateStatsDisplay(data.stats);
        });
    }

    // Show notification toast
    function showNotification(activity, activityType) {
        const toast = document.getElementById('activityToast');
        const toastBody = document.getElementById('toastBody');
        
        if (!toast || !toastBody) return;
        
        let icon = 'fas fa-info-circle';
        let message = '';
        
        if (activityType === 'payment') {
            icon = 'fas fa-shopping-cart text-success';
            message = `<strong>${activity.username}</strong> purchased <strong>${activity.book_title}</strong> for $${activity.price.toFixed(2)}`;
        } else if (activityType === 'book') {
            icon = 'fas fa-book text-info';
            message = `New book added: <strong>${activity.title}</strong>`;
        } else if (activityType === 'user') {
            icon = 'fas fa-user-plus text-primary';
            message = `New user registered: <strong>${activity.username}</strong>`;
        }
        
        toastBody.innerHTML = `<i class="${icon} me-2"></i>${message}`;
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        bsToast.show();
    }

    // Update payment activity in the table
    function updatePaymentActivity(payment) {
        const recentPaymentsTable = document.querySelector('.table tbody');
        if (!recentPaymentsTable) return;
        
        // Create new row
        const newRow = document.createElement('tr');
        newRow.className = 'table-success';
        newRow.style.animation = 'fadeIn 0.5s';
        
        const dateStr = payment.created_at ? 
            new Date(payment.created_at).toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }).replace(',', '') : 'N/A';
        
        newRow.innerHTML = `
            <td class="ps-3">${payment.username}</td>
            <td><strong>${payment.book_title}</strong></td>
            <td><span class="text-success fw-bold">$${payment.price.toFixed(2)}</span></td>
            <td class="pe-3">${dateStr}</td>
        `;
        
        // Insert at the top
        recentPaymentsTable.insertBefore(newRow, recentPaymentsTable.firstChild);
        
        // Remove highlight after 3 seconds
        setTimeout(() => {
            newRow.classList.remove('table-success');
        }, 3000);
        
        // Keep only last 10 rows
        while (recentPaymentsTable.children.length > 10) {
            recentPaymentsTable.removeChild(recentPaymentsTable.lastChild);
        }
    }

    // Update dashboard statistics display
    function updateStatsDisplay(stats) {
        // Update summary cards
        const summaryCards = document.querySelectorAll('.summary-card');
        if (summaryCards.length < 4) return;
        
        const totalUsersEl = summaryCards[0].querySelector('h3');
        const totalBooksEl = summaryCards[1].querySelector('h3');
        const totalPaymentsEl = summaryCards[2].querySelector('h3');
        const totalRevenueEl = summaryCards[3].querySelector('h3');
        
        if (totalUsersEl && stats.total_users !== undefined) {
            animateValue(totalUsersEl, parseInt(totalUsersEl.textContent) || 0, stats.total_users);
        }
        if (totalBooksEl && stats.total_books !== undefined) {
            animateValue(totalBooksEl, parseInt(totalBooksEl.textContent) || 0, stats.total_books);
        }
        if (totalPaymentsEl && stats.total_payments !== undefined) {
            animateValue(totalPaymentsEl, parseInt(totalPaymentsEl.textContent) || 0, stats.total_payments);
        }
        if (totalRevenueEl && stats.total_revenue !== undefined) {
            const currentRevenue = parseFloat(totalRevenueEl.textContent.replace('$', '')) || 0;
            animateValue(totalRevenueEl, currentRevenue, stats.total_revenue, true);
        }
    }

    // Animate number changes
    function animateValue(element, start, end, isCurrency = false) {
        const duration = 500;
        const startTime = performance.now();
        
        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = start + (end - start) * progress;
            element.textContent = isCurrency ? 
                '$' + current.toFixed(2) : 
                Math.floor(current);
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }
        
        requestAnimationFrame(update);
    }

    // Update dashboard stats (triggers refresh)
    function updateDashboardStats() {
        // The server will send dashboard_update event
        // This function can be used to manually trigger if needed
    }

    // Add fade-in animation CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .table-success {
            background-color: #d1e7dd !important;
        }
    `;
    document.head.appendChild(style);

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeStats();
            initializeDashboard();
        });
    } else {
        initializeStats();
        initializeDashboard();
    }
})();
