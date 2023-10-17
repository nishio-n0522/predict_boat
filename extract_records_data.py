import os
from pathlib import Path
from typing import Tuple

from pyparsing import Word, alphas, nums, Literal, ParseResults


def get_each_race_list(text: str) -> list[list[Tuple[ParseResults, int, int]]]:
    search_pattern = "KBGN"
    kbgn = Word(nums, exact=2) + Literal(search_pattern)
    return list(kbgn.scanString(text))

def get_each_target_text(start_delimiter: list[Tuple[ParseResults, int, int]]) -> str:
    search_pattern = "KEND"
    start_index = start_delimiter[2]+1
    end_delimiter = Literal(start_delimiter[0][0]+search_pattern)
    end_match = end_delimiter.scanString(content)
    return content[start_index:list(end_match)[0][1]-1]

def get_race_index(target_str: str) -> int:
    r_index = target_str.index("R")
    return int(target_str[r_index-2:r_index])

def get_wind_speed(target_str: str) -> int:
    r_index = target_str.index("m")
    return int(target_str[r_index-2:r_index])

def get_wave_height(target_str: str) -> int:
    r_index = target_str.index("cm")
    return int(target_str[r_index-2:r_index])


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

def extract_each_race_results(each_race_results: list[str]): 
    # print(each_race_results)
    race_results_list = remove_empty_text(remove_full_width_space(each_race_results[0]).split(" "))
    line1 = remove_empty_text(remove_full_width_space(each_race_results[1]).split(" "))
    line3 = remove_empty_text(remove_full_width_space(each_race_results[3]).split(" "))

    for i, each_line in enumerate(each_race_results):
        print(i, each_line)
    
    
    decisive_factor = line1[9]

def get_data_from_line0(line0):
    race_index = get_race_index(line0[0])
    race_name = line0[1]
    additional_info = line0[2] if len(line0) == 10 else None
    weather = line0[4]
    wind_direction = line0[6]
    wind_speed = get_wind_speed(line0[7])
    wave_height = get_wave_height(line0[9])
    print("====", race_index, race_name, additional_info, weather, wind_direction, wind_speed, wave_height)
    return race_index, race_name, additional_info, weather, wind_direction, wind_speed, wave_height


def remove_empty_text(text_list: list[str]) -> list[str]:
    return [each_text for each_text in text_list if each_text != ""]

def remove_full_width_space(text:str) -> str:
    return text.replace("\u3000", "")





if __name__=='__main__':
    with open("samples/k230901.txt", "r", encoding="utf-8") as f:
        content = f.read()

    race_list = get_each_race_list(content)
    
    for start_match in race_list[0:1]:
        target_text = get_each_target_text(start_match)
        target_text_line_list = target_text.split("\n")

        target_text_line_list = remove_empty_text(target_text_line_list)
        each_race_results_list = divide_each_race_results(target_text_line_list)

        for each_race_results in each_race_results_list:
            extract_each_race_results(each_race_results)