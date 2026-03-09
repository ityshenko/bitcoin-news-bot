import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_name='bot.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """Создание таблиц базы данных"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                subscribed INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT,
                published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                btc_price REAL,
                btc_change_24h REAL,
                sentiment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_user(self, user_id, username=None):
        """Добавить пользователя"""
        try:
            self.cursor.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False
    
    def remove_user(self, user_id):
        """Удалить пользователя"""
        try:
            self.cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка удаления пользователя: {e}")
            return False
    
    def get_all_users(self):
        """Получить всех активных пользователей"""
        self.cursor.execute('SELECT user_id FROM users WHERE subscribed = 1')
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_user_count(self):
        """Получить количество пользователей"""
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE subscribed = 1')
        return self.cursor.fetchone()[0]
    
    def add_news(self, title, url, source=None, published_at=None):
        """Добавить новость"""
        try:
            self.cursor.execute(
                'INSERT OR IGNORE INTO news (title, url, source, published_at) VALUES (?, ?, ?, ?)',
                (title, url, source, published_at)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления новости: {e}")
            return False
    
    def news_exists(self, url):
        """Проверить существование новости"""
        self.cursor.execute('SELECT COUNT(*) FROM news WHERE url = ?', (url,))
        return self.cursor.fetchone()[0] > 0
    
    def add_analytics(self, date, btc_price, btc_change_24h, sentiment):
        """Добавить аналитику"""
        try:
            self.cursor.execute(
                'INSERT INTO analytics (date, btc_price, btc_change_24h, sentiment) VALUES (?, ?, ?, ?)',
                (date, btc_price, btc_change_24h, sentiment)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления аналитики: {e}")
            return False
    
    def get_analytics_by_date(self, date):
        """Получить аналитику по дате"""
        self.cursor.execute(
            'SELECT * FROM analytics WHERE date = ?',
            (date,)
        )
        return self.cursor.fetchone()
    
    def close(self):
        """Закрыть соединение"""
        self.conn.close()
