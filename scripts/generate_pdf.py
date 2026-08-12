#!/usr/bin/env python3
"""
地理風水鑑定書PDF生成スクリプト

使い方:
    python3 generate_pdf.py <input.json> <output.pdf> [--type A|B]

--type A : ネット鑑定（現地調査なし、入力フォームベース）。assets/template_typeA.html を使用
--type B : 現地調査＋巒頭分析（デフォルト）。assets/template.html を使用

入力JSONのスキーマは references/data_schema.md（TypeB）/ data_schema_typeA.md（TypeA）を参照。
鑑定士名・屋号のみを表示し、系譜情報は出力に含めない。
"""
import sys
import re
import json
import argparse
import shutil
from pathlib import Path
from datetime import date
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML
except ImportError:
    print("weasyprint が見つかりません。`pip install weasyprint --break-system-packages` を実行してください。", file=sys.stderr)
    sys.exit(1)

SKILL_DIR = Path(__file__).resolve().parent.parent

# pyIGRF は係数ファイルをパッケージ内の固定パスから読むが、
# pip配布物に含まれていないことがあるため、同梱の係数ファイルで補完する。
# （pyIGRFはimport時に係数ファイルを即読み込むため、importlib.util.find_specで
# 　モジュールを実行せずに設置先パスだけ特定してから、事前にファイルを配置する）
import importlib.util as _ilu
_spec = _ilu.find_spec("pyIGRF")
if _spec and _spec.origin:
    _pkg_coeffs_path = Path(_spec.origin).resolve().parent / "src" / "igrf14coeffs.txt"
    _bundled_coeffs = SKILL_DIR / "assets" / "igrf14coeffs.txt"
    if _bundled_coeffs.exists() and not _pkg_coeffs_path.exists():
        _pkg_coeffs_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(_bundled_coeffs, _pkg_coeffs_path)

try:
    import pyIGRF
    _IGRF_AVAILABLE = True
except Exception:
    _IGRF_AVAILABLE = False

TEMPLATE_BY_TYPE = {
    "A": "template_typeA.html",
    "B": "template.html",
}

DIRECTION_TO_CLASS = {
    "北": "n", "北東": "ne", "東": "e", "南東": "se",
    "南": "s", "南西": "sw", "西": "w", "北西": "nw",
    "中央": "c",
}

DIRECTION_TO_DEGREES = {
    "北": 0, "北東": 45, "東": 90, "南東": 135,
    "南": 180, "南西": 225, "西": 270, "北西": 315,
}
DEGREES_TO_DIRECTION = {v: k for k, v in DIRECTION_TO_DEGREES.items()}

OPPOSITE_DIRECTION = {
    "北": "南", "南": "北", "東": "西", "西": "東",
    "北東": "南西", "南西": "北東", "南東": "北西", "北西": "南東",
}

# 都道府県庁所在地における西偏角（2020.0年値、度）
# 出典：国土地理院「日本各地の偏角」https://www.gsi.go.jp/buturisokuchi/geomag_index.html
# GSIの磁気図は5年おきに更新される。以下は2020.0年値をベースに、
# 直近の変化傾向（+0.3〜0.4度/5年）から2026年時点の概算値として +0.4 を加算している。
# 精度が必要な場合は「地磁気値(予測値)計算サイト」で都度確認すること。
_DECLINATION_2020 = {
    "北海道": 9.7, "青森県": 8.7, "岩手県": 8.6, "宮城県": 8.6, "秋田県": 8.8, "山形県": 7.5, "福島県": 8.1,
    "茨城県": 7.5, "栃木県": 7.9, "群馬県": 8.0, "埼玉県": 7.7, "千葉県": 7.5, "東京都": 7.6, "神奈川県": 7.6,
    "新潟県": 8.7, "富山県": 8.3, "石川県": 8.3, "福井県": 8.5, "山梨県": 6.6, "長野県": 8.0,
    "岐阜県": 8.1, "静岡県": 7.2, "愛知県": 8.0, "三重県": 7.7,
    "滋賀県": 7.9, "京都府": 7.9, "大阪府": 7.6, "兵庫県": 7.8, "奈良県": 7.9, "和歌山県": 7.7,
    "鳥取県": 8.5, "島根県": 8.4, "岡山県": 7.9, "広島県": 7.8, "山口県": 7.7,
    "徳島県": 7.7, "香川県": 7.9, "愛媛県": 7.5, "高知県": 7.7,
    "福岡県": 7.7, "佐賀県": 7.6, "長崎県": 7.2, "熊本県": 7.2, "大分県": 7.6,
    "宮崎県": 7.0, "鹿児島県": 7.2, "沖縄県": 5.5,
}
_DECLINATION_EXTRAPOLATION = 0.4  # 2020.0年値→現在の概算補正（度）
PREFECTURE_DECLINATION = {k: round(v + _DECLINATION_EXTRAPOLATION, 1) for k, v in _DECLINATION_2020.items()}


