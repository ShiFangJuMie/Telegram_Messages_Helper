from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras

from db import Database, db_params
from logger import logging

# 初始化数据库对象
db = Database(db_params)


def aggregate_messages():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    # 计算前一天的日期范围
    end_date = datetime.now().date()
    start_date = (datetime.now() - timedelta(days=1)).date()

    try:
        # 查询前一天的消息
        cur.execute("""
            SELECT chat_id, chat_name, id, sender_name, message
            FROM messages
            WHERE is_bot != 'true' AND date >= %s AND date < %s
            ORDER BY chat_id, id
        """, (start_date, end_date))

        current_chat_id = None
        current_chat_name = ""
        messages = []
        for chat_id, chat_name, _, sender_name, message in cur.fetchall():
            if chat_id != current_chat_id and current_chat_id is not None:
                # 写入上一个chat_id的聚合消息到新表
                cur.execute("""
                    INSERT INTO messages_aggregated (chat_id, chat_name, aggregated_date, messages)
                    VALUES (%s, %s, %s, %s)
                """, (current_chat_id, current_chat_name, start_date, '\n'.join(messages)))  # 使用换行符分割多条消息
                messages = []

            message = message.replace('\n', ' ')  # 将多行消息合并为一行
            messages.append(f"[{sender_name}]说:{message}")
            current_chat_id = chat_id
            current_chat_name = chat_name

        # 确保最后一组数据被写入
        if messages:
            cur.execute("""
                INSERT INTO messages_aggregated (chat_id, chat_name, aggregated_date, messages)
                VALUES (%s, %s, %s, %s)
            """, (current_chat_id, current_chat_name, start_date, '\n'.join(messages)))

        conn.commit()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        conn.rollback()
    finally:
        logging.debug(f"{start_date} Message aggregation completed")
        cur.close()
        conn.close()


if __name__ == '__main__':
    aggregate_messages()
