let selectedUserId = null;  // Хранит ID пользователя, с которым мы общаемся в чате
let socket = null; 
let messagePollingInterval = null;  // Таймер для периодической загрузки сообщений

async function logout() {
    try {
        const response = await fetch('/users/logout/', { 
            method: 'POST', 
            credentials: 'include'
        });

        if (response.ok) {
            window.location.href = '/users/'; 
        } else {
            console.error('Ошибка при выходе');
        }
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error);
    }
}

async function selectUser(userId, userName, event) {
    selectedUserId = userId;  
    document.getElementById('chatHeader').innerHTML = `<span>Чат с ${userName}</span><button class="logout-button" id="logoutButton">Выход</button>`;
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendButton').disabled = false;

    document.querySelectorAll('.user-item').forEach(item => item.classList.remove('active'));
    event.target.classList.add('active'); 

    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = ''; 
    messagesContainer.style.display = 'block'; 

    document.getElementById('logoutButton').onclick = logout;

    await loadMessages(userId);
    connectWebSocket();
    startMessagePolling(userId);
}

async function loadMessages(userId) {
    try {
        const response = await fetch(`/messages/${userId}`); 
        const messages = await response.json();  

        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = messages.map(message =>
            createMessageElement(message.text, message.sender_id)
        ).join(''); 
    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error); 
    }
}

function connectWebSocket() {
    if (socket) socket.close();  
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.hostname;
    socket = new WebSocket(`${protocol}://localhost:8000/ws/${selectedUserId}`);  

    socket.onopen = () => console.log('WebSocket соединение установлено');  

    socket.onmessage = (event) => {
        const incomingMessage = JSON.parse(event.data);  
        if (incomingMessage.recipient_id === selectedUserId || incomingMessage.sender_id === selectedUserId) {
            addMessage(incomingMessage.content, incomingMessage.sender_id);  
        }
    };

    socket.onclose = () => console.log('WebSocket соединение закрыто');  
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();  

    if (message && selectedUserId) { 
        const payload = {recipient_id: selectedUserId, content: message}; 

        try {
            await fetch('/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });

            socket.send(JSON.stringify(payload));  
            addMessage(message, ""); 
            messageInput.value = ''; 
        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);  
        }
    }
}

function addMessage(text, sender_id) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.insertAdjacentHTML('beforeend', createMessageElement(text, sender_id));  
    messagesContainer.scrollTop = messagesContainer.scrollHeight;  
}

function createMessageElement(text, sender_id) {
    const messageClass = sender_id === selectedUserId ? 'received' : 'sent';
    return `<div class="message ${messageClass}">${text}</div>`;
}



function startMessagePolling(userId) {
    clearInterval(messagePollingInterval); 
}

document.querySelectorAll('.user-item').forEach(item => {
    item.onclick = event => selectUser(item.getAttribute('data-user-id'), item.textContent, event);  
});

document.getElementById('sendButton').onclick = sendMessage;  

document.getElementById('messageInput').onkeypress = async (e) => {
    if (e.key === 'Enter') {  
        await sendMessage();  
    }
};
