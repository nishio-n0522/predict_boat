"""
推論実行エンジン

特徴量からレース結果を予測
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import pickle

logger = logging.getLogger(__name__)


class PredictionEngine:
    """レース結果予測エンジン"""

    def __init__(self, model_path: Optional[Path] = None):
        """
        初期化

        Args:
            model_path: 学習済みモデルのパス（Noneの場合はルールベース）
        """
        self.model = None
        self.model_type = "rule_based"

        if model_path and model_path.exists():
            try:
                self.load_model(model_path)
                self.model_type = "ml_model"
                logger.info(f"モデルをロード: {model_path}")
            except Exception as e:
                logger.warning(f"モデルのロード失敗: {e}. ルールベースを使用します。")

    def load_model(self, model_path: Path):
        """
        学習済みモデルをロード

        Args:
            model_path: モデルファイルのパス
        """
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info("モデルをロードしました")

    def predict(self, features_df: pd.DataFrame) -> Dict:
        """
        レース結果を予測

        Args:
            features_df: 特徴量DataFrame（6艇分）

        Returns:
            予測結果の辞書
        """
        if self.model_type == "ml_model" and self.model is not None:
            return self._predict_ml(features_df)
        else:
            return self._predict_rule_based(features_df)

    def _predict_ml(self, features_df: pd.DataFrame) -> Dict:
        """
        機械学習モデルで予測

        Args:
            features_df: 特徴量DataFrame

        Returns:
            予測結果
        """
        try:
            # モデルの入力形式に合わせてデータを準備
            X = features_df.drop(columns=['boat_number', 'venue_id', 'player_id', 'motor_number', 'boat_id'], errors='ignore')

            # 予測実行
            predictions = self.model.predict_proba(X)

            # 結果を整形
            result = self._format_predictions(features_df, predictions)
            result['model_type'] = 'machine_learning'

            return result

        except Exception as e:
            logger.error(f"ML予測エラー: {e}. ルールベースにフォールバック")
            return self._predict_rule_based(features_df)

    def _predict_rule_based(self, features_df: pd.DataFrame) -> Dict:
        """
        ルールベースで予測（統計的手法）

        Args:
            features_df: 特徴量DataFrame

        Returns:
            予測結果
        """
        if features_df.empty or len(features_df) < 6:
            logger.warning("データが不十分です")
            return self._create_empty_result()

        # スコア計算
        scores = []
        for idx, row in features_df.iterrows():
            score = self._calculate_boat_score(row)
            scores.append({
                'boat_number': int(row.get('boat_number', idx + 1)),
                'score': score
            })

        # スコア順にソート
        scores_sorted = sorted(scores, key=lambda x: x['score'], reverse=True)

        # 確率に変換（ソフトマックス）
        score_values = np.array([s['score'] for s in scores_sorted])
        probabilities = self._softmax(score_values)

        # 結果を整形
        predictions = []
        for i, (boat_info, prob) in enumerate(zip(scores_sorted, probabilities)):
            predictions.append({
                'rank': i + 1,
                'boat_number': boat_info['boat_number'],
                'probability': float(prob),
                'score': float(boat_info['score'])
            })

        result = {
            'predictions': predictions,
            'model_type': 'rule_based',
            'top3': [p['boat_number'] for p in predictions[:3]],
            'win_probability': {p['boat_number']: p['probability'] for p in predictions}
        }

        return result

    def _calculate_boat_score(self, boat_features: pd.Series) -> float:
        """
        1艇のスコアを計算

        Args:
            boat_features: 艇の特徴量

        Returns:
            スコア
        """
        score = 0.0

        # 選手の全国勝率（重み: 30%）
        player_national_win_rate = float(boat_features.get('player_national_win_rate', 0.0))
        score += player_national_win_rate * 0.30

        # 選手の当地勝率（重み: 25%）
        player_local_win_rate = float(boat_features.get('player_local_win_rate', 0.0))
        score += player_local_win_rate * 0.25

        # モーター2連対率（重み: 15%）
        motor_2nd_rate = float(boat_features.get('motor_2nd_rate', 0.0))
        score += motor_2nd_rate * 0.15

        # 節間成績勝率（重み: 20%）
        session_win_rate = float(boat_features.get('session_win_rate', 0.0))
        score += session_win_rate * 0.20

        # 展示タイム（重み: 10%、タイムが速いほど高スコア）
        exhibition_time = float(boat_features.get('exhibition_time', 0.0))
        if exhibition_time > 0:
            # 展示タイムの逆数を正規化してスコア化（6.5-7.0秒を想定）
            time_score = max(0, (7.5 - exhibition_time) / 1.0)  # 6.5秒で1.0、7.5秒で0.0
            score += time_score * 0.10

        # オッズ（重み: -5%、低オッズほど高スコア）
        # 実際の期待値とは逆の補正として使用
        win_odds = float(boat_features.get('win_odds', 0.0))
        if win_odds > 0:
            odds_score = max(0, (20 - win_odds) / 20)  # 1.0倍で1.0、20倍以上で0.0
            score += odds_score * 0.05

        return score

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """
        ソフトマックス関数

        Args:
            x: スコア配列

        Returns:
            確率配列
        """
        exp_x = np.exp(x - np.max(x))  # オーバーフロー対策
        return exp_x / np.sum(exp_x)

    def _format_predictions(self, features_df: pd.DataFrame, predictions: np.ndarray) -> Dict:
        """
        予測結果をフォーマット

        Args:
            features_df: 特徴量DataFrame
            predictions: 予測確率配列

        Returns:
            フォーマットされた結果
        """
        results = []
        for idx, row in features_df.iterrows():
            boat_num = int(row.get('boat_number', idx + 1))
            prob = float(predictions[idx][1]) if len(predictions[idx]) > 1 else float(predictions[idx][0])
            results.append({
                'boat_number': boat_num,
                'probability': prob
            })

        # 確率順にソート
        results_sorted = sorted(results, key=lambda x: x['probability'], reverse=True)

        # ランク付け
        for i, r in enumerate(results_sorted):
            r['rank'] = i + 1

        return {
            'predictions': results_sorted,
            'top3': [r['boat_number'] for r in results_sorted[:3]],
            'win_probability': {r['boat_number']: r['probability'] for r in results_sorted}
        }

    def _create_empty_result(self) -> Dict:
        """空の結果を作成"""
        return {
            'predictions': [],
            'model_type': 'none',
            'top3': [],
            'win_probability': {},
            'error': 'データが不十分です'
        }

    def predict_quinella(self, predictions: List[Dict]) -> List[Tuple[int, int, float]]:
        """
        2連単の予測

        Args:
            predictions: 単勝予測結果

        Returns:
            [(1着艇番, 2着艇番, 確率), ...] のリスト
        """
        quinella_predictions = []

        # 上位艇の組み合わせを計算
        top_boats = predictions[:4]  # 上位4艇を対象

        for i, boat1 in enumerate(top_boats):
            for boat2 in top_boats:
                if boat1['boat_number'] != boat2['boat_number']:
                    # 確率の積で2連単確率を概算
                    prob = boat1['probability'] * boat2['probability']
                    quinella_predictions.append((
                        boat1['boat_number'],
                        boat2['boat_number'],
                        prob
                    ))

        # 確率順にソート
        quinella_predictions.sort(key=lambda x: x[2], reverse=True)

        return quinella_predictions[:10]  # 上位10通り

    def predict_trifecta(self, predictions: List[Dict]) -> List[Tuple[int, int, int, float]]:
        """
        3連単の予測

        Args:
            predictions: 単勝予測結果

        Returns:
            [(1着艇番, 2着艇番, 3着艇番, 確率), ...] のリスト
        """
        trifecta_predictions = []

        # 上位艇の組み合わせを計算
        top_boats = predictions[:4]  # 上位4艇を対象

        for i, boat1 in enumerate(top_boats):
            for boat2 in top_boats:
                if boat1['boat_number'] != boat2['boat_number']:
                    for boat3 in top_boats:
                        if boat3['boat_number'] not in [boat1['boat_number'], boat2['boat_number']]:
                            # 確率の積で3連単確率を概算
                            prob = boat1['probability'] * boat2['probability'] * boat3['probability']
                            trifecta_predictions.append((
                                boat1['boat_number'],
                                boat2['boat_number'],
                                boat3['boat_number'],
                                prob
                            ))

        # 確率順にソート
        trifecta_predictions.sort(key=lambda x: x[3], reverse=True)

        return trifecta_predictions[:10]  # 上位10通り


if __name__ == "__main__":
    # テスト用
    import sys
    from fetch_live_data import fetch_race_card_simple
    from prediction.data_preprocessor import RaceDataPreprocessor

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Usage: python inference_engine.py <venue> <race_number>")
        sys.exit(1)

    venue = sys.argv[1]
    race_number = int(sys.argv[2])

    # 出走表を取得
    print(f"=== {venue} R{race_number} の予測 ===\n")
    card = fetch_race_card_simple(venue, race_number)

    # 前処理
    preprocessor = RaceDataPreprocessor()
    try:
        features_df = preprocessor.preprocess_race_card(card)

        # 予測
        engine = PredictionEngine()
        result = engine.predict(features_df)

        print(f"モデルタイプ: {result['model_type']}\n")
        print("=== 単勝予測 ===")
        for pred in result['predictions']:
            print(f"{pred['rank']}位: {pred['boat_number']}号艇 (確率: {pred['probability']:.1%})")

        print(f"\n推奨: {'-'.join(map(str, result['top3']))}")

        # 2連単予測
        quinella = engine.predict_quinella(result['predictions'])
        print("\n=== 2連単予測（上位5通り） ===")
        for i, (b1, b2, prob) in enumerate(quinella[:5], 1):
            print(f"{i}. {b1}-{b2} (確率: {prob:.2%})")

        # 3連単予測
        trifecta = engine.predict_trifecta(result['predictions'])
        print("\n=== 3連単予測（上位5通り） ===")
        for i, (b1, b2, b3, prob) in enumerate(trifecta[:5], 1):
            print(f"{i}. {b1}-{b2}-{b3} (確率: {prob:.3%})")

    finally:
        preprocessor.close()
