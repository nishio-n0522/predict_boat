from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import Session

from db.db_setting import Base

class Player(Base):
    """
    選手テーブル

    id: Integer [PK]
        選手登番

    name: String
        名前

    """

    __tablename__ = 'player'
    __table_args__ = {
        'comment': '選手テーブル'
    }

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, 
                 id,
                 name):
        
        self.id = id
        self.name = name

def get_or_create(session: Session, id: int, name: str):
    player = session.query(Player).filter_by(id=id).one_or_none()
    if player is None:
        player = Player(id, name)
        session.add(player)
        session.commit()
    return player

def get(session: Session, id: int):
    player = session.query(Player).filter_by(id=id).one_or_none()
    return player