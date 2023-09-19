from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class Motor(Base):
    """
    モーターテーブル

    motor_number: Integer
        モーター番号
    stadium_id: Integer
        ボートレース場id
    date: Date
        レース日
    latest_top2finish_rate: Float
        最新2着以内率

    """

    __tablename__ = 'motor'
    __table_args__ = {
        'comment': 'モーターテーブル'
    }

    motor_number = Column('motor_number', Integer, primary_key=True)
    stadium_id = Column('stadium_id', Integer, primary_key=True)
    date = Column('date', Date, primary_key=True)
    latest_top2finish_rate = Column('latest_top2finish_rate', Float)

if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)