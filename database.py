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
                    complete integer,
                    sgg_id text
                );"""]
    if conn is not None:
        for tablita in tablitas :
            try:
                c = conn.cursor()
                c.execute(tablita)
            except Error as e:
                print(e)
        try:
            conn.cursor().execute("ALTER TABLE events ADD COLUMN sgg_id TEXT")
            conn.commit()
        except Error:
            pass
        try:
            conn.cursor().execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_events_sgg_id "
                "ON events(sgg_id) WHERE sgg_id IS NOT NULL"
            )
            conn.commit()
        except Error:
            pass
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

def get_event_by_sgg_id(conn, sgg_id) :
    cur = conn.cursor()
    cur.execute("SELECT slug, complete FROM events WHERE sgg_id = ?", (sgg_id,))
    return cur.fetchone()

def insert_events(conn, events) :
    sql = ''' INSERT OR IGNORE INTO events (slug, sgg_id, complete)
              VALUES(?,?,0) '''
    cur = conn.cursor()
    cur.executemany(sql, events)
    conn.commit()

def update_event_slug(conn, sgg_id, new_slug) :
    cur = conn.cursor()
    cur.execute("UPDATE events SET slug = ? WHERE sgg_id = ?", (new_slug, sgg_id))
    conn.commit()

def delete_event(conn, slug) :
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE slug = ?", (slug,))
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
    