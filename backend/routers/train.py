"""
学習APIルーター
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.train import TrainingRequest, TrainingResponse
from backend.services.training_service import TrainingService

router = APIRouter(prefix="/api/train", tags=["training"])
training_service = TrainingService()


@router.post("", response_model=TrainingResponse)
async def start_training(request: TrainingRequest):
    """学習を開始"""
    # タスクIDを生成
    task_id = str(uuid.uuid4())

    # 出力パスを生成
    if request.output_path is None:
        timestamp = Path(request.dataset_path).stem
        request.output_path = f"models_trained/{request.model_type}_model_{task_id[:8]}.pkl"

    return TrainingResponse(
        task_id=task_id,
        model_type=request.model_type,
        status="queued",
        message="学習タスクが開始されました。WebSocketで進捗を確認してください。"
    )


@router.websocket("/ws/{task_id}")
async def training_websocket(websocket: WebSocket, task_id: str):
    """学習進捗をWebSocketでストリーミング"""
    await websocket.accept()

    try:
        # クエリパラメータから設定を取得
        data = await websocket.receive_json()

        model_type = data.get("model_type")
        dataset_path = data.get("dataset_path", "data/processed/training_dataset.csv")
        output_path = data.get("output_path")
        parameters = data.get("parameters", {})

        if output_path is None:
            output_path = f"models_trained/{model_type}_model_{task_id[:8]}.pkl"

        # モデルタイプに応じた学習処理
        if model_type == "lightgbm":
            async for progress in training_service.train_lightgbm(
                task_id, dataset_path, output_path, parameters
            ):
                await websocket.send_json(progress.model_dump())

        elif model_type == "transformer":
            async for progress in training_service.train_transformer(
                task_id, dataset_path, output_path, parameters
            ):
                await websocket.send_json(progress.model_dump())

        elif model_type == "bayesian":
            async for progress in training_service.train_bayesian(
                task_id, dataset_path, output_path, parameters
            ):
                await websocket.send_json(progress.model_dump())

        else:
            await websocket.send_json({
                "status": "failed",
                "message": f"不明なモデルタイプ: {model_type}"
            })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {task_id}")
        training_service.cancel_task(task_id)
    except Exception as e:
        print(f"Error in training websocket: {e}")
        await websocket.send_json({
            "status": "failed",
            "message": str(e)
        })
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.delete("/{task_id}")
async def cancel_training(task_id: str):
    """学習をキャンセル"""
    training_service.cancel_task(task_id)
    return {"message": f"タスク {task_id} をキャンセルしました"}
