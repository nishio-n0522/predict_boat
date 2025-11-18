# ボートレース予測AIウェブアプリケーション

機械学習を用いたボートレース予測システムのウェブアプリケーション。

## 機能概要

### 1. モデル学習
- **対応モデル**: LightGBM、Transformer、階層ベイズ
- **リアルタイム進捗表示**: WebSocketを用いた学習進捗のリアルタイム表示
- **パラメータ調整**: エポック数、バッチサイズ、学習率などの調整可能
- **データ指定**: 訓練データセットのパス指定

### 2. レース予測
- **モデル選択**: 学習済みモデルから選択
- **予測実行**: レース日、競艇場ID、レース番号を指定して予測
- **詳細表示**:
  - 各艇の3着以内確率
  - 推奨3連単ボックス買い
  - 特徴量重要度（モデルごとの手法）

### 3. モデル比較
- **複数モデル比較**: 最大3つのモデルを同時に比較
- **可視化**:
  - レーダーチャート（各艇の確率比較）
  - 推奨艇の比較テーブル
  - モデル間一致度
  - 各艇の統計（平均、標準偏差、範囲）

## 技術スタック

### バックエンド
- **FastAPI**: RESTful API
- **WebSocket**: リアルタイム進捗通知
- **Pydantic**: データバリデーション
- **Uvicorn**: ASGIサーバー

### フロントエンド
- **React 18**: UIフレームワーク
- **TypeScript**: 型安全性
- **Vite**: 高速ビルドツール
- **TailwindCSS**: ユーティリティファーストCSS
- **Recharts**: データ可視化
- **React Router**: ルーティング
- **Axios**: HTTP通信

## セットアップ

### 前提条件
- Python 3.9以上
- Node.js 18以上
- npm または yarn

### 1. 依存関係のインストール

#### バックエンド
```bash
# プロジェクトルートで実行
pip install -r requirements.txt
```

#### フロントエンド
```bash
cd frontend
npm install
```

### 2. 環境変数の設定

フロントエンドの環境変数を設定：
```bash
cd frontend
cp .env.example .env
```

`.env`ファイルを編集：
```env
VITE_API_BASE_URL=http://localhost:8000
```

## 起動方法

### 開発環境

#### 1. バックエンドサーバーを起動
```bash
# プロジェクトルートで実行
python backend/main.py
```

バックエンドは http://localhost:8000 で起動します。

APIドキュメントは http://localhost:8000/docs で確認できます。

#### 2. フロントエンドサーバーを起動
```bash
cd frontend
npm run dev
```

フロントエンドは http://localhost:5173 で起動します。

## ディレクトリ構造

```
predict_boat/
├── backend/                    # バックエンドAPI
│   ├── main.py                # FastAPIアプリケーション
│   ├── routers/               # APIルーター
│   │   ├── train.py          # 学習API
│   │   ├── predict.py        # 推論API
│   │   └── models.py         # モデル管理API
│   ├── services/              # ビジネスロジック
│   │   ├── training_service.py
│   │   └── prediction_service.py
│   └── schemas/               # Pydanticスキーマ
│       ├── train.py
│       ├── predict.py
│       └── models.py
│
├── frontend/                   # Reactフロントエンド
│   ├── src/
│   │   ├── pages/            # ページコンポーネント
│   │   │   ├── TrainingPage.tsx       # 学習実行ページ
│   │   │   ├── PredictionPage.tsx     # 予測実行ページ
│   │   │   └── ComparisonPage.tsx     # モデル比較ページ
│   │   ├── services/         # APIサービス
│   │   │   └── api.ts
│   │   ├── types/            # 型定義
│   │   │   └── index.ts
│   │   ├── App.tsx           # メインアプリ
│   │   └── main.tsx          # エントリーポイント
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── ml_models/                  # 機械学習モデル
│   ├── predict.py             # LightGBM予測
│   ├── predict_transformer.py # Transformer予測
│   ├── predict_bayesian.py    # 階層ベイズ予測
│   └── ...
│
└── models_trained/            # 訓練済みモデル保存先
```

## API エンドポイント

### 学習API
- `POST /api/train` - 学習を開始
- `WebSocket /api/train/ws/{task_id}` - 学習進捗をストリーミング
- `DELETE /api/train/{task_id}` - 学習をキャンセル

### 推論API
- `POST /api/predict` - レース予測
- `POST /api/predict/compare` - 複数モデル比較
- `POST /api/predict/feature-importance` - 特徴量重要度取得

### モデル管理API
- `GET /api/models` - モデル一覧取得
- `GET /api/models/{model_name}` - モデル情報取得
- `DELETE /api/models/{model_name}` - モデル削除

## 使用例

### 1. モデルを学習する

1. ブラウザで http://localhost:5173 にアクセス
2. 「モデル学習」をクリック
3. モデルタイプを選択（LightGBM / Transformer / 階層ベイズ）
4. パラメータを調整
5. 「学習を開始」ボタンをクリック
6. リアルタイムで進捗を確認

### 2. レースを予測する

1. 「レース予測」ページに移動
2. 学習済みモデルを選択
3. レース情報を入力（日付、競艇場ID、レース番号）
4. 「予測を実行」ボタンをクリック
5. 結果を確認：
   - 各艇の確率
   - 推奨3艇
   - 特徴量重要度

### 3. モデルを比較する

1. 「モデル比較」ページに移動
2. 比較したいモデルを複数選択
3. レース情報を入力
4. 「比較を実行」ボタンをクリック
5. 結果を確認：
   - レーダーチャート
   - 推奨艇の比較
   - モデル間一致度
   - 各艇の統計

## 開発

### バックエンドの追加開発

新しいAPIエンドポイントを追加する場合：

1. `backend/schemas/` にスキーマを定義
2. `backend/services/` にビジネスロジックを実装
3. `backend/routers/` にルーターを追加
4. `backend/main.py` でルーターを登録

### フロントエンドの追加開発

新しいページを追加する場合：

1. `frontend/src/pages/` に新しいページコンポーネントを作成
2. `frontend/src/App.tsx` にルートを追加
3. 必要に応じて `frontend/src/types/` に型を追加
4. 必要に応じて `frontend/src/services/api.ts` にAPI呼び出しを追加

## トラブルシューティング

### バックエンドが起動しない

```bash
# 依存関係を再インストール
pip install -r requirements.txt

# ポートが使用されているか確認
lsof -i :8000
```

### フロントエンドが起動しない

```bash
# node_modulesを削除して再インストール
cd frontend
rm -rf node_modules package-lock.json
npm install

# ポートが使用されているか確認
lsof -i :5173
```

### CORS エラーが発生する

バックエンドの `backend/main.py` でCORS設定を確認：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WebSocketが接続できない

1. バックエンドが起動しているか確認
2. ブラウザのコンソールでエラーを確認
3. ファイアウォール設定を確認

## 本番環境へのデプロイ

### バックエンド

```bash
# Gunicornを使用する場合
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### フロントエンド

```bash
cd frontend
npm run build
# distフォルダをWebサーバーにデプロイ
```

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します！

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。
