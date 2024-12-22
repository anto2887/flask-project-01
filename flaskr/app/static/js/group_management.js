class GroupManager {
    constructor() {
        this.initializeEventListeners();
        this.qrModal = document.getElementById('qrModal');
    }

    initializeEventListeners() {
        document.getElementById('showQRCode').addEventListener('click', () => this.showQRCode());
        document.getElementById('regenerateCode').addEventListener('click', () => this.regenerateInviteCode());
        
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === this.qrModal) {
                this.qrModal.classList.add('hidden');
            }
        });
    }

    async regenerateInviteCode() {
        if (!confirm('Are you sure you want to regenerate the invite code? Old code will no longer work.')) {
            return;
        }

        try {
            const response = await fetch('/group/regenerate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Error regenerating invite code');
        }
    }

    async promoteMember(userId) {
        try {
            const response = await fetch('/group/promote-member', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: userId })
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Error promoting member');
        }
    }

    async removeMember(userId) {
        if (!confirm('Are you sure you want to remove this member?')) {
            return;
        }

        try {
            const response = await fetch('/group/remove-member', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_id: userId })
            });

            const data = await response.json();
            if (data.status === 'success') {
                window.location.reload();
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Error removing member');
        }
    }

    showQRCode() {
        const inviteCode = document.querySelector('.invite-code').textContent;
        
        // Clear previous QR code
        const qrContainer = document.getElementById('qrCode');
        qrContainer.innerHTML = '';
        
        // Generate new QR code
        new QRCode(qrContainer, {
            text: inviteCode,
            width: 256,
            height: 256
        });
        
        this.qrModal.classList.remove('hidden');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed bottom-4 right-4 bg-red-100 text-red-700 p-4 rounded shadow-lg';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    new GroupManager();
});