from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "mysql+aiomysql://demo_user:demo_pass@localhost:3306/demo_db"

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)   

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session