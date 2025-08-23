document.getElementById('CreateButton').onclick = CreateChat;

function CreateChat() {
    const title = document.getElementById("username").value.trim();
    const input = document.getElementById("membersInput").value;
    const membersList = input.split(',').map(s => s.trim()).filter(Boolean);

    if (!title) return alert("Введите название чата");
    if (membersList.length === 0) return alert("Введите хотя бы одного участника");

    fetch('/group_chats/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ title: title, members: membersList })
    })
    .then(async res => {
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const msg = data.detail || "Ошибка при создании чата";
            throw new Error(msg);
        }
        return data;
    })
    .then(data => {
        console.log("Чат создан:", data);
        window.location.href = "/group_chats/chat";
    })
    .catch(err => {
        console.error("Ошибка при создании чата:", err);
        alert(err.message);
    });
}
