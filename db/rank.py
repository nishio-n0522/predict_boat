from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import Session

from db.db_setting import Base

class Rank(Base):
    """
    階級テーブル

    id: Integer [PK]

    rank_name: String
        階級

    """

    __tablename__ = 'rank'
    __table_args__ = {
        'comment': '階級'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    rank_name = Column(String)

    def __init__(self, rank_name):
        self.rank_name = rank_name

def get_or_create(session: Session, rank_name: str):
    rank = session.query(Rank).filter_by(rank_name=rank_name).one_or_none()
    if rank is None:
        rank = Rank(rank_name)
        session.add(rank)
        session.commit()
    return rank
