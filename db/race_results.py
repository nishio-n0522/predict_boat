from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from db.setting import Engine
from db.setting import Base

class User(Base):
    """
    レース結果
    """

    __tablename__ = 'race_results'
    __table_args__ = {
        'comment': '各レースの条件と結果のテーブル'
    }

    stadium_id = Column('stadium_id', Integer, primary_key=True)
    date = Column('date', DateTime, primary_key=True)
    race_index = Column('race_index', Integer, primary_key=True)
    series_name = Column('series_name', Text)
    weather = Column('weather', )


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)