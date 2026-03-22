import psycopg2

conn = psycopg2.connect(
    dbname="cyhackt",
    user="cyberuser",
    password="projet123",
    host="localhost",
    port="5432"
)

print("Connexion OK")

conn.close()
