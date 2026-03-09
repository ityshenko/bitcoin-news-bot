import aiohttp
import ssl
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


def get_connector():
    """Создать новый SSL connector"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return aiohttp.TCPConnector(ssl=ssl_context, limit=10, ttl_dns_cache=300)


class Analytics:
    async def get_btc_data(self, days=30):
        """Get Bitcoin market data from CoinGecko"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        connector = get_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
            url = f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}'
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    logger.info(f"CoinGecko market_chart: status={resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Got {len(data.get('prices', []))} price points")
                        return data
                    else:
                        logger.error(f"CoinGecko error: {resp.status} - {await resp.text()}")
            except asyncio.TimeoutError:
                logger.error("CoinGecko timeout")
            except Exception as e:
                logger.error(f"Error fetching BTC data: {e}")
        return None

    async def get_btc_price(self):
        """Get current Bitcoin price"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        connector = get_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
            url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true'
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    logger.info(f"CoinGecko price: status={resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Price data: {data}")
                        btc = data.get('bitcoin', {})
                        return {
                            'price': btc.get('usd', 0),
                            'change_24h': btc.get('usd_24h_change', 0)
                        }
                    else:
                        logger.error(f"CoinGecko price error: {resp.status}")
            except asyncio.TimeoutError:
                logger.error("CoinGecko price timeout")
            except Exception as e:
                logger.error(f"Error fetching BTC price: {e}")
        return None

    async def get_market_data(self):
        """Get detailed Bitcoin market data"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        connector = get_connector()
        async with aiohttp.ClientSession(connector=connector) as session:
            url = 'https://api.coingecko.com/api/v3/coins/bitcoin'
            params = {'localization': 'true'}
            try:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    logger.info(f"CoinGecko market data: status={resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info("Got market data")
                        return data
                    else:
                        logger.error(f"CoinGecko market data error: {resp.status}")
            except asyncio.TimeoutError:
                logger.error("CoinGecko market data timeout")
            except Exception as e:
                logger.error(f"Error fetching market data: {e}")
        return None
    
    def calculate_sentiment(self, price_data, market_data=None):
        """Calculate market sentiment based on price data"""
        if not price_data:
            return "Нейтрально"
        
        change_24h = price_data.get('change_24h', 0)
        
        if change_24h > 5:
            return "🚀 Очень бычий"
        elif change_24h > 2:
            return "📈 Бычий"
        elif change_24h > -2:
            return "➡️ Нейтрально"
        elif change_24h > -5:
            return "📉 Медвежий"
        else:
            return "💥 Очень медвежий"
    
    async def get_forecast(self, days=7, hours=None):
        """Generate price forecast based on trend analysis"""
        try:
            logger.info(f"Getting forecast for days={days}, hours={hours}")
            
            if hours:
                market_data = await self.get_btc_data(days=7)
            elif days >= 365:
                market_data = await self.get_btc_data(days=365)
            else:
                market_data = await self.get_btc_data(days=max(days, 30))

            current_data = await self.get_btc_price()

            if not market_data:
                logger.warning("No market data for forecast")
                # Fallback: use current price only
                if current_data:
                    return {
                        'current_price': current_data.get('price', 0),
                        'trend': 'unknown',
                        'projected_price': current_data.get('price', 0),
                        'confidence': 'Низкая'
                    }
                return None

            if not current_data:
                logger.warning("No current price data for forecast")
                return None

            prices = [p[1] for p in market_data.get('prices', [])]
            logger.info(f"Got {len(prices)} price points for forecast")

            if len(prices) < 7:
                logger.warning(f"Not enough price points ({len(prices)}) for forecast")
                current_price = current_data.get('price', 0)
                return {
                    'current_price': current_price,
                    'trend': 'unknown',
                    'projected_price': current_price,
                    'confidence': 'Низкая'
                }

            current_price = current_data.get('price', 0)

            sma_7 = sum(prices[-7:]) / 7 if len(prices) >= 7 else current_price
            sma_14 = sum(prices[-14:]) / 14 if len(prices) >= 14 else sma_7
            sma_30 = sum(prices[-30:]) / 30 if len(prices) >= 30 else sma_14

            if len(prices) >= 7:
                week_ago_price = prices[0]
                monthly_trend = (current_price - week_ago_price) / week_ago_price
            else:
                monthly_trend = 0

            if sma_7 > sma_14 and sma_14 > sma_30:
                trend = "upward"
                trend_strength = 1.5
            elif sma_7 < sma_14 and sma_14 < sma_30:
                trend = "downward"
                trend_strength = -1.5
            else:
                trend = "sideways"
                trend_strength = 0.5

            if hours:
                volatility_factor = 0.002
                days_factor = hours / 24
            elif days == 1:
                volatility_factor = 0.015
                days_factor = 1
            elif days <= 7:
                volatility_factor = 0.03
                days_factor = days / 7
            elif days <= 30:
                volatility_factor = 0.08
                days_factor = days / 30
            else:
                volatility_factor = 0.25
                days_factor = days / 365

            trend_component = monthly_trend * trend_strength * days_factor
            volatility_component = volatility_factor * (1 if trend == "upward" else -1 if trend == "downward" else 0)

            total_change = trend_component + volatility_component
            total_change = max(-0.5, min(0.5, total_change))

            projected_price = current_price * (1 + total_change)

            if hours:
                confidence = "Высокая"
            elif days <= 1:
                confidence = "Средняя"
            elif days <= 7:
                confidence = "Средняя"
            elif days <= 30:
                confidence = "Низкая"
            else:
                confidence = "Очень низкая"

            logger.info(f"Forecast: trend={trend}, projected={projected_price:.2f}")

            return {
                'current_price': current_price,
                'trend': trend,
                'sma_7': sma_7,
                'sma_14': sma_14,
                'sma_30': sma_30,
                'projected_price': projected_price,
                'confidence': confidence,
                'change_percent': total_change * 100
            }
        except Exception as e:
            logger.error(f"Error in get_forecast: {e}")
            # Return fallback
            current_data = await self.get_btc_price()
            if current_data:
                return {
                    'current_price': current_data.get('price', 0),
                    'trend': 'unknown',
                    'projected_price': current_data.get('price', 0),
                    'confidence': 'Ошибка прогноза'
                }
            return None
    
    def format_analytics_message(self, price_data, market_data=None, forecast=None):
        """Format analytics data for Telegram message"""
        if not price_data:
            return "❌ Не удалось загрузить данные аналитики. Попробуйте позже."

        price = price_data.get('price', 0)
        change_24h = price_data.get('change_24h', 0)
        sentiment = self.calculate_sentiment(price_data, market_data)

        market_cap = ""
        if market_data:
            market_cap_data = market_data.get('market_data', {})
            market_cap_value = market_cap_data.get('market_cap', {}).get('usd', 0)
            if market_cap_value:
                market_cap = f"\n💎 Капитализация: <b>${market_cap_value:,.0f}</b>"

        message = "📊 <b>Аналитика Bitcoin</b>\n\n"
        message += f"💰 Цена: <b>${price:,.2f}</b>\n"

        change_emoji = "🟢" if change_24h >= 0 else "🔴"
        message += f"{change_emoji} 24ч: <b>{change_24h:+.2f}%</b>\n"
        message += f"📊 Настроение: <b>{sentiment}</b>{market_cap}\n"

        if forecast and forecast.get('trend') != 'unknown':
            trend_emoji = "📈" if forecast['trend'] == 'upward' else "📉" if forecast['trend'] == 'downward' else "➡️"
            message += f"\n{trend_emoji} <b>Прогноз на 7 дней</b>\n"
            message += f"Тренд: {forecast['trend'].title()}\n"
            message += f"Цель: ${forecast['projected_price']:,.2f} ({forecast['change_percent']:+.1f}%)\n"
            message += f"Уверенность: {forecast['confidence']}\n"
        elif forecast:
            message += f"\n⚠️ <b>Прогноз недоступен</b> - недостаточно данных для анализа\n"

        message += f"\n⏰ Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return message
