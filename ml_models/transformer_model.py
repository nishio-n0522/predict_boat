"""
時系列Transformerモデル

ボートレース予測用のTransformerベースモデル。
- Feature-wise Attention
- 事前重要度の組み込み
- Attention Weightsの可視化
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple
import numpy as np


class FeatureGating(nn.Module):
    """
    Feature-wise Attention Gate

    各特徴量に学習可能な重要度を与える
    """

    def __init__(self, n_features: int, init_weights: Optional[np.ndarray] = None):
        """
        初期化

        Args:
            n_features: 特徴量数
            init_weights: 初期重要度（Noneの場合は均等）
        """
        super().__init__()

        if init_weights is not None:
            # 事前重要度がある場合は初期値として設定
            self.gate_weights = nn.Parameter(torch.tensor(init_weights, dtype=torch.float32))
        else:
            # 均等な重みで初期化
            self.gate_weights = nn.Parameter(torch.ones(n_features))

        # ゲート用の変換層
        self.gate_transform = nn.Sequential(
            nn.Linear(n_features, n_features),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        前向き伝播

        Args:
            x: 入力 (batch_size, seq_len, n_features)

        Returns:
            Tuple: (ゲート済み特徴量, ゲート重み)
        """
        # ゲート重みを計算
        gate = self.gate_transform(x)  # (batch_size, seq_len, n_features)

        # 事前重要度を適用
        gate = gate * self.gate_weights.unsqueeze(0).unsqueeze(0)

        # 特徴量にゲートを適用
        gated_x = x * gate

        return gated_x, gate


