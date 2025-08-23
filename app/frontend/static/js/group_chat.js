let currentUsername;
const userCache = {};
let socket = null;
let messagePollingInterval = null;
let selectedGroupId = null;

async function exitGroup(chatId) {
    const response = await fetch('/group_chats/exit', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId })
    });

    if (response.ok) {
        alert('Вы вышли из чата');
        closeMembersModal();
        location.reload();
    } else {
        console.error('Ошибка при выходе из чата');
    }
}

function closeMembersModal() {
    const modal = document.getElementById("membersModal");
    if (modal) modal.style.display = "none";
}

function confirmAction(message, onConfirm) {
    const modal = document.getElementById("confirmModal");
    const confirmText = document.getElementById("confirmText");
    const yesBtn = document.getElementById("confirmYes");
    const noBtn = document.getElementById("confirmNo");

    confirmText.textContent = message;
    modal.style.display = "flex";

    function cleanup() {
        yesBtn.removeEventListener('click', yesHandler);
        noBtn.removeEventListener('click', noHandler);
        modal.style.display = "none";
    }

    function yesHandler() { cleanup(); onConfirm(); }
    function noHandler() { cleanup(); }

    yesBtn.addEventListener('click', yesHandler);
    noBtn.addEventListener('click', noHandler);
}

async function ShowMembers() {
    const currentUserId = document.querySelector(".chat-container").dataset.userId;
    const currentUsernameLocal = document.querySelector(".chat-container").dataset.username;

    try {
        const membersRes = await fetch("/group_chats/group_members", {
            method: "POST",
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: selectedGroupId })
        });
        const members = await membersRes.json();

        const ownerRes = await fetch("/group_chats/group_owner", {
            method: "POST",
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: selectedGroupId })
        });
        const ownerId = await ownerRes.json();

        const membersList = members.map(member => {
            let buttons = "";
            if (member === currentUsernameLocal) {
                buttons += `<button onclick="confirmAction('Вы уверены, что хотите выйти из группы?', () => exitGroup('${selectedGroupId}'))">Выйти</button>`;
            } else if (String(ownerId) === currentUserId) {
                buttons += `<button onclick="removeMember('${member}')">Удалить</button>`;
            }
            return `<div>${member}${buttons}</div>`;
        }).join('');

        document.getElementById("membersModalContent").innerHTML = membersList;
        document.getElementById("membersModal").style.display = "block";
    } catch (err) {
        console.error("Ошибка при загрузке участников:", err);
    }
}

async function removeMember(member_name) {
    try {
        const res = await fetch("/group_chats/delete_member", {
            method: "DELETE",
            credentials: "include",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: selectedGroupId, member_name })
        });
        if (!res.ok) throw new Error("Ошибка при удалении");
        await res.json();
        console.log("Удалён:", member_name);
        await ShowMembers();
    } catch (err) {
        console.error(err);
    }
}

async function apiFetch(url, options = {}) {
    options.credentials = 'include';
    let response = await fetch(url, options);
    if (response.status === 401) {
        const refreshResponse = await fetch('/users/refresh', { method: 'POST', credentials: 'include' });
        if (refreshResponse.ok) response = await fetch(url, options);
        else window.location.href = "/users/login";
    }
    return response;
}

async function logout() {
    try {
        const res = await fetch('/users/logout/', { method: 'POST' });
        if (res.ok) window.location.href = '/users/';
        else console.error('Ошибка при выходе');
    } catch (err) {
        console.error(err);
    }
}

function createMessageElement(text, sender_id, messageId) {
    const messageClass = sender_id === document.querySelector(".chat-container").dataset.userId ? 'sent' : 'received';
    let username = userCache[sender_id] || 'Unknown';

    if (!userCache[sender_id]) {
        fetch('/group_chats/get_username', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: sender_id })
        })
        .then(res => res.json())
        .then(data => {
            userCache[sender_id] = data.username || 'Unknown';
            const msgElem = document.getElementById(`msg-${messageId}`);
            if (msgElem) msgElem.innerHTML = `(${userCache[sender_id]}) ${text}`;
        });
    }

    return `<div class="message ${messageClass}" id="msg-${messageId}">(${username}) ${text}</div>`;
}

