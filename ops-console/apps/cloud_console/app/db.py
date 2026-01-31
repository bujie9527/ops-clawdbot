"""
SQLAlchemy 2.0：engine / sessionmaker / DeclarativeBase / get_db / ping_db。
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """依赖注入：获取数据库会话（yield session）。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> tuple[bool, str]:
    """
    执行 SELECT 1 检测数据库连通性。
    返回 (成功与否, 错误信息；成功时错误信息为空字符串)。
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, ""
    except Exception as e:
        return False, str(e)