class PositionalEncoding(nn.Module):
    """位置エンコーディング"""

    def __init__(self, d_model: int, max_len: int = 100):
        """
        初期化

        Args:
            d_model: モデルの次元数
            max_len: 最大系列長
        """
        super().__init__()

        # 位置エンコーディングを事前計算
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)

        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向き伝播

        Args:
            x: 入力 (batch_size, seq_len, d_model)

        Returns:
            位置エンコーディングを追加した入力
        """
        return x + self.pe[:, :x.size(1), :]


class BoatRaceTransformer(nn.Module):
    """
    ボートレース予測用Transformerモデル

    6艇分の特徴量から、各艇が3着以内に入る確率を予測
    """

    def __init__(
        self,
        n_features: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 3,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        feature_importance: Optional[np.ndarray] = None,
        use_feature_gating: bool = True
    ):
        """
        初期化

        Args:
            n_features: 入力特徴量数
            d_model: モデルの次元数
            nhead: アテンションヘッド数
            num_layers: Transformerレイヤー数
            dim_feedforward: フィードフォワード層の次元数
            dropout: ドロップアウト率
            feature_importance: 事前の特徴量重要度
            use_feature_gating: Feature Gatingを使用するか
        """
        super().__init__()

        self.n_features = n_features
        self.d_model = d_model
        self.use_feature_gating = use_feature_gating

        # Feature Gating
        if use_feature_gating:
            self.feature_gate = FeatureGating(n_features, feature_importance)

        # 入力射影
        self.input_projection = nn.Linear(n_features, d_model)

        # 位置エンコーディング
        self.pos_encoder = PositionalEncoding(d_model, max_len=6)  # 6艇

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # 出力層
        self.output_projection = nn.Sequential(
            nn.Linear(d_model, dim_feedforward // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward // 2, 1)
        )

        # Attention weightsを保存するための変数
        self.attention_weights = None
        self.feature_gate_weights = None

        # フックを登録してAttention weightsを取得
        self._register_attention_hooks()

    def _register_attention_hooks(self):
        """Attention weightsを取得するためのフックを登録"""
        def hook_fn(module, input, output):
            # TransformerEncoderLayerの出力からattention weightsを取得
            if hasattr(module, 'self_attn'):
                self.attention_weights = output

        # 最後のTransformerレイヤーにフックを登録
        if hasattr(self.transformer_encoder, 'layers'):
            self.transformer_encoder.layers[-1].register_forward_hook(hook_fn)

    def forward(
        self,
        x: torch.Tensor,
        return_attention: bool = False
    ) -> Tuple[torch.Tensor, Optional[Dict]]:
        """
        前向き伝播

        Args:
            x: 入力特徴量 (batch_size, 6, n_features) - 6艇分
            return_attention: Attention weightsを返すか

        Returns:
            Tuple: (予測確率, attention情報)
                - 予測確率: (batch_size, 6) - 各艇が3着以内に入る確率
                - attention情報: {'attention_weights': ..., 'feature_gates': ...}
        """
        batch_size = x.size(0)

        # Feature Gatingを適用
        if self.use_feature_gating:
            x, feature_gates = self.feature_gate(x)
            self.feature_gate_weights = feature_gates
        else:
            feature_gates = None

        # 入力射影
        x = self.input_projection(x)  # (batch_size, 6, d_model)

        # 位置エンコーディング
        x = self.pos_encoder(x)

        # Transformer Encoder
        x = self.transformer_encoder(x)  # (batch_size, 6, d_model)

        # 出力射影
        logits = self.output_projection(x).squeeze(-1)  # (batch_size, 6)

        # シグモイドで確率に変換
        probs = torch.sigmoid(logits)

        # Attention情報を返す
        attention_info = None
        if return_attention:
            attention_info = {
                'attention_weights': self.attention_weights,
                'feature_gates': feature_gates
            }

        return probs, attention_info

    def get_feature_importance(self) -> np.ndarray:
        """
        Feature Gatingから特徴量重要度を取得

        Returns:
            np.ndarray: 特徴量重要度
        """
        if not self.use_feature_gating:
            return None

        with torch.no_grad():
            importance = self.feature_gate.gate_weights.cpu().numpy()

        return importance


class BoatRaceTransformerPredictor:
    """
    Transformerモデルのラッパークラス

    訓練・予測・評価を簡単に行えるようにする
    """

    def __init__(
        self,
        n_features: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 3,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        feature_importance: Optional[np.ndarray] = None,
        use_feature_gating: bool = True,
        device: str = None
    ):
        """
        初期化

        Args:
            n_features: 入力特徴量数
            d_model: モデルの次元数
            nhead: アテンションヘッド数
            num_layers: Transformerレイヤー数
            dim_feedforward: フィードフォワード層の次元数
            dropout: ドロップアウト率
            feature_importance: 事前の特徴量重要度
            use_feature_gating: Feature Gatingを使用するか
            device: デバイス (cpu/cuda)
        """
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        self.model = BoatRaceTransformer(
            n_features=n_features,
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            feature_importance=feature_importance,
            use_feature_gating=use_feature_gating
        ).to(self.device)

        self.n_features = n_features
        self.feature_names = None

    def predict(
        self,
        X: np.ndarray,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[Dict]]:
        """
        予測実行

        Args:
            X: 入力特徴量 (n_races, 6, n_features)
            return_attention: Attention weightsを返すか

        Returns:
            Tuple: (予測確率, attention情報)
        """
        self.model.eval()

        with torch.no_grad():
            # numpy -> torch
            X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)

            # 予測
            probs, attention_info = self.model(X_tensor, return_attention=return_attention)

            # torch -> numpy
            probs_np = probs.cpu().numpy()

        return probs_np, attention_info

    def save(self, path: str):
        """モデルを保存"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'n_features': self.n_features,
            'feature_names': self.feature_names,
            'device': str(self.device)
        }, path)
        print(f"モデルを保存しました: {path}")

    def load(self, path: str):
        """モデルを読み込み"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.n_features = checkpoint['n_features']
        self.feature_names = checkpoint.get('feature_names')
        print(f"モデルを読み込みました: {path}")

    def get_feature_importance(self) -> np.ndarray:
        """特徴量重要度を取得"""
        return self.model.get_feature_importance()


if __name__ == "__main__":
    # テスト
    print("=" * 80)
    print("ボートレース予測Transformerモデル テスト")
    print("=" * 80)

    # パラメータ
    batch_size = 4
    n_features = 20

    # ダミーデータ
    X = np.random.randn(batch_size, 6, n_features).astype(np.float32)

    # 事前重要度（例）
    feature_importance = np.random.rand(n_features).astype(np.float32)

    # モデル作成
    predictor = BoatRaceTransformerPredictor(
        n_features=n_features,
        d_model=128,
        nhead=8,
        num_layers=3,
        feature_importance=feature_importance,
        use_feature_gating=True
    )

    print(f"デバイス: {predictor.device}")
    print(f"入力形状: {X.shape}")

    # 予測
    probs, attention_info = predictor.predict(X, return_attention=True)

    print(f"出力形状: {probs.shape}")
    print(f"予測確率サンプル:")
    print(probs[0])

    # 特徴量重要度
    importance = predictor.get_feature_importance()
    print(f"\n特徴量重要度:")
    print(importance)

    print("\n✅ テスト成功")
