from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class Stadium(Base):
    """
    ボートレース場テーブル

    stadium_id: Integer
        ボートレース場id
    name: Text
        名前
    motor_change_timing: Date
        モーター交換時期
    boat_change_timing: Date
        ボート交換時期

    """

    __tablename__ = 'stadium'
    __table_args__ = {
        'comment': '支部テーブル'
    }

    stadium_id = Column('stadium_id', Integer, primary_key=True)
    name = Column('name', Text)
    motor_change_timing = Column('motor_change_timing', Date)
    boat_change_timing = Column('boat_change_timing', Date)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)