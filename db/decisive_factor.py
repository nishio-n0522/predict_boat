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

if __name__ == "__main__":
    Base.metadata.create_all(bind=Engine)