import os
from pathlib import Path
from typing import Tuple
import datetime as dt

from pyparsing import Word, nums, Literal, ParseResults, Combine, Optional, alphas, Group, oneOf
from sqlalchemy.orm.session import Session

from db.db_setting import session_factory
import db


def get_each_race_list(text: str) -> list[list[Tuple[ParseResults, int, int]]]:
    search_pattern = "KBGN"
    kbgn = Word(nums, exact=2) + Literal(search_pattern)
    return list(kbgn.scanString(text))

def get_each_target_text_for_result(result_content: str, start_delimiter: list[Tuple[ParseResults, int, int]]) -> str:
    search_pattern = "KEND"
    start_index = start_delimiter[2]+1
    end_delimiter = Literal(start_delimiter[0][0]+search_pattern)
    end_match = end_delimiter.scanString(result_content)
    return result_content[start_index:list(end_match)[0][1]-1]

def extract_wind_direction_and_speed(text) -> str:
    directions = ["北", "南", "東", "西", "北東", "北西", "南東", "南西"]
    direction = oneOf(directions)

    distance = Combine(Word(nums) + Optional("m"))
    pattern = Group(direction + distance)
    parsed = pattern.parseString(text)
    return parsed[0][0], parsed[0][1]

def get_race_index(target_str: str) -> int:
    return int(target_str.replace("R", ""))

def get_wind_speed(target_str: str) -> int:
    return int(target_str.replace("m",""))

def get_wave_height(target_str: str) -> int:
    return int(target_str.replace("cm",""))


def divide_each_race_results(target_text_line_list: list[str]) -> list[list[str]]:
    search_pattern = "  着 艇 登番 　選　手　名　　ﾓｰﾀｰ ﾎﾞｰﾄ 展示 進入 ｽﾀｰﾄﾀｲﾐﾝｸ ﾚｰｽﾀｲﾑ"
    delimiter_index_list = []
    for i, each_line in enumerate(target_text_line_list):
        if search_pattern in each_line:
            delimiter_index_list.append(i-1)
    
    divide_each_race_list = []

    for i, start_index in enumerate(delimiter_index_list):
        if i == len(delimiter_index_list) - 1:
            divide_each_race_list.append(target_text_line_list[start_index:])
        else:
            divide_each_race_list.append(target_text_line_list[start_index:delimiter_index_list[i+1]])

    return divide_each_race_list

def get_data_from_line0(line0: list[str]):
    special_rule = line0.pop(2) if len(line0) == 10 else None
    race_index = get_race_index(line0[0])
    race_name = line0[1]
    weather = line0[3]
    wind_direction = line0[5]
    wind_speed = get_wind_speed(line0[6])
    wave_height = get_wave_height(line0[8])
    return race_index, race_name, special_rule, weather, wind_direction, wind_speed, wave_height

def extract_each_race_results(session: Session, date: dt.date, stadium: db.stadium.Stadium, each_race_results: list[str]):
    is_refund_data = False
    each_boat_data_list = []
    for i, each_line in enumerate(each_race_results):
        if "単勝" in each_line:
            is_refund_data = True
        if i == 0:
            race_index = int(remove_all_blank(each_line[0:4]))
            race_name = str(remove_all_blank(each_line[12:20]))
            special_rule = str(remove_all_blank(each_line[20:31]))
            if special_rule == "":
                special_rule = None

            H_index = each_line[31:].find("H")
            each_line = each_line[31+H_index:]

            weather=str(remove_all_blank(each_line[8:11]))
            wind_direction = str(remove_all_blank(each_line[15:17]))
            wind_speed = int(remove_all_blank(each_line[17:20]))
            wave_height = int(remove_all_blank(each_line[24:28]))
        elif i == 1:
            race_time_index = each_line.find("ﾚｰｽﾀｲﾑ")
            decisive_factor = str(remove_all_blank(each_line[race_time_index+6:]))
        elif i == 2:
            pass
        elif not is_refund_data:
            each_boat_data_dict = {}
            try:
                order_of_arrival = int(remove_all_blank(each_line[0:4]))
            except Exception as e:
                order_of_arrival = 99
            each_boat_data_dict["order_of_arrival"] = int(order_of_arrival)
            each_boat_data_dict["boat_number"] = int(remove_all_blank(each_line[4:7]))

            player_id = int(remove_all_blank(each_line[8:12]))
            player_name = str(remove_all_blank(each_line[13:21]))

            motor_number = int(remove_all_blank(each_line[21:24]))
            boat_number = int(remove_all_blank(each_line[24:29]))

            try:
                sample_time = float(remove_all_blank(each_line[29:35]))
            except Exception as e:
                sample_time = None

            try:
                starting_order = int(remove_all_blank(each_line[35:39]))
            except Exception as e:
                starting_order = None

            try:
                start_timing = float(remove_all_blank(each_line[39:47]))
            except Exception as e:
                start_timing = None
            
            try:
                race_time = dt.time(minute=int(each_line[47:53]), second=int(each_line[54:56]), microsecond=int(each_line[57:58])*100000)
            except Exception as e:
                race_time = None
        elif is_refund_data:
            print(i, each_line)


