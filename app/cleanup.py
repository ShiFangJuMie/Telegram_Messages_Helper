from db import Database, db_params

# 初始化数据库对象
db = Database(db_params)


def main():
    # 删除7天前的记录
    db.delete_old_messages(7)


if __name__ == '__main__':
    main()
