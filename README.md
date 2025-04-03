project/
├── src/
│   ├── auth/              # Аутентификация и авторизация
│   │   ├── auth.py
│   │   └── routes.py
│   ├── chat/              # Реализация чата
│   │   └── routes.py
│   ├── db/                # Подключение к базе данных и модели
│   │   ├── database.py
│   │   └── models.py
│   ├── user/              # Работа с пользователями
│   │   ├── routes.py
│   │   └── schemas.py
│   └── core/              # Конфигурация
│       └── config.py
├── main.py                # Главный файл приложения
└── uploads/               # Папка для хранения загруженных файлов (например, фото)


curl.exe -X GET "http://127.0.0.1:8000/users/me" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJpbmciLCJleHAiOjE3NDMzMjAyODh9.etBkNF7axc9c_8s-sEo2q72ZnpTXA5_BCwSzo_DtuU4"
Ответ:
{"user_id":1,"username":"string","email":"string","profile_picture":null,"created_at":"2025-03-30T06:25:36.117052Z","updated_at":null}