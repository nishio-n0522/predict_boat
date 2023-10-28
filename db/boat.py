from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

import db
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

    def __init__(self, boat_number: int, stadium: db.stadium.Stadium):
        self.boat_number = boat_number
        self.stadium = stadium

def get_or_create(session: Session, boat_number: int, stadium: db.stadium.Stadium, latest_top2finish_rate: float):
    boat = session.query(Boat).filter_by(boat_number=boat_number, stadium=stadium).first()
    if latest_top2finish_rate == 0 or boat == None:
        boat = Boat(boat_number, stadium)
        session.add(boat)
        session.commit()
    return boat

def get(session: Session, boat_number: int, stadium: db.stadium.Stadium):
    boat = session.query(Boat).filter_by(boat_number=boat_number, stadium=stadium).first()
    # if boat == None:
    #     boat = Boat(boat_number, stadium)
    #     session.add(boat)
    #     session.commit()
    return boat
