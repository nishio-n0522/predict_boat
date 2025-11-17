"""
階層ベイズモデル予測スクリプト

訓練済み階層ベイズモデルで予測（不確実性込み）
"""

import sys
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd
import pickle

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from ml_models.hierarchical_bayesian_model import HierarchicalBayesianModel
from ml_models.feature_engineering import FeatureExtractor


class BayesianRacePredictor:
    """階層ベイズ予測器"""

    def __init__(self, model_path: str):
        """
        初期化

        Args:
            model_path: 訓練済みモデルのパス
        """
        # モデル読み込み
        with open(model_path, 'rb') as f:
            metadata = pickle.load(f)

        self.model = HierarchicalBayesianModel(
            n_players=metadata['n_players'],
            n_motors=metadata['n_motors'],
            n_stadiums=metadata['n_stadiums'],
            n_features=metadata['n_features'],
            feature_names=metadata['feature_names']
        )

        self.model.load(model_path)

        # Scaler読み込み
        scaler_path = Path(model_path).parent / "bayesian_scaler.pkl"
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)

        # 特徴量抽出器
        self.feature_extractor = FeatureExtractor()

        print(f"モデルを読み込みました: {model_path}")

    def predict_race(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int,
        return_uncertainty: bool = True
    ) -> pd.DataFrame:
        """
        レースを予測

        Args:
            race_date: レース日
            stadium_id: 競艇場ID
            race_index: レース番号
            return_uncertainty: 不確実性を返すか

        Returns:
            pd.DataFrame: 予測結果
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

        # 標準化
        X_scaled = self.scaler.transform(X.values)

        # 仮想的なID（訓練時と同じロジック）
        # 注: 実際のシステムでは選手登番・モーター番号を使用すべき
        player_ids = np.zeros(6, dtype=int)  # 簡易版
        motor_ids = np.zeros(6, dtype=int)
        stadium_ids_arr = np.full(6, stadium_id, dtype=int)

        # 予測実行
        if return_uncertainty:
            # 全MCMCサンプルでの予測
            probs_samples = self.model.predict_proba(
                X_scaled, player_ids, motor_ids, stadium_ids_arr,
                return_samples=True
            )  # (n_mcmc_samples, 6)

            # 統計量を計算
            probs_mean = probs_samples.mean(axis=0)
            probs_std = probs_samples.std(axis=0)
            probs_lower = np.percentile(probs_samples, 2.5, axis=0)
            probs_upper = np.percentile(probs_samples, 97.5, axis=0)

            result_df = pd.DataFrame({
                'boat_number': boat_numbers,
                'probability': probs_mean,
                'std': probs_std,
                'ci_lower': probs_lower,
                'ci_upper': probs_upper
            })
        else:
            # 平均のみ
            probs = self.model.predict_proba(
                X_scaled, player_ids, motor_ids, stadium_ids_arr,
                return_samples=False
            )

            result_df = pd.DataFrame({
                'boat_number': boat_numbers,
                'probability': probs
            })

        result_df = result_df.sort_values('probability', ascending=False).reset_index(drop=True)

        return result_df

    def print_prediction(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int
    ):
        """予測結果を表示"""
        result_df = self.predict_race(race_date, stadium_id, race_index, return_uncertainty=True)

        print("=" * 80)
        print(f"レース: {race_date} 場ID:{stadium_id} R{race_index}")
        print("=" * 80)

        print("\n【全艇の予測確率（不確実性込み）】")
        print("-" * 80)
        for _, row in result_df.iterrows():
            boat_num = int(row['boat_number'])
            prob = float(row['probability'])
            std = float(row['std'])
            ci_lower = float(row['ci_lower'])
            ci_upper = float(row['ci_upper'])
            print(f"  {boat_num}号艇: {prob:.3f} ({prob*100:.1f}%) "
                  f"± {std:.3f} | 95%CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

        print("\n【推奨購入】")
        print("-" * 80)

        # 上位2艇
        top2 = result_df.head(2)
        print(f"確実に買う2艇:")
        print(f"  1番手: {int(top2.iloc[0]['boat_number'])}号艇 (確率: {top2.iloc[0]['probability']:.3f})")
        print(f"  2番手: {int(top2.iloc[1]['boat_number'])}号艇 (確率: {top2.iloc[1]['probability']:.3f})")

        # 3番手候補
        third = result_df.iloc[2]
        print(f"\n3艇目の候補:")
        print(f"  3番手: {int(third['boat_number'])}号艇 (確率: {third['probability']:.3f})")

        # 推奨3艇
        recommended = result_df.head(3)
        boats = [int(b) for b in recommended['boat_number'].values]
        expected_hit = recommended['probability'].mean()

        print(f"\n3連単ボックス買い推奨:")
        print(f"  {boats[0]}-{boats[1]}-{boats[2]} (6点)")
        print(f"  期待的中率: {expected_hit:.3f}")

        print("=" * 80)

    def close(self):
        """リソースをクローズ"""
        self.feature_extractor.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="階層ベイズ予測")
    parser.add_argument("--model", type=str, default="models_trained/bayesian_model.pkl")
    parser.add_argument("--date", type=str, required=True, help="レース日 (YYYY-MM-DD)")
    parser.add_argument("--stadium", type=int, required=True, help="競艇場ID")
    parser.add_argument("--race", type=int, help="レース番号（指定しない場合は全レース）")

    args = parser.parse_args()

    # 日付をパース
    race_date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()

    # 予測器を初期化
    predictor = BayesianRacePredictor(args.model)

    try:
        if args.race:
            # 単一レース予測
            predictor.print_prediction(race_date, args.stadium, args.race)
        else:
            # 全レース予測
            print(f"\n{race_date} 場ID:{args.stadium} 予測結果")
            print("=" * 80)

            for race_index in range(1, 13):
                try:
                    predictor.print_prediction(race_date, args.stadium, race_index)
                    print()
                except Exception as e:
                    print(f"R{race_index}: スキップ ({e})")
                    continue

    finally:
        predictor.close()


if __name__ == "__main__":
    main()
