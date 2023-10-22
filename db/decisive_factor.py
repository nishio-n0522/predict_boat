from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.session import Session

from db.db_setting import Engine
from db.db_setting import Base

class DecisiveFactor(Base):
    """
    決まり手テーブル

    id: Integer [PK]

    decisive_factor_name: String
        決まり手

    """

    __tablename__ = 'decisive_factor'
    __table_args__ = {
        'comment': '決まり手'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    decisive_factor_name = Column(String)

    def __init__(self, decisive_factor_name):
        self.decisive_factor_name = decisive_factor_name

def get_or_create(session: Session, decisive_factor_name: str):
    decisive_factor = session.query(DecisiveFactor).filter_by(decisive_factor_name=decisive_factor_name).one_or_none()
    if decisive_factor is None:
        decisive_factor = DecisiveFactor(decisive_factor_name)
        session.add(decisive_factor)
        session.commit()
    return decisive_factor
