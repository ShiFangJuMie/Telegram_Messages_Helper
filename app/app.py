from db import Database, db_params
import os
from flask import Flask, render_template, request
from datetime import datetime
import re

app = Flask(__name__)
db = Database(db_params)

# 假设身份验证代码
AUTH_CODE = os.getenv('AUTH_CODE')


@app.route('/')
def index():
    auth_code = request.args.get('auth')
    if auth_code != AUTH_CODE:
        return 'Unauthorized', 401

    messages = []
    start_date = request.args.get('start_date')
    # 从URL参数获取end_date，如果没有则使用当前时间
    end_date = request.args.get('end_date') or datetime.now().strftime('%Y-%m-%dT%H:%M')

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:.\d+)?(?:Z|[+-]\d{2}:\d{2})?$")

    if start_date and not date_pattern.match(start_date):
        return "Invalid start_date format.", 500
    if end_date and not date_pattern.match(end_date):
        return "Invalid end_date format.", 500

    if start_date:
        try:
            with db.connection() as conn:
                with conn.cursor() as cur:
                    # 使用参数化查询进行安全的SQL查询
                    query = """
                    SELECT chat_name, sender_name, message
                    FROM telegram_messages 
                    WHERE is_bot = 'false' AND date BETWEEN %s AND %s
                    ORDER BY chat_id, msg_id
                    """
                    # 将日期和时间字符串转换为ISO标准格式
                    start_date_iso = datetime.fromisoformat(start_date.replace("T", " "))
                    end_date_iso = datetime.fromisoformat(end_date.replace("T", " "))
                    cur.execute(query, (start_date_iso, end_date_iso))
                    rows = cur.fetchall()
                    for row in rows:
                        chat_name = row['chat_name']
                        sender_name = row['sender_name']
                        sender_name = sender_name[:4] + '...' if len(sender_name) > 4 else sender_name
                        message = row['message'].replace('\n', ' ')
                        messages.append((chat_name, sender_name, message))
        except Exception as e:
            print(f"An error occurred while fetching messages: {e}")

    # 格式化消息以便在HTML中显示
    html_messages = ""
    current_chat_name = None
    for chat_name, sender_name, message in messages:
        sender_name = sender_name[:4] if len(sender_name) > 4 else sender_name
        message = message.replace('\n', ' ')

        # 如果chat_name变化了，添加一个新的chat_name标记
        if current_chat_name != chat_name:
            html_messages += f'----来源：{chat_name}----\n'
            current_chat_name = chat_name

        html_messages += f'{sender_name}: {message}\n'

    # 传递整个HTML内容到模板
    return render_template('index.html', auth_code=auth_code, messages=html_messages)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
