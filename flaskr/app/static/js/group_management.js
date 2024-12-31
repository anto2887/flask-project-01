class GroupManager {
    constructor() {
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (!this.csrfToken) {
            console.error('CSRF token not found. Group management functionality may be limited.');
        }
        this.initializeEventListeners();
        this.qrModal = document.getElementById('qrModal');
    }

    initializeEventListeners() {
        document.getElementById('showQRCode')?.addEventListener('click', () => this.showQRCode());
        document.getElementById('regenerateCode')?.addEventListener('click', () => this.regenerateInviteCode());
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === this.qrModal) {
                this.qrModal.classList.add('hidden');
            }
        });
    }

    async regenerateInviteCode() {
        if (!this.csrfToken) {
            this.showError('Security token missing. Please refresh the page.');
            return;
        }

        if (!confirm('Are you sure you want to regenerate the invite code? Old code will no longer work.')) {
            return;
        }

        try {
            const response = await fetch('/group/regenerate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                this.showError(data.message || 'Failed to regenerate code');
            }
        } catch (error) {
            console.error('Error regenerating invite code:', error);
            this.showError('Error regenerating invite code');
        }
    }

    async promoteMember(userId) {
        if (!this.csrfToken) {
            this.showError('Security token missing. Please refresh the page.');
            return;
        }

        try {
            const response = await fetch('/group/promote-member', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ user_id: userId }),
                credentials: 'same-origin'
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                this.showError(data.message || 'Failed to promote member');
            }
        } catch (error) {
            console.error('Error promoting member:', error);
            this.showError('Error promoting member');
        }
    }

    async removeMember(userId) {
        if (!this.csrfToken) {
            this.showError('Security token missing. Please refresh the page.');
            return;
        }

        if (!confirm('Are you sure you want to remove this member?')) {
            return;
        }

        try {
            const response = await fetch('/group/remove-member', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ user_id: userId }),
                credentials: 'same-origin'
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                this.showError(data.message || 'Failed to remove member');
            }
        } catch (error) {
            console.error('Error removing member:', error);
            this.showError('Error removing member');
        }
    }

    showQRCode() {
        const inviteCode = document.querySelector('.invite-code')?.textContent;
        if (!inviteCode) {
            this.showError('Invite code not found');
            return;
        }
        
        // Clear previous QR code
        const qrContainer = document.getElementById('qrCode');
        if (!qrContainer) {
            this.showError('QR code container not found');
            return;
        }
        qrContainer.innerHTML = '';
        
        // Generate new QR code
        try {
            new QRCode(qrContainer, {
                text: inviteCode,
                width: 256,
                height: 256
            });
            
            this.qrModal.classList.remove('hidden');
        } catch (error) {
            console.error('Error generating QR code:', error);
            this.showError('Failed to generate QR code');
        }
    }

    showError(message) {
        const existingErrors = document.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message fixed bottom-4 right-4 bg-red-100 text-red-700 p-4 rounded shadow-lg z-50';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    // Debug check for CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (!csrfToken) {
        console.error('CSRF token meta tag not found');
    } else {
        console.log('CSRF token found, initializing GroupManager');
    }
    
    new GroupManager();
});