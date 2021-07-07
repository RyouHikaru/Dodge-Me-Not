import sqlite3
from sqlite3 import Error

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    
    return conn

def insert_score(conn, record):
    sql = '''INSERT INTO game_records(player_name, level, score)
             VALUES(?, ?, ?)'''
    cur = conn.cursor()
    cur.execute(sql, record)
    conn.commit()
    return cur.lastrowid

def query_scores(conn):
    cur = conn.cursor()
    cur.execute("SELECT player_name, level, score FROM game_records ORDER BY score DESC LIMIT 10")

    rows = cur.fetchall()

    return rows

db_file = r"game.db"
create_table_sql = """CREATE TABLE IF NOT EXISTS game_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT,
                        level INTEGER,
                        score INTEGER
                    );"""

def main():
    create_table_sql = """CREATE TABLE IF NOT EXISTS game_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            player_name TEXT,
                            level INTEGER,
                            score INTEGER
                        );"""

    conn = create_connection(db_file)

    if conn is not None:
        create_table(conn, create_table_sql)
        conn.close()
    else:
        print("Cannot create DB connection.")
