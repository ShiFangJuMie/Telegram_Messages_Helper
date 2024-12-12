from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras

from db import Database, db_params

# 初始化数据库对象
db = Database(db_params)


def aggregate_messages():
    # 连接到数据库
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    # 计算前一天的日期范围
    end_date = datetime.now().date()
    start_date = (datetime.now() - timedelta(days=1)).date()

    # 查询前一天的消息
    cur.execute("""
        SELECT chat_id, chat_name, id, sender_name, message
        FROM messages
        WHERE is_bot != 'true' AND date >= %s AND date < %s
        ORDER BY chat_name, id
    """, (start_date, end_date))

    # 将消息聚合到新表
    current_chat_id = None
    current_chat_name = ""
    messages = []
    seen_messages = set()
    rows = cur.fetchall()

    # 增加一个虚拟的最后一行来触发最后一次插入
    if rows:
        rows.append((None, None, None, None, None))

    for chat_id, chat_name, _, sender_name, message in rows:
        if chat_id != current_chat_id and current_chat_id is not None:
            try:
                # 写入上一个chat_id的聚合消息到新表
                cur.execute("""
                    INSERT INTO messages_aggregated (chat_id, chat_name, aggregated_date, messages)
                    VALUES (%s, %s, %s, %s)
                """, (current_chat_id, current_chat_name, start_date, '\n'.join(messages)))  # 使用换行符分割多条消息
                conn.commit()
            except Exception as e:
                print(f"An error occurred while inserting aggregated messages: {e}")
                conn.rollback()
            messages = []
            seen_messages = set()

        # 拼接数据(不写为else，避免第一条消息被跳过)
        if message is not None:  # 忽略虚拟的最后一行
            message = message.replace('\n', ' ')  # 将多行消息合并为一行
            # 尝试将同一个群聊中的消息去重（实验性功能）
            if message not in seen_messages:
                seen_messages.add(message)
                messages.append(f"{sender_name}说:{message}")
            current_chat_id = chat_id
            current_chat_name = chat_name

    # 关闭数据库连接
    cur.close()
    conn.close()
    print(f"{start_date} Message aggregation completed")


if __name__ == '__main__':
    aggregate_messages()