def get_declination_igrf(latitude: float, longitude: float):
    """緯度経度からIGRF-14モデルで偏角を直接計算する（国土地理院公表値との誤差0.1度以内を確認済み）。
    現在の年（西暦、小数）を使用して現時点の推定値を返す。"""
    if not _IGRF_AVAILABLE:
        return None
    year_decimal = date.today().year + (date.today().timetuple().tm_yday / 365.25)
    D, I, H, X, Y, Z, F = pyIGRF.igrf_value(latitude, longitude, 0, year_decimal)
    return round(abs(D), 1)


def get_declination(data: dict):
    """緯度経度があればIGRFで直接計算（市区町村レベルの精度）、
    なければ都道府県庁所在地の代表値にフォールバックする。"""
    lat, lon = data.get("latitude"), data.get("longitude")
    if lat is not None and lon is not None:
        igrf_result = get_declination_igrf(float(lat), float(lon))
        if igrf_result is not None:
            return igrf_result, "igrf"
    prefecture = (data.get("prefecture") or "").strip()
    return PREFECTURE_DECLINATION.get(prefecture), "prefecture"


def correct_direction_to_magnetic(direction_label: str, declination: float):
    """真北基準の方位ラベルを、偏角を用いて磁北基準の方位ラベルに変換する（8方位に丸める）。
    磁北方位 = 真北方位 + 西偏角（度）
    「中央」は方位角を持たない特別な位置（中宮・太極）のため補正対象外。"""
    if not direction_label or declination is None or direction_label == "中央":
        return direction_label
    base_deg = DIRECTION_TO_DEGREES.get(direction_label)
    if base_deg is None:
        return direction_label
    corrected = round((base_deg + declination) / 45) * 45 % 360
    return DEGREES_TO_DIRECTION[corrected]

SECTION_LABELS = {
    "greeting": "ごあいさつ・鑑定概要",
    "life_gua": "あなたの命卦",
    "luantou": "巒頭（形勢）分析",
    "rooms": "お部屋ごとの方位鑑定",
    "xuankong": "玄空飛星分析",
    "bazhai": "八宅法分析",
    "room_energy": "お写真から見る室内の気の流れ",
    "family": "ご家族の方位鑑定",
    "scores": "総合エネルギーバランス",
    "actions": "開運行動プラン",
    "qimen": "吉日・タイミングのご案内",
    "themes": "ご相談内容に応じた重点解説",
}


def build_section_numbers(data: dict):
    """データに含まれるキーから、章の並び・番号・目次を動的に組み立てる（TypeA/TypeB共通）"""
    order = ["greeting"]
    if data.get("life_gua"):
        order.append("life_gua")
    if data.get("luantou_rows"):
        order.append("luantou")
    if data.get("rooms"):
        order.append("rooms")
    if data.get("xuankong_lead") or data.get("xuankong_rows"):
        order.append("xuankong")
    if data.get("bazhai_rows"):
        order.append("bazhai")
    if data.get("room_energy_photos"):
        order.append("room_energy")
    if data.get("family_members"):
        order.append("family")
    if data.get("scores"):
        order.append("scores")
    if data.get("actions"):
        order.append("actions")
    if data.get("qimen"):
        order.append("qimen")
    if data.get("theme_sections"):
        order.append("themes")

    numbers = {}
    toc = []
    for i, key in enumerate(order, start=1):
        numbers[key] = i
        toc.append({"number": i, "title": SECTION_LABELS[key]})
    return numbers, toc


def _parse_directions(text: str) -> list:
    """「東南・南・北・東」のような文字列を方位クラスのリストに変換"""
    if not text:
        return []
    parts = [p.strip() for p in text.replace("、", "・").replace(",", "・").split("・")]
    classes = []
    for p in parts:
        # 「東南」のような表記のゆれを「南東」に正規化
        normalized = p.replace("東南", "南東").replace("西南", "南西").replace("東北", "北東").replace("西北", "北西")
        cls = DIRECTION_TO_CLASS.get(normalized)
        if cls:
            classes.append(cls)
    return classes


def _direction_base_class(text: str):
    """「南西（座）」のような表記から基本方位を抜き出し、クラス名に変換する"""
    if not text:
        return None
    base = re.split(r"[（(]", text)[0].strip()
    base = base.replace("東南", "南東").replace("西南", "南西").replace("東北", "北東").replace("西北", "北西")
    return DIRECTION_TO_CLASS.get(base)


