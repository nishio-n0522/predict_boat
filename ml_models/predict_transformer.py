"""
Transformer予測スクリプト

訓練済みTransformerモデルを使用してレースを予測
"""

import sys
from pathlib import Path
import datetime as dt
import numpy as np
import pandas as pd
import torch

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from ml_models.transformer_model import BoatRaceTransformer
from ml_models.feature_engineering import FeatureExtractor
from ml_models.predict import RacePredictionResult


class TransformerRacePredictor:
    """Transformer予測器"""

    def __init__(self, model_path: str):
        """
        初期化

        Args:
            model_path: 訓練済みモデルのパス
        """
        # デバイス
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # モデル読み込み
        checkpoint = torch.load(model_path, map_location=self.device)

        self.n_features = checkpoint['n_features']
        self.feature_names = checkpoint['feature_names']
        model_args = checkpoint['args']

        # モデル再構築
        self.model = BoatRaceTransformer(
            n_features=self.n_features,
            d_model=model_args.get('d_model', 128),
            nhead=model_args.get('nhead', 8),
            num_layers=model_args.get('num_layers', 3),
            use_feature_gating=model_args.get('use_feature_gating', True)
        ).to(self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        # 特徴量抽出器
        self.feature_extractor = FeatureExtractor()

        print(f"モデルを読み込みました: {model_path}")
        print(f"デバイス: {self.device}")

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

        # Transformer用に形状を変換: (1, 6, n_features)
        X_array = X.values.reshape(1, 6, -1).astype(np.float32)

        # 予測実行
        with torch.no_grad():
            X_tensor = torch.tensor(X_array, dtype=torch.float32).to(self.device)
            probs, _ = self.model(X_tensor, return_attention=False)
            probs = probs.cpu().numpy()[0]  # (6,)

        # 結果をDataFrameにまとめる
        result_df = pd.DataFrame({
            'boat_number': boat_numbers,
            'probability': probs
        })

        # RacePredictionResultに変換
        return RacePredictionResult(
            race_date=race_date,
            stadium_id=stadium_id,
            race_index=race_index,
            predictions=result_df
        )

    def print_prediction(
        self,
        race_date: dt.date,
        stadium_id: int,
        race_index: int
    ):
        """予測結果を表示"""
        result = self.predict_race(race_date, stadium_id, race_index)
        result.print_summary()

    def close(self):
        """リソースをクローズ"""
        self.feature_extractor.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Transformer予測")
    parser.add_argument("--model", type=str, default="models_trained/transformer_model.pt")
    parser.add_argument("--date", type=str, required=True, help="レース日 (YYYY-MM-DD)")
    parser.add_argument("--stadium", type=int, required=True, help="競艇場ID")
    parser.add_argument("--race", type=int, help="レース番号（指定しない場合は全レース）")

    args = parser.parse_args()

    # 日付をパース
    race_date = dt.datetime.strptime(args.date, "%Y-%m-%d").date()

    # 予測器を初期化
    predictor = TransformerRacePredictor(args.model)

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
