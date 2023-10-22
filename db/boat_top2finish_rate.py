import datetime as dt

from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import relationship

import db
from db.db_setting import Base


class BoatTop2finishRate(Base):
    """
    ボート2着以内率テーブル

    id: Integer [PK]

    boat_number: Integer
        ボート番号
    race_date: Date
        レース開催日
    latest_top2finish_rate: Float
        最新2着以内率

    """

    __tablename__ = 'boat_top2finish_rate'
    __table_args__ = {
        'comment': 'ボート2着以内率'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    boat_id = Column(Integer, ForeignKey("boat.id"))
    date = Column(Date)
    latest_top2finish_rate = Column(Float)

    boat = relationship("Boat", backref="boat_top2finish_rate")

    def __init__(self, boat: db.boat.Boat, date: dt.date, latest_top2finish_rate: float):
        self.boat = boat
        self.date = date
        self.latest_top2finish_rate = latest_top2finish_rate

def create(session: Session, boat: db.boat.Boat, date: dt.date, latest_top2finish_rate: float):
    boat_top2finish_rate = session.query(BoatTop2finishRate).filter_by(boat=boat, date=date).one_or_none()
    if boat_top2finish_rate is None:
        boat_top2finish_rate = BoatTop2finishRate(boat, date, latest_top2finish_rate)
        session.add(boat_top2finish_rate)
        session.commit()
