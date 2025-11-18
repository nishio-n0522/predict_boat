#!/usr/bin/env python3
"""データベースの構造とサンプルデータを確認するスクリプト"""

import sqlite3
from pathlib import Path

def check_database():
    db_path = Path(__file__).parent / "sqlite.sqlite3"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブル一覧
    print("=" * 80)
    print("Tables in database:")
    print("=" * 80)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

    # each_race_resultのスキーマ確認
    print("\n" + "=" * 80)
    print("Schema of 'each_race_result' table:")
    print("=" * 80)
    cursor.execute("PRAGMA table_info(each_race_result);")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:30s} {col[2]:15s} nullable={col[3]==0}")

    # レース名のサンプル
    print("\n" + "=" * 80)
    print("Sample race_name values:")
    print("=" * 80)
    cursor.execute("SELECT DISTINCT race_name FROM each_race_result LIMIT 30;")
    race_names = cursor.fetchall()
    for name in race_names:
        print(f"  - {name[0]}")

    # special_ruleのサンプル
    print("\n" + "=" * 80)
    print("Sample special_rule values:")
    print("=" * 80)
    cursor.execute("""
        SELECT DISTINCT sr.special_rule_name
        FROM each_race_result err
        LEFT JOIN special_rule sr ON err.special_rule_id = sr.id
        LIMIT 30;
    """)
    special_rules = cursor.fetchall()
    for rule in special_rules:
        print(f"  - {rule[0]}")

    # データ件数
    print("\n" + "=" * 80)
    print("Record counts:")
    print("=" * 80)
    cursor.execute("SELECT COUNT(*) FROM each_race_result;")
    print(f"  Total races: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM each_boat_data;")
    print(f"  Total boat data: {cursor.fetchone()[0]}")

    cursor.execute("SELECT MIN(date), MAX(date) FROM each_race_result;")
    date_range = cursor.fetchone()
    print(f"  Date range: {date_range[0]} to {date_range[1]}")

    # サンプルレース詳細
    print("\n" + "=" * 80)
    print("Sample race details (1 race):")
    print("=" * 80)
    cursor.execute("""
        SELECT
            err.date,
            s.stadium_name,
            err.race_index,
            err.race_name,
            sr.special_rule_name,
            w.weather_name,
            wd.wind_direction_name,
            err.wind_speed,
            err.wave_height
        FROM each_race_result err
        LEFT JOIN stadium s ON err.stadium_id = s.id
        LEFT JOIN special_rule sr ON err.special_rule_id = sr.id
        LEFT JOIN weather w ON err.weather_id = w.id
        LEFT JOIN wind_direction wd ON err.wind_direction_id = wd.id
        LIMIT 1;
    """)
    sample = cursor.fetchone()
    if sample:
        print(f"  Date: {sample[0]}")
        print(f"  Stadium: {sample[1]}")
        print(f"  Race index: {sample[2]}")
        print(f"  Race name: {sample[3]}")
        print(f"  Special rule: {sample[4]}")
        print(f"  Weather: {sample[5]}")
        print(f"  Wind direction: {sample[6]}")
        print(f"  Wind speed: {sample[7]} m/s")
        print(f"  Wave height: {sample[8]} cm")

    conn.close()

if __name__ == "__main__":
    check_database()
