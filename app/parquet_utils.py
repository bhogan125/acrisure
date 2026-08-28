import pyarrow as pa
import pyarrow.parquet as pq

from .db import get_connection


# Adapted from a google search on best ways to write sqlite3 data to parquet in python
def export_to_parquet(file_path: str) -> None:
    """
    Exports the VINcache table to a Parquet file by fetching all rows from the database,
    transposing them into columnar data, converting that to a PyArrow table, and writing that
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM VINcache")
        rows = cur.fetchall()
        # Per the Py3 docs, cursor.description is a 7-tuple where only the first item is filled in
        cols = [description[0] for description in cur.description]

        data_dict = {cols[i]: [row[i] for row in rows] for i in range(len(cols))}
        table = pa.table(data_dict)

        pq.write_table(table, file_path)
