import sqlite3
from database import database_path

print("DB path:", database_path.resolve())

conn = sqlite3.connect(database_path)
cur = conn.cursor()

cur.execute("DELETE FROM jobs")
conn.commit()
conn.close()

print("✅ jobs table cleared.")
