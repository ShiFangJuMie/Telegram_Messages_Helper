import os
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
AI_API_MODEL = os.getenv('AI_API_MODEL')


def load_prompt_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read().strip()


def call_ai_api(message):
    if len(message) <= 100:
        return "100个字都不到的群，没有总结价值。"
    if AI_API_MODEL == 'coze' and len(PROMPT)+len(message) >= 200000:
        return "超过200000字符，超出CDP可用的最大上下文，无法总结。"
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
        'max_tokens': 4096,
        'temperature': 0.8,
        'stream': False
    }
    try:
        response = requests.post(AI_API_URL, headers=headers, json=data)
        response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
        result = response.json()
        # 返回需要写入数据库的文本
        return result['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None


def process_aggregated_messages():
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    try:
        # 查询聚合消息
        cur.execute("""
            SELECT id, messages
            FROM messages_aggregated
            WHERE ai_summary IS NULL
        """)
        
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
    # 从文件中加载预设的prompt
    PROMPT_FILE_PATH = 'prompt.txt'  # 假设文件名为 prompt.txt
    try:
        PROMPT = load_prompt_from_file(PROMPT_FILE_PATH)
    except Exception as e:
        logging.error(f"Failed to load prompt from file: {e}")
        PROMPT = "请将以下聊天记录进行总结：\n"  # 如果加载失败，使用默认值
        
    process_aggregated_messages()
