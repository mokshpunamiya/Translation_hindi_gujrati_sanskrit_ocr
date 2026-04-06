import psycopg2
from config.settings import Config

def check_db():
    try:
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dbname='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (Config.DB_NAME,))
        exists = cursor.fetchone()
        if exists:
            print("DB_STATUS: EXIST")
        else:
            print("DB_STATUS: NOT_EXIST")
        conn.close()
    except Exception as e:
        print(f"DB_STATUS: ERROR - {e}")

if __name__ == "__main__":
    check_db()
