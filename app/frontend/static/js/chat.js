// Переменные
let selectedUserId = null;  // Хранит ID пользователя, с которым мы общаемся в чате
let socket = null;          // Хранит объект WebSocket для соединения с сервером
let messagePollingInterval = null;  // Таймер для периодической загрузки сообщений

// Функция для выхода из аккаунта
async function logout() {
    try {
        const response = await fetch('/users/logout/', { 
            method: 'POST', 
            credentials: 'include' // Передаем куки, чтобы сервер знал, кто выходит
        });

        if (response.ok) {
            window.location.href = '/users/'; // Если все ок, перенаправляем на страницу авторизации
        } else {
            console.error('Ошибка при выходе'); // Ловим ошибки, если что-то пошло не так
        }
    } catch (error) {
        console.error('Ошибка при выполнении запроса:', error); // Обрабатываем ошибки сети
    }
}

// Выбор пользователя для общения
async function selectUser(userId, userName, event) {
    selectedUserId = userId;  // Запоминаем, с кем ведется беседа
    document.getElementById('chatHeader').innerHTML = `<span>Чат с ${userName}</span><button class="logout-button" id="logoutButton">Выход</button>`;
    document.getElementById('messageInput').disabled = false; // Активируем ввод сообщений
    document.getElementById('sendButton').disabled = false;   // Активируем кнопку отправки

    document.querySelectorAll('.user-item').forEach(item => item.classList.remove('active')); // Убираем выделение с других пользователей
    event.target.classList.add('active');  // Подсвечиваем текущего пользователя

    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';  // Очищаем окно сообщений
    messagesContainer.style.display = 'block';  // Показываем окно сообщений

    document.getElementById('logoutButton').onclick = logout;  // Привязываем функцию выхода

    await loadMessages(userId);  // Загружаем предыдущие сообщения с этим пользователем
    connectWebSocket();  // Открываем WebSocket для обмена сообщениями в реальном времени
    startMessagePolling(userId);  // Начинаем периодически проверять новые сообщения
}

// Загрузка предыдущих сообщений
async function loadMessages(userId) {
    try {
        const response = await fetch(`/messages/${userId}`);  // Делаем запрос на сервер, чтобы получить старые сообщения
        const messages = await response.json();  // Преобразуем ответ в JSON

        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = messages.map(message =>
            createMessageElement(message.text, message.recipient_id)  // Преобразуем каждое сообщение в HTML-элемент
        ).join('');  // Склеиваем элементы и вставляем их в контейнер сообщений
    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);  // Ловим ошибки при загрузке
    }
}

// Соединение с WebSocket
function connectWebSocket() {
    if (socket) socket.close();  // Если соединение уже было, закрываем его
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.hostname; // ← это реально работает с браузера
    socket = new WebSocket(`${protocol}://localhost:8000/ws/${selectedUserId}`);  // Открываем новое WebSocket-соединение

    socket.onopen = () => console.log('WebSocket соединение установлено');  // Логируем успешное подключение

    socket.onmessage = (event) => {
        const incomingMessage = JSON.parse(event.data);  // Получаем новое сообщение от сервера
        if (incomingMessage.recipient_id === selectedUserId) {  // Проверяем, кому адресовано сообщение
            addMessage(incomingMessage.content, incomingMessage.recipient_id);  // Добавляем сообщение в чат
        }
    };

    socket.onclose = () => console.log('WebSocket соединение закрыто');  // Логируем закрытие соединения
}

// Отправка сообщения
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();  // Берем текст сообщения

    if (message && selectedUserId) {  // Проверяем, что сообщение не пустое и выбран собеседник
        const payload = {recipient_id: selectedUserId, content: message};  // Формируем данные для отправки

        try {
            await fetch('/messages', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)  // Отправляем сообщение на сервер
            });

            socket.send(JSON.stringify(payload));  // Также отправляем сообщение через WebSocket
            addMessage(message, selectedUserId);  // Добавляем сообщение в чат
            messageInput.value = '';  // Очищаем поле ввода
        } catch (error) {
            console.error('Ошибка при отправке сообщения:', error);  // Ловим ошибки
        }
    }
}

// Добавление нового сообщения в чат
function addMessage(text, recipient_id) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.insertAdjacentHTML('beforeend', createMessageElement(text, recipient_id));  // Добавляем новое сообщение в конец чата
    messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Прокручиваем чат вниз, чтобы показать последнее сообщение
}

// Формирование HTML-элемента для сообщения
function createMessageElement(text, recipient_id) {
    const userID = parseInt(selectedUserId, 10);  // Преобразуем ID в число
    const messageClass = userID === recipient_id ? 'my-message' : 'other-message';  // Определяем, кто отправил сообщение: мы или другой пользователь
    return `<div class="message ${messageClass}">${text}</div>`;  // Возвращаем HTML для отображения сообщения
}

// Периодическая проверка новых сообщений
function startMessagePolling(userId) {
    clearInterval(messagePollingInterval);  // Очищаем старый таймер
    messagePollingInterval = setInterval(() => loadMessages(userId), 1000);  // Каждую секунду загружаем новые сообщения
}

// Привязка действий к элементам
document.querySelectorAll('.user-item').forEach(item => {
    item.onclick = event => selectUser(item.getAttribute('data-user-id'), item.textContent, event);  // Привязываем обработчик клика для выбора пользователя
});

document.getElementById('sendButton').onclick = sendMessage;  // Привязываем отправку сообщения на кнопку "Отправить"

document.getElementById('messageInput').onkeypress = async (e) => {
    if (e.key === 'Enter') {  // Если пользователь нажимает Enter в поле ввода сообщения
        await sendMessage();  // Отправляем сообщение
    }
};