# audioinsight

## 🔑 Google Cloud Speech-to-Text Credentials

Для работы сервиса транскрипции необходим сервисный ключ Google Cloud в формате JSON.

### Как получить credentials

1. **Создайте проект** в [Google Cloud Console](https://console.cloud.google.com/).
2. **Включите API**:  Перейдите в "APIs & Services" → "Library" → найдите и включите "Speech-to-Text API".
3. **Создайте сервисный аккаунт**:
   - "IAM & Admin" → "Service Accounts" → "Create Service Account"
   - Дайте роль: `Cloud Speech-to-Text User`
   - Скачайте ключ в формате JSON.
4. **Переименуйте файл** (например):
   ```
   audioinsight-460812-a14416636db4.json
   ```
5. **Положите файл** в папку `backend/` вашего проекта (рядом с кодом).

### Важно
- **Не коммитьте этот файл в репозиторий!**  Он уже добавлен в `.gitignore` для безопасности.
- Если вы делаете форк или клон проекта — получите свой ключ и положите его в нужное место.

### Пример `.gitignore`
```
backend/audioinsight-*.json
```

## 🧑‍💻 Для разработчиков

- Все секреты (ключи, .env) должны быть в `.gitignore`.
- Для запуска анализа нужны рабочие ключи Google и Anthropic.
- Для тестов и презентаций используйте mock-режим.
- Код оформлен с учётом best practices (TypeScript, React 18, FastAPI, Tailwind CSS).

## 📄 Лицензия

MIT License

## 🤝 Контакты и поддержка

- Issues и предложения: [GitHub Issues](https://github.com/yourusername/audioinsight/issues)
- Автор: [yourusername](https://github.com/yourusername)