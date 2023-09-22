from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.ext.declarative import declarative_base

# 接続先DBの設定
DATABASE = 'sqlite:///db.sqlite3'

# Engine の作成
Engine = create_engine(
  DATABASE,
  echo=False
)
Base = declarative_base()

# Sessionの作成
_SessionFactory = scoped_session(
  Session(
    autocommit = False,
    autoflush = False,
    bind = Engine
  ) 
)

# modelで使用する
Base = declarative_base()
Base.query = _SessionFactory.query_property()

def session_factory():
    Base.metadata.create_all(Engine)
    return _SessionFactory()