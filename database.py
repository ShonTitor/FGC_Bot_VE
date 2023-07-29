import sqlite3
from sqlite3 import Error

def create_connection(db_file) :
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    create_tables(conn)
    return conn

def create_tables(conn) :
    tablitas = [""" CREATE TABLE IF NOT EXISTS events (
                    slug text PRIMARY KEY,
                    complete integer
                );"""]
    if conn is not None:
        for tablita in tablitas :
            try:
                c = conn.cursor()
                c.execute(tablita)
            except Error as e:
                print(e)
    else:
        print("Error! cannot create the database connection.")

def drop_tables(conn) :
    tablitas = ["DROP TABLE events;"]
    if conn is not None:
        for tablita in tablitas :
            try:
                c = conn.cursor()
                c.execute(tablita)
            except Error as e:
                print(e)
        create_tables(conn)
    else:
        print("Error! cannot create the database connection.")

def complete_events(conn) :
    cur = conn.cursor()
    cur.execute("""
SELECT slug FROM events
WHERE complete = 1""")
    rows = cur.fetchall()
    rows = [str(r[0]) for r in rows]
    rows.sort()
    return rows

def pending_events(conn) :
    cur = conn.cursor()
    cur.execute("""
SELECT slug FROM events
WHERE complete = 0""")
    rows = cur.fetchall()
    rows = [str(r[0]) for r in rows]
    rows.sort()
    return rows

def event_exists(conn, slug) :
    cur = conn.cursor()
    cur.execute("""
SELECT slug FROM events
WHERE slug = ?""", (slug,))
    rows = cur.fetchall()
    return len(rows) > 0

def insert_events(conn, slugs) :
    sql = ''' INSERT INTO events (slug, complete)
              VALUES(?,0) '''
    cur = conn.cursor()
    cur.executemany(sql, [(slug,) for slug in slugs])
    conn.commit()

def complete_event(conn, slug) :
    sql = ''' UPDATE events
              SET complete = 1
              WHERE slug = ?'''
    cur = conn.cursor()
    cur.execute(sql, (slug,))
    conn.commit()

def set_all_pending(conn) :
    sql = ''' UPDATE events
              SET complete = 0'''
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

if __name__ == "__main__" :
    conn = create_connection("molly.db")
    insert_events(conn, ["perro", "gato"])
    print(pending_events(conn))

