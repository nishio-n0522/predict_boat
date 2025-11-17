"""
レースグレード分類モジュール

レース名からグレードを判定します。
- 一般戦: GENERAL
- G3: G3
- G2: G2
- G1: G1
- SG: SG
- PSG1: PSG1
"""

import re
from enum import Enum


class RaceGrade(Enum):
    """レースグレード"""
    GENERAL = "一般戦"
    G3 = "G3"
    G2 = "G2"
    G1 = "G1"
    SG = "SG"
    PSG1 = "PSG1"
    UNKNOWN = "不明"


def classify_race_grade(race_name: str, special_rule: str = None) -> RaceGrade:
    """
    レース名からグレードを分類

    Args:
        race_name: レース名
        special_rule: 特別規定（あれば）

    Returns:
        RaceGrade: レースグレード
    """
    if not race_name:
        return RaceGrade.UNKNOWN

    race_name = str(race_name).upper()

    # SG判定
    if "SG" in race_name or "スペシャルグレード" in race_name:
        return RaceGrade.SG

    # PSG1判定
    if "PSG1" in race_name or "プレミアムSG" in race_name:
        return RaceGrade.PSG1

    # G1判定
    if re.search(r'G[1１]', race_name) or "グレード1" in race_name:
        return RaceGrade.G1

    # G2判定
    if re.search(r'G[2２]', race_name) or "グレード2" in race_name:
        return RaceGrade.G2

    # G3判定
    if re.search(r'G[3３]', race_name) or "グレード3" in race_name:
        return RaceGrade.G3

    # 一般戦のキーワード判定
    general_keywords = [
        "一般", "予選", "準優勝戦", "優勝戦", "特別選抜",
        "企業杯", "新鋭", "ルーキー", "レディース"
    ]

    for keyword in general_keywords:
        if keyword in race_name:
            return RaceGrade.GENERAL

    # デフォルトは一般戦とみなす
    return RaceGrade.GENERAL


def is_target_race(grade: RaceGrade) -> bool:
    """
    予測対象のレースかどうか判定

    Args:
        grade: レースグレード

    Returns:
        bool: True=予測対象（一般戦・G3）, False=対象外
    """
    return grade in [RaceGrade.GENERAL, RaceGrade.G3]


if __name__ == "__main__":
    # テスト
    test_cases = [
        "一般戦",
        "G3○○杯",
        "G2チャンピオンカップ",
        "G1全日本選手権",
        "SGグランプリ",
        "予選第1戦",
        "優勝戦",
    ]

    print("=" * 60)
    print("レースグレード分類テスト")
    print("=" * 60)

    for race_name in test_cases:
        grade = classify_race_grade(race_name)
        is_target = is_target_race(grade)
        print(f"{race_name:30s} -> {grade.value:10s} (予測対象: {is_target})")
