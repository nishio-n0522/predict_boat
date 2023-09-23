from sqlalchemy import Column, Integer, String

from db.setting import Engine
from db.setting import Base

class Rank(Base):
    """
    級別テーブル

    id: Integer [PK]

    rank_name: String
        階級

    """

    __tablename__ = 'rank'
    __table_args__ = {
        'comment': '級別'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    rank_name = Column(String)

if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)