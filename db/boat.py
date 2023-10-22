from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.db_setting import Base

class Boat(Base):
    """
    ボートテーブル

    id: Integer [PK]

    boat_number: Integer
        ボート番号
    stadium_id: Integer [FK]
        支部id

    """

    __tablename__ = 'boat'
    __table_args__ = {
        'comment': 'ボート'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    boat_number = Column(Integer)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))

    stadium = relationship("Stadium", backref="boat")

    def __init__(self, boat_number, stadium_id):
        self.boat_number = boat_number
        self.stadium_id = stadium_id

# def get_or_create_rank(session, *args):
#     rank = session.query(Boat).filter_by(boat).one_or_none()
#     if rank is None:
#         rank = Rank(rank_name)
#         session.add(rank)
#         session.commit()
#     return rank

