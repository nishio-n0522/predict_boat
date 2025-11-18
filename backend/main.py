"""
FastAPIバックエンドサーバー

ボートレース予測AIのバックエンドAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import train, predict, models

# FastAPIアプリケーション
app = FastAPI(
    title="ボートレース予測AI API",
    description="学習・推論・モデル管理のためのREST API",
    version="1.0.0",
)

# CORS設定（React開発サーバーからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Viteのデフォルトポート
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(train.router)
app.include_router(predict.router)
app.include_router(models.router)


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "ボートレース予測AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "training": "/api/train",
            "prediction": "/api/predict",
            "models": "/api/models"
        }
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
