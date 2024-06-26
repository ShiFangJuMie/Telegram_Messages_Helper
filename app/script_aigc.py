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
    model = os.getenv('AI_API_MODEL')
    max_tokens = 4096
    content = f"{PROMPT}{message}"
    content_length = len(PROMPT) + len(message)

    if len(message) < 200:  # 如果消息长度小于200，直接返回原文
        return f"本次总结因内容太少而跳过，以下为原文：\n{message}"

    # 此处模型分流规则相当个性化，请根据自己的需求进行修改
    if model != 'coze' and 'gemini' not in model and content_length > 128000:
        return "上下文超过128k，可能无法总结。如果你使用的模型支持更大的上下文，请手动修改代码。"

    if model == 'coze':  # 如果AI模型为Coze，根据消息长度调整模型
        if content_length < 30000:  # 如果长度不超过30k，使用chat2api gpt-4o总结（应对Coze的使用配额）
            model = 'gpt-4o'
        if content_length >= 128000:  # 如果长度超过128k，使用gemini总结
            model = 'gemini'
        if content_length >= 200000:  # 如果消息长度超过200k，放弃总结
            return "上下文超过200k，超出CDP(Gemini)极限，无法总结。"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {AI_API_KEY}'
    }
    data = {
        'messages': [
            {
                'content': content,
                'role': 'user'
            }
        ],
        'model': model,
        'max_tokens': max_tokens,
        'temperature': 0.8,
        'stream': False
    }
    try:
        response = requests.post(AI_API_URL, headers=headers, json=data)
        response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
        result = response.json()
        response_content = result['choices'][0]['message']['content'].strip()
        response_model = result['model'].strip()

        return f"本次总结由{model}({response_model})模型驱动：\n{response_content}"

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
            ORDER BY id
        """, (yesterday,))

        rows = cur.fetchall()
        for row_id, messages in rows:
            logging.info(f"Processing aggregated messages for row ID {row_id}")

            # 调用AI API处理消息
            ai_result = call_ai_api(messages)
            if ai_result is not None:
                if len(ai_result) < 200:
                    # 如果AI处理结果太短，将原文呈现到前台显示。（避免某些敏感信息不断重试导致过多的token消耗和封号风险）
                    logging.warning(f"AI processing result is too short for row ID {row_id}")
                    ai_result = f"AI处理结果不达预期效果，以下为原文：\n{messages}"

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
