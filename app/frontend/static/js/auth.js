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



// Обработка кликов по вкладкам
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => showTab(tab.dataset.tab));
});

// Функция отображения выбранной вкладки
function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.form').forEach(form => form.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Form`).classList.add('active');
}

// Функция для валидации данных формы
const validateForm = fields => fields.every(field => field.trim() !== '');

// Функция для отправки запросов
const sendRequest = async (url, data) => {
    try {
        const response = await apiFetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message || 'Операция выполнена успешно!');
            return result;
        } else {
            alert(result.message || 'Ошибка выполнения запроса!');
            return null;
        }
    } catch (error) {
        console.error("Ошибка:", error);
        alert('Произошла ошибка на сервере');
    }
};

// Функция для обработки формы
const handleFormSubmit = async (formType, url, fields) => {
    if (!validateForm(fields)) {
        alert('Пожалуйста, заполните все поля.');
        return;
    }

    const data = await sendRequest(url, formType === 'login'
        ? {username: fields[0], password: fields[1]}
        : {img: fields[0], username: fields[1], email: fields[2], password: fields[3]});

    if (data && formType === 'login') {
        window.location.href = '/chat';
    }
};

// Обработка формы входа
document.getElementById('loginButton').addEventListener('click', async (event) => {
    event.preventDefault();

    const name = document.querySelector('#loginForm input[placeholder="username"]').value;
    const password = document.querySelector('#loginForm input[placeholder="password"]').value;

    await handleFormSubmit('login', '/users/login', [name, password]);
});

// Обработка формы регистрации
document.getElementById('registerButton').addEventListener('click', async (event) => {
    event.preventDefault();

    const imgUrl = document.querySelector('#registerForm input[placeholder="img"]').value;
    const name = document.querySelector('#registerForm input[placeholder="username"]').value;
    const email = document.querySelector('#registerForm input[placeholder="email"]').value;
    const password = document.querySelectorAll('#registerForm input[placeholder="password"]')[0].value;

    await handleFormSubmit('register', '/users/register', [imgUrl, name, email, password]);
});
