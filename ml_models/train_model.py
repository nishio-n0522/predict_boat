"""
LightGBMモデル訓練スクリプト

3着以内に入る確率を予測するモデルを訓練します。
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score,
    recall_score, f1_score, classification_report
)
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))


class BoatRacePredictor:
    """ボートレース予測モデル"""

    def __init__(self, params: dict = None):
        """
        初期化

        Args:
            params: LightGBMパラメータ
        """
        self.params = params or self._get_default_params()
        self.model = None
        self.feature_names = None

    def _get_default_params(self) -> dict:
        """デフォルトパラメータを取得"""
        return {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'seed': 42
        }

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        num_boost_round: int = 1000,
        early_stopping_rounds: int = 50
    ):
        """
        モデルを訓練

        Args:
            X_train: 訓練特徴量
            y_train: 訓練ラベル
            X_val: 検証特徴量
            y_val: 検証ラベル
            num_boost_round: ブースティングラウンド数
            early_stopping_rounds: Early stopping rounds
        """
        print("=" * 80)
        print("モデル訓練開始")
        print("=" * 80)
        print(f"訓練データ: {len(X_train)} 行")
        print(f"検証データ: {len(X_val)} 行")
        print(f"特徴量数: {X_train.shape[1]}")
        print()

        # LightGBMデータセット作成
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        # 訓練
        self.model = lgb.train(
            self.params,
            train_data,
            num_boost_round=num_boost_round,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'valid'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=early_stopping_rounds),
                lgb.log_evaluation(period=100)
            ]
        )

        self.feature_names = X_train.columns.tolist()

        print()
        print("=" * 80)
        print("訓練完了")
        print(f"Best iteration: {self.model.best_iteration}")
        print(f"Best score: {self.model.best_score['valid']['binary_logloss']:.4f}")
        print("=" * 80)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        予測実行

        Args:
            X: 特徴量

        Returns:
            np.ndarray: 予測確率
        """
        if self.model is None:
            raise ValueError("モデルが訓練されていません")

        return self.model.predict(X, num_iteration=self.model.best_iteration)

    def evaluate(self, X: pd.DataFrame, y: pd.Series, threshold: float = 0.5) -> dict:
        """
        モデルを評価

        Args:
            X: 特徴量
            y: ラベル
            threshold: 閾値

        Returns:
            dict: 評価指標
        """
        y_pred_proba = self.predict(X)
        y_pred = (y_pred_proba >= threshold).astype(int)

        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred),
            'f1': f1_score(y, y_pred),
            'roc_auc': roc_auc_score(y, y_pred_proba)
        }

        return metrics

    def save(self, path: str):
        """
        モデルを保存

        Args:
            path: 保存先パス
        """
        if self.model is None:
            raise ValueError("モデルが訓練されていません")

        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # モデルとメタデータを保存
        save_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'params': self.params
        }

        joblib.dump(save_data, model_path)
        print(f"モデルを保存しました: {model_path}")

    def load(self, path: str):
        """
        モデルを読み込み

        Args:
            path: モデルパス
        """
        save_data = joblib.load(path)
        self.model = save_data['model']
        self.feature_names = save_data['feature_names']
        self.params = save_data['params']

        print(f"モデルを読み込みました: {path}")

    def plot_feature_importance(self, top_n: int = 20, save_path: str = None):
        """
        特徴量重要度をプロット

        Args:
            top_n: 表示する上位N個
            save_path: 保存先パス（Noneの場合は表示のみ）
        """
        if self.model is None:
            raise ValueError("モデルが訓練されていません")

        importance = self.model.feature_importance(importance_type='gain')
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False).head(top_n)

        plt.figure(figsize=(10, 8))
        sns.barplot(data=feature_importance, x='importance', y='feature')
        plt.title(f'特徴量重要度 (Top {top_n})')
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"特徴量重要度を保存しました: {save_path}")
        else:
            plt.show()


def load_and_prepare_data(dataset_path: str, test_size: float = 0.2):
    """
    データを読み込んで前処理

    Args:
        dataset_path: データセットパス
        test_size: テストデータの割合

    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    print("データ読み込み中...")
    df = pd.read_csv(dataset_path)

    print(f"データサイズ: {len(df)} 行 x {len(df.columns)} 列")

    # 目的変数がないデータを除外
    df = df[df['target_top3'].notna()].copy()

    print(f"有効データ: {len(df)} 行")

    # 特徴量と目的変数を分離
    exclude_cols = [
        'target_top3', 'order_of_arrival',
        'race_date', 'stadium_id', 'race_index', 'race_name'
    ]
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    X = df[feature_cols].copy()
    y = df['target_top3'].copy()

    # 欠損値処理
    X = X.fillna(0)

    # データ分割（日付順で分割）
    # 訓練: 60%, 検証: 20%, テスト: 20%
    n_samples = len(X)
    train_end = int(n_samples * 0.6)
    val_end = int(n_samples * 0.8)

    X_train = X.iloc[:train_end]
    y_train = y.iloc[:train_end]

    X_val = X.iloc[train_end:val_end]
    y_val = y.iloc[train_end:val_end]

    X_test = X.iloc[val_end:]
    y_test = y.iloc[val_end:]

    print()
    print("データ分割:")
    print(f"  訓練: {len(X_train)} 行 (正例率: {y_train.mean():.3f})")
    print(f"  検証: {len(X_val)} 行 (正例率: {y_val.mean():.3f})")
    print(f"  テスト: {len(X_test)} 行 (正例率: {y_test.mean():.3f})")
    print()

    return X_train, X_val, X_test, y_train, y_val, y_test


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="LightGBMモデル訓練")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/processed/training_dataset.csv",
        help="訓練データセットパス"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models_trained/lightgbm_model.pkl",
        help="モデル保存先パス"
    )
    parser.add_argument(
        "--num-boost-round",
        type=int,
        default=1000,
        help="ブースティングラウンド数"
    )

    args = parser.parse_args()

    # データ読み込み
    X_train, X_val, X_test, y_train, y_val, y_test = load_and_prepare_data(
        args.dataset
    )

    # モデル訓練
    predictor = BoatRacePredictor()
    predictor.train(
        X_train, y_train,
        X_val, y_val,
        num_boost_round=args.num_boost_round
    )

    # 評価
    print("\n訓練データでの評価:")
    train_metrics = predictor.evaluate(X_train, y_train)
    for metric, value in train_metrics.items():
        print(f"  {metric}: {value:.4f}")

    print("\n検証データでの評価:")
    val_metrics = predictor.evaluate(X_val, y_val)
    for metric, value in val_metrics.items():
        print(f"  {metric}: {value:.4f}")

    print("\nテストデータでの評価:")
    test_metrics = predictor.evaluate(X_test, y_test)
    for metric, value in test_metrics.items():
        print(f"  {metric}: {value:.4f}")

    # モデル保存
    predictor.save(args.output)

    # 特徴量重要度をプロット
    importance_path = Path(args.output).parent / "feature_importance.png"
    predictor.plot_feature_importance(top_n=20, save_path=str(importance_path))


if __name__ == "__main__":
    main()
