# Утренний пинок

Личный Telegram-бот: погода с советом по одежде, GitHub-дайджест и резюме профиля.

## Подготовка

1. Создайте бота у [@BotFather](https://t.me/BotFather) и получите токен.
2. Скопируйте `.env.example` в `.env` и заполните `TELEGRAM_BOT_TOKEN`, `GITHUB_TOKEN` и `GITHUB_USERNAME`.
3. При необходимости укажите Gemini API key в `LLM_API_KEY`; по умолчанию используется модель `gemini-3.5-flash-lite`. Без ключа бот использует короткий шаблонный совет.
4. Установите зависимости и запустите бота:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

При первом `/start` бот привяжется к чату владельца, если `OWNER_CHAT_ID` не задан. База SQLite создаётся автоматически в `data/morning_bot.sqlite3`.

Если бот не может отправлять сообщения из текущей сети, задайте `TELEGRAM_PROXY` в `.env` (например, `socks5://user:password@host:1080`). Если прямое соединение доступно, оставьте переменную пустой.

## Команды

- `/start` — привязать чат и получить приветствие.
- `/weather` — погода в активном городе.
- `/resume` — краткое резюме GitHub-профиля.
- `/issues` — открытые issues, где требуется ответ владельца.
- `/streak` — серия контрибуций GitHub.
- `/settings` — город, время отправки, язык и порог ожидания ответа.

## Структура

- `database/` — схема SQLite и операции с настройками и городами.
- `services/` — клиенты Open-Meteo, LLM и GitHub REST/GraphQL.
- `handlers/` — Telegram-команды и меню настроек.
- `scheduler/` — сборка и отправка утреннего дайджеста.
- `utils/` — настройка консольного логирования.

Планировщик использует часовой пояс из `TIMEZONE` (по умолчанию `Europe/Minsk`). Бот работает локально, пока запущен процесс `python main.py`.
