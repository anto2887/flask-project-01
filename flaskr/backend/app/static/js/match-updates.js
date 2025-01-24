class MatchUpdater {
    constructor() {
        this.updateInterval = 60000; // 1 minute
        this.liveMatchesContainer = document.getElementById('live-matches-container');
        this.predictionInputsContainer = document.getElementById('prediction-inputs');
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
        this.initializeEventListeners();
        this.startUpdates();
    }

    initializeEventListeners() {
        // Prediction submission handlers
        document.querySelectorAll('.submit-prediction').forEach(button => {
            button.addEventListener('click', (e) => this.handlePredictionSubmit(e));
        });

        // Reset prediction handlers
        document.querySelectorAll('.reset-prediction').forEach(button => {
            button.addEventListener('click', (e) => this.handlePredictionReset(e));
        });

        // Input validation
        document.querySelectorAll('.score-input').forEach(input => {
            input.addEventListener('input', (e) => this.validateScoreInput(e));
        });
    }

    startUpdates() {
        this.updateLiveMatches();
        setInterval(() => this.updateLiveMatches(), this.updateInterval);
    }

    async updateLiveMatches() {
        try {
            const response = await fetch('/api/live-matches', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });
            const data = await response.json();

            if (data.status === 'success') {
                this.renderLiveMatches(data.matches);
            }
        } catch (error) {
            console.error('Error updating live matches:', error);
        }
    }

    renderLiveMatches(matches) {
        if (!this.liveMatchesContainer) return;

        const matchesHtml = matches.length ? matches.map(match => this.createMatchCard(match)).join('') 
                                         : '<p class="no-matches">No live matches at the moment</p>';
        
        this.liveMatchesContainer.innerHTML = matchesHtml;
    }

    createMatchCard(match) {
        return `
            <div class="match-card" data-fixture-id="${match.fixture_id}">
                <div class="match-status">${match.status}</div>
                <div class="match-teams">
                    <div class="team home-team">
                        <img src="${match.home_team_logo}" alt="${match.home_team} logo" class="team-logo">
                        <span class="team-name">${match.home_team}</span>
                        <span class="score">${match.home_score}</span>
                    </div>
                    <div class="vs">VS</div>
                    <div class="team away-team">
                        <span class="score">${match.away_score}</span>
                        <span class="team-name">${match.away_team}</span>
                        <img src="${match.away_team_logo}" alt="${match.away_team} logo" class="team-logo">
                    </div>
                </div>
            </div>
        `;
    }

    validateScoreInput(event) {
        const input = event.target;
        const value = input.value;

        // Only allow non-negative integers
        if (value < 0 || !Number.isInteger(Number(value))) {
            input.value = 0;
        }
    }

    async handlePredictionSubmit(event) {
        const button = event.target;
        const fixtureId = button.dataset.fixtureId;
        const matchCard = button.closest('.match-card');
        
        if (!matchCard) return;

        const homeScore = matchCard.querySelector('input[name="home_score"]').value;
        const awayScore = matchCard.querySelector('input[name="away_score"]').value;

        if (!homeScore || !awayScore) {
            alert('Please enter both scores');
            return;
        }

        try {
            button.disabled = true;
            const response = await fetch('/api/submit-prediction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    fixture_id: fixtureId,
                    score1: parseInt(homeScore),
                    score2: parseInt(awayScore)
                }),
                credentials: 'same-origin'
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                // Disable inputs and change button states
                matchCard.querySelectorAll('.score-input').forEach(input => {
                    input.disabled = true;
                });
                button.textContent = 'Submitted';
                matchCard.querySelector('.reset-prediction').disabled = false;
            } else {
                alert(data.message || 'Failed to submit prediction');
                button.disabled = false;
            }
        } catch (error) {
            console.error('Error submitting prediction:', error);
            alert('Failed to submit prediction');
            button.disabled = false;
        }
    }

    async handlePredictionReset(event) {
        const button = event.target;
        const fixtureId = button.dataset.fixtureId;
        const matchCard = button.closest('.match-card');
        
        if (!matchCard) return;

        try {
            button.disabled = true;
            const response = await fetch(`/api/reset-prediction/${fixtureId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                },
                credentials: 'same-origin'
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                // Re-enable inputs and reset values
                matchCard.querySelectorAll('.score-input').forEach(input => {
                    input.disabled = false;
                    input.value = '';
                });
                matchCard.querySelector('.submit-prediction').disabled = false;
                matchCard.querySelector('.submit-prediction').textContent = 'Submit';
            } else {
                alert(data.message || 'Failed to reset prediction');
            }
            button.disabled = false;
        } catch (error) {
            console.error('Error resetting prediction:', error);
            alert('Failed to reset prediction');
            button.disabled = false;
        }
    }

    // Helper method to format dates
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize when document loads
document.addEventListener('DOMContentLoaded', () => {
    // Check for CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (!csrfToken) {
        console.error('CSRF token meta tag not found');
        return;
    }
    console.log('CSRF token found, initializing MatchUpdater');
    
    new MatchUpdater();
});