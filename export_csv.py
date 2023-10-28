from pathlib import Path
import csv

from sqlalchemy import create_engine, MetaData

# SQLiteデータベースへの接続
DATABASE_URL = "sqlite:///sqlite.sqlite3"
engine = create_engine(DATABASE_URL)

# メタデータの取得とテーブルの選択
metadata = MetaData()
metadata.reflect(engine)

table_names = list(metadata.tables.keys())

csv_dir = Path("csv_data")
csv_dir.mkdir(parents=True, exist_ok=True)

for table_name in table_names:

    your_table = metadata.tables[table_name]

    # テーブルの全レコードを取得
    connection = engine.connect()
    results = connection.execute(your_table.select()).fetchall()

    # CSVファイルとして書き出し
    with open(csv_dir / f"{table_name}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        
        # ヘッダーを書き込む
        writer.writerow(your_table.columns.keys())
        
        # レコードを書き込む
        writer.writerows(results)
