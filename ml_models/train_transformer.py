"""
Transformer訓練スクリプト

時系列Transformerモデルを訓練します。
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from tqdm import tqdm
import matplotlib.pyplot as plt

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from ml_models.transformer_model import BoatRaceTransformer, BoatRaceTransformerPredictor
from ml_models.feature_importance_analyzer import FeatureImportanceAnalyzer


class BoatRaceDataset(Dataset):
    """ボートレースデータセット"""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        """
        初期化

        Args:
            X: 特徴量 (n_races, 6, n_features)
            y: ラベル (n_races, 6)
        """
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def prepare_data_for_transformer(dataset_path: str):
    """
    データセットをTransformer用に変換

    Args:
        dataset_path: データセットパス

    Returns:
        tuple: (X_train, y_train, X_val, y_val, X_test, y_test, feature_names)
    """
    print("データ読み込み中...")
    df = pd.read_csv(dataset_path)

    print(f"データサイズ: {len(df)} 行")

    # 目的変数がないデータを除外
    df = df[df['target_top3'].notna()].copy()

    print(f"有効データ: {len(df)} 行")

    # 特徴量と目的変数を分離
    exclude_cols = [
        'target_top3', 'order_of_arrival',
        'race_date', 'stadium_id', 'race_index', 'race_name'
    ]
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    # レースごとにグループ化
    race_groups = df.groupby(['race_date', 'stadium_id', 'race_index'])

    X_list = []
    y_list = []

    for (race_date, stadium_id, race_index), race_df in race_groups:
        if len(race_df) != 6:  # 6艇揃っていない場合はスキップ
            continue

        # 特徴量
        X_race = race_df[feature_cols].fillna(0).values  # (6, n_features)

        # ラベル
        y_race = race_df['target_top3'].values  # (6,)

        X_list.append(X_race)
        y_list.append(y_race)

    X = np.array(X_list)  # (n_races, 6, n_features)
    y = np.array(y_list)  # (n_races, 6)

    print(f"\nレース数: {len(X)}")
    print(f"特徴量形状: {X.shape}")
    print(f"ラベル形状: {y.shape}")

    # データ分割（日付順で分割）
    n_races = len(X)
    train_end = int(n_races * 0.6)
    val_end = int(n_races * 0.8)

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    print()
    print("データ分割:")
    print(f"  訓練: {len(X_train)} レース")
    print(f"  検証: {len(X_val)} レース")
    print(f"  テスト: {len(X_test)} レース")
    print()

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols


def train_epoch(model, dataloader, optimizer, criterion, device):
    """1エポック訓練"""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for X_batch, y_batch in dataloader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)

        optimizer.zero_grad()

        # 順伝播
        probs, _ = model(X_batch)

        # 損失計算
        loss = criterion(probs, y_batch)

        # 逆伝播
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        # 予測を保存
        all_preds.append(probs.detach().cpu().numpy())
        all_labels.append(y_batch.cpu().numpy())

    avg_loss = total_loss / len(dataloader)

    # 全体の精度を計算
    all_preds = np.concatenate(all_preds).flatten()
    all_labels = np.concatenate(all_labels).flatten()

    return avg_loss


def evaluate(model, dataloader, criterion, device):
    """評価"""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            # 順伝播
            probs, _ = model(X_batch)

            # 損失計算
            loss = criterion(probs, y_batch)
            total_loss += loss.item()

            # 予測を保存
            all_preds.append(probs.cpu().numpy())
            all_labels.append(y_batch.cpu().numpy())

    avg_loss = total_loss / len(dataloader)

    # 全体の精度を計算
    all_preds = np.concatenate(all_preds).flatten()
    all_labels = np.concatenate(all_labels).flatten()

    # メトリクス
    metrics = {
        'loss': avg_loss,
        'accuracy': accuracy_score(all_labels, (all_preds >= 0.5).astype(int)),
        'precision': precision_score(all_labels, (all_preds >= 0.5).astype(int)),
        'recall': recall_score(all_labels, (all_preds >= 0.5).astype(int)),
        'f1': f1_score(all_labels, (all_preds >= 0.5).astype(int)),
        'roc_auc': roc_auc_score(all_labels, all_preds)
    }

    return metrics


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Transformer訓練")
    parser.add_argument("--dataset", type=str, default="data/processed/training_dataset.csv")
    parser.add_argument("--output", type=str, default="models_trained/transformer_model.pt")
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--nhead", type=int, default=8)
    parser.add_argument("--num-layers", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--use-feature-gating", action="store_true", default=True)

    args = parser.parse_args()

    # データ準備
    X_train, y_train, X_val, y_val, X_test, y_test, feature_names = prepare_data_for_transformer(
        args.dataset
    )

    n_features = X_train.shape[2]

    # Dataset & DataLoader
    train_dataset = BoatRaceDataset(X_train, y_train)
    val_dataset = BoatRaceDataset(X_val, y_val)
    test_dataset = BoatRaceDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)

    # デバイス
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"デバイス: {device}")

    # モデル作成
    model = BoatRaceTransformer(
        n_features=n_features,
        d_model=args.d_model,
        nhead=args.nhead,
        num_layers=args.num_layers,
        use_feature_gating=args.use_feature_gating
    ).to(device)

    print(f"\nモデル構成:")
    print(f"  特徴量数: {n_features}")
    print(f"  d_model: {args.d_model}")
    print(f"  nhead: {args.nhead}")
    print(f"  num_layers: {args.num_layers}")
    print(f"  Feature Gating: {args.use_feature_gating}")

    # 最適化器・損失関数
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCELoss()

    # 訓練
    print("\n" + "=" * 80)
    print("訓練開始")
    print("=" * 80)

    best_val_loss = float('inf')
    history = {'train_loss': [], 'val_loss': [], 'val_roc_auc': []}

    for epoch in range(args.epochs):
        # 訓練
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)

        # 検証
        val_metrics = evaluate(model, val_loader, criterion, device)

        # 記録
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_metrics['loss'])
        history['val_roc_auc'].append(val_metrics['roc_auc'])

        # 表示
        print(f"Epoch {epoch+1}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_metrics['loss']:.4f} | "
              f"Val ROC-AUC: {val_metrics['roc_auc']:.4f}")

        # ベストモデル保存
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'n_features': n_features,
                'feature_names': feature_names,
                'args': vars(args)
            }, output_path)

    print("\n" + "=" * 80)
    print("訓練完了")
    print("=" * 80)

    # テスト評価
    print("\nテストデータでの評価:")
    test_metrics = evaluate(model, test_loader, criterion, device)
    for metric, value in test_metrics.items():
        print(f"  {metric}: {value:.4f}")

    # 学習曲線をプロット
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    axes[0].plot(history['train_loss'], label='Train')
    axes[0].plot(history['val_loss'], label='Validation')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Learning Curve')
    axes[0].legend()
    axes[0].grid(True)

    axes[1].plot(history['val_roc_auc'])
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('ROC-AUC')
    axes[1].set_title('Validation ROC-AUC')
    axes[1].grid(True)

    plt.tight_layout()

    curve_path = Path(args.output).parent / "learning_curve.png"
    plt.savefig(curve_path, dpi=300, bbox_inches='tight')
    print(f"\n学習曲線を保存しました: {curve_path}")

    print(f"\nモデルを保存しました: {args.output}")


if __name__ == "__main__":
    main()
