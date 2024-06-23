import os
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
import requests

from db import Database, db_params
from logger import logging

# 初始化数据库对象
db = Database(db_params)

# 从环境变量中获取API URL、API Key和模型
AI_API_URL = os.getenv('AI_API_URL')
AI_API_KEY = os.getenv('AI_API_KEY')

def load_prompt_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read().strip()


def call_ai_api(message):
    AI_API_MODEL = os.getenv('AI_API_MODEL')
    max_tokens = 4096
    
    if len(message) <= 200:
        return f"本次总结因内容太少而跳过，以下为原文：\n{message}"  # 如果消息长度小于200，直接返回原文
    if AI_API_MODEL == 'coze' and len(PROMPT) + len(message) >= 128000:
        AI_API_MODEL = 'gemini'
        max_tokens = 8192
        # return "上下文超过128k，超出CDP(GPT-4o)极限，无法总结。"
    if AI_API_MODEL == 'gemini' and len(PROMPT) + len(message) >= 200000:
        return "上下文超过200k，超出CDP(Gemini)极限，无法总结。"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {AI_API_KEY}'
    }
    data = {
        'messages': [
            {
                'content': f"{PROMPT}{message}",
                'role': 'user'
            }
        ],
        'model': AI_API_MODEL,
        'max_tokens': max_tokens,
        'temperature': 0.8,
        'stream': False
    }
    try:
        response = requests.post(AI_API_URL, headers=headers, json=data)
        response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
        result = response.json()
        response_content = result['choices'][0]['message']['content'].strip()
        # 返回需要写入数据库的文本
        return f"本次总结由{AI_API_MODEL}模型驱动：\n{response_content}"
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None


def process_aggregated_messages():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    try:
        # 获取当前日期和1天前的日期
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 查询聚合消息
        cur.execute("""
            SELECT id, messages
            FROM messages_aggregated
            WHERE ai_summary IS NULL
            AND aggregated_date >= %s
        """, (yesterday,))

        rows = cur.fetchall()
        for row_id, messages in rows:
            logging.info(f"Processing aggregated messages for row ID {row_id}")

            # 调用AI API处理消息
            ai_result = call_ai_api(messages)
            if ai_result:
                # 更新AI处理结果到数据库
                cur.execute("""
                    UPDATE messages_aggregated
                    SET ai_summary = %s
                    WHERE id = %s
                """, (ai_result, row_id))
                conn.commit()
            else:
                logging.warning(f"Failed to process messages for row ID {row_id}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    print("Starting job_aigc")
    # 从文件中加载预设的prompt
    PROMPT_FILE_PATH = 'prompt.txt'
    try:
        PROMPT = load_prompt_from_file(PROMPT_FILE_PATH)
    except Exception as e:
        logging.error(f"Failed to load prompt from file: {e}")
        PROMPT = "请将以下聊天记录进行总结：\n"  # 如果加载失败，使用默认值

    process_aggregated_messages()
    print("Finished job_aigc")