def enrich_directional_data(data: dict) -> dict:
    """磁北補正・座向きの自動算出・九宮コンパス表示用データの付与を行う"""

    # --- 磁北補正 ---
    # 「間取り図・登記図に記載の方角を見た」場合のみ、真北→磁北の補正を行う。
    # スマホのコンパスアプリ等で直接計測した場合は、すでに磁北基準のため補正しない。
    declination = None
    declination_method = None
    direction_source = data.get("direction_source", "floor_plan")
    if direction_source == "floor_plan":
        declination, declination_method = get_declination(data)
        data["declination_applied"] = declination
        if declination is not None:
            if declination_method == "igrf":
                basis_text = f"ご住所の緯度経度から、国際標準の地磁気モデル（IGRF）を用いて市区町村レベルで算出した偏角は約{declination}度です。"
            else:
                basis_text = f"{data.get('prefecture', 'ご住所の都道府県')}の代表値（都道府県庁所在地基準）としての偏角は約{declination}度です。"
            data["magnetic_note"] = (
                f"{basis_text}"
                "間取り図に記載の方位は真北基準であることが一般的なため、"
                "国土地理院の地磁気観測データに基づき、"
                "この鑑定では方位を磁北基準に補正した上で判定しています。"
            )
    else:
        data["declination_applied"] = 0.0

    def correct(label):
        if declination is None:
            return label
        return correct_direction_to_magnetic(label, declination)

    # --- 座向き（座＝背にする方角／向＝正面にする方角）の自動算出 ---
    # 「向」は玄関ドアが外を向いている方角（ドアを開けて外に出る方角）で決まる。
    # 玄関が家のどの位置にあるか（entrance_dir）とは独立した概念。
    entrance_facing_raw = data.get("entrance_facing_dir")
    if entrance_facing_raw:
        facing = correct(entrance_facing_raw)
        data["facing"] = facing
        data["sitting"] = OPPOSITE_DIRECTION.get(facing, "")

    # --- 各部屋の方位を磁北補正 ---
    for room in data.get("rooms", []):
        if room.get("direction"):
            room["direction"] = correct(room["direction"])

    if data.get("entrance_dir"):
        data["entrance_dir"] = correct(data["entrance_dir"])

    # --- 九宮コンパス表示用データ ---
    for room in data.get("rooms", []):
        cls = DIRECTION_TO_CLASS.get(room.get("direction", "").strip())
        room["compass_map"] = {cls: "single"} if cls else {}

    # --- 巒頭の各要素（方位の記載がある場合のみコンパスを付与） ---
    for row in data.get("luantou_rows", []):
        if row.get("direction"):
            cls = DIRECTION_TO_CLASS.get(row["direction"].strip())
            row["compass_map"] = {cls: "single"} if cls else {}

    # --- 八宅法：吉方位・凶方位をまとめた一枚のコンパスを生成 ---
    if data.get("bazhai_rows"):
        agg = {}
        for row in data["bazhai_rows"]:
            cls = DIRECTION_TO_CLASS.get(row.get("direction", "").strip())
            if not cls:
                continue
            agg[cls] = "bad" if "凶" in row.get("kind", "") else "good"
        if agg:
            data["bazhai_compass_map"] = agg

    for member in data.get("family_members", []):
        compass_map = {}
        for cls in _parse_directions(member.get("good_directions", "")):
            compass_map[cls] = "good"
        for cls in _parse_directions(member.get("bad_directions", "")):
            compass_map[cls] = "bad"
        member["compass_map"] = compass_map

    xuankong_grid = {}
    for row in data.get("xuankong_rows", []):
        cls = _direction_base_class(row.get("direction", ""))
        if cls:
            xuankong_grid[cls] = row
    if xuankong_grid:
        data["xuankong_grid"] = xuankong_grid

    return data


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render_html(data: dict, report_type: str) -> str:
    env = Environment(loader=FileSystemLoader(str(SKILL_DIR / "assets")))
    template = env.get_template(TEMPLATE_BY_TYPE[report_type])
    return template.render(**data)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    parser.add_argument("--type", dest="report_type", choices=["A", "B"], default="B")
    args = parser.parse_args()

    input_path, output_path, report_type = args.input_path, args.output_path, args.report_type
    data = load_data(input_path)
    data = enrich_directional_data(data)
    section_numbers, toc_items = build_section_numbers(data)
    data["section_numbers"] = section_numbers
    data["toc_items"] = toc_items

    # ブランディング保護: 系譜名・特定の師名が混入していないか簡易チェック
    forbidden_terms = ["御堂龍児", "御堂龍児師"]
    serialized = json.dumps(data, ensure_ascii=False)
    for term in forbidden_terms:
        if term in serialized:
            print(f"警告: 入力データに出力禁止ワード「{term}」が含まれています。鑑定書には表示されないよう除去してください。", file=sys.stderr)
            sys.exit(1)

    html_str = render_html(data, report_type)
    HTML(string=html_str, base_url=str(SKILL_DIR / "assets")).write_pdf(output_path)
    print(f"生成完了: {output_path}（Type{report_type}）")


if __name__ == "__main__":
    main()
