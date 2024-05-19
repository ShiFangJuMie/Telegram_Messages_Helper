import os
from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from logger import logging
from datetime import datetime


db_params = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'dbname': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT')
}


class Database:
    def __init__(self, db):
        self.db_params = db

    @contextmanager
    def connection(self):
        conn = psycopg2.connect(**self.db_params, cursor_factory=psycopg2.extras.DictCursor)
        try:
            yield conn
        finally:
            conn.close()

    def insert_message(self, message_data):
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO telegram_messages (msg_id, sender_id, sender_name, chat_id, chat_name, message, date, is_bot) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cur.execute(query, message_data)
                    conn.commit()
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            pass

    def delete_old_messages(self, days=7):
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    # 删除7天前的记录
                    query = """
                    DELETE FROM telegram_messages
                    WHERE date < (NOW() - INTERVAL '%s day')
                    """
                    cur.execute(query, [days])
                    conn.commit()
                    rows_deleted = cur.rowcount
                    print(f"Deleted {rows_deleted} old messages.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            pass

    def get_messages_count(self, start_date, start_time, end_date, end_time, use_current_time):
        # 根据提供的日期和时间构造完整的开始和结束时间戳
        start_timestamp = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
        if use_current_time:
            end_timestamp = datetime.now()
        else:
            end_timestamp = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')

        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT COUNT(*)
                    FROM telegram_messages
                    WHERE date BETWEEN %s AND %s
                    """
                    cur.execute(query, [start_timestamp, end_timestamp])
                    count = cur.fetchone()[0]
                    return count
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return 0

    def get_messages(self, start_datetime, end_datetime, chat_id):
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT message
                    FROM telegram_messages
                    WHERE date BETWEEN %s AND %s AND chat_id = %s
                    """
                    cur.execute(query, [start_datetime, end_datetime, chat_id])
                    # 获取所有符合条件的消息
                    messages = cur.fetchall()
                    return messages
        except Exception as e:
            print(f"An error occurred while querying messages: {e}")
            return []
