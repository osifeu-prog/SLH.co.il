import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

e = create_engine(os.getenv("DATABASE_URL"))

with e.connect() as c:
    print("airdrops cols:")
    for r in c.execute(text("""
        select column_name, data_type
        from information_schema.columns
        where table_name = 'airdrops'
        order by ordinal_position
    """)):
        print(" ", r)

    print("\nusers sample:")
    for r in c.execute(text("""
        select *
        from users
        order by id desc
        limit 3
    """)):
        print(" ", r)
