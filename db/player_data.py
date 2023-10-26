import datetime as dt

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session

from db.player import Player
from db.rank import Rank
from db.branch import Branch
from db.db_setting import Base

class PlayerData(Base):
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

    __tablename__ = 'player_data'
    __table_args__ = {
        'comment': '選手個人データ'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("player.id"), index=True)
    date = Column(Date, index=True)
    age = Column(Integer)
    weight = Column(Integer)
    branch_id = Column(Integer, ForeignKey("branch.id"))
    rank_id = Column(Integer, ForeignKey("rank.id"))

    player = relationship("Player", backref="player_data")
    branch = relationship("Branch", backref="player_data")
    rank = relationship("Rank", backref="player_data")

    def __init__(self, 
                 player: Player,
                 date: dt.date,
                 age: int, 
                 weight: int, 
                 branch: Branch, 
                 rank: Rank):
        
        self.player = player
        self.date = date
        self.age = age
        self.weight = weight
        self.branch = branch
        self.rank = rank

def create(session: Session, player: Player, date: dt.date, age: int, weight: int, branch: Branch, rank: Rank):
    player_data = session.query(PlayerData).filter_by(player=player, date=date).one_or_none()
    if player_data is None:
        player_data = PlayerData(player, date, age, weight, branch, rank)
        session.add(player_data)
        # session.commit()