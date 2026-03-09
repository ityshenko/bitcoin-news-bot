import asyncio
import logging
import io
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.tl.types import Message
from config import Config
from database import Database
from news_parser import NewsParser
from analytics import Analytics

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def create_price_chart(prices_data, current_price):
    """Создать простой ASCII график цены"""
    if not prices_data or len(prices_data) < 7:
        return None
    
    # Берём последние 14 точек
    prices = [p[1] for p in prices_data[-14:]]
    
    if not prices:
        return None
    
    min_price = min(prices)
    max_price = max(prices)
    range_price = max_price - min_price if max_price != min_price else 1
    
    # Создаём график
    height = 8
    width = len(prices)
    
    chart = []
    for row in range(height, 0, -1):
        line = ""
        threshold = min_price + (range_price * row / height)
        for price in prices:
            if price >= threshold:
                line += "🟩"
            else:
                line += "⬜"
        chart.append(line)
    
    return "\n".join(chart)


class BitcoinBot:
    def __init__(self):
        self.client = TelegramClient(
            'bitcoin_bot_session',
            Config.API_ID,
            Config.API_HASH
        )
        
        self.db = Database()
        self.news_parser = NewsParser(Config.CRYPTOPANIC_API_KEY)
        self.analytics = Analytics()

        self.news_task = None
        self.analytics_task = None
        self.hourly_task = None

    async def start(self):
        """Start the bot"""
        logger.info("Запуск Bitcoin News Bot...")

        await self.client.start(bot_token=Config.TELEGRAM_BOT_TOKEN)

        # Register handlers
        self.client.add_event_handler(self.cmd_start, events.NewMessage(pattern='/start'))
        self.client.add_event_handler(self.cmd_help, events.NewMessage(pattern='/help'))
        self.client.add_event_handler(self.cmd_news, events.NewMessage(pattern='/news'))
        self.client.add_event_handler(self.cmd_forecast, events.NewMessage(pattern='/forecast'))
        self.client.add_event_handler(self.cmd_analytics, events.NewMessage(pattern='/analytics'))
        self.client.add_event_handler(self.cmd_stats, events.NewMessage(pattern='/stats'))
        self.client.add_event_handler(self.cmd_unsubscribe, events.NewMessage(pattern='/unsubscribe'))
        self.client.add_event_handler(self.cmd_subscribe, events.NewMessage(pattern='/subscribe'))

        # Register callback handler for inline buttons
        self.client.add_event_handler(self.callback_handler, events.CallbackQuery)

        # Start scheduled tasks
        self.hourly_task = asyncio.create_task(self.hourly_scheduler())
        self.analytics_task = asyncio.create_task(self.analytics_scheduler())

        logger.info("Бот успешно запущен!")
        logger.info("📰 Ежечасная рассылка включена")
        await self.client.run_until_disconnected()
    
    async def cmd_start(self, event):
        """Handle /start command"""
        user_id = event.sender_id
        username = event.sender.username
        
        self.db.add_user(user_id, username)
        
        await event.respond("🔄 Загружаю данные о Bitcoin...")
        
        price_data = await self.analytics.get_btc_price()
        news_list = await self.news_parser.fetch_all_news(limit=3)
        
        message = "👋 <b>Добро пожаловать в Bitcoin News Bot!</b>\n\n"
        
        if price_data:
            price = price_data.get('price', 0)
            change = price_data.get('change_24h', 0)
            change_emoji = "🟢" if change >= 0 else "🔴"
            message += f"💰 <b>Курс Bitcoin: ${price:,.2f}</b>\n"
            message += f"{change_emoji} <b>24ч: {change:+.2f}%</b>\n\n"
        
        if news_list:
            message += "📰 <b>Последние новости:</b>\n"
            for i, news in enumerate(news_list[:3], 1):
                title = news.get('title', 'Без названия')
                source = news.get('source', 'Неизвестно')
                message += f"{i}. {title} <i>({source})</i>\n"
            message += "\n"
        
        message += (
            "<b>Доступные команды:</b>\n"
            "📊 /analytics — Полная аналитика рынка\n"
            "🔮 /forecast — Прогноз курса (час, день, месяц, год)\n"
            "📰 /news — Свежие новости Bitcoin\n"
            "📈 /stats — Статистика бота\n"
            "❓ /help — Помощь\n\n"
            "🔔 Вы подписаны на автоматические обновления!"
        )
        
        keyboard = [
            [Button.inline("📊 Аналитика", b"analytics")],
            [Button.inline("🔮 Прогноз", b"forecast")],
            [Button.inline("📰 Новости", b"news")]
        ]
        
        await event.respond(message, parse_mode='html', buttons=keyboard)
        logger.info(f"Пользователь {user_id} запустил бота")
    
    async def cmd_help(self, event):
        """Handle /help command"""
        message = (
            "📖 <b>Справка Bitcoin News Bot</b>\n\n"
            "<b>Команды:</b>\n"
            "/start — Запустить бота\n"
            "/news — Последние новости Bitcoin (каждые 60 мин)\n"
            "/analytics — Полная аналитика рынка с графиком\n"
            "/forecast — Прогноз цены на разный срок\n"
            "/stats — Статистика бота\n"
            "/unsubscribe — Отписаться от уведомлений\n"
            "/subscribe — Подписаться на уведомления\n"
            "/help — Эта справка\n\n"
            "<b>О боте:</b>\n"
            "Бот собирает новости о Bitcoin и предоставляет аналитику.\n\n"
            "📧 Поддержка: Свяжитесь с владельцем бота"
        )
        
        await event.respond(message, parse_mode='html')
    
    async def cmd_news(self, event):
        """Handle /news command"""
        await event.respond("📰 Загружаю последние новости...")

        news_list = await self.news_parser.fetch_all_news(limit=10)

        if not news_list:
            await event.respond("❌ Не удалось загрузить новости. Попробуйте позже.")
            return

        # Формируем одно сообщение со всеми новостями
        message = "📰 <b>Последние новости Bitcoin</b>\n\n"
        for i, news in enumerate(news_list[:10], 1):
            title = news.get('title', 'Без названия')
            source = news.get('source', 'Неизвестно')
            url = news.get('url', '')
            message += f"{i}. <b>{title}</b>\n"
            message += f"   Источник: {source}\n"
            message += f"   🔗 <a href='{url}'>Подробнее</a>\n\n"
        
        await event.respond(message, parse_mode='html')
        logger.info(f"Новости отправлены пользователю {event.sender_id}")
    
    async def cmd_analytics(self, event):
        """Handle /analytics command with chart"""
        await event.respond("📊 Загружаю аналитику...")
        
        price_data = await self.analytics.get_btc_price()
        market_data = await self.analytics.get_market_data()
        forecast = await self.analytics.get_forecast()
        chart_data = await self.analytics.get_btc_data(days=14)
        
        message = self.analytics.format_analytics_message(price_data, market_data, forecast)
        
        # Создаём ASCII график
        chart = None
        if chart_data:
            prices = chart_data.get('prices', [])
            current = price_data.get('price', 0) if price_data else 0
            chart = create_price_chart(prices, current)
        
        if chart:
            message += f"\n\n<b>График цены (14 дней):</b>\n<code>{chart}</code>"
        
        await event.respond(message, parse_mode='html')
        
        if price_data:
            today = datetime.now().date().isoformat()
            sentiment = self.analytics.calculate_sentiment(price_data, market_data)
            self.db.add_analytics(today, price_data.get('price', 0), price_data.get('change_24h', 0), sentiment)
        
        logger.info(f"Аналитика отправлена пользователю {event.sender_id}")
    
    async def cmd_forecast(self, event):
        """Handle /forecast command"""
        await event.respond("🔮 Формирую прогноз...")
        
        forecast_1h = await self.analytics.get_forecast(hours=1)
        forecast_1d = await self.analytics.get_forecast(days=1)
        forecast_1w = await self.analytics.get_forecast(days=7)
        forecast_1m = await self.analytics.get_forecast(days=30)
        forecast_1y = await self.analytics.get_forecast(days=365)
        
        if not forecast_1d:
            await event.respond("❌ Не удалось сформировать прогноз. Попробуйте позже.")
            return
        
        current_price = forecast_1d.get('current_price', 0)
        
        message = f"🔮 <b>Прогноз курса Bitcoin</b>\n\n"
        message += f"💰 <b>Текущая цена: ${current_price:,.2f}</b>\n\n"
        
        if forecast_1h:
            trend_1h = forecast_1h.get('trend', 'unknown')
            proj_1h = forecast_1h.get('projected_price', current_price)
            trend_emoji = "📈" if trend_1h == 'upward' else "📉"
            message += f"⏰ <b>1 час:</b> {trend_emoji} ${proj_1h:,.2f} ({trend_1h.title()})\n"
        
        if forecast_1d:
            trend_1d = forecast_1d.get('trend', 'unknown')
            proj_1d = forecast_1d.get('projected_price', current_price)
            trend_emoji = "📈" if trend_1d == 'upward' else "📉"
            message += f"📅 <b>1 день:</b> {trend_emoji} ${proj_1d:,.2f} ({trend_1d.title()})\n"
        
        if forecast_1w:
            trend_1w = forecast_1w.get('trend', 'unknown')
            proj_1w = forecast_1w.get('projected_price', current_price)
            trend_emoji = "📈" if trend_1w == 'upward' else "📉"
            message += f"📆 <b>1 неделя:</b> {trend_emoji} ${proj_1w:,.2f} ({trend_1w.title()})\n"
        
        if forecast_1m:
            trend_1m = forecast_1m.get('trend', 'unknown')
            proj_1m = forecast_1m.get('projected_price', current_price)
            trend_emoji = "📈" if trend_1m == 'upward' else "📉"
            message += f"🗓️ <b>1 месяц:</b> {trend_emoji} ${proj_1m:,.2f} ({trend_1m.title()})\n"
        
        if forecast_1y:
            trend_1y = forecast_1y.get('trend', 'unknown')
            proj_1y = forecast_1y.get('projected_price', current_price)
            trend_emoji = "📈" if trend_1y == 'upward' else "📉"
            message += f"📊 <b>1 год:</b> {trend_emoji} ${proj_1y:,.2f} ({trend_1y.title()})\n"
        
        message += (
            f"\n⚠️ <i>Это не финансовая рекомендация. "
            f"Криптовалютные рынки высоковолатильны.</i>\n"
            f"⏰ Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        await event.respond(message, parse_mode='html')
        logger.info(f"Прогноз отправлен пользователю {event.sender_id}")
    
    async def cmd_stats(self, event):
        """Handle /stats command"""
        user_count = self.db.get_user_count()
        
        message = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Активных подписчиков: <b>{user_count}</b>\n"
            f"📰 Источники: CoinGecko + Binance\n"
            f"⏰ Интервал: {Config.NEWS_INTERVAL} минут\n"
            f"🕐 Время аналитики: {Config.ANALYTIC_TIME} UTC\n\n"
            f"🤖 Версия бота: 1.0.0"
        )
        
        await event.respond(message, parse_mode='html')
    
    async def cmd_unsubscribe(self, event):
        """Handle /unsubscribe command"""
        message = (
            "⚠️ <b>Отписка от уведомлений</b>\n\n"
            "Чтобы остановить автоматические обновления:\n"
            "1. Заглушите чат в Telegram\n"
            "2. Или заблокируйте бота\n\n"
            "Используйте /subscribe чтобы подтвердить подписку."
        )
        
        await event.respond(message, parse_mode='html')
    
    async def cmd_subscribe(self, event):
        """Handle /subscribe command"""
        user_id = event.sender_id
        username = event.sender.username
        
        self.db.add_user(user_id, username)
        
        message = (
            "✅ <b>Вы подписаны!</b>\n\n"
            "Теперь вы будете получать автоматические обновления.\n"
            f"📰 Новости каждые {Config.NEWS_INTERVAL} минут\n"
            f"📊 Ежедневная аналитика в {Config.ANALYTIC_TIME} UTC"
        )
        
        await event.respond(message, parse_mode='html')
        logger.info(f"Пользователь {user_id} подписался")
    
    async def callback_handler(self, event):
        """Handle inline button callbacks"""
        data = event.data.decode('utf-8')
        
        if data == 'analytics':
            await event.answer("📊 Загружаю аналитику...")
            
            price_data = await self.analytics.get_btc_price()
            market_data = await self.analytics.get_market_data()
            forecast = await self.analytics.get_forecast()
            chart_data = await self.analytics.get_btc_data(days=14)
            
            message = self.analytics.format_analytics_message(price_data, market_data, forecast)
            
            # ASCII график
            if chart_data:
                prices = chart_data.get('prices', [])
                current = price_data.get('price', 0) if price_data else 0
                chart = create_price_chart(prices, current)
                if chart:
                    message += f"\n\n<b>График цены (14 дней):</b>\n<code>{chart}</code>"
            
            await event.respond(message, parse_mode='html')
            
            if price_data:
                today = datetime.now().date().isoformat()
                sentiment = self.analytics.calculate_sentiment(price_data, market_data)
                self.db.add_analytics(today, price_data.get('price', 0), price_data.get('change_24h', 0), sentiment)
            
            await event.answer("✅")
            
        elif data == 'forecast':
            await event.answer("🔮 Формирую прогноз...")
            
            forecast_1h = await self.analytics.get_forecast(hours=1)
            forecast_1d = await self.analytics.get_forecast(days=1)
            forecast_1w = await self.analytics.get_forecast(days=7)
            forecast_1m = await self.analytics.get_forecast(days=30)
            forecast_1y = await self.analytics.get_forecast(days=365)
            
            if not forecast_1d:
                await event.respond("❌ Не удалось сформировать прогноз. Попробуйте позже.")
                await event.answer("Ошибка")
                return
            
            current_price = forecast_1d.get('current_price', 0)
            
            message = f"🔮 <b>Прогноз курса Bitcoin</b>\n\n"
            message += f"💰 <b>Текущая цена: ${current_price:,.2f}</b>\n\n"
            
            if forecast_1h:
                trend_1h = forecast_1h.get('trend', 'unknown')
                proj_1h = forecast_1h.get('projected_price', current_price)
                trend_emoji = "📈" if trend_1h == 'upward' else "📉"
                message += f"⏰ <b>1 час:</b> {trend_emoji} ${proj_1h:,.2f} ({trend_1h.title()})\n"
            
            if forecast_1d:
                trend_1d = forecast_1d.get('trend', 'unknown')
                proj_1d = forecast_1d.get('projected_price', current_price)
                trend_emoji = "📈" if trend_1d == 'upward' else "📉"
                message += f"📅 <b>1 день:</b> {trend_emoji} ${proj_1d:,.2f} ({trend_1d.title()})\n"
            
            if forecast_1w:
                trend_1w = forecast_1w.get('trend', 'unknown')
                proj_1w = forecast_1w.get('projected_price', current_price)
                trend_emoji = "📈" if trend_1w == 'upward' else "📉"
                message += f"📆 <b>1 неделя:</b> {trend_emoji} ${proj_1w:,.2f} ({trend_1w.title()})\n"
            
            if forecast_1m:
                trend_1m = forecast_1m.get('trend', 'unknown')
                proj_1m = forecast_1m.get('projected_price', current_price)
                trend_emoji = "📈" if trend_1m == 'upward' else "📉"
                message += f"🗓️ <b>1 месяц:</b> {trend_emoji} ${proj_1m:,.2f} ({trend_1m.title()})\n"
            
            if forecast_1y:
                trend_1y = forecast_1y.get('trend', 'unknown')
                proj_1y = forecast_1y.get('projected_price', current_price)
                trend_emoji = "📈" if trend_1y == 'upward' else "📉"
                message += f"📊 <b>1 год:</b> {trend_emoji} ${proj_1y:,.2f} ({trend_1y.title()})\n"
            
            message += (
                f"\n⚠️ <i>Это не финансовая рекомендация.</i>\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            await event.respond(message, parse_mode='html')
            await event.answer("✅")
            
        elif data == 'news':
            await event.answer("📰 Загружаю новости...")

            news_list = await self.news_parser.fetch_all_news(limit=10)

            if not news_list:
                await event.respond("❌ Не удалось загрузить новости. Попробуйте позже.")
                await event.answer("Нет новостей")
                return

            # Формируем одно сообщение со всеми новостями
            message = "📰 <b>Последние новости Bitcoin</b>\n\n"
            for i, news in enumerate(news_list[:10], 1):
                title = news.get('title', 'Без названия')
                source = news.get('source', 'Неизвестно')
                url = news.get('url', '')
                message += f"{i}. <b>{title}</b>\n"
                message += f"   Источник: {source}\n"
                message += f"   🔗 <a href='{url}'>Подробнее</a>\n\n"
            
            await event.respond(message, parse_mode='html')
            await event.answer("✅")

    async def hourly_scheduler(self):
        """Ежечасная рассылка: курс, прогноз, новости в одном сообщении"""
        while True:
            try:
                # Ждём 1 час (3600 секунд)
                await asyncio.sleep(3600)

                users = self.db.get_all_users()
                if not users:
                    continue

                # Получаем все данные
                price_data = await self.analytics.get_btc_price()
                news_list = await self.news_parser.fetch_all_news(limit=5)
                forecast_1d = await self.analytics.get_forecast(days=1)
                forecast_1w = await self.analytics.get_forecast(days=7)

                if not price_data:
                    continue

                price = price_data.get('price', 0)
                change = price_data.get('change_24h', 0)
                change_emoji = "🟢" if change >= 0 else "🔴"

                # Формируем единое сообщение
                message = "⏰ <b>Ежечасное обновление Bitcoin</b>\n\n"
                message += f"💰 <b>Курс: ${price:,.2f}</b>\n"
                message += f"{change_emoji} <b>24ч: {change:+.2f}%</b>\n\n"

                # Прогноз
                if forecast_1d:
                    trend_1d = forecast_1d.get('trend', 'unknown')
                    proj_1d = forecast_1d.get('projected_price', price)
                    trend_emoji = "📈" if trend_1d == 'upward' else "📉" if trend_1d == 'downward' else "➡️"
                    message += f"🔮 <b>Прогноз на 24ч:</b> {trend_emoji} ${proj_1d:,.0f} ({trend_1d.title()})\n"

                if forecast_1w:
                    trend_1w = forecast_1w.get('trend', 'unknown')
                    proj_1w = forecast_1w.get('projected_price', price)
                    trend_emoji = "📈" if trend_1w == 'upward' else "📉" if trend_1w == 'downward' else "➡️"
                    message += f"🔮 <b>Прогноз на неделю:</b> {trend_emoji} ${proj_1w:,.0f} ({trend_1w.title()})\n\n"
                else:
                    message += "\n"

                # Новости
                if news_list:
                    message += "📰 <b>Новости:</b>\n"
                    for i, news in enumerate(news_list[:5], 1):
                        title = news.get('title', 'Без названия')
                        message += f"{i}. {title}\n"

                message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                # Отправляем всем пользователям
                for user_id in users:
                    try:
                        await self.client.send_message(user_id, message, parse_mode='html')
                    except Exception as e:
                        logger.error(f"Ошибка отправки пользователю {user_id}: {e}")

                logger.info(f"✅ Ежечасная рассылка: {len(users)} пользователей")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в ежечасном планировщике: {e}")
                await asyncio.sleep(300)

    async def news_scheduler(self):
        """Schedule news updates"""
        interval = Config.NEWS_INTERVAL * 60
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                users = self.db.get_all_users()
                if not users:
                    continue
                
                news_list = await self.news_parser.fetch_all_news(limit=5)
                price_data = await self.analytics.get_btc_price()
                
                if news_list and price_data:
                    price = price_data.get('price', 0)
                    change = price_data.get('change_24h', 0)
                    change_emoji = "🟢" if change >= 0 else "🔴"
                    
                    message = f"📰 <b>Обновление новостей Bitcoin</b>\n\n"
                    message += f"💰 Курс: ${price:,.2f} ({change_emoji} {change:+.2f}%)\n\n"
                    
                    for news in news_list:
                        message += self.news_parser.format_news_message(news) + "\n\n"
                    
                    for user_id in users:
                        try:
                            await self.client.send_message(user_id, message, parse_mode='html')
                            
                            for news in news_list:
                                self.db.add_news(
                                    news.get('title', ''),
                                    news.get('url', ''),
                                    news.get('source', ''),
                                    news.get('published_at', '')
                                )
                        except Exception as e:
                            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
                
                logger.info(f"Рассылка новостей: {len(users)} пользователей")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике новостей: {e}")
                await asyncio.sleep(60)
    
    async def analytics_scheduler(self):
        """Schedule daily analytics"""
        while True:
            try:
                now = datetime.now()
                target_time = datetime.strptime(Config.ANALYTIC_TIME, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
                
                if target_time < now:
                    target_time = target_time.replace(day=target_time.day + 1)
                
                wait_seconds = (target_time - now).total_seconds()
                logger.info(f"Следующая аналитика через {wait_seconds / 3600:.1f} ч")
                
                await asyncio.sleep(wait_seconds)
                
                users = self.db.get_all_users()
                if not users:
                    continue
                
                price_data = await self.analytics.get_btc_price()
                market_data = await self.analytics.get_market_data()
                forecast = await self.analytics.get_forecast()
                
                message = self.analytics.format_analytics_message(price_data, market_data, forecast)
                
                for user_id in users:
                    try:
                        await self.client.send_message(user_id, message, parse_mode='html')
                    except Exception as e:
                        logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
                
                if price_data:
                    today = datetime.now().date().isoformat()
                    sentiment = self.analytics.calculate_sentiment(price_data, market_data)
                    self.db.add_analytics(today, price_data.get('price', 0), price_data.get('change_24h', 0), sentiment)
                
                logger.info(f"Рассылка аналитики: {len(users)} пользователей")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике аналитики: {e}")
                await asyncio.sleep(3600)
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Остановка бота...")

        if self.hourly_task:
            self.hourly_task.cancel()
        if self.analytics_task:
            self.analytics_task.cancel()

        self.db.close()
        await self.client.disconnect()


async def main():
    bot = BitcoinBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        logger.error(f"Ошибка бота: {e}")
        await bot.stop()


if __name__ == '__main__':
    asyncio.run(main())
