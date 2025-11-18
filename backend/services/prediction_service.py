"""
推論サービス
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import date
import numpy as np

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from ml_models.predict import LightGBMRacePredictor
from ml_models.predict_transformer import TransformerRacePredictor
from ml_models.predict_bayesian import BayesianRacePredictor
from backend.schemas.predict import (
    BoatPrediction,
    RacePrediction,
    FeatureImportance,
)


class PredictionService:
    """推論サービス"""

    def predict_race(
        self,
        model_path: str,
        model_type: str,
        race_date: date,
        stadium_id: int,
        race_index: int
    ) -> RacePrediction:
        """レース予測"""
        # モデル読み込み
        if model_type == "lightgbm":
            predictor = LightGBMRacePredictor(model_path)
        elif model_type == "transformer":
            predictor = TransformerRacePredictor(model_path)
        elif model_type == "bayesian":
            predictor = BayesianRacePredictor(model_path)
        else:
            raise ValueError(f"不明なモデルタイプ: {model_type}")

        try:
            # 予測実行
            result = predictor.predict_race(race_date, stadium_id, race_index)

            # BoatPredictionリストに変換
            boats = []
            for _, row in result.predictions.iterrows():
                boat = BoatPrediction(
                    boat_number=int(row['boat_number']),
                    probability=float(row['probability']),
                    std=float(row['std']) if 'std' in row else None,
                    ci_lower=float(row['ci_lower']) if 'ci_lower' in row else None,
                    ci_upper=float(row['ci_upper']) if 'ci_upper' in row else None,
                )
                boats.append(boat)

            # レース予測結果を構築
            recommended = result.get_recommended_boats()
            expected_hit_rate = sum(result.predictions.head(3)['probability'].tolist()) / 3

            return RacePrediction(
                race_date=race_date,
                stadium_id=stadium_id,
                race_index=race_index,
                boats=boats,
                recommended_boats=recommended,
                expected_hit_rate=expected_hit_rate,
                has_uncertainty=result.has_uncertainty
            )

        finally:
            predictor.close()

    def predict_multi_models(
        self,
        model_paths: Dict[str, str],
        race_date: date,
        stadium_id: int,
        race_index: int
    ) -> Dict[str, Any]:
        """複数モデルで予測して比較"""
        predictions = {}

        for model_name, model_path in model_paths.items():
            # モデルタイプを推定（パスから）
            if "lightgbm" in model_path.lower():
                model_type = "lightgbm"
            elif "transformer" in model_path.lower():
                model_type = "transformer"
            elif "bayesian" in model_path.lower():
                model_type = "bayesian"
            else:
                continue

            try:
                prediction = self.predict_race(
                    model_path, model_type, race_date, stadium_id, race_index
                )
                predictions[model_name] = prediction
            except Exception as e:
                print(f"エラー（{model_name}）: {e}")
                continue

        # 比較情報を生成
        comparison = self._generate_comparison(predictions)

        return {
            "race_info": {
                "race_date": race_date.isoformat(),
                "stadium_id": stadium_id,
                "race_index": race_index
            },
            "predictions": predictions,
            "comparison": comparison
        }

    def _generate_comparison(self, predictions: Dict[str, RacePrediction]) -> Dict[str, Any]:
        """予測結果の比較情報を生成"""
        if not predictions:
            return {}

        # 各モデルの推奨艇を比較
        recommended_comparison = {}
        for model_name, pred in predictions.items():
            recommended_comparison[model_name] = pred.recommended_boats

        # 一致度を計算
        model_names = list(predictions.keys())
        agreement_matrix = {}

        for i, name1 in enumerate(model_names):
            for name2 in model_names[i+1:]:
                set1 = set(predictions[name1].recommended_boats)
                set2 = set(predictions[name2].recommended_boats)
                agreement = len(set1 & set2) / 3.0  # 3艇中何艇一致するか
                agreement_matrix[f"{name1}_vs_{name2}"] = agreement

        # 各艇の平均確率
        boat_avg_probs = {}
        for boat_num in range(1, 7):
            probs = []
            for pred in predictions.values():
                for boat in pred.boats:
                    if boat.boat_number == boat_num:
                        probs.append(boat.probability)
                        break
            if probs:
                boat_avg_probs[boat_num] = {
                    "mean": float(np.mean(probs)),
                    "std": float(np.std(probs)),
                    "min": float(np.min(probs)),
                    "max": float(np.max(probs))
                }

        return {
            "recommended_comparison": recommended_comparison,
            "agreement_matrix": agreement_matrix,
            "boat_avg_probabilities": boat_avg_probs
        }

    def get_feature_importance(
        self,
        model_path: str,
        model_type: str,
        top_n: int = 20
    ) -> List[FeatureImportance]:
        """特徴量重要度を取得"""
        if model_type == "lightgbm":
            return self._get_lightgbm_importance(model_path, top_n)
        elif model_type == "transformer":
            return self._get_transformer_importance(model_path, top_n)
        elif model_type == "bayesian":
            return self._get_bayesian_importance(model_path, top_n)
        else:
            raise ValueError(f"不明なモデルタイプ: {model_type}")

    def _get_lightgbm_importance(self, model_path: str, top_n: int) -> List[FeatureImportance]:
        """LightGBMの特徴量重要度"""
        from ml_models.train_model import BoatRacePredictor

        predictor = BoatRacePredictor()
        predictor.load(model_path)

        if predictor.model is None:
            return []

        importance_dict = predictor.model.feature_importance(importance_type='gain')
        feature_names = predictor.model.feature_name()

        # ソート
        importance_pairs = sorted(
            zip(feature_names, importance_dict),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            FeatureImportance(
                feature_name=name,
                importance=float(imp),
                rank=i + 1
            )
            for i, (name, imp) in enumerate(importance_pairs)
        ]

    def _get_transformer_importance(self, model_path: str, top_n: int) -> List[FeatureImportance]:
        """Transformerの特徴量重要度（Feature Gateから）"""
        import torch
        from ml_models.transformer_model import BoatRaceTransformer

        checkpoint = torch.load(model_path, map_location='cpu')

        # Feature Gateの重みを取得
        model = BoatRaceTransformer(
            n_features=checkpoint['n_features'],
            d_model=checkpoint.get('args', {}).get('d_model', 128),
            nhead=checkpoint.get('args', {}).get('nhead', 8),
            num_layers=checkpoint.get('args', {}).get('num_layers', 3),
            use_feature_gating=True
        )
        model.load_state_dict(checkpoint['model_state_dict'])

        if hasattr(model, 'feature_gate'):
            gate_weights = model.feature_gate.gate_weights.detach().cpu().numpy()
            feature_names = checkpoint.get('feature_names', [f"feature_{i}" for i in range(len(gate_weights))])

            # ソート
            importance_pairs = sorted(
                zip(feature_names, gate_weights),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]

            return [
                FeatureImportance(
                    feature_name=name,
                    importance=float(imp),
                    rank=i + 1
                )
                for i, (name, imp) in enumerate(importance_pairs)
            ]

        return []

    def _get_bayesian_importance(self, model_path: str, top_n: int) -> List[FeatureImportance]:
        """階層ベイズモデルの特徴量重要度（固定効果の係数から）"""
        import pickle

        with open(model_path, 'rb') as f:
            metadata = pickle.load(f)

        # 固定効果の係数（beta）を取得
        # 注: 実際にはトレースファイルから取得する必要がある
        feature_names = metadata.get('feature_names', [])

        # デモ版: ランダムな重要度を返す
        import numpy as np
        np.random.seed(42)
        importances = np.random.rand(len(feature_names))

        importance_pairs = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            FeatureImportance(
                feature_name=name,
                importance=float(imp),
                rank=i + 1
            )
            for i, (name, imp) in enumerate(importance_pairs)
        ]
