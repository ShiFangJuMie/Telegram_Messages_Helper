import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from logger import logging


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
                    INSERT INTO messages (msg_id, sender_id, sender_name, chat_id, chat_name, message, date, is_bot) 
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
                    DELETE FROM messages
                    WHERE date < (NOW() - INTERVAL '%s day')
                    """
                    cur.execute(query, [days])
                    conn.commit()
                    rows_deleted = cur.rowcount
                    logging.info(f"Deleted {rows_deleted} old messages.")
                    # 删除7天前的记录
                    query = """
                    DELETE FROM messages_aggregated
                    WHERE aggregated_date < (NOW() - INTERVAL '%s day')
                    """
                    cur.execute(query, [days])
                    conn.commit()
                    rows_deleted = cur.rowcount
                    logging.info(f"Deleted {rows_deleted} old aggregated messages.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            pass

    def get_messages(self, start_date):
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT chat_name, chat_id, messages
                    FROM messages_aggregated
                    WHERE aggregated_date = %s
                    ORDER BY id
                    """
                    cur.execute(query, (start_date,))
                    rows = cur.fetchall()
                    return rows
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            pass

    def get_summary(self, start_date):
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT chat_name, chat_id, ai_summary
                    FROM messages_aggregated
                    WHERE aggregated_date = %s
                    ORDER BY id
                    """
                    cur.execute(query, (start_date,))
                    rows = cur.fetchall()
                    return rows
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        finally:
            pass
