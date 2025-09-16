# # # app/extensions.py
# from langgraph.checkpoint.postgres import PostgresSaver
# import psycopg

DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
# conn = psycopg.connect(DB_URI,autocommit=True)
# # def connect():
# #     return psycopg.connect(DB_URI, autocommit=True)

# # checkpointer = PostgresSaver(connect)
# checkpointer = PostgresSaver(conn)
# # checkpointer.setup()  # make sure schema exists
# # app/extensions.py
import time
import psycopg
from langgraph.checkpoint.postgres import PostgresSaver

class HealthyPostgresSaver(PostgresSaver):
    def __init__(self, db_uri: str, max_retries: int = 5, backoff: float = 2.0):
        self.db_uri = db_uri
        self.conn = None
        self.max_retries = max_retries
        self.backoff = backoff  # seconds (exponential base)

    def _connect(self):
        """Try to connect with retries and exponential backoff."""
        delay = self.backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                return psycopg.connect(self.db_uri, autocommit=True)
            except psycopg.OperationalError as e:
                if attempt == self.max_retries:
                    raise
                print(f"[DB] Connection attempt {attempt} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2  # exponential backoff

    def _ensure_connection(self):
        if self.conn is None or self.conn.closed:
            self.conn = self._connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        except psycopg.OperationalError:
            if self.conn is not None:
                self.conn.close()
            self.conn = self._connect()

    def get_tuple(self, config):
        self._ensure_connection()
        return super().get_tuple(config)

    def put_tuple(self, config, value):
        self._ensure_connection()
        return super().put_tuple(config, value)


# use this instead
checkpointer = HealthyPostgresSaver(DB_URI)
