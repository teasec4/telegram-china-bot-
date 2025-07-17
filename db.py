import sqlite3
from config import DB_PATH

class Database:
    def __init__(self, path=DB_PATH):
        self.conn = sqlite3.connect(path)
        self.create_tables()
    
    def create_tables(self):
        with self.conn:
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            description TEXT,
                            contact TEXT,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP      
                        )
            ''')
    
    def add_request(self, user_id:int, description:str, contact:str):
        with self.conn:
            self.conn.execute(
                'INSERT INTO requests (user_id, description, contact) VALUES (?, ?, ?)',
                (user_id, description, contact)
            )
    
    def user_has_request(self, user_id:int) -> bool:
        with self.conn:
            result = self.conn.execute(
                'SELECT 1 FROM requests WHERE user_id = ? LIMIT 1' , (int(user_id),)
            ).fetchone()
            return result is not None
        
    def delete_request(self, user_id:int):
        with self.conn:
            self.conn.execute(
                'DELETE FROM requests WHERE user_id = ?', (int(user_id),)
            )

    def get_request_by_user(self, user_id:int):
        with self.conn:
            result = self.conn.execute(
                'SELECT description, contact FROM requests WHERE user_id = ?',
                (int(user_id),)
            ).fetchone()
            return result
    
    def get_all_requests(self):
        with self.conn:
            return self.conn.execute('SELECT * FROM requests').fetchall()
        
    def close(self):
        self.conn.close()