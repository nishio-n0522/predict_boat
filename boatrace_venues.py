"""
ボートレース場の情報を管理するモジュール

全24場の競艇場情報（ID、名前、URL）を定義
"""

from typing import Dict, List, Optional


class VenueInfo:
    """競艇場情報を保持するクラス"""

    def __init__(self, venue_id: int, name: str, name_en: str, url: str):
        """
        初期化

        Args:
            venue_id: 競艇場ID
            name: 競艇場名（日本語）
            name_en: 競艇場名（英語・ファイル名用）
            url: 公式サイトURL
        """
        self.venue_id = venue_id
        self.name = name
        self.name_en = name_en
        self.url = url

    def __repr__(self):
        return f"VenueInfo(id={self.venue_id}, name={self.name}, url={self.url})"


# 全24場の競艇場情報
# IDは公式のボートレース場番号に準拠
VENUES: Dict[int, VenueInfo] = {
    1: VenueInfo(1, "桐生", "kiryu", "https://www.kiryu-kyotei.com/"),
    2: VenueInfo(2, "戸田", "toda", "https://www.boatrace-toda.jp/"),
    3: VenueInfo(3, "江戸川", "edogawa", "https://www.boatrace-edogawa.com/"),
    4: VenueInfo(4, "平和島", "heiwajima", "https://www.heiwajima.gr.jp/"),
    5: VenueInfo(5, "多摩川", "tamagawa", "https://www.boatrace-tamagawa.com/"),
    6: VenueInfo(6, "浜名湖", "hamanako", "https://www.boatrace-hamanako.jp/"),
    7: VenueInfo(7, "蒲郡", "gamagori", "https://www.gamagori-kyotei.com/"),
    8: VenueInfo(8, "常滑", "tokoname", "https://www.boatrace-tokoname.jp/"),
    9: VenueInfo(9, "津", "tsu", "https://www.boatrace-tsu.com/"),
    10: VenueInfo(10, "三国", "mikuni", "https://www.boatrace-mikuni.jp/"),
    11: VenueInfo(11, "びわこ", "biwako", "https://www.boatrace-biwako.jp/"),
    12: VenueInfo(12, "住之江", "suminoe", "https://www.boatrace-suminoe.jp/"),
    13: VenueInfo(13, "尼崎", "amagasaki", "https://www.boatrace-amagasaki.jp/"),
    14: VenueInfo(14, "鳴門", "naruto", "https://www.n14.jp/"),
    15: VenueInfo(15, "丸亀", "marugame", "https://www.marugameboat.jp/"),
    16: VenueInfo(16, "児島", "kojima", "https://www.kojimaboat.jp/"),
    17: VenueInfo(17, "宮島", "miyajima", "https://www.boatrace-miyajima.com/"),
    18: VenueInfo(18, "徳山", "tokuyama", "https://www.boatrace-tokuyama.jp/"),
    19: VenueInfo(19, "下関", "shimonoseki", "https://www.boatrace-shimonoseki.jp/"),
    20: VenueInfo(20, "若松", "wakamatsu", "https://www.wmb.jp/"),
    21: VenueInfo(21, "芦屋", "ashiya", "https://www.boatrace-ashiya.com/"),
    22: VenueInfo(22, "福岡", "fukuoka", "https://www.boatrace-fukuoka.com/"),
    23: VenueInfo(23, "唐津", "karatsu", "https://www.boatrace-karatsu.jp/"),
    24: VenueInfo(24, "大村", "omura", "https://omurakyotei.jp/"),
}


def get_venue_by_id(venue_id: int) -> Optional[VenueInfo]:
    """
    IDから競艇場情報を取得

    Args:
        venue_id: 競艇場ID

    Returns:
        競艇場情報、見つからない場合はNone
    """
    return VENUES.get(venue_id)


def get_venue_by_name(name: str) -> Optional[VenueInfo]:
    """
    名前から競艇場情報を取得

    Args:
        name: 競艇場名（日本語または英語）

    Returns:
        競艇場情報、見つからない場合はNone
    """
    for venue in VENUES.values():
        if venue.name == name or venue.name_en == name.lower():
            return venue
    return None


