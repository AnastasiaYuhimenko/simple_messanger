let selectedUserId = null;  // Хранит ID пользователя, с которым мы общаемся в чате
let socket = null; 
let messagePollingInterval = null;  // Таймер для периодической загрузки сообщений
const modal = document.getElementById("myModal"); // окошко для минут

document.getElementById("lateButton").onclick = function() {
  modal.style.display = "block";
}

function startMessagePolling(userId) {
    clearInterval(messagePollingInterval); 
    messagePollingInterval = setInterval(async () => {
        try {
            const response = await apiFetch(`/messages/${userId}`);
            const messages = await response.json();
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = messages.map(m => createMessageElement(m.text, m.sender_id)).join('');
        } catch (error) {
            console.error('Ошибка при опросе сообщений:', error);
        }
    }, 1000);
}

async function minutesentr() {
    const input = document.getElementById("minutes").value;
    if (isNaN(input) || input < 0) {
    alert("Введите корректное количество минут");
    return;
    }
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();  

    if (message && selectedUserId) { 
        const payload = {
            message: {
                recipient_id: selectedUserId,
                content: message
            },
            time: input
}; 

        try {
            await apiFetch('/messages_late', {
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
  modal.style.display = "none"; // Закрыть окно
}

// обёртка над fetch для рефреша токена
async function apiFetch(url, options = {}) {
    try {
        options.credentials = 'include';  

        let response = await fetch(url, options);
        if (response.status === 401) {
            console.warn("Токен истёк, обновляем");

            const refreshResponse = await fetch('/users/refresh', {
                method: 'POST',
                credentials: 'include'
            });

            if (refreshResponse.ok) {
                console.log("Токен обновлён");
                response = await fetch(url, options);
            } else {
                console.error("Не удалось обновить токен");
                window.location.href = "/users/login";  
            }
        }

        return response;
    } catch (error) {
        console.error("Ошибка при запросе:", error);
        throw error;
    }
}


async function logout() {
    try {
        const response = await apiFetch('/users/logout/', { 
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
    document.getElementById('lateButton').disabled = false;


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
        const response = await apiFetch(`/messages/${userId}`); 
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
            await apiFetch('/messages', {
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

document.querySelectorAll('.user-item').forEach(item => {
    item.onclick = event => selectUser(item.getAttribute('data-user-id'), item.textContent, event);  
});

document.getElementById('sendButton').onclick = sendMessage;  

document.getElementById('messageInput').onkeypress = async (e) => {
    if (e.key === 'Enter') {  
        await sendMessage();  
    }
};
