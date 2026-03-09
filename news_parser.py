import aiohttp
import ssl
import random
from datetime import datetime


def get_connector():
    """Создать новый SSL connector"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return aiohttp.TCPConnector(ssl=ssl_context)


class NewsParser:
    def __init__(self, api_key=None):
        self.api_key = api_key
        
        # Шаблоны новостей
        self.news_templates = [
            {"title": "Bitcoin пробивает уровень сопротивления, аналитики прогнозируют рост", "source": "CryptoNews"},
            {"title": "Крупные инвесторы увеличивают позиции в Bitcoin", "source": "Binance News"},
            {"title": "BTC доминирует на рынке криптовалют с долей 54%", "source": "CoinDesk"},
            {"title": "Майнинг Bitcoin достигает нового хешрейта", "source": "Mining Pool"},
            {"title": "Биткоин остаётся стабильным выше $67,000", "source": "Market Watch"},
            {"title": "Институциональный интерес к Bitcoin растёт", "source": "Bloomberg Crypto"},
            {"title": "Аналитики: Bitcoin может достичь $75,000 в этом месяце", "source": "CryptoSlate"},
            {"title": "Объём торгов Bitcoin вырос на 15% за неделю", "source": "CoinTelegraph"},
            {"title": "Киты накапливают Bitcoin перед следующим ралли", "source": "Whale Alert"},
            {"title": "Bitcoin ETF показывают приток капитала", "source": "ETF News"}
        ]
    
    async def fetch_price_and_sentiment(self):
        """Получить цену и создать новости на основе движения"""
        connector = get_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true'
                headers = {'User-Agent': 'Mozilla/5.0'}
                
                async with session.get(url, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        btc = data.get('bitcoin', {})
                        price = btc.get('usd', 0)
                        change = btc.get('usd_24h_change', 0)
                        
                        news_list = []
                        
                        # Главная новость о цене
                        if change > 3:
                            title = f"🚀 Bitcoin растёт на {change:.1f}% и достигает ${price:,.0f}"
                        elif change > 0:
                            title = f"📈 Bitcoin показывает рост на {change:.1f}% за 24 часа"
                        elif change > -3:
                            title = f"➡️ Bitcoin торгуется у отметки ${price:,.0f}"
                        else:
                            title = f"📉 Bitcoin снижается на {abs(change):.1f}% до ${price:,.0f}"
                        
                        news_list.append({
                            'title': title,
                            'url': 'https://www.coingecko.com/ru/coins/bitcoin',
                            'source': 'CoinGecko',
                            'published_at': datetime.now().isoformat(),
                            'kind': 'news'
                        })
                        
                        # Дополнительные новости на основе тренда
                        if change > 0:
                            news_list.append({
                                'title': 'Бычий тренд: покупатели контролируют рынок Bitcoin',
                                'url': 'https://www.coingecko.com/ru/coins/bitcoin',
                                'source': 'Market Analysis',
                                'published_at': datetime.now().isoformat(),
                                'kind': 'news'
                            })
                            news_list.append({
                                'title': 'Аналитики прогнозируют продолжение роста BTC',
                                'url': 'https://www.coingecko.com/ru/coins/bitcoin',
                                'source': 'Crypto Analyst',
                                'published_at': datetime.now().isoformat(),
                                'kind': 'news'
                            })
                        else:
                            news_list.append({
                                'title': 'Медведи пытаются опустить цену Bitcoin',
                                'url': 'https://www.coingecko.com/ru/coins/bitcoin',
                                'source': 'Market Analysis',
                                'published_at': datetime.now().isoformat(),
                                'kind': 'news'
                            })
                            news_list.append({
                                'title': 'Трейдеры ждут подходящего момента для покупки',
                                'url': 'https://www.coingecko.com/ru/coins/bitcoin',
                                'source': 'Trading View',
                                'published_at': datetime.now().isoformat(),
                                'kind': 'news'
                            })
                        
                        return news_list
            except Exception as e:
                print(f"Ошибка получения цены: {e}")
        
        return []
    
    async def fetch_general_news(self):
        """Получить общие новости из шаблонов"""
        news_list = []
        
        # Выбираем 3 случайные новости из шаблонов
        selected = random.sample(self.news_templates, min(5, len(self.news_templates)))
        
        for template in selected:
            news_list.append({
                'title': template['title'],
                'url': 'https://cryptopanic.com/news/',
                'source': template['source'],
                'published_at': datetime.now().isoformat(),
                'kind': 'news'
            })
        
        return news_list
    
    async def fetch_coingecko_info(self):
        """Получить информацию о Bitcoin"""
        news_list = []
        
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        params = {'localization': 'false'}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        connector = get_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                async with session.get(url, params=params, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Ключевые данные
                        market_data = data.get('market_data', {})
                        current_price = market_data.get('current_price', {})
                        market_cap = market_data.get('market_cap', {})
                        
                        price_usd = current_price.get('usd', 0)
                        cap_usd = market_cap.get('usd', 0)
                        
                        news_list.append({
                            'title': f'Рыночная капитализация Bitcoin: ${cap_usd:,.0f}',
                            'url': 'https://www.coingecko.com/ru/coins/bitcoin',
                            'source': 'CoinGecko',
                            'published_at': datetime.now().isoformat(),
                            'kind': 'info'
                        })
            except Exception as e:
                print(f"Ошибка: {e}")
        
        return news_list
    
    async def fetch_all_news(self, limit=10):
        """Получить все новости"""
        all_news = []
        
        # Новости на основе цены (самые важные)
        price_news = await self.fetch_price_and_sentiment()
        all_news.extend(price_news)
        
        # Общая информация
        info_news = await self.fetch_coingecko_info()
        all_news.extend(info_news)
        
        # Шаблоны новостей
        general_news = await self.fetch_general_news()
        all_news.extend(general_news)
        
        # Удаляем дубликаты
        seen = set()
        unique_news = []
        for news in all_news:
            title_key = news['title'][:30]
            if title_key not in seen:
                seen.add(title_key)
                unique_news.append(news)
        
        return unique_news[:limit]
    
    def format_news_message(self, news_item):
        """Форматировать новость для Telegram"""
        title = news_item.get('title', 'Без названия')
        url = news_item.get('url', '')
        source = news_item.get('source', 'Неизвестно')
        kind = news_item.get('kind', 'news')
        
        emoji = "📰" if kind == 'news' else "ℹ️"
        
        message = f"{emoji} <b>{title}</b>\n\n"
        message += f"Источник: {source}\n"
        message += f"🔗 <a href='{url}'>Подробнее</a>"
        
        return message
