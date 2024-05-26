from db import Database, db_params
from logger import logging

db = Database(db_params)


def main():
    db.delete_old_messages(7)
    logging.info("Message from 7 days ago has been deleted")


if __name__ == '__main__':
    main()
