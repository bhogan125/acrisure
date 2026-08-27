from datetime import datetime
import sqlite3

DB_PATH = "cache.db"

def init_db() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS VINcache (
                vin TEXT PRIMARY KEY,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                model_year TEXT NOT NULL,
                body_class TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        connection.commit()

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def insert_vin_data(vin: str, make: str, model: str,
                    model_year: str, body_class: str) -> None:
    with get_connection() as conn:
        cur = conn.cursor()
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            INSERT INTO VINcache (vin, make, model, model_year, body_class, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (vin, make, model, model_year, body_class),
        )
        pass

def fetch_vin_data(vin: str) -> dict[str, str] | None:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM VINcache WHERE vin = ?",
            (vin,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {  # TODO - I think row is a tuple, confirm
            "vin": row["vin"],
            "make": row["make"],
            "model": row["model"],
            "model_year": row["model_year"],
            "body_class": row["body_class"],
            "timestamp": row["timestamp"],
        }

def delete_vin_data(vin: str) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM VINcache WHERE vin = ?",
            (vin,),
        )
        # If it existed, then 1 row would be deleted, setting rowcount to 1
        return cur.rowcount > 0
