import sqlite3

conn = sqlite3.connect('petshop.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE pets ADD COLUMN allergies TEXT;")
    print("Column 'allergies' added to 'pets' table.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")

conn.commit()
conn.close()
