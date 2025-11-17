"""
予測実行スクリプト

訓練済みモデルを使用して、レースの予測を行います。
- 6艇のうち最も舟券内（3着以内）にくると思われる2艇の予想と確率
- 残り4艇のうち、3着以内になる確率の高い舟と確率
"""

import sys
from pathlib import Path
import datetime as dt
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from ml_models.train_model import BoatRacePredictor
from ml_models.feature_engineering import FeatureExtractor


class RacePredictionResult:
    """レース予測結果"""

    def __init__(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int,
        predictions: pd.DataFrame
    ):
        """
        初期化

        Args:
            race_date: レース日
            stadium_id: 競艇場ID
            race_index: レース番号
            predictions: 予測結果（boat_number, probabilityを含む）
        """
        self.race_date = race_date
        self.stadium_id = stadium_id
        self.race_index = race_index
        self.predictions = predictions.sort_values('probability', ascending=False)

    def get_top2_boats(self) -> tuple:
        """
        最も3着以内に来る確率が高い2艇を取得

        Returns:
            tuple: (boat_numbers, probabilities)
        """
        top2 = self.predictions.head(2)
        return (
            top2['boat_number'].tolist(),
            top2['probability'].tolist()
        )

    def get_third_candidate(self) -> tuple:
        """
        残り4艇のうち、3着以内になる確率が高い艇を取得

        Returns:
            tuple: (boat_number, probability)
        """
        remaining = self.predictions.iloc[2:]
        best = remaining.iloc[0]
        return (int(best['boat_number']), float(best['probability']))

    def get_recommended_boats(self) -> list:
        """
        推奨する3艇を取得（3連単ボックス買い用）

        Returns:
            list: [艇番1, 艇番2, 艇番3]
        """
        top3 = self.predictions.head(3)
        return top3['boat_number'].tolist()

    def print_summary(self):
        """予測結果のサマリーを表示"""
        print("=" * 80)
        print(f"レース: {self.race_date} 場ID:{self.stadium_id} R{self.race_index}")
        print("=" * 80)

        print("\n【全艇の予測確率】")
        print("-" * 80)
        for _, row in self.predictions.iterrows():
            boat_num = int(row['boat_number'])
            prob = float(row['probability'])
            print(f"  {boat_num}号艇: {prob:.3f} ({prob*100:.1f}%)")

        print("\n【推奨購入】")
        print("-" * 80)
        top2_boats, top2_probs = self.get_top2_boats()
        print(f"確実に買う2艇:")
        print(f"  1番手: {top2_boats[0]}号艇 (確率: {top2_probs[0]:.3f})")
        print(f"  2番手: {top2_boats[1]}号艇 (確率: {top2_probs[1]:.3f})")

        third_boat, third_prob = self.get_third_candidate()
        print(f"\n3艇目の候補:")
        print(f"  3番手: {third_boat}号艇 (確率: {third_prob:.3f})")

        recommended = self.get_recommended_boats()
        print(f"\n3連単ボックス買い推奨:")
        print(f"  {recommended[0]}-{recommended[1]}-{recommended[2]} (6点)")
        print(f"  期待的中率: {sum(self.predictions.head(3)['probability'].tolist()) / 3:.3f}")

        print("=" * 80)


class RacePredictor:
    """レース予測器"""

    def __init__(self, model_path: str):
        """
        初期化

        Args:
            model_path: 訓練済みモデルのパス
        """
        self.predictor = BoatRacePredictor()
        self.predictor.load(model_path)
        self.feature_extractor = FeatureExtractor()

    def predict_race(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int
    ) -> RacePredictionResult:
        """
        レースを予測

        Args:
            race_date: レース日
            stadium_id: 競艇場ID
            race_index: レース番号

        Returns:
            RacePredictionResult: 予測結果
        """
        # 特徴量を抽出
        features_df = self.feature_extractor.extract_race_features(
            race_date=race_date,
            stadium_id=stadium_id,
            race_index=race_index
        )

        if features_df.empty:
            raise ValueError(f"レースが見つかりません: {race_date} {stadium_id} R{race_index}")

        if len(features_df) != 6:
            raise ValueError(f"6艇分のデータが揃っていません: {len(features_df)}艇")

        # 艇番を保存
        boat_numbers = features_df['boat_number'].values

        # 予測に不要な列を削除
        exclude_cols = [
            'boat_number', 'target_top3', 'order_of_arrival',
            'race_date', 'stadium_id', 'race_index', 'race_name'
        ]
        X = features_df.drop(columns=[col for col in exclude_cols if col in features_df.columns])

        # 欠損値処理
        X = X.fillna(0)

        # 予測実行
        probabilities = self.predictor.predict(X)

        # 結果をまとめる
        predictions = pd.DataFrame({
            'boat_number': boat_numbers,
            'probability': probabilities
        })

        return RacePredictionResult(
            race_date=race_date,
            stadium_id=stadium_id,
            race_index=race_index,
            predictions=predictions
        )

    def predict_multiple_races(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_indices: list = None
    ) -> list:
        """
        複数レースを予測

        Args:
            race_date: レース日
            stadium_id: 競艇場ID
            race_indices: レース番号リスト（Noneの場合は全レース）

        Returns:
            list: RacePredictionResultのリスト
        """
        if race_indices is None:
            race_indices = list(range(1, 13))  # 1R~12R

        results = []
        for race_index in race_indices:
            try:
                result = self.predict_race(race_date, stadium_id, race_index)
                results.append(result)
            except Exception as e:
                print(f"エラー: {race_date} {stadium_id} R{race_index}: {e}")
                continue

        return results

    def close(self):
        """リソースをクローズ"""
        self.feature_extractor.close()


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="レース予測")
    parser.add_argument(
        "--model",
        type=str,
        default="models_trained/lightgbm_model.pkl",
        help="訓練済みモデルのパス"
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="レース日 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--stadium",
        type=int,
        required=True,
        help="競艇場ID"
    )
    parser.add_argument(
        "--race",
        type=int,
        help="レース番号（指定しない場合は全レース予測）"
    )

    args = parser.parse_args()

    # 日付をパース
    race_date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()

    # 予測器を初期化
    predictor = RacePredictor(args.model)

    try:
        if args.race:
            # 単一レース予測
            result = predictor.predict_race(race_date, args.stadium, args.race)
            result.print_summary()
        else:
            # 全レース予測
            results = predictor.predict_multiple_races(race_date, args.stadium)

            print(f"\n{race_date} 場ID:{args.stadium} 予測結果")
            print("=" * 80)

            for result in results:
                result.print_summary()
                print()

    finally:
        predictor.close()


if __name__ == "__main__":
    main()
