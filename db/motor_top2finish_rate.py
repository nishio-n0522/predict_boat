import datetime as dt

from sqlalchemy import Column, Integer, Float, ForeignKey, Date
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import relationship

import db
from db.db_setting import Base


class MotorTop2finishRate(Base):
    """
    モーター2着以内率テーブル

    id: Integer [PK]

    motor_number: Integer
        モーター番号
    date: Date
        レース開催日
    latest_top2finish_rate: Float
        最新2着以内率

    """

    __tablename__ = 'motor_top2finish_rate'
    __table_args__ = {
        'comment': 'モーター2着以内率'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    motor_id = Column(Integer, ForeignKey("motor.id"))
    date = Column(Date)
    latest_top2finish_rate = Column(Float)

    motor = relationship("Motor", backref="motor_top2finish_rate")

    def __init__(self, motor: db.motor.Motor, date: dt.date, latest_top2finish_rate: float):
        self.motor = motor
        self.date = date
        self.latest_top2finish_rate = latest_top2finish_rate

def create(session: Session, motor: db.motor.Motor, date: dt.date, latest_top2finish_rate: float):
    motor_top2finish_rate = session.query(MotorTop2finishRate).filter_by(motor=motor, date=date).one_or_none()
    if motor_top2finish_rate is None:
        motor_top2finish_rate = MotorTop2finishRate(motor, date, latest_top2finish_rate)
        session.add(motor_top2finish_rate)
        session.commit()
