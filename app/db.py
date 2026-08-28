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
    """
    Inserts VIN data into the cache. If any of the fields are missing, they will be replaced with
    "MISSING" to satisfy the table schema.
    """
    # In case this information was somehow not available in the vPIC API response
    # This satisfies the table schema, since none of these fields are nullable
    if not make:
        make = "MISSING"
    if not model:
        model = "MISSING"
    if not model_year:
        model_year = "MISSING"
    if not body_class:
        body_class = "MISSING"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO VINcache (vin, make, model, model_year, body_class, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (vin, make, model, model_year, body_class),
        )

def fetch_vin_data(vin: str) -> dict[str, str] | None:
    """
    Returns the VIN data from the cache if it exists
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM VINcache WHERE vin = ?",
            (vin,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return {
            "vin": row["vin"],
            "make": row["make"],
            "model": row["model"],
            "model_year": row["model_year"],
            "body_class": row["body_class"],
            "timestamp": row["timestamp"],
        }

def delete_vin_data(vin: str) -> bool:
    """
    Deletes the VIN data from the cache if it exists
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM VINcache WHERE vin = ?",
            (vin,),
        )
        # If it existed, then 1 row would be deleted, setting rowcount to 1
        return cur.rowcount > 0
