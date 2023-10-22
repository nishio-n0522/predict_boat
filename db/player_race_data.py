from datetime import date as dt

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.db_setting import Base

class PlayerRaceData(Base):
    """
    選手個人データテーブル

    id: Integer [PK]
        選手登番

    player_id: Integer
        選手登板
    date: Date
        日時
    age: Integer
        年齢
    weight: Float
        体重
    branch_id: Integer [FK]
        支部id
    rank_id: Integer [FK]
        階級id

    """

    __tablename__ = 'player_race_data'
    __table_args__ = {
        'comment': '選手個人データ'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("player.id"))
    date = Column(Date)
    age = Column(Integer)
    weight = Column(Integer)
    branch_id = Column(Integer, ForeignKey("branch.id"))
    rank_id = Column(String, ForeignKey("rank.id"))

    player = relationship("Player", backref="player_race_data")
    branch = relationship("Branch", backref="player_race_data")
    rank = relationship("Rank", backref="player_race_data")

    def __init__(self, 
                 player_id: int,
                 date: dt,
                 age: int, 
                 weight: int, 
                 branch_id: int, 
                 rank_id: int):
        
        self.player_id = player_id
        self.date = date
        self.age = age
        self.weight = weight
        self.branch_id = branch_id
        self.rank_id = rank_id

def get_or_create_player(session: Session, player_id: int, date: dt, age: int, weight: int, branch_id: int, rank_id: int):
    player_race_data = session.query(PlayerRaceData).filter_by(player_id=player_id, date=date).one_or_none()
    if player_race_data is None:
        player_race_data = PlayerRaceData(player_id, date, age, weight, branch_id, rank_id)
        session.add(player_race_data)
        session.commit()
    return player_race_data