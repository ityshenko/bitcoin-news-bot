# Bitcoin News Bot

🤖 Telegram-бот для отслеживания новостей и аналитики Bitcoin с ежечасными обновлениями.

## 🚀 Возможности

- 📰 **Новости Bitcoin** - актуальные новости из криптомира
- 💰 **Курс BTC** - текущая цена и изменение за 24 часа
- 🔮 **Прогнозы** - прогноз на 1 час, день, неделю, месяц, год
- 📊 **Аналитика** - рыночные данные и sentiment анализ
- ⏰ **Ежечасные уведомления** - автоматическая рассылка каждый час
- 📈 **График цены** - визуализация изменения цены за 14 дней

## 📋 Требования

- Python 3.8+
- Telegram Bot Token
- API ID и Hash от Telegram
- CryptoPanic API Key (опционально)

## ⚙️ Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/YOUR_USERNAME/bitcoin-news-bot.git
cd bitcoin-news-bot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте файл `.env.example` в `.env`:
```bash
cp .env.example .env
```

Заполните `.env` своими данными:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
API_ID=12345678
API_HASH=your_api_hash_here
CRYPTOPANIC_API_KEY=your_api_key_here
ANALYTIC_TIME=17:00
NEWS_INTERVAL=60
```

### 4. Запуск бота
```bash
python bot.py
```

## 🎮 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запустить бота |
| `/help` | Показать справку |
| `/news` | Последние новости |
| `/analytics` | Аналитика с графиком |
| `/forecast` | Прогноз курса |
| `/stats` | Статистика бота |
| `/subscribe` | Подписаться на уведомления |
| `/unsubscribe` | Отписаться от уведомлений |

## 🔑 Получение API ключей

### Telegram Bot
1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Придумайте имя и username
4. Скопируйте токен

### Telegram API ID/Hash
1. Перейдите на [my.telegram.org](https://my.telegram.org)
2. Войдите по номеру телефона
3. Создайте новое приложение
4. Скопируйте API ID и API Hash

### CryptoPanic API (опционально)
1. Зарегистрируйтесь на [cryptopanic.com](https://cryptopanic.com)
2. Перейдите в Settings → API Keys
3. Сгенерируйте ключ

## 🌐 Размещение 24/7

### Вариант 1: PythonAnywhere (Бесплатно)
1. Зарегистрируйтесь на [pythonanywhere.com](https://www.pythonanywhere.com)
2. Загрузите файлы проекта
3. Создайте Web App или запустите через Console
4. Настройте Scheduled Task для автозапуска

### Вариант 2: Railway (Бесплатно)
1. Зарегистрируйтесь на [railway.app](https://railway.app)
2. Подключите GitHub репозиторий
3. Добавьте переменные окружения
4. Деплой автоматически

### Вариант 3: VPS (От $5/мес)
- DigitalOcean, Linode, Vultr, Hetzner
- Ubuntu 20.04+
- Python 3.8+
- systemd для автозапуска

### Вариант 4: Heroku
1. Создайте аккаунт на [heroku.com](https://www.heroku.com)
2. Установите Heroku CLI
3. Создайте Procfile:
```
worker: python bot.py
```
4. Задеплойте: `git push heroku main`

## 📁 Структура проекта

```
bitcoin-news-bot/
├── bot.py              # Основной файл бота
├── config.py           # Конфигурация
├── database.py         # База данных SQLite
├── news_parser.py      # Парсер новостей
├── analytics.py        # Аналитика и прогнозы
├── requirements.txt    # Зависимости Python
├── .env.example        # Шаблон переменных
├── .gitignore          # Игнор файлы
└── README.md           # Документация
```

## 🔧 Настройка

### Изменение интервала рассылки
В файле `.env` измените `NEWS_INTERVAL` (в минутах):
```env
NEWS_INTERVAL=60  # Рассылка каждый час
```

### Время ежедневной аналитики
В файле `.env` измените `ANALYTIC_TIME` (UTC):
```env
ANALYTIC_TIME=17:00  # 17:00 UTC
```

## 🐛 Решение проблем

### Бот не запускается
```bash
# Проверьте Python
python --version  # Должен быть 3.8+

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Ошибка API
- Проверьте токены в `.env`
- Убедитесь в наличии интернета
- Проверьте лимиты API

### Бот не отвечает
- Убедитесь что скрипт запущен
- Проверьте логи консоли
- Перезапустите бота

## 📝 Лицензия

MIT License

## 👥 Поддержка

По вопросам и предложениям обращайтесь к владельцу бота.

---

**⚠️ Предупреждение:** Этот бот предоставляет информацию только в образовательных целях. Не является финансовой рекомендацией.
