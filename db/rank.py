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

    def __init__(self, rank_name):
        self.rank_name = rank_name

def get_or_create_rank(session, rank_name):
    rank = session.query(Rank).filter_by(rank_name).one_or_none()
    if rank is None:
        rank = Rank(rank_name)
        session.add(rank)
        session.commit()
    return rank


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)