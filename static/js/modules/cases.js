// static/js/modules/cases.js
class CasesManager {
    constructor() {
        this.init();
    }

    init() {
        // Bind close case buttons
        document.addEventListener('click', (e) => {
            if (e.target.hasAttribute('data-close-case')) {
                e.preventDefault();
                const caseId = e.target.getAttribute('data-close-case');
                this.closeCase(caseId);
            }
        });
    }

    closeCase(caseId) {
        if (confirm('Are you sure you want to close this case?')) {
            fetch('/cases/' + caseId + '/close', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Failed to close case');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error closing case');
            });
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new CasesManager();
});