import os
from flask import Flask, render_template, request
from datetime import datetime, timedelta
from db import Database, db_params

app = Flask(__name__)
db = Database(db_params)

PAGE_LIMIT = 50000  # 设置页面字符阈值为50k


def create_messages_list(rows):
    messages_list = []
    current_page_messages = ""
    current_page_length = 0

    for row in rows:
        # 格式化当前行的消息
        formatted_message = f'群组名称：{row["chat_name"]}\n{row["messages"]}\n\n'
        message_length = len(formatted_message.encode('utf-8'))
        
        # 如果添加这个消息会超出当前页面的限制，则先将当前页面添加到列表，再开始新的一页
        if current_page_length + message_length > PAGE_LIMIT:
            messages_list.append(current_page_messages)  # 完成当前页面
            current_page_messages = formatted_message  # 开始新的页面
            current_page_length = message_length  # 重置当前页面的长度计数
        else:
            # 添加消息到当前页面
            current_page_messages += formatted_message
            current_page_length += message_length
        
    # 添加最后一页，如果有的话
    if current_page_messages:
        messages_list.append(current_page_messages)

    return messages_list


@app.route('/')
def index():
    # 简单的身份验证
    if os.getenv('AUTH_CODE') != request.args.get('auth'):
        return "Unauthorized", 401
        
    page = request.args.get('page', default=1, type=int)  # 获取当前页数，默认为1
    show_all = request.args.get('all') == 'true'  # 检查是否传入all参数(忽略分页，显示全部消息)

    # 获取并格式化 start_date 参数
    start_date_str = request.args.get('start_date')
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD.", 400
    else:
        # 计算前一天的日期
        start_date = (datetime.now() - timedelta(days=1)).date()

    try:
        rows = db.get_messages(start_date)
        html_messages = ""

        if show_all:
            # 如果传入 all 参数，返回所有消息
            for row in rows:
                html_messages += f'群组名称：{row["chat_name"]}\n{row["messages"]}\n\n'
        else:
            messages_list = create_messages_list(rows)

            # 根据页码选择要显示的消息
            if page <= len(messages_list):
                html_messages = messages_list[page-1]
                if page == len(messages_list):
                    html_messages += "\n--当前为最后一页--"
            else:
                html_messages = "没有更多的记录了"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        html_messages = "加载消息时发生错误。"

    return render_template('index.html', messages=html_messages)


@app.route('/summary')
def summary():
    # 简单的身份验证
    if os.getenv('AUTH_CODE') != request.args.get('auth'):
        return "Unauthorized", 401

    # 获取并格式化 start_date 参数
    start_date_str = request.args.get('start_date')
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD.", 400
    else:
        # 计算前一天的日期
        start_date = (datetime.now() - timedelta(days=1)).date()

    try:
        rows = db.get_summary(start_date)
        html_messages = ""
        for row in rows:
            html_messages += f'<pre>【群组名称：{row["chat_name"]}】\n{row["ai_summary"]}\n\n</pre>'
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        html_messages = "加载消息时发生错误。"

    return render_template('index.html', messages=html_messages)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
