from sqlalchemy import Column, Integer, String

from db.setting import Engine
from db.setting import Base

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

def get_or_create_decisive_factor(session, decisive_factor_name):
    decisive_factor = session.query(DecisiveFactor).filter_by(decisive_factor_name).one_or_none()
    if decisive_factor is None:
        decisive_factor = DecisiveFactor(decisive_factor)
        session.add(decisive_factor)
        session.commit()
    return decisive_factor

if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)