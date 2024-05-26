from telethon import TelegramClient
import os

# 初始化变量
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
session_name = os.path.join('data', os.getenv('TELEGRAM_SESSION'))

# 创建 Telegram 客户端
client = TelegramClient(session_name, api_id, api_hash)


async def main():
    # 登录 Telegram 客户端
    await client.start()
    
    # 获取对话列表（群组，频道等）
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            print(f"Group Title: {dialog.name} | Chat ID: {dialog.id}")

# 运行客户端
with client:
    client.loop.run_until_complete(main())