def extract_each_race_results_1(session: Session, date: dt.date, stadium: db.stadium.Stadium, each_race_results: list[str]):
    each_race_results_dict = {}

    # 1業目のデータから必要なデータを取得
    line0 = remove_all_empty_text(each_race_results.pop(0))
    if len(line0) == 8:
        new_line0 = []
        for i, value in enumerate(line0):
            if i == 5:
                wind_direction, wind_speed = extract_wind_direction_and_speed(value)
                new_line0.append(wind_direction)
                new_line0.append(wind_speed)
            else:
                new_line0.append(value)
        line0 = new_line0
    
        print(line0)


    try:
        race_index, race_name, special_rule, weather, wind_direction, wind_speed, wave_height = get_data_from_line0(line0)
    except Exception as e:
        raise Exception(e, line0)

    # 外部テーブルに無依存なやつ
    each_race_results_dict["race_index"] = race_index
    each_race_results_dict["race_name"] = race_name
    each_race_results_dict["wind_speed"] = wind_speed
    each_race_results_dict["wave_height"] = wave_height
    
    # 既存のレコードの取得もしくは、追加して取得
    each_race_results_dict["weather"] = db.weather.get_or_create(session, weather)
    each_race_results_dict["wind_direction"] = db.wind_direction.get_or_create(session, wind_direction)
    each_race_results_dict["special_rule"] = db.special_rule.get_or_create(session, special_rule)

    # 2行目のデータから必要なデータを取得
    line1 = remove_all_empty_text(each_race_results.pop(0))
    each_race_results_dict["decisive_factor"] = db.decisive_factor.get_or_create(session, line1[9])

    # データ分割用の飾り文字列を削除
    each_race_results.pop(0)

    # 各ボートの結果を保存
    each_boat_data = []
    for i, each_line in enumerate(each_race_results):
        try:
            each_line_text_list = remove_all_empty_text(each_line)

            if "単勝" in each_line_text_list:
                try:
                    each_race_results_dict["win_refund"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["win_refund"] = None
            elif "複勝" in each_line_text_list:
                try:
                    each_race_results_dict["place_refund"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["place_refund"] = None
            elif "２連単" in each_line_text_list:
                try:
                    each_race_results_dict["perfecta_refund"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["perfecta_refund"] = None
            elif "２連複" in each_line_text_list:
                try:
                    each_race_results_dict["quinella_refund"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["quinella_refund"] = None
            elif "拡連複" in each_line_text_list:
                try:
                    each_race_results_dict["boxed_quinella_refund1"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["boxed_quinella_refund1"] = None
                try:
                    each_race_results_dict["boxed_quinella_refund2"] = int(remove_all_empty_text(each_race_results.pop(i+1))[1])
                except Exception as e:
                    each_race_results_dict["boxed_quinella_refund2"] = None
                try:
                    each_race_results_dict["boxed_quinella_refund3"] = int(remove_all_empty_text(each_race_results.pop(i+1))[1])
                except Exception as e:
                    each_race_results_dict["boxed_quinella_refund3"] = None
            elif "３連単" in each_line_text_list:
                try:
                    each_race_results_dict["trifecta_refund"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["trifecta_refund"] = None
            elif "３連複" in each_line_text_list:
                try:
                    each_race_results_dict["boxed_trifecta_refund"] = int(each_line_text_list[2])
                except Exception as e:
                    each_race_results_dict["boxed_trifecta_refund"] = None
            else:
                each_boat_data_dict = {}
                try:
                    each_boat_data_dict["order_of_arrival"] = int(each_line_text_list[0])
                except Exception as e:
                    each_boat_data_dict["order_of_arrival"] = 99
                
                each_boat_data_dict["boat_number"] = int(each_line_text_list[1])
                each_boat_data_dict["player"] = db.player.get(session, id=int(each_line_text_list[2]))
                each_boat_data_dict["motor"] = db.motor.get(session, int(each_line_text_list[4]), stadium)
                each_boat_data_dict["boat"] = db.boat.get(session, int(each_line_text_list[5]), stadium)

                try:
                    each_boat_data_dict["sample_time"] = float(each_line_text_list[6])
                except Exception as e:
                    each_boat_data_dict["sample_time"] = None

                try:    
                    each_boat_data_dict["starting_order"] = int(each_line_text_list[7])
                except Exception as e:
                    each_boat_data_dict["starting_order"] = None

                try:
                    each_boat_data_dict["start_timing"] = float(each_line_text_list[8])
                except Exception as e:
                    each_boat_data_dict["start_timing"] = None

                if len(each_line_text_list) == 10:
                    each_boat_data_dict["race_time"] = dt.time(minute=int(each_line_text_list[9][0]), second=int(each_line_text_list[9][2:4]), microsecond=int(each_line_text_list[9][5:])*100000)
                else:
                    each_boat_data_dict["race_time"] = None

                each_boat_data.append(each_boat_data_dict)
        except Exception as e:
            print(e, each_line_text_list)

    each_race_results_dict["stadium"] = stadium
    each_race_results_dict["date"] = date
    each_race = db.each_race_results.create_and_get(session, **each_race_results_dict)

    for each_boat_data_dict in each_boat_data:
        each_boat_data_dict["each_race_result"] = each_race
        db.each_boat_data.create(session, **each_boat_data_dict)
        

def register_race_result_for_db(result_content):
    race_list = get_each_race_list(result_content)
    
    for start_match in race_list:
        session = session_factory()

        target_text = get_each_target_text_for_result(result_content, start_match)
        target_text_line_list = target_text.split("\n")
        target_text_line_list = remove_empty_text(target_text_line_list)

        stadium_id = int(start_match[0][0])
        stadium_name = remove_full_width_space(target_text_line_list[0][0:3])

        stadium = db.stadium.get_or_create(session, stadium_id, stadium_name)

        each_race_results_list = divide_each_race_results(target_text_line_list)

        for each_race_results in each_race_results_list:
            extract_each_race_results(session, this_race_date, stadium, each_race_results)

        session.close()


def get_each_param_list(text: str) -> list[list[Tuple[ParseResults, int, int]]]:
    search_pattern = "BBGN"
    kbgn = Word(nums, exact=2) + Literal(search_pattern)
    return list(kbgn.scanString(text))

def get_each_target_text_for_param(param_content:str, start_delimiter: list[Tuple[ParseResults, int, int]]) -> str:
    search_pattern = "BEND"
    start_index = start_delimiter[2]+1
    end_delimiter = Literal(start_delimiter[0][0]+search_pattern)
    end_match = end_delimiter.scanString(param_content)
    return param_content[start_index:list(end_match)[0][1]]

def divide_each_race_params(target_text_line_list: list[str]) -> list[list[str]]:
    search_pattern1 = "艇 選手 選手  年 支 体級    全国      当地     モーター   ボート   今節成績  早"
    delimiter_index_list = []
    for i, each_line in enumerate(target_text_line_list):
        if search_pattern1 in each_line:
            delimiter_index_list.append(i-2)
    
    divide_each_race_list = []

    for i, start_index in enumerate(delimiter_index_list):
        if i == len(delimiter_index_list) - 1:
            divide_each_race_list.append(target_text_line_list[start_index:])
        else:
            divide_each_race_list.append(target_text_line_list[start_index:delimiter_index_list[i+1]])

    return divide_each_race_list

def extract_each_race_params(session: Session, date: dt.date, stadium: db.stadium.Stadium, each_race_params: list[str]):
    search_pattern1 = "艇 選手 選手  年 支 体級    全国      当地     モーター   ボート   今節成績  早"
    search_pattern2 = "番 登番  名   齢 部 重別 勝率  2率  勝率  2率  NO  2率  NO  2率  １２３４５６見"
    search_pattern3 = "-------------------------------------------------------------------------------"
    each_race_params.pop(0)

    for each_line in each_race_params:
        if each_line in [search_pattern1, search_pattern2, search_pattern3]:
            continue
    
        player_id = int(remove_all_blank(each_line[2:6]))
        player_name = str(remove_all_blank(each_line[6:10]))
        player = db.player.get_or_create(session, id=player_id, name=player_name)

        player_rank = str(remove_all_blank(each_line[16:18]))
        rank = db.rank.get_or_create(session, rank_name=player_rank)

        player_branch = str(remove_all_blank(each_line[12:14]))
        branch = db.branch.get_or_create(session, player_branch)

        player_age = int(remove_all_blank(each_line[10:12]))
        player_weight = int(remove_all_blank(each_line[14:16]))
        db.player_data.create(session, player, date, player_age, player_weight, branch, rank)

        player_national_win_rate = float(remove_all_blank(each_line[18:23]))
        player_national_top2finish_rate = float(remove_all_blank(each_line[23:29]))
        db.player_national_win_rate.create(session, player, date, player_national_win_rate, player_national_top2finish_rate)

        player_local_win_rate = float(remove_all_blank(each_line[29:35]))
        player_local_top2finish_rate = float(remove_all_blank(each_line[35:41]))
        db.player_local_win_rate.create(session, player, stadium, date, player_local_win_rate, player_local_top2finish_rate)
        
        motor_number = int(remove_all_blank(each_line[41:44]))
        motor_top2finish_rate = float(remove_all_blank(each_line[44:50])) 
        motor = db.motor.get_or_create(session, motor_number,stadium, motor_top2finish_rate)
        db.motor_top2finish_rate.create(session, motor, date, motor_top2finish_rate)

        boat_number = int(remove_all_blank(each_line[50:53]))
        boat_top2finish_rate = float(remove_all_blank(each_line[53:59]))
        boat = db.boat.get_or_create(session, boat_number, stadium, boat_top2finish_rate)
        db.boat_top2finish_rate.create(session, boat, date, boat_top2finish_rate)


def register_race_param_for_db(this_race_date:dt.date, param_content: str):
    param_list = get_each_param_list(param_content)
    
    for start_match in param_list:
        session = session_factory()

        target_text = get_each_target_text_for_param(param_content, start_match)
        target_text_line_list = target_text.split("\n")
        target_text_line_list = remove_empty_text(target_text_line_list)

        stadium_id = int(start_match[0][0])
        stadium_name = remove_full_width_space(target_text_line_list[0][6:9])
        stadium = db.stadium.get_or_create(session, stadium_id, stadium_name)

        each_race_params_list = divide_each_race_params(target_text_line_list)

        for each_race_params in each_race_params_list:
            extract_each_race_params(session, this_race_date, stadium, each_race_params)

        session.close()

def remove_empty_text(text_list: list[str]) -> list[str]:
    return [each_text for each_text in text_list if each_text != ""]

def remove_full_width_space(text:str) -> str:
    return text.replace("\u3000", "")

def remove_all_blank(text:str) -> str:
    text.replace(" ", "")
    return text.replace("\u3000", "")

def remove_all_empty_text(text: str) -> str:
    return remove_empty_text(remove_full_width_space(text).split(" "))


if __name__=='__main__':
    # base_dir = "uncompressed_data"
    base_dir = "samples"
    file_list = list(Path(f"{base_dir}/competitive_record").glob("*.txt"))

    for target_file in file_list:   
        with open(target_file, "r", encoding="utf-8") as f:
            result_content = f.read()

        file_name = str(target_file.stem)
        this_race_date = dt.date(year=int(file_name[1:3])+2000, month=int(file_name[3:5]), day=int(file_name[5:7]))

        param_file = Path(f"./{base_dir}") / "race_parameters" / f"b{file_name[1:]}.txt"
        with open(param_file, "r", encoding="utf-8") as f:
            param_content = f.read()

        # register_race_param_for_db(this_race_date, param_content)

        register_race_result_for_db(result_content)



