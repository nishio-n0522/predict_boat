from sqlalchemy import Column, Integer, String, Float, ForeignKey

from db.setting import Engine
from db.setting import Base

class Player(Base):
    """
    選手テーブル

    id: Integer [PK]
        選手登番

    name: String
        名前
    age: Integer
        年齢
    stadium_id: Integer [FK]
        支部id
    weight: Float
        体重
    rank_id: Integer [FK]
        級別id
    latest_national_win_rate: Float
        最新全国勝率
    latest_national_top2finish_rate: Float
        最新全国2着以内勝率
    latest_local_win_rate: Float
        最新当地勝率
    latest_local_top2finish_rate: Float
        最新当地2着以内勝率

    """

    __tablename__ = 'weather'
    __table_args__ = {
        'comment': '天気の種類を管理するテーブル'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    stadium_id = Column(Integer, ForeignKey("stadium.id"))
    weight = Column(Float)
    rank = Column(String, ForeignKey("rank.id"))
    latest_national_win_rate = Column(Float)
    latest_national_top2finish_rate = Column(Float)
    latest_local_win_rate = Column(Float)
    latest_local_top2finish_rate = Column(Float)


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)