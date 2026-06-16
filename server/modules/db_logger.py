import asyncpg
from config import settings

connection_pool = None


# create a pool and create query table using create_query_table() function
async def init_db():
    global connection_pool
    connection_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
    )
    await create_query_table()


# create a query table with columns: id, query, answer, sources, created_at
async def create_query_table():
    async with connection_pool.transaction():
        await connection_pool.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)


# append to the query table with the given query, answer, and sources
async def log_query(query: str, answer: str, sources: list):
    async with connection_pool.transaction():
        await connection_pool.execute(
            """
            INSERT INTO query_log (query, answer, sources)
            VALUES ($1, $2, $3)
            """,
            query,
            answer,
            sources,
        )
