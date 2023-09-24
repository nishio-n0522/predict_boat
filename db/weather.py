from sqlalchemy import Column, Integer, String

from db.setting import Engine
from db.setting import Base

class Weather(Base):
    """
    天候テーブル

    id: Integer [PK]

    weather_name: String
        天候名

    """

    __tablename__ = 'weather'
    __table_args__ = {
        'comment': '天候'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    weather_name = Column(String)

    def __init__(self, weather_name):
        self.weather_name = weather_name


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)