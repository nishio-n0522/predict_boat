import os
import time
from pathlib import Path
from typing import Tuple
import datetime as dt
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager

from pyparsing import Word, nums, Literal, ParseResults, Combine, Optional, alphas, Group, oneOf
from sqlalchemy.orm.session import Session

from db.db_setting import session_factory
import db

PARAM_SEPARATOR_LINE = "-------------------------------------------------------------------------------"
RESULT_SEPARATOR_LINE = "-------------------------------------------------------------------------------"


@contextmanager
def transaction(session: Session):
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

def register_race_result_for_db(date: dt.date, result_content: list[str]):
    is_stadium = False
    is_refund_data = False
    is_each_result_info = False

    is_no_game = False

    each_boat_result_list = []

    session = session_factory()
    t0 = time.perf_counter()
    for i, each_line in enumerate(result_content):
        if "レース不成立" in each_line:
            is_no_game = True
            print("happen no game")
            return

        if "KBGN" in each_line:
            is_stadium = True
            stadium_id = int(each_line[0:2])
            continue

        if is_stadium:
            stadium_name = remove_all_blank(each_line[0:3])
            stadium = db.stadium.get_or_create(session, stadium_id, stadium_name)
            is_stadium = False
            continue

        if RESULT_SEPARATOR_LINE in each_line:
            each_boat_data_list = []
            each_race_results_dict = {
                "date": date,
                "stadium": stadium
            }

            race_meta_info_line = result_content[i-2]
            decisive_factor_line = result_content[i-1]

            each_race_results_dict["race_index"]= int(remove_all_blank(race_meta_info_line[0:4]))
            each_race_results_dict["race_name"] = str(remove_all_blank(race_meta_info_line[12:20]))

            special_rule = str(remove_all_blank(race_meta_info_line[20:31]))
            if special_rule == "":
                special_rule = None
            each_race_results_dict["special_rule"] = db.special_rule.get_or_create(session, special_rule)

            H_index = race_meta_info_line[31:].find("H")
            race_meta_info_line = race_meta_info_line[31+H_index:]

            each_race_results_dict["weather"] = db.weather.get_or_create(session, str(remove_all_blank(race_meta_info_line[8:11])))

            each_race_results_dict["wind_direction"] = db.wind_direction.get_or_create(session, str(remove_all_blank(race_meta_info_line[15:17])))
            each_race_results_dict["wind_speed"] = int(remove_all_blank(race_meta_info_line[17:20]))
            each_race_results_dict["wave_height"] = int(remove_all_blank(race_meta_info_line[24:28]))

            each_race_results_dict["decisive_factor"] = db.decisive_factor.get_or_create(session, str(remove_all_blank(decisive_factor_line[49:])))

            is_each_result_info = True
            continue

        if "単勝" in each_line:
            is_refund_data = True

            if "不成立" in each_line:
                refund = None
            elif remove_all_blank(each_line[0:12]) == "": 
                refund = int(remove_all_blank(each_line[23:32]))
            else:
                refund = int(remove_all_blank(each_line[23:29]))

            if refund == "":
                refund = None

            each_race_results_dict["win_refund"] = refund
            
            continue

        if "KEND" in each_line:
            is_stadium = False
            is_each_result_info = False
            continue

        if is_each_result_info:
            if each_line == "\n":
                is_each_result_info = False
                continue

            each_boat_data_dict = {}
            try:
                order_of_arrival = int(remove_all_blank(each_line[0:4]))
            except Exception as e:
                order_of_arrival = 99
            each_boat_data_dict["order_of_arrival"] = int(order_of_arrival)
            each_boat_data_dict["boat_number"] = int(remove_all_blank(each_line[4:7]))

            each_boat_data_dict["player"] = db.player.get(session, id=int(remove_all_blank(each_line[8:12])))
            each_boat_data_dict["motor"] = db.motor.get(session, int(remove_all_blank(each_line[21:24])), stadium)
            each_boat_data_dict["boat"] = db.boat.get(session, int(remove_all_blank(each_line[24:29])), stadium)

            try:
                each_boat_data_dict["sample_time"] = float(remove_all_blank(each_line[29:35]))
            except Exception as e:
                each_boat_data_dict["sample_time"] = None

            try:
                each_boat_data_dict["starting_order"] = int(remove_all_blank(each_line[35:39]))
            except Exception as e:
                each_boat_data_dict["starting_order"] = None

            try:
                each_boat_data_dict["start_timing"] = float(remove_all_blank(each_line[39:47]))
            except Exception as e:
                each_boat_data_dict["start_timing"] = None
            
            try:
                each_boat_data_dict["race_time"] = dt.time(minute=int(each_line[47:53]), second=int(each_line[54:56]), microsecond=int(each_line[57:58])*100000)
            except Exception as e:
                each_boat_data_dict["race_time"] = None
            
            each_boat_data_list.append(each_boat_data_dict)

            continue


        if is_refund_data:
            if each_line == "\n":
                is_refund_data = False

                if not is_no_game:
                    each_race = db.each_race_results.create_and_get(session, **each_race_results_dict)
                    each_boat_result_list.append({"each_race": each_race, "each_boat_data": each_boat_data_list})

                continue

            if "不成立" in each_line:
                refund = None
            elif remove_all_blank(each_line[0:12]) == "": 
                refund = int(remove_all_blank(each_line[23:32]))
            else:
                refund = int(remove_all_blank(each_line[23:29]))

            if refund == "":
                refund = None

            if remove_all_blank(each_line[0:12]) == "複勝":
                each_race_results_dict["place_refund1"] = refund
                try:
                    each_race_results_dict["place_refund2"] = int(remove_all_blank(each_line[33:]))
                except Exception as e:
                    pass
            elif remove_all_blank(each_line[0:12]) == "２連単":
                each_race_results_dict["perfecta_refund"] = refund
            elif remove_all_blank(each_line[0:12]) == "２連複":
                each_race_results_dict["quinella_refund"] = refund
            elif remove_all_blank(each_line[0:12]) == "拡連複":
                each_race_results_dict["boxed_quinella_refund1"] = refund
            elif remove_all_blank(each_line[0:12]) == "３連単":
                each_race_results_dict["trifecta_refund"] = refund
            elif remove_all_blank(each_line[0:12]) == "３連複":
                each_race_results_dict["boxed_trifecta_refund"] = refund
            else:
                if "boxed_quinella_refund2" not in each_race_results_dict.keys():
                    each_race_results_dict["boxed_quinella_refund2"] = refund
                elif "boxed_quinella_refund3" not in each_race_results_dict.keys():
                    each_race_results_dict["boxed_quinella_refund3"] = refund

            continue

    for each_boat_result in each_boat_result_list:
        each_race = each_boat_result["each_race"]
        for each_boat_data_dict in each_boat_result["each_boat_data"]:
            each_boat_data_dict["each_race_result"] = each_race
            each_boat_data = db.each_boat_data.EachBoatData(**each_boat_data_dict)
            session.add(each_boat_data)
    session.commit()

    print("処理時間", time.perf_counter() - t0)
    session.close()
            

