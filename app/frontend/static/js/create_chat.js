function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

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


document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("CreateForm");
    const input = form.querySelector("input");
    const button = document.getElementById("CreateButton");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = input.value.trim();
        if (!username) {
            alert("Введите имя пользователя");
            return;
        }

        try {
            // Отправляем запрос на сервер
            const response = await apiFetch("/create_chat", {
                method: "POST",
                credentials: 'include',
                headers: {
                'Content-Type': 'application/json'
            },
                body: JSON.stringify({"user2_username": username})
            });

            if (response.ok) {
                const data = await response.json();
    
                // достаём свой id из cookie
                const myId = getCookie("user_id");

                // ищем id собеседника
                const otherUserId = data.users.find(u => u !== myId);

                window.location.href = '/chat';
            

            } else {
                const error = await response.json();
                alert("Ошибка: " + (error.detail || "Не удалось создать чат"));
            }
        } catch (err) {
            console.error("Ошибка запроса:", err);
            alert("Не удалось соединиться с сервером");
        }
    });
});
