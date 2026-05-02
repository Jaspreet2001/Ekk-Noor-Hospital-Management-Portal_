import psycopg2
import psycopg2.extras

hostname = "localhost"
database = "postgres"
username = "postgres"
password = "kakkar3010"
port_id  = 5432

conn = None   # ✅ Move these OUTSIDE and BEFORE try block
cur  = None

try:
    conn = psycopg2.connect(
        host     = hostname,
        dbname   = database,
        user     = username,
        password = password,
        port     = port_id
    )                         # ✅ Closing bracket is here — clean and correct

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # ✅ Cursor created successfully  

    create_script = '''CREATE TABLE IF NOT EXISTS login(
        id       SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
    )'''

    cur.execute(create_script)

    insert_script = '''INSERT INTO login (username, password) VALUES (%s, %s)'''
    insert_values = [('admin', 'admin123'),('admin2', 'admin456'),('admin3', 'admin789')]
    for record in insert_values:
     cur.execute(insert_script, record)
    conn.commit()             # ✅ Saves the table to the database
    print("Table created successfully!")

    cur.execute("SELECT * FROM login")
    for record in cur.fetchall():
        print(record)

    delete_script = '''DELETE FROM login WHERE username = %s'''
    delete_value = ('admin2',)
    cur.execute(delete_script, delete_value)
    conn.commit()
    print("Record deleted successfully!")



except Exception as error:
    print("Error:", error)

finally:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()
    print("Connection closed.")