def register_race_param_for_db(date:dt.date, param_content_list: list[str]):
    is_stadium = False
    is_each_boat_info = False
    separator_line_count = 0

    player_dict = {"player_id": [], "player_name": []}

    player_rank_list = []
    player_branch_list = []

    player_data_dict = {
        "player_id": [],
        "date": [], 
        "player_age": [], 
        "player_weight": [], 
        "branch_name": [], 
        "rank_name": []
    }

    player_national_win_rate_dict = {
        "player_id": [],
        "date": [], 
        "player_national_win_rate": [], 
        "player_national_top2finish_rate": []
    }

    player_local_win_rate_dict = {
        "player_id": [],
        "stadium": [],
        "date": [], 
        "player_local_win_rate": [], 
        "player_local_top2finish_rate": []
    }

    motor_dict = {
        "motor_number": [],
        "stadium": [],
        "motor_top2finish_rate": []
    }

    boat_dict = {
        "boat_number": [],
        "stadium": [],
        "boat_top2finish_rate": []
    }


    session = session_factory()
    t0 = time.perf_counter()
    for each_line in param_content_list:
        if "BBGN" in each_line:
            is_stadium = True
            stadium_id = int(each_line[0:2])
            continue

        if is_stadium:
            stadium_name = remove_all_blank(each_line[6:9])
            stadium = db.stadium.get_or_create(session, stadium_id, stadium_name)
            is_stadium = False
            continue

        if PARAM_SEPARATOR_LINE in each_line:
            separator_line_count += 1

            if separator_line_count == 2:
                is_each_boat_info = True
                separator_line_count = 0
            continue

        if not is_each_boat_info:
            continue

        if each_line == "\n":
            is_each_boat_info = False
            continue
        elif "BEND" in each_line:
            is_stadium = False
            is_each_boat_info = False
            continue

        player_id = int(remove_all_blank(each_line[2:6]))
        if not player_id in player_dict["player_id"]:
            player_dict["player_id"].append(player_id)
            player_dict["player_name"].append(str(remove_all_blank(each_line[6:10])))

        player_rank = str(remove_all_blank(each_line[16:18]))
        if not player_rank in player_rank_list:
            player_rank_list.append(player_rank)

        player_branch = str(remove_all_blank(each_line[12:14]))
        if not player_branch in player_branch_list:
            player_branch_list.append(player_branch)
            
        player_data_dict["player_id"].append(player_id)
        player_data_dict["date"].append(date)
        player_data_dict["player_age"].append(int(remove_all_blank(each_line[10:12])))
        player_data_dict["player_weight"].append(int(remove_all_blank(each_line[14:16])))
        player_data_dict["branch_name"].append(player_branch)
        player_data_dict["rank_name"].append(player_rank)

        player_national_win_rate_dict["player_id"].append(player_id)
        player_national_win_rate_dict["date"].append(date)
        player_national_win_rate_dict["player_national_win_rate"].append(float(remove_all_blank(each_line[18:23])))
        player_national_win_rate_dict["player_national_top2finish_rate"].append(float(remove_all_blank(each_line[23:29])))

        player_local_win_rate_dict["player_id"].append(player_id)
        player_local_win_rate_dict["date"].append(date)
        player_local_win_rate_dict["stadium"].append(stadium)
        player_local_win_rate_dict["player_local_win_rate"].append(float(remove_all_blank(each_line[29:35])))
        player_local_win_rate_dict["player_local_top2finish_rate"].append(float(remove_all_blank(each_line[35:41])))
        

        motor_number = int(remove_all_blank(each_line[41:44]))
        motor_top2finish_rate = float(remove_all_blank(each_line[44:50])) 
        motor_dict["motor_number"].append(motor_number)
        motor_dict["stadium"].append(stadium)
        motor_dict["motor_top2finish_rate"].append(motor_top2finish_rate)

        boat_number = int(remove_all_blank(each_line[50:53]))
        boat_top2finish_rate = float(remove_all_blank(each_line[53:59]))
        boat_dict["boat_number"].append(boat_number)
        boat_dict["stadium"].append(stadium)
        boat_dict["boat_top2finish_rate"].append(boat_top2finish_rate)


    with transaction(session) as session:
        for i in range(len(player_dict["player_id"])):
            player_id = player_dict["player_id"][i]
            player_name = player_dict["player_name"][i]
            player = session.query(db.player.Player).filter_by(id=player_id).one_or_none()
            if player is None:
                player = db.player.Player(player_id, player_name)
                session.add(player)

    with transaction(session) as session:
        for player_rank in player_rank_list:
            rank = session.query(db.rank.Rank).filter_by(rank_name=player_rank).one_or_none()
            if not rank:
                rank = db.rank.Rank(player_rank)
                session.add(rank)

    with transaction(session) as session:
        for player_branch in player_branch_list:
            branch = session.query(db.branch.Branch).filter_by(branch_name=player_branch).one_or_none()
            if not branch:
                branch = db.branch.Branch(branch_name=player_branch)
                session.add(branch)
    
    with transaction(session) as session:
        for i in range(len(player_data_dict["player_id"])):
            player = session.query(db.player.Player).filter_by(id=player_data_dict["player_id"][i]).one_or_none()
            date = player_data_dict["date"][i]
            player_age = player_data_dict["player_age"][i]
            player_weight = player_data_dict["player_weight"][i]
            branch = session.query(db.branch.Branch).filter_by(branch_name=player_data_dict["branch_name"][i]).one_or_none()
            rank = session.query(db.rank.Rank).filter_by(rank_name=player_data_dict["rank_name"][i]).one_or_none()
            player_data = session.query(db.player_data.PlayerData).filter_by(player=player, date=date).one_or_none()
            if player_data is None:
                player_data = db.player_data.PlayerData(player, date, player_age, player_weight, branch, rank)
                session.add(player_data)
                
    with transaction(session) as session:
        for i in range(len(player_national_win_rate_dict["player_id"])):
            player = session.query(db.player.Player).filter_by(id=player_national_win_rate_dict["player_id"][i]).one_or_none()
            date = player_national_win_rate_dict["date"][i]
            player_national_win_rate_value = player_national_win_rate_dict["player_national_win_rate"][i]
            player_national_top2finish_rate = player_national_win_rate_dict["player_national_top2finish_rate"][i]
            player_national_win_rate = session.query(db.player_national_win_rate.PlayerNationalWinRate).filter_by(player=player, race_date=date).one_or_none()
            if not player_national_win_rate:
                player_national_win_rate = db.player_national_win_rate.PlayerNationalWinRate(player, date, player_national_win_rate_value, player_national_top2finish_rate)
                session.add(player_national_win_rate)
    
    with transaction(session) as session:
        for i in range(len(player_local_win_rate_dict["player_id"])):
            player = session.query(db.player.Player).filter_by(id=player_local_win_rate_dict["player_id"][i]).one_or_none()
            stadium = player_local_win_rate_dict["stadium"][i]
            date = player_local_win_rate_dict["date"][i]
            player_local_win_rate_value = player_local_win_rate_dict["player_local_win_rate"][i]
            player_local_top2finish_rate = player_local_win_rate_dict["player_local_top2finish_rate"][i]
            player_local_win_rate = session.query(db.player_local_win_rate.PlayerLocalWinRate).filter_by(player=player, race_date=date).one_or_none()
            if not player_local_win_rate:
                player_local_win_rate = db.player_local_win_rate.PlayerLocalWinRate(player, stadium, date, player_local_win_rate_value, player_local_top2finish_rate)
                session.add(player_local_win_rate)

    with transaction(session) as session:
        for i in range(len(motor_dict["motor_number"])):
            motor_number = motor_dict["motor_number"][i]
            stadium = motor_dict["stadium"][i]
            motor = session.query(db.motor.Motor).filter_by(motor_number=motor_number, stadium=stadium).first()
            if motor is None or motor_dict["motor_top2finish_rate"][i] == 0:
                motor = db.motor.Motor(motor_number=motor_number, stadium=stadium)
                session.add(motor)
    
    with transaction(session) as session:
        for i in range(len(motor_dict["motor_number"])):
            motor_number = motor_dict["motor_number"][i]
            stadium = motor_dict["stadium"][i]
            motor = session.query(db.motor.Motor).filter_by(motor_number=motor_number, stadium=stadium).first()
            motor_top2finish_rate = session.query(db.motor_top2finish_rate.MotorTop2finishRate).filter_by(motor=motor, date=date).first()
            if not motor_top2finish_rate:
                motor_top2finish_rate = db.motor_top2finish_rate.MotorTop2finishRate(motor, date, motor_dict["motor_top2finish_rate"][i])
                session.add(motor_top2finish_rate)
                

    with transaction(session) as session:
        for i in range(len(boat_dict["boat_number"])):
            boat_number = boat_dict["boat_number"][i]
            stadium = boat_dict["stadium"][i]
            boat = session.query(db.boat.Boat).filter_by(boat_number=boat_number, stadium=stadium).first()
            if boat is None or boat_dict["boat_top2finish_rate"][i] == 0:
                boat = db.boat.Boat(boat_number=boat_number, stadium=stadium)
                session.add(boat)
    
    with transaction(session) as session:
        for i in range(len(boat_dict["boat_number"])):
            boat_number = boat_dict["boat_number"][i]
            stadium = boat_dict["stadium"][i]
            boat = session.query(db.boat.Boat).filter_by(boat_number=boat_number, stadium=stadium).first()
            boat_top2finish_rate = session.query(db.boat_top2finish_rate.BoatTop2finishRate).filter_by(boat=boat, date=date).first()
            if not boat_top2finish_rate:
                boat_top2finish_rate = db.boat_top2finish_rate.BoatTop2finishRate(boat, date, boat_dict["boat_top2finish_rate"][i])
                session.add(boat_top2finish_rate)
    
    print("処理時間", time.perf_counter() - t0)
    session.close()


def remove_all_blank(text:str) -> str:
    text = text.replace(" ", "")
    text = text.replace("　", "")
    return text.replace("\u3000", "")

if __name__=='__main__':
    base_dir = "uncompressed_data"
    # base_dir = "samples"
    file_list = list(Path(f"{base_dir}/competitive_record").glob("*.txt"))

    for target_file in file_list[0:100]:
        with open(target_file, "r", encoding="utf-8") as f:
            result_content = f.readlines()

        file_name = str(target_file.stem)
        this_race_date = dt.date(year=int(file_name[1:3])+2000, month=int(file_name[3:5]), day=int(file_name[5:7]))

        param_file = Path(f"./{base_dir}") / "race_parameters" / f"b{file_name[1:]}.txt"
        with open(param_file, "r", encoding="utf-8") as f:
            param_content = f.readlines()

        print("start", target_file, param_file)

        register_race_param_for_db(this_race_date, param_content)

        register_race_result_for_db(this_race_date, result_content)




