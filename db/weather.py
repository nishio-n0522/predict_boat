from sqlalchemy import Column, Integer, String, Float, Date, Text, Numeric

from db.setting import Engine
from db.setting import Base

class Weather(Base):
    """
    天気テーブル

    weather_id: Integer
        天気id
    weather_type: Text
        天気種類

    """

    __tablename__ = 'weather'
    __table_args__ = {
        'comment': '天気の種類を管理するテーブル'
    }

    weather_id = Column('weather_id', Integer, primary_key=True)
    weather_type = Column('weather_type', Text)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)