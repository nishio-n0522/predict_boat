import os
from pathlib import Path
from typing import Tuple
from datetime import date

from pyparsing import Word, nums, Literal, ParseResults
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

def extract_each_race_results(session: Session, each_race_results: list[str]):
    # each_race_results_dict 
    each_race_results_dict = {}

    # 1業目のデータから必要なデータを取得
    line0 = remove_all_empty_text(each_race_results.pop(0))
    race_index, race_name, special_rule, weather, wind_direction, wind_speed, wave_height = get_data_from_line0(line0)

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
        each_line_text_list = remove_all_empty_text(each_line)

        if "単勝" in each_line_text_list:
            each_race_results_dict["win_refund"] = int(each_line_text_list[2])
        elif "複勝" in each_line_text_list:
            each_race_results_dict["place_refund"] = int(each_line_text_list[2])
        elif "２連単" in each_line_text_list:
            each_race_results_dict["perfecta_refund"] = int(each_line_text_list[2])
        elif "２連複" in each_line_text_list:
            each_race_results_dict["quinella_refund"] = int(each_line_text_list[2])
        elif "拡連複" in each_line_text_list:
            each_race_results_dict["boxed_quinella_refund1"] = int(each_line_text_list[2])
            each_race_results_dict["boxed_quinella_refund2"] = int(remove_all_empty_text(each_race_results.pop(i+1))[1])
            each_race_results_dict["boxed_quinella_refund3"] = int(remove_all_empty_text(each_race_results.pop(i+1))[1])
        elif "３連単" in each_line_text_list:
            each_race_results_dict["trifecta_refund"] = int(each_line_text_list[2])
        elif "３連複" in each_line_text_list:
            each_race_results_dict["boxed_trifecta_refund"] = int(each_line_text_list[2])
        else:
            each_boat_data.append(each_line_text_list)

    return each_race_results_dict, each_boat_data
        
def get_data_from_line0(line0: list[str]):
    special_rule = line0.pop(2) if len(line0) == 10 else None
    race_index = get_race_index(line0[0])
    race_name = line0[1]
    weather = line0[3]
    wind_direction = line0[5]
    wind_speed = get_wind_speed(line0[6])
    wave_height = get_wave_height(line0[8])
    return race_index, race_name, special_rule, weather, wind_direction, wind_speed, wave_height

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
            each_race_results_dict, each_boat_data = extract_each_race_results(session, each_race_results)
            each_race_results_dict["stadium"] = stadium
            each_race_results_dict["date"] = this_race_date
            each_race_result = db.each_race_results.EachRaceResult(**each_race_results_dict)
            session.add(each_race_result)
            session.commit()


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

def extract_each_race_params(each_race_params: list[str]):
    search_pattern1 = "艇 選手 選手  年 支 体級    全国      当地     モーター   ボート   今節成績  早"
    search_pattern2 = "番 登番  名   齢 部 重別 勝率  2率  勝率  2率  NO  2率  NO  2率  １２３４５６見"
    search_pattern3 = "-------------------------------------------------------------------------------"
    print(int(remove_all_empty_text(each_race_params.pop(0))[0].replace("Ｒ", "")))
    for each_line in each_race_params:

        if not each_line in [search_pattern1, search_pattern2, search_pattern3]:
            each_param_list = remove_all_empty_text(each_line[:58])
            print(each_param_list)



def register_race_param_for_db(param_content):
    param_list = get_each_param_list(param_content)
    
    for start_match in param_list[0:1]:
        # session = session_factory()

        target_text = get_each_target_text_for_param(param_content, start_match)
        target_text_line_list = target_text.split("\n")
        target_text_line_list = remove_empty_text(target_text_line_list)

        # print(target_text_line_list)

        # stadium_id = int(start_match[0][0])
        # stadium_name = remove_full_width_space(target_text_line_list[0][0:3])

        # # stadium = db.stadium.get_or_create(session, stadium_id, stadium_name)

        each_race_params_list = divide_each_race_params(target_text_line_list)

        for each_race_params in each_race_params_list[0:1]:
            extract_each_race_params(each_race_params)





def remove_empty_text(text_list: list[str]) -> list[str]:
    return [each_text for each_text in text_list if each_text != ""]

def remove_full_width_space(text:str) -> str:
    return text.replace("\u3000", "")

def remove_all_empty_text(text: str) -> str:
    return remove_empty_text(remove_full_width_space(text).split(" "))





if __name__=='__main__':
    with open("samples/k230901.txt", "r", encoding="utf-8") as f:
        result_content = f.read()

    file_name = "k230901"
    this_race_date = date(year=int(file_name[1:3])+2000, month=int(file_name[3:5]), day=int(file_name[5:7]))

    param_file = Path("./samples") / f"b{file_name[1:]}.txt"
    with open(param_file, "r", encoding="utf-8") as f:
        param_content = f.read()

    # register_race_param_for_db(param_content)

    # for each_param in param_list[0:1]:
    #     print(each_param, "\n")

    register_race_result_for_db(result_content)



