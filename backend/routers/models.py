"""
モデル管理APIルーター
"""

import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException

from backend.schemas.models import ModelInfo, ModelListResponse

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelListResponse)
async def list_models():
    """訓練済みモデル一覧を取得"""
    models_dir = Path("models_trained")

    if not models_dir.exists():
        return ModelListResponse(models=[], total=0)

    models = []

    # .pkl と .pt ファイルを検索
    for file_path in models_dir.glob("*"):
        if file_path.suffix not in [".pkl", ".pt"]:
            continue

        # モデルタイプを推定
        name = file_path.stem
        if "lightgbm" in name.lower():
            model_type = "lightgbm"
        elif "transformer" in name.lower():
            model_type = "transformer"
        elif "bayesian" in name.lower():
            model_type = "bayesian"
        else:
            model_type = "unknown"

        # ファイル情報を取得
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        file_size = stat.st_size

        models.append(
            ModelInfo(
                name=name,
                model_type=model_type,
                path=str(file_path),
                created_at=created_at,
                file_size=file_size,
                metadata={}
            )
        )

    # 作成日時でソート（新しい順）
    models.sort(key=lambda x: x.created_at or datetime.min, reverse=True)

    return ModelListResponse(
        models=models,
        total=len(models)
    )


@router.get("/{model_name}", response_model=ModelInfo)
async def get_model(model_name: str):
    """特定のモデル情報を取得"""
    models_dir = Path("models_trained")

    # .pkl と .pt の両方を試す
    for ext in [".pkl", ".pt"]:
        file_path = models_dir / f"{model_name}{ext}"
        if file_path.exists():
            # モデルタイプを推定
            if "lightgbm" in model_name.lower():
                model_type = "lightgbm"
            elif "transformer" in model_name.lower():
                model_type = "transformer"
            elif "bayesian" in model_name.lower():
                model_type = "bayesian"
            else:
                model_type = "unknown"

            stat = file_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            file_size = stat.st_size

            return ModelInfo(
                name=model_name,
                model_type=model_type,
                path=str(file_path),
                created_at=created_at,
                file_size=file_size,
                metadata={}
            )

    raise HTTPException(status_code=404, detail=f"モデル '{model_name}' が見つかりません")


@router.delete("/{model_name}")
async def delete_model(model_name: str):
    """モデルを削除"""
    models_dir = Path("models_trained")

    # .pkl と .pt の両方を試す
    deleted = False
    for ext in [".pkl", ".pt"]:
        file_path = models_dir / f"{model_name}{ext}"
        if file_path.exists():
            file_path.unlink()
            deleted = True

    if not deleted:
        raise HTTPException(status_code=404, detail=f"モデル '{model_name}' が見つかりません")

    return {"message": f"モデル '{model_name}' を削除しました"}
