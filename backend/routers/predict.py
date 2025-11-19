"""
推論APIルーター
"""

from fastapi import APIRouter, HTTPException
from typing import List

from backend.schemas.predict import (
    PredictionRequest,
    RacePrediction,
    MultiModelPredictionRequest,
    MultiModelPredictionResponse,
    FeatureImportanceRequest,
    FeatureImportanceResponse,
    FeatureImportance,
)
from backend.services.prediction_service import PredictionService

router = APIRouter(prefix="/api/predict", tags=["prediction"])
prediction_service = PredictionService()


@router.post("", response_model=RacePrediction)
async def predict_race(request: PredictionRequest):
    """レースを予測"""
    try:
        result = prediction_service.predict_race(
            model_path=request.model_path,
            model_type=request.model_type,
            race_date=request.race_date,
            stadium_id=request.stadium_id,
            race_index=request.race_index or 1
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=MultiModelPredictionResponse)
async def compare_predictions(request: MultiModelPredictionRequest):
    """複数モデルで予測して比較"""
    try:
        result = prediction_service.predict_multi_models(
            model_paths=request.model_paths,
            race_date=request.race_date,
            stadium_id=request.stadium_id,
            race_index=request.race_index
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feature-importance", response_model=FeatureImportanceResponse)
async def get_feature_importance(request: FeatureImportanceRequest):
    """特徴量重要度を取得"""
    try:
        features = prediction_service.get_feature_importance(
            model_path=request.model_path,
            model_type=request.model_type,
            top_n=request.top_n
        )

        # メソッド名を決定
        method_map = {
            "lightgbm": "Gain-based Importance",
            "transformer": "Feature Gate Weights",
            "bayesian": "Fixed Effects Coefficients"
        }

        return FeatureImportanceResponse(
            model_type=request.model_type,
            method=method_map.get(request.model_type, "Unknown"),
            features=features
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
