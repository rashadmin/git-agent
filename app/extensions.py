# # app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

# DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
# conn = psycopg.connect(DB_URI,autocommit=True)
# def connect():
#     return 
# psycopg.connect(DB_URI, autocommit=True)

# checkpointer = PostgresSaver(connect)
# checkpointer = PostgresSaver(conn)
# checkpointer.setup()  # make sure schema exists
# app/extensions.py
import psycopg
from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
import logging

logging.basicConfig(level=logging.INFO)
# from flask import current_app
# DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"
# pool = ConnectionPool(DB_URI, open=True,min_size=10,max_lifetime=600,max_size=15,
#                       kwargs={"prepare_threshold": None, "row_factory": dict_row, 'autocommit':True,
#     "keepalives": 1,
#     "keepalives_idle": 30,
#     "keepalives_interval": 10,
#     "keepalives_count": 3
# })

# from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
# from psycopg.errors import OperationalError, DatabaseError
import logging
from contextlib import contextmanager
from psycopg.errors import OperationalError
from psycopg_pool import ConnectionPool, PoolTimeout
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row


# Database connection URI
DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"

# Connection pool (optimized for single-loop usage)
pool = ConnectionPool(
    DB_URI,
    open=True,
    min_size=4,
    max_size=10,
    max_idle=300,
    max_lifetime=600,  # recycle before Supabase kills
    kwargs={
        "prepare_threshold": None,
        "row_factory": dict_row,
        "autocommit": True,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 3,
    }
)

# Cache for compiled graph
_cached_graph = None


@contextmanager
def graph_context():
    """
    Provides a compiled graph with PostgresSaver checkpointing.
    - Graph is compiled once and cached.
    - A fresh connection is acquired each time from the pool.
    - Errors like SSL drops are handled by retry wrapper around invocation.
    """
    global _cached_graph
    from app.agent_call.graph import builder

    logging.info("[POOL] Waiting for connection...")
    with pool.connection() as conn:
        try:
            logging.info(f"[POOL] acquired conn={id(conn)} stats={pool.get_stats()}")

            # Compile graph once if not cached
            if _cached_graph is None:
                logging.info("[GRAPH] Compiling graph (first time)...")
                _cached_graph = builder.compile(checkpointer=PostgresSaver(conn))

            # Fresh checkpointer for this iteration
            checkpointer = PostgresSaver(conn)
            graph = builder.compile(checkpointer=checkpointer)

            yield graph

        except Exception as e:
            logging.error(f"[POOL] Error in graph_context: {e}", exc_info=True)
            raise
        finally:
            logging.info(f"[POOL] released conn={id(conn)} stats={pool.get_stats()}")


# Define what we consider transient and retryable
def is_retryable_error(exception: Exception) -> bool:
    transient_errors = (
        OperationalError,      # DB dropped connection
        PoolTimeout,           # couldn't get a connection
    )
    # string-matching for pipeline / SSL errors
    msg = str(exception).lower()
    if any(keyword in msg for keyword in [
        "ssl connection", 
        "connection has been closed",
        "pipeline [bad]",
        "flush request failed",
    ]):
        return True
    return isinstance(exception, transient_errors)


# Retry wrapper for graph invocation
@retry(
    stop=stop_after_attempt(3),  # try up to 3 times
    wait=wait_fixed(2),          # wait 2s between retries
    retry=retry_if_exception(is_retryable_error),
    reraise=True,
)
def run_graph(graph, data, config):
    """
    Invokes the graph with retry logic for transient DB/SSL errors.
    """
    return graph.invoke(data, config=config)




# @retry(
#     retry=retry_if_exception_type((OperationalError, DatabaseError)),
#     stop=stop_after_attempt(3),    # retry up to 3 times
#     wait=wait_fixed(2),            # wait 2s between retries
#     reraise=True
# )
# @contextmanager
# def graph_context():
#     logging.info("[POOL] Waiting for connection...")
#     from app.agent_call.graph import builder
#     with pool.connection() as conn:
#         try:
#             logging.info(f"[POOL] acquired conn={id(conn)} open={pool.get_stats()}")
#         # conn = psycopg.connect(DB_URI, autocommit=True, prepare_threshold=None, row_factory=dict_row)
#             checkpointer = PostgresSaver(conn)
#             yield builder.compile(checkpointer=checkpointer)
#         finally:
#             conn.close()
#     logging.info(f"[POOL] released conn={id(conn)} open={pool.get_stats()}")
# def graph_context():
#     from app.agent_call.graph import builder
#     with pool.connection() as conn:

#         try:
#             conn.prepare_threshold = None
#             checkpointer = PostgresSaver(conn)
#             graph = builder.compile(checkpointer=checkpointer)
#             yield graph
#         finally:
#             print(None)

    # try:
    #     checkpointer = PostgresSaver(conn)
    #     graph = builder.compile(checkpointer=checkpointer)
    #     print('Started')
    #     yield graph
    # finally:
    #     conn.close()
    #     print('Closed')
