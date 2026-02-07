// Chat widget for Safety.uz
(function() {
    'use strict';
    
    let chatWidget = null;
    let isOpen = false;
    
    function createChatWidget() {
        // Create chat widget HTML
        chatWidget = document.createElement('div');
        chatWidget.id = 'chat-widget';
        chatWidget.innerHTML = `
            <div class="chat-widget-container">
                <div class="chat-widget-header">
                    <h6>Yordam kerakmi?</h6>
                    <button class="chat-widget-close" onclick="toggleChat()">&times;</button>
                </div>
                <div class="chat-widget-body">
                    <div class="chat-messages">
                        <div class="chat-message bot">
                            <p>Assalomu alaykum! Safety.uz chat botiga xush kelibsiz. Qanday yordam bera olaman?</p>
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" placeholder="Xabaringizni yozing..." id="chatInput">
                        <button onclick="sendMessage()">Yuborish</button>
                    </div>
                </div>
            </div>
            <div class="chat-widget-bubble" onclick="toggleChat()">
                <i class="bi bi-chat-dots"></i>
            </div>
        `;
        
        // Add styles
        const styles = `
            #chat-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
                font-family: Arial, sans-serif;
            }
            
            .chat-widget-container {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 350px;
                height: 450px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 5px 25px rgba(0,0,0,0.2);
                display: none;
                flex-direction: column;
                overflow: hidden;
            }
            
            .chat-widget-container.open {
                display: flex;
            }
            
            .chat-widget-header {
                background: #667eea;
                color: white;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .chat-widget-close {
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
            }
            
            .chat-widget-body {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            .chat-messages {
                flex: 1;
                padding: 15px;
                overflow-y: auto;
                background: #f9f9f9;
            }
            
            .chat-message {
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 10px;
                max-width: 80%;
            }
            
            .chat-message.bot {
                background: #e3f2fd;
                margin-right: auto;
            }
            
            .chat-message.user {
                background: #667eea;
                color: white;
                margin-left: auto;
            }
            
            .chat-input {
                padding: 15px;
                border-top: 1px solid #ddd;
                display: flex;
                gap: 10px;
            }
            
            .chat-input input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            
            .chat-input button {
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            
            .chat-widget-bubble {
                width: 60px;
                height: 60px;
                background: #667eea;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 3px 10px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
            }
            
            .chat-widget-bubble:hover {
                transform: scale(1.1);
            }
        `;
        
        // Add styles to head
        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
        
        document.body.appendChild(chatWidget);
    }
    
    window.toggleChat = function() {
        if (!chatWidget) {
            createChatWidget();
        }
        
        const container = chatWidget.querySelector('.chat-widget-container');
        isOpen = !isOpen;
        
        if (isOpen) {
            container.classList.add('open');
        } else {
            container.classList.remove('open');
        }
    };
    
    window.sendMessage = function() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        const messagesContainer = chatWidget.querySelector('.chat-messages');
        
        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'chat-message user';
        userMessage.innerHTML = `<p>${message}</p>`;
        messagesContainer.appendChild(userMessage);
        
        // Clear input
        input.value = '';
        
        // Add bot response
        setTimeout(function() {
            const botMessage = document.createElement('div');
            botMessage.className = 'chat-message bot';
            botMessage.innerHTML = `<p>Rahmat! Sizning xabaringiz qabul qilindi. Tez orada operatorimiz javob beradi.</p>`;
            messagesContainer.appendChild(botMessage);
            
            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 1000);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
    
    // Handle Enter key in chat input
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.target.id === 'chatInput') {
            sendMessage();
        }
    });
    
    // Initialize chat widget after page load
    setTimeout(function() {
        if (!chatWidget) {
            createChatWidget();
        }
    }, 1000);
})();
