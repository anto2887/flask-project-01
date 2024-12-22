class GroupJoiner {
    constructor() {
        this.html5QrcodeScanner = null;
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
        try {
            const response = await fetch('/group/join', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ invite_code: code })
            });

            const data = await response.json();

            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('An error occurred while joining the group');
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'mt-4 p-4 bg-red-100 text-red-700 rounded';
        errorDiv.textContent = message;
        
        const container = document.querySelector('.container');
        container.appendChild(errorDiv);

        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    new GroupJoiner();
});