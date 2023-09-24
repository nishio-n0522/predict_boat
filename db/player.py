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

    __tablename__ = 'player'
    __table_args__ = {
        'comment': '選手テーブル'
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

    def __init__(self, 
                 id,
                 name, 
                 age, 
                 stadium_id, 
                 weight, 
                 rank, 
                 latest_national_win_rate, 
                 latest_national_top2finish_rate, 
                 latest_local_win_rate, 
                 latest_local_top2finish_rate):
        
        self.id = id
        self.name = name
        self.age = age
        self.stadium_id = stadium_id
        self.weight = weight
        self.rank = rank
        self.latest_national_win_rate = latest_national_win_rate
        self.latest_national_top2finish_rate = latest_national_top2finish_rate
        self.latest_local_win_rate = latest_local_win_rate
        self.latest_local_top2finish_rate = latest_local_top2finish_rate


if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)