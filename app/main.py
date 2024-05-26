import os
import re
from db import Database, db_params
from logger import logging
from telethon import TelegramClient, events
from telethon.tl.types import User, Channel
from telethon.errors import (
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    PhoneNumberUnoccupiedError
)

# 使用环境变量获取配置信息
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
session_name = os.path.join('data', os.getenv('TELEGRAM_SESSION'))

# 群组白名单
whitelist_chats_env = os.getenv('TELEGRAM_WHITELIST_CHAT', '')
whitelist_chats = [int(chat_id) for chat_id in whitelist_chats_env.split(',')] if whitelist_chats_env else None

# 群组黑名单
blacklist_chats_env = os.getenv('TELEGRAM_BLACKLIST_CHAT', '')
blacklist_chats = [int(chat_id) for chat_id in blacklist_chats_env.split(',')] if blacklist_chats_env else []

# 关键词黑名单
blacklist_keywords_env = os.getenv('TELEGRAM_BLACKLIST_KEYWORDS', '')
blacklist_keywords = blacklist_keywords_env.split(',') if blacklist_keywords_env else []


# 将通配符转换为正则表达式
def wildcard_to_regex(pattern):
    return re.compile(re.escape(pattern).replace(r'\*', '.*'))


# 初始化
db = Database(db_params)
client = TelegramClient(session_name, api_id, api_hash)
# 转换黑名单关键字为正则表达式
blacklist_patterns = [wildcard_to_regex(keyword) for keyword in blacklist_keywords]


@client.on(events.NewMessage(incoming=True, chats=whitelist_chats))
async def new_message_listener(event):
    # 检查event.chat是否为None，并尝试获取title属性
    if event.chat:
        chat_title = event.chat.title if hasattr(event.chat, 'title') else None
    else:
        chat_title = None

    # 检查消息是否来自黑名单中的群组或频道
    if event.chat_id in blacklist_chats:
        logging.debug(f"Ignored message from blacklisted chat: {chat_title} / {event.chat_id}")
        return

    # 检查消息文本是否为空(忽略表情、贴纸、图片、视频、文件等)
    if event.text is None or event.text.strip() == '':
        logging.debug("Ignored message with no text or known media type")
        return
        
    # 检查消息内容是否包含黑名单中的关键字
    for pattern in blacklist_patterns:
        if pattern.search(event.text):
            logging.debug(f"Ignored message containing blacklisted keyword pattern: {pattern.pattern}")
            return
            
    # 获取被引用消息的文本
    quoted_text = ''
    if event.reply_to_msg_id:
        try:
            quoted_message = await event.get_reply_message()
            if quoted_message and quoted_message.text:
                quoted_text = f"引用消息: {quoted_message.text} \n回复: "
        except Exception as e:
            logging.error(f"Failed to fetch quoted message: {e}")
            
    try:
        # 如果event.sender为None，则可能是匿名管理员或频道发的消息
        if event.sender:
            if isinstance(event.sender, User):
                # 获取个人用户的姓名和机器人状态
                first_name = event.sender.first_name or ""
                last_name = event.sender.last_name or ""
                sender_name = (first_name + " " + last_name).strip()
                is_bot = event.sender.bot
            elif isinstance(event.sender, Channel):
                # 获取通道的标题作为发送者名字
                sender_name = event.chat.title if event.chat else "unknown channel"
                is_bot = False
            else:
                sender_name = "Unknown Sender"
                is_bot = None
                logging.debug(f"Unknown sender type: {type(event.sender).__name__}")
        else:
            sender_name = "Unknown"
            is_bot = None
            logging.debug("Sender is None, possibly an anonymous admin or system message")

        # 截断超过300字符的消息，并添加省略号，如果LLM输入上限不是问题，那么久移除或调高
        message_text = f"{quoted_text}{event.text}"
        if len(message_text) > 300:
            message_text = message_text[:300] + '...'

        message_data = (
            event.id,
            event.sender_id,
            sender_name,
            event.chat_id,
            chat_title,
            message_text,
            event.date,
            is_bot
        )

        # 将消息插入数据库
        db.insert_message(message_data)
    except Exception as e:
        logging.error(f"Failed to insert message: {e}")


async def main():
    try:
        await client.start()
        logging.info("Client started successfully.")
        await client.run_until_disconnected()
    except (PhoneCodeInvalidError, SessionPasswordNeededError, PhoneNumberUnoccupiedError) as e:
        logging.error(f"Authentication failed: {e}")
        exit(401)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        exit(500)


if __name__ == '__main__':
    client.loop.run_until_complete(main())
