from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import os
import sys
import psycopg2
import pandas as pd
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from dotenv import load_dotenv


# Add logging
import logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
logger = logging.getLogger(__name__)
load_dotenv()

# ---------- Database ----------
class Database:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        self.conn = None
    
    def connect(self) -> "Database":
        try:
            logger.info(f"Connecting to database...")
            self.conn = psycopg2.connect(self.conn_str)
            logger.info("Database connected successfully")
            return self
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self) -> None:
        if self.conn:
            self.conn.close()
            logger.info("Database disconnected")
    
    def query(self, sql: str) -> pd.DataFrame:
        try:
            logger.info(f"Executing query: {sql[:100]}...")
            with self.conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
            logger.info(f"Query returned {len(rows)} rows")
            return pd.DataFrame(rows, columns=cols)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

# ---------- Lifespan context ----------
@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    logger.info("Starting server lifespan")
    conn_str = os.environ.get("PGCONN_STRING")
    if not conn_str:
        logger.error("PGCONN_STRING not set")
        raise ValueError("PGCONN_STRING environment variable not set")
    
    logger.info("Initializing database connection")
    db = Database(conn_str).connect()
    try:
        logger.info("Yielding app context")
        yield AppContext(db=db)
    finally:
        logger.info("Cleaning up database connection")
        db.disconnect()

# ---------- MCP server ----------
mcp = FastMCP("My App", lifespan=app_lifespan)

# ---------- Tool ----------
@mcp.tool(
    name="run_postgis_query",
    description="Run a SQL query on PostGIS and return a table"
)
def run_postgis_query(
    ctx: Context[ServerSession, AppContext],
    sql: str
) -> list[dict]:
    logger.info(f"Tool called with SQL: {sql[:100]}...")
    try:
        df = ctx.request_context.lifespan_context.db.query(sql)
        result = df.to_dict(orient="records")
        logger.info(f"Returning {len(result)} records")
        return result
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting MCP server")
    mcp.run()



