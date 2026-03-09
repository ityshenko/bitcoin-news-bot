import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH')
    CRYPTOPANIC_API_KEY = os.getenv('CRYPTOPANIC_API_KEY')
    ANALYTIC_TIME = os.getenv('ANALYTIC_TIME', '17:00')
    NEWS_INTERVAL = int(os.getenv('NEWS_INTERVAL', '60'))
