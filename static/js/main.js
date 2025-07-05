// Toggle AI Assistant
function toggleAssistant() {
    const container = document.getElementById('assistantContainer');
    container.style.display = container.style.display === 'none' ? 'flex' : 'none';
}

// Handle AI Assistant questions
function askQuestion() {
    const question = document.getElementById('userQuestion').value;
    if (!question.trim()) return;

    const messagesDiv = document.getElementById('assistantMessages');
    messagesDiv.innerHTML += `<div class="user-message">${question}</div>`;
    
    // Get context from current page
    const context = document.body.innerText.substring(0, 1000);
    
    fetch('/ask_gemini', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `question=${encodeURIComponent(question)}&context=${encodeURIComponent(context)}`
    })
    .then(response => response.text())
    .then(answer => {
        messagesDiv.innerHTML += `<div class="assistant-message">${answer}</div>`;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
    
    document.getElementById('userQuestion').value = '';
}

// Handle Enter key in assistant input
document.getElementById('userQuestion').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        askQuestion();
    }
});

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});