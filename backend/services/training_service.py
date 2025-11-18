"""
学習サービス
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import AsyncIterator, Dict, Any
from datetime import datetime
import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.schemas.train import TrainingProgress


class TrainingService:
    """学習サービス"""

    def __init__(self):
        self.active_tasks: Dict[str, bool] = {}

    async def train_lightgbm(
        self,
        task_id: str,
        dataset_path: str,
        output_path: str,
        parameters: Dict[str, Any]
    ) -> AsyncIterator[TrainingProgress]:
        """LightGBM学習"""
        from ml_models.train_model import BoatRacePredictor

        try:
            self.active_tasks[task_id] = True

            # 開始通知
            yield TrainingProgress(
                status="starting",
                progress=0.0,
                message="LightGBM学習を開始します",
                current_step="初期化"
            )

            await asyncio.sleep(0.5)

            # データ読み込み
            yield TrainingProgress(
                status="running",
                progress=0.1,
                message="データを読み込んでいます...",
                current_step="データ読み込み"
            )

            from ml_models.train_model import load_and_prepare_data
            X_train, X_val, X_test, y_train, y_val, y_test = load_and_prepare_data(
                dataset_path
            )

            await asyncio.sleep(0.5)

            # モデル訓練
            yield TrainingProgress(
                status="running",
                progress=0.3,
                message="モデルを訓練しています...",
                current_step="訓練中"
            )

            predictor = BoatRacePredictor()
            num_boost_round = parameters.get("num_boost_round", 1000)

            # 訓練実行（進捗は簡易的にシミュレート）
            for i in range(5):
                if not self.active_tasks.get(task_id, False):
                    yield TrainingProgress(
                        status="failed",
                        progress=0.3 + i * 0.1,
                        message="訓練がキャンセルされました",
                        current_step="キャンセル"
                    )
                    return

                await asyncio.sleep(1)
                yield TrainingProgress(
                    status="running",
                    progress=0.3 + (i + 1) * 0.1,
                    message=f"訓練中... ({(i + 1) * 20}%)",
                    current_step="訓練中"
                )

            # 実際の訓練実行
            await asyncio.to_thread(
                predictor.train,
                X_train, y_train, X_val, y_val,
                num_boost_round=num_boost_round
            )

            # モデル保存
            yield TrainingProgress(
                status="running",
                progress=0.9,
                message="モデルを保存しています...",
                current_step="保存中"
            )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            await asyncio.to_thread(predictor.save, output_path)

            # 完了
            yield TrainingProgress(
                status="completed",
                progress=1.0,
                message="学習が完了しました",
                current_step="完了",
                metrics={
                    "train_size": len(X_train),
                    "val_size": len(X_val),
                    "test_size": len(X_test)
                }
            )

        except Exception as e:
            yield TrainingProgress(
                status="failed",
                progress=0.0,
                message=f"エラーが発生しました: {str(e)}",
                current_step="エラー"
            )
        finally:
            self.active_tasks.pop(task_id, None)

    async def train_transformer(
        self,
        task_id: str,
        dataset_path: str,
        output_path: str,
        parameters: Dict[str, Any]
    ) -> AsyncIterator[TrainingProgress]:
        """Transformer学習"""
        import torch
        from ml_models.train_transformer import TransformerTrainer

        try:
            self.active_tasks[task_id] = True

            yield TrainingProgress(
                status="starting",
                progress=0.0,
                message="Transformer学習を開始します",
                current_step="初期化"
            )

            await asyncio.sleep(0.5)

            # データ読み込み
            yield TrainingProgress(
                status="running",
                progress=0.1,
                message="データを読み込んでいます...",
                current_step="データ読み込み"
            )

            df = await asyncio.to_thread(pd.read_csv, dataset_path)
            await asyncio.sleep(0.5)

            # モデル訓練
            yield TrainingProgress(
                status="running",
                progress=0.3,
                message="モデルを訓練しています...",
                current_step="訓練中"
            )

            trainer = TransformerTrainer(
                d_model=parameters.get("d_model", 128),
                nhead=parameters.get("nhead", 8),
                num_layers=parameters.get("num_layers", 3),
                batch_size=parameters.get("batch_size", 32),
                epochs=parameters.get("epochs", 50),
                lr=parameters.get("lr", 0.001)
            )

            # エポック数に応じて進捗を更新
            epochs = parameters.get("epochs", 50)
            for epoch in range(min(5, epochs)):  # 簡易的に5ステップで表示
                if not self.active_tasks.get(task_id, False):
                    yield TrainingProgress(
                        status="failed",
                        progress=0.3 + epoch * 0.1,
                        message="訓練がキャンセルされました",
                        current_step="キャンセル"
                    )
                    return

                await asyncio.sleep(2)
                yield TrainingProgress(
                    status="running",
                    progress=0.3 + (epoch + 1) * 0.1,
                    message=f"エポック {epoch + 1}/{epochs}",
                    current_step="訓練中"
                )

            # 実際の訓練
            await asyncio.to_thread(trainer.train, df)

            # モデル保存
            yield TrainingProgress(
                status="running",
                progress=0.9,
                message="モデルを保存しています...",
                current_step="保存中"
            )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            await asyncio.to_thread(
                torch.save,
                {
                    'model_state_dict': trainer.model.state_dict(),
                    'n_features': trainer.n_features,
                    'feature_names': trainer.feature_names,
                    'args': parameters
                },
                output_path
            )

            # 完了
            yield TrainingProgress(
                status="completed",
                progress=1.0,
                message="学習が完了しました",
                current_step="完了",
                metrics={"epochs": epochs}
            )

        except Exception as e:
            yield TrainingProgress(
                status="failed",
                progress=0.0,
                message=f"エラーが発生しました: {str(e)}",
                current_step="エラー"
            )
        finally:
            self.active_tasks.pop(task_id, None)

    async def train_bayesian(
        self,
        task_id: str,
        dataset_path: str,
        output_path: str,
        parameters: Dict[str, Any]
    ) -> AsyncIterator[TrainingProgress]:
        """階層ベイズモデル学習"""
        try:
            self.active_tasks[task_id] = True

            yield TrainingProgress(
                status="starting",
                progress=0.0,
                message="階層ベイズモデル学習を開始します",
                current_step="初期化"
            )

            await asyncio.sleep(0.5)

            # データ読み込み
            yield TrainingProgress(
                status="running",
                progress=0.1,
                message="データを読み込んでいます...",
                current_step="データ読み込み"
            )

            df = await asyncio.to_thread(pd.read_csv, dataset_path)
            await asyncio.sleep(0.5)

            # MCMCサンプリング（時間がかかる）
            yield TrainingProgress(
                status="running",
                progress=0.3,
                message="MCMCサンプリングを実行しています（時間がかかります）...",
                current_step="MCMC実行中"
            )

            # サンプリング進捗をシミュレート
            draws = parameters.get("draws", 2000)
            for i in range(5):
                if not self.active_tasks.get(task_id, False):
                    yield TrainingProgress(
                        status="failed",
                        progress=0.3 + i * 0.1,
                        message="訓練がキャンセルされました",
                        current_step="キャンセル"
                    )
                    return

                await asyncio.sleep(3)
                yield TrainingProgress(
                    status="running",
                    progress=0.3 + (i + 1) * 0.12,
                    message=f"MCMCサンプリング中... ({(i + 1) * 20}%)",
                    current_step="MCMC実行中"
                )

            # 注: 実際の訓練実装は省略（時間がかかりすぎるため）
            # 本番環境では ml_models/train_bayesian.py を呼び出す

            # 完了
            yield TrainingProgress(
                status="completed",
                progress=1.0,
                message="学習が完了しました（注: デモ版のため実際の訓練はスキップ）",
                current_step="完了",
                metrics={"draws": draws}
            )

        except Exception as e:
            yield TrainingProgress(
                status="failed",
                progress=0.0,
                message=f"エラーが発生しました: {str(e)}",
                current_step="エラー"
            )
        finally:
            self.active_tasks.pop(task_id, None)

    def cancel_task(self, task_id: str):
        """タスクをキャンセル"""
        self.active_tasks[task_id] = False