def get_all_venues() -> List[VenueInfo]:
    """
    全競艇場情報を取得

    Returns:
        競艇場情報のリスト
    """
    return sorted(VENUES.values(), key=lambda v: v.venue_id)


def get_venue_names() -> List[str]:
    """
    全競艇場名を取得

    Returns:
        競艇場名（日本語）のリスト
    """
    return [venue.name for venue in get_all_venues()]


def get_venue_ids() -> List[int]:
    """
    全競艇場IDを取得

    Returns:
        競艇場IDのリスト
    """
    return sorted(VENUES.keys())


# 各会場のサイト構造パターン定義
# 実際のサイト構造に応じて調整が必要
VENUE_URL_PATTERNS = {
    # パターン1: /race/YYYYMMDD/形式（多くの会場で使用）
    "pattern1": [
        "race/{date}/",
        "race/{date}/{race_number:02d}/",
        "race/{date}/racer/",
        "race/{date}/{race_number:02d}/live/",
    ],
    # パターン2: /races/YYYYMMDD/形式
    "pattern2": [
        "races/{date}/",
        "races/{date}/{race_number}/",
        "races/{date}/racer/",
        "races/{date}/{race_number}/live/",
    ],
    # パターン3: クエリパラメータ形式
    "pattern3": [
        "race?date={date}",
        "race?date={date}&race={race_number}",
        "racer?date={date}",
        "live?date={date}&race={race_number}",
    ],
    # パターン4: 日付なし（当日自動表示）
    "pattern4": [
        "today/",
        "today/race{race_number}/",
        "today/racer/",
        "today/race{race_number}/live/",
    ],
}


# 各会場のURL構造パターンマッピング
# 実際のサイトを調査して設定する必要がある
VENUE_PATTERN_MAP = {
    1: "pattern1",   # 桐生
    2: "pattern1",   # 戸田
    3: "pattern1",   # 江戸川
    4: "pattern1",   # 平和島
    5: "pattern1",   # 多摩川
    6: "pattern1",   # 浜名湖
    7: "pattern1",   # 蒲郡
    8: "pattern1",   # 常滑
    9: "pattern1",   # 津
    10: "pattern1",  # 三国
    11: "pattern1",  # びわこ
    12: "pattern1",  # 住之江
    13: "pattern1",  # 尼崎
    14: "pattern1",  # 鳴門
    15: "pattern1",  # 丸亀
    16: "pattern1",  # 児島
    17: "pattern1",  # 宮島
    18: "pattern1",  # 徳山
    19: "pattern1",  # 下関
    20: "pattern1",  # 若松
    21: "pattern1",  # 芦屋
    22: "pattern1",  # 福岡
    23: "pattern1",  # 唐津
    24: "pattern1",  # 大村
}


def get_venue_url_patterns(venue_id: int) -> List[str]:
    """
    指定した会場のURLパターンを取得

    Args:
        venue_id: 競艇場ID

    Returns:
        URLパターンのリスト
    """
    pattern_name = VENUE_PATTERN_MAP.get(venue_id, "pattern1")
    return VENUE_URL_PATTERNS.get(pattern_name, VENUE_URL_PATTERNS["pattern1"])


if __name__ == "__main__":
    # テスト用
    print("=== 全競艇場情報 ===")
    for venue in get_all_venues():
        print(f"{venue.venue_id:2d}. {venue.name:6s} ({venue.name_en:12s}) - {venue.url}")

    print("\n=== ID検索テスト ===")
    venue = get_venue_by_id(18)
    if venue:
        print(f"ID=18: {venue.name} - {venue.url}")

    print("\n=== 名前検索テスト ===")
    venue = get_venue_by_name("徳山")
    if venue:
        print(f"徳山: ID={venue.venue_id} - {venue.url}")

    venue = get_venue_by_name("tokuyama")
    if venue:
        print(f"tokuyama: ID={venue.venue_id} - {venue.url}")
