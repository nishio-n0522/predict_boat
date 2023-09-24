import db




def add_race_result():
    session = db.setting.session_factory()
    

    session.commit()
    session.close()