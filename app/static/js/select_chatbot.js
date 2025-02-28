// static/js/select_chatbot.js
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to chatbot selection buttons
    document.querySelectorAll('.chatbot-option').forEach(button => {
        button.addEventListener('click', function(e) {
            const chatbotType = this.getAttribute('data-type');
            
            // If "New User" button was clicked
            if (this.classList.contains('new-user-btn')) {
                createNewUser(chatbotType);
                e.preventDefault(); // Prevent default navigation
            }
        });
    });
    
    // Function to create a new user
    function createNewUser(chatbotType) {
        // Show loading indicator
        const loadingElement = document.getElementById('loading-indicator');
        if (loadingElement) loadingElement.style.display = 'block';
        
        // Make API request to create new user
        fetch('/new_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chatbot_type: chatbotType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error creating new user:', data.error);
                alert('Error creating new user: ' + data.error);
            } else {
                // Redirect to chat page with new thread_id
                window.location.href = `/chat/${chatbotType}`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        })
        .finally(() => {
            // Hide loading indicator
            if (loadingElement) loadingElement.style.display = 'none';
        });
    }
});