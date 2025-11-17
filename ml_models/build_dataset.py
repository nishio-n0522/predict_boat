"""
訓練データセット構築スクリプト

データベースから全レースの特徴量を抽出し、訓練用データセットを作成します。
"""

import datetime as dt
import sys
from pathlib import Path
from tqdm import tqdm
import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from db.db_setting import session_factory
import db
from ml_models.feature_engineering import FeatureExtractor
from ml_models.race_grade_classifier import classify_race_grade, is_target_race


def build_dataset(
    start_date: dt.date = dt.date(2020, 4, 1),
    end_date: dt.date = dt.date(2023, 9, 6),
    output_path: str = "data/processed/training_dataset.csv",
    target_grades_only: bool = True
):
    """
    訓練データセットを構築

    Args:
        start_date: 開始日
        end_date: 終了日
        output_path: 出力先パス
        target_grades_only: True=一般戦・G3のみ抽出
    """
    print("=" * 80)
    print("訓練データセット構築開始")
    print("=" * 80)
    print(f"期間: {start_date} ~ {end_date}")
    print(f"対象: {'一般戦・G3のみ' if target_grades_only else '全グレード'}")
    print()

    session = session_factory()
    extractor = FeatureExtractor(session)

    # 対象期間のレースを取得
    races = session.query(db.each_race_results.EachRaceResult).filter(
        db.each_race_results.EachRaceResult.date >= start_date,
        db.each_race_results.EachRaceResult.date <= end_date
    ).order_by(
        db.each_race_results.EachRaceResult.date,
        db.each_race_results.EachRaceResult.stadium_id,
        db.each_race_results.EachRaceResult.race_index
    ).all()

    print(f"対象レース数: {len(races)}")

    all_features = []
    skipped_count = 0
    processed_count = 0

    for race in tqdm(races, desc="特徴量抽出中"):
        # グレード判定
        if target_grades_only:
            grade = classify_race_grade(race.race_name)
            if not is_target_race(grade):
                skipped_count += 1
                continue

        # 各レースの特徴量を抽出
        try:
            features_df = extractor.extract_race_features(
                race_date=race.date,
                stadium_id=race.stadium_id,
                race_index=race.race_index,
                lookback_days=90
            )

            if features_df.empty or len(features_df) != 6:
                skipped_count += 1
                continue

            # レース識別情報を追加
            features_df['race_date'] = race.date
            features_df['stadium_id'] = race.stadium_id
            features_df['race_index'] = race.race_index
            features_df['race_name'] = race.race_name

            all_features.append(features_df)
            processed_count += 1

        except Exception as e:
            print(f"\nエラー: {race.date} {race.stadium_id} R{race.race_index}: {e}")
            skipped_count += 1
            continue

    print()
    print("=" * 80)
    print(f"処理完了")
    print(f"  処理成功: {processed_count} レース")
    print(f"  スキップ: {skipped_count} レース")
    print("=" * 80)

    if not all_features:
        print("警告: データが抽出されませんでした")
        return

    # データフレームを結合
    dataset = pd.concat(all_features, ignore_index=True)

    print(f"データセットサイズ: {len(dataset)} 行 x {len(dataset.columns)} 列")
    print(f"欠損値数: {dataset.isnull().sum().sum()}")

    # 目的変数の分布
    if 'target_top3' in dataset.columns:
        target_counts = dataset['target_top3'].value_counts()
        print(f"\n目的変数の分布:")
        print(f"  3着以内: {target_counts.get(1, 0)} ({target_counts.get(1, 0) / len(dataset) * 100:.1f}%)")
        print(f"  4着以下: {target_counts.get(0, 0)} ({target_counts.get(0, 0) / len(dataset) * 100:.1f}%)")

    # ファイルに保存
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False, encoding='utf-8')

    print(f"\nデータセットを保存しました: {output_path}")
    print(f"ファイルサイズ: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    extractor.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="訓練データセット構築")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2020-04-01",
        help="開始日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2023-09-06",
        help="終了日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/training_dataset.csv",
        help="出力先パス"
    )
    parser.add_argument(
        "--all-grades",
        action="store_true",
        help="全グレードを対象にする（デフォルトは一般戦・G3のみ）"
    )

    args = parser.parse_args()

    start_date = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_date = dt.datetime.strptime(args.end_date, "%Y-%m-%d").date()

    build_dataset(
        start_date=start_date,
        end_date=end_date,
        output_path=args.output,
        target_grades_only=not args.all_grades
    )
