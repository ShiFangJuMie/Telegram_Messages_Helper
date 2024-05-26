import os
from db import Database, db_params
from logger import logging
from datetime import datetime, timedelta
import sys
import requests
import psycopg2
import psycopg2.extras

db = Database(db_params)
wechat_base_url = os.getenv('WECHAT_BASE_URL')


def fetch_messages(date):
    url = f'{wechat_base_url}/messages?date={date}'
    response = requests.get(url)
    response.raise_for_status()  # 如果请求失败，抛出异常
    return response.json()  # 返回 JSON 数据


def insert_messages(messages):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    try:
        for message in messages:
            query = """
            INSERT INTO messages (chat_id, chat_name, sender_name, sender_id, message, date, is_bot)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(query, (
                message['chat_id'],
                message['chat_name'],
                message['sender_name'],
                message['sender_id'],
                message['message'],
                message['date'],
                'false'  # is_bot 设置为 False
            ))
        conn.commit()  # 提交事务
    except Exception as e:
        conn.rollback()  # 发生错误时回滚事务
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    if not wechat_base_url:
        logging.info(f"Environment variable WECHAT_BASE_URL is not set. Skipping execution.")
        sys.exit(0)

    if len(sys.argv) > 2:
        print(f"Usage: python script_sync_wechat.py [YYYY-MM-DD]")
        sys.exit(1)

    if len(sys.argv) == 2:
        date = sys.argv[1]
        # 验证日期格式
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        # 没有指定日期时，使用当前日期的前一天
        date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    try:
        messages = fetch_messages(date)
        insert_messages(messages)
        logging.debug(f"{date} WeChat message synchronized")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
