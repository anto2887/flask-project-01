class GroupJoiner {
    constructor() {
        this.html5QrcodeScanner = null;
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        if (!this.csrfToken) {
            console.error('CSRF token not found. Group joining functionality may be limited.');
        }
        this.initializeForm();
        this.initializeQRScanner();
    }

    initializeForm() {
        const form = document.getElementById('joinForm');
        const input = document.getElementById('invite_code');

        // Format input as user types
        input.addEventListener('input', (e) => {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (value.length > 4) {
                value = value.slice(0, 4) + '-' + value.slice(4, 8);
            }
            e.target.value = value;
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitCode(input.value);
        });
    }

    initializeQRScanner() {
        const startButton = document.getElementById('startScanner');
        const stopButton = document.getElementById('stopScanner');
        const scannerDiv = document.getElementById('qrScanner');

        startButton.addEventListener('click', () => {
            startButton.style.display = 'none';
            scannerDiv.classList.remove('hidden');
            this.startScanner();
        });

        stopButton.addEventListener('click', () => {
            this.stopScanner();
            scannerDiv.classList.add('hidden');
            startButton.style.display = 'block';
        });
    }

    startScanner() {
        this.html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", 
            { 
                fps: 10,
                qrbox: { width: 250, height: 250 }
            }
        );

        this.html5QrcodeScanner.render((decodedText) => {
            this.submitCode(decodedText);
            this.stopScanner();
        });
    }

    stopScanner() {
        if (this.html5QrcodeScanner) {
            this.html5QrcodeScanner.clear();
            this.html5QrcodeScanner = null;
        }
    }

    async submitCode(code) {
        if (!this.csrfToken) {
            this.showError('Security token missing. Please refresh the page.');
            return;
        }

        try {
            const response = await fetch('/group/join', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ invite_code: code }),
                credentials: 'same-origin'
            });

            const data = await response.json();
            console.log('Join response:', data);

            if (data.status === 'success') {
                window.location.href = data.redirect_url || '/';
            } else {
                this.showError(data.message || 'Failed to join group');
            }
        } catch (error) {
            console.error('Error joining group:', error);
            this.showError('An error occurred while joining the group');
        }
    }

    showError(message) {
        // Remove any existing error messages
        const existingErrors = document.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());

        // Create and show new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message mt-4 p-4 bg-red-100 text-red-700 rounded';
        errorDiv.textContent = message;
        
        const container = document.querySelector('.container');
        container.appendChild(errorDiv);

        // Remove error message after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    showSuccess(message) {
        // Remove any existing messages
        const existingMessages = document.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());

        // Create and show success message
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message mt-4 p-4 bg-green-100 text-green-700 rounded';
        successDiv.textContent = message;
        
        const container = document.querySelector('.container');
        container.appendChild(successDiv);

        // Remove success message after 5 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    // Debug check for CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (!csrfToken) {
        console.error('CSRF token meta tag not found');
    } else {
        console.log('CSRF token found, initializing GroupJoiner');
    }
    
    new GroupJoiner();
});