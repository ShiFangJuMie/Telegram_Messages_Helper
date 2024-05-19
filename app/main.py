import os
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
# 白名单
whitelist_chats_env = os.getenv('TELEGRAM_WHITELIST_CHAT', '')
whitelist_chats = [int(chat_id) for chat_id in whitelist_chats_env.split(',')] if whitelist_chats_env else None
# 黑名单
blacklist_chats_env = os.getenv('TELEGRAM_BLACKLIST_CHAT', '')
blacklist_chats = [int(chat_id) for chat_id in blacklist_chats_env.split(',')] if blacklist_chats_env else []

# 初始化
db = Database(db_params)
client = TelegramClient(session_name, api_id, api_hash)


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

        # logging.info(f"id: {event.id}")
        # logging.info(f"sender_id: {event.sender_id}")
        # logging.info(f"sender_name: {sender_name}")
        # logging.info(f"chat_id: {event.chat_id}")
        # logging.info(f"chat_title: {chat_title}")
        # logging.info(f"text: {event.text}")
        # logging.info(f"date: {event.date}")
        # logging.info(f"is_bot: {is_bot}")

        message_data = (
            event.id,
            event.sender_id,
            sender_name,
            event.chat_id,
            chat_title,
            event.text,
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