function addMessage(text, sender_id) {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.insertAdjacentHTML('beforeend', createMessageElement(text, sender_id, Date.now()));
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function startMessagePolling(groupId) {
    clearInterval(messagePollingInterval);
    messagePollingInterval = setInterval(async () => {
        try {
            const res = await apiFetch(`/group_chats/messages/${groupId}`);
            const messages = await res.json();
            const messagesContainer = document.getElementById('messages');
            messagesContainer.innerHTML = messages.map((m, i) => createMessageElement(m.text, m.sender_id, i)).join('');
        } catch (err) {
            console.error('Ошибка при опросе сообщений:', err);
        }
    }, 1000);
}

function connectWebSocket() {
    if (socket) socket.close();
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${protocol}://localhost:8000/ws/${selectedGroupId}`);
    socket.onopen = () => console.log('WS соединение установлено');
    socket.onmessage = e => {
        const msg = JSON.parse(e.data);
        if (msg.chat_id === selectedGroupId) addMessage(msg.text, msg.sender_id);
    };
    socket.onclose = () => console.log('WS соединение закрыто');
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || !selectedGroupId) return;

    const payload = { chat_id: selectedGroupId, text: message };
    await fetch('/group_chats/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    socket.send(JSON.stringify(payload));
    addMessage(message, document.querySelector(".chat-container").dataset.userId);
    input.value = '';
}

async function minutesentr() {
    const inputMinutes = document.getElementById("minutes").value;
    if (isNaN(inputMinutes) || inputMinutes < 0) return alert("Введите корректное количество минут");

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message || !selectedGroupId) return;

    const payload = { message: { chat_id: selectedGroupId, text: message }, time: inputMinutes };
    await fetch('/group_chats/messages_late', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    socket.send(JSON.stringify(payload));
    addMessage(message, document.querySelector(".chat-container").dataset.userId);
    messageInput.value = '';
    document.getElementById("myModal").style.display = "none";
}

async function loadMessages(chatId) {
    const res = await apiFetch(`/group_chats/messages/${chatId}`);
    const messages = await res.json();
    const container = document.getElementById('messages');
    container.innerHTML = messages.map(m => createMessageElement(m.text, m.sender_id)).join('');
}

async function selectGroup(chatId, chatTitle, event) {
    selectedGroupId = chatId;
    document.getElementById('chatHeader').innerHTML = `
        <span>Чат ${chatTitle}</span>
        <button class="chat-members" id="ChatMembers">Участники чата</button>
        <button class="logout-button" id="logoutButton">Выход</button>
    `;
    document.getElementById('ChatMembers').onclick = ShowMembers;
    document.getElementById('logoutButton').onclick = logout;
    document.getElementById('messageInput').disabled = false;
    document.getElementById('sendButton').disabled = false;
    document.getElementById('lateButton').disabled = false;

    document.querySelectorAll('.user-item').forEach(item => item.classList.remove('active'));
    event.target.classList.add('active');

    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    messagesContainer.style.display = 'block';

    await loadMessages(chatId);
    connectWebSocket();
    startMessagePolling(chatId);
}

document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.querySelector('.chat-container');
    currentUsername = chatContainer.dataset.username;
    console.log(currentUsername);

    document.getElementById('addMemberButton').onclick = () => {
        const form = document.getElementById('addMemberForm');
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    };

    document.getElementById('submitNewMember').onclick = async () => {
        const input = document.getElementById('newMemberUsername');
        const newUsername = input.value.trim();
        if (!newUsername) return alert("Введите username");

        const res = await fetch('/group_chats/add_member', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: selectedGroupId, new_user: newUsername })
        });
        const data = await res.json();
        if (data.status_code === "200 ok") {
            alert(`${newUsername} добавлен(а)`);
            input.value = '';
            document.getElementById('addMemberForm').style.display = 'none';
            ShowMembers();
        }
    };

    document.getElementById("minutesButton").onclick = minutesentr;
    document.getElementById("lateButton").onclick = () => document.getElementById("myModal").style.display = "block";

    document.querySelectorAll('.user-item').forEach(item => {
        item.onclick = event => selectGroup(item.getAttribute('data-user-id'), item.textContent, event);
    });

    document.getElementById('sendButton').onclick = sendMessage;
    document.getElementById('messageInput').onkeypress = async e => { if (e.key === 'Enter') await sendMessage(); };
    document.getElementById('ChatMembers').onclick = () => { if (!selectedGroupId) return alert("Сначала выберите чат!"); ShowMembers(); };
});
