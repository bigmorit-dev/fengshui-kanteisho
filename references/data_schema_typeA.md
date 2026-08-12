# 入力データスキーマ（TypeA・ネット鑑定）

`scripts/generate_pdf.py --type A` に渡すJSONの構造。TypeA入力フォーム（`assets/typeA_intake_form.html`）で集めたデータを、このスキーマに変換してから生成する。

```json
{
  "report_title": "地理風水鑑定書（ネット鑑定）",
  "client_name": "〇〇",
  "report_date": "2026年8月12日",
  "property_label": "神奈川県内 マンション（2LDK）",
  "practitioner_name": "ガモウ（我望）",
  "cover_disclaimer": "本鑑定はオンラインでいただいた情報に基づくものです。現地に伺っての巒頭（地形・気の流れ）分析は含まれておりませんが、いただいた情報をできる限り丁寧に読み解き、実際の暮らしに活かせる内容となるよう努めております。",

  "prefecture": "神奈川県",
  "latitude": 35.4437,
  "longitude": 139.6380,
  "direction_source": "floor_plan",
  "entrance_dir": "南東",
  "entrance_facing_dir": "南",

  "concerns": ["仕事運", "人間関係運"],
  "overview_text": "ご相談内容を踏まえた鑑定概要の文章",

  "life_gua": {
    "type": "東四命",
    "explanation": "東四命の資質・傾向を説明する文章"
  },

  "rooms": [
    {"name": "玄関", "direction": "南東", "fortune": "吉", "commentary": "玄関の解説文"},
    {"name": "リビング", "direction": "南", "fortune": "吉", "commentary": "リビングの解説文"},
    {"name": "寝室", "direction": "北", "fortune": "要注意", "commentary": "寝室の解説文"},
    {"name": "キッチン", "direction": "北東", "fortune": "吉", "commentary": "キッチンの解説文"},
    {"name": "浴室・トイレ", "direction": "南西", "fortune": "要改善", "commentary": "浴室・トイレの解説文"}
  ],

  "xuankong_lead": "玄空飛星分析のリード文",
  "xuankong_rows": [
    {"direction": "北", "stars": "山星6・向星8・運星9", "fortune": "吉"}
  ],

  "room_energy_photos": [
    {"room_label": "玄関", "commentary": "写真から見立てた解説文（Claudeが画像を直接見て生成）"},
    {"room_label": "リビング", "commentary": "..."}
  ],
  "room_energy_summary": "写真全体を通じての総評",

  "family_members": [
    {
      "relation": "ご本人",
      "birthdate": "1990年5月12日",
      "life_gua": "東四命",
      "good_directions": "東南・南・北・東",
      "bad_directions": "西・北西・南西・北東",
      "note": "この方向けの一言アドバイス"
    },
    {
      "relation": "配偶者",
      "birthdate": "1988年11月3日",
      "life_gua": "西四命",
      "good_directions": "西・北西・南西・北東",
      "bad_directions": "東南・南・北・東",
      "note": "この方向けの一言アドバイス"
    }
  ],

  "scores": [
    {"label": "金運", "value": 68},
    {"label": "健康運", "value": 72},
    {"label": "人間関係運", "value": 80},
    {"label": "仕事運", "value": 60}
  ],

  "actions": [
    {"priority": "高", "text": "行動提案の文章"}
  ],
  "key_message": "開運行動プランの中で最も伝えたい一文",

  "qimen": {
    "event": "引っ越し",
    "target_date": "2026年10月頃",
    "commentary": "吉日・タイミングについての解説文（入力があった場合のみこのオブジェクトを含める）"
  },

  "theme_sections": [
    {"theme": "仕事運", "commentary": "仕事運についての重点解説"},
    {"theme": "人間関係運", "commentary": "人間関係運についての重点解説"}
  ],

  "maxim": "締めの格言・一言",
  "closing_text": "今後の見通し・フォローアップへの導線となる一文"
}
```

## 磁北補正・座向きの算出について（重要）

TypeAでは、以下2点をスクリプト側（`enrich_directional_data`関数）で自動処理する。JSONを書く際は元データをそのまま入れればよく、手動で補正計算する必要はない。

### 1. 磁北補正（2段階の精度）
偏角（磁北と真北のずれ）の算出には2段階の方式がある。**精度を優先し、可能な限り①を使う。**

**① 緯度経度による直接計算（市区町村レベル、推奨）**
- `latitude` / `longitude` をJSONに含めると、IGRF-14地磁気モデル（国際標準の地磁気モデル。国土地理院公表値との誤差0.1度以内を確認済み）でその地点の偏角を直接計算する
- Claudeがこのスキルを実行する際、依頼主の市区町村情報（フォームの`city`欄）がわかれば、**web検索でその市区町村役場や中心地のおおよその緯度経度を調べて`latitude`/`longitude`に設定する。** 数キロ程度の誤差は偏角の計算結果にほとんど影響しないため、正確な住所地点まで特定する必要はない
- 特に都道府県が広い、または南北に長い・離島を含む場合（北海道、鹿児島県、東京都〈離島部〉、沖縄県など）は、県代表値との差が大きくなりやすいため、緯度経度の指定を優先する

**② 都道府県代表値（フォールバック）**
- `latitude`/`longitude` が無い場合、都道府県庁所在地の偏角テーブル（2020.0年値＋概算補正）を使う
- `prefecture`（都道府県）は**必須**。このテーブルを使って方位を補正する

いずれの場合も、`direction_source` が `"floor_plan"`（間取り図・登記図に記載の方角を見た＝真北基準）の場合のみ補正を行う。`"compass"`（スマホのコンパスアプリ等で直接計測＝すでに磁北基準）の場合は補正しない。

- 補正対象：`rooms[].direction`、`entrance_dir`、`entrance_facing_dir`
- 出典：国土地理院「日本各地の偏角」「地磁気値(予測値)計算サイト」 https://www.gsi.go.jp/buturisokuchi/geomag_index.html

### 2. 座向きの自動算出
- `facing`（向）と `sitting`（座）はJSON側で直接指定する必要はない。`entrance_facing_dir`（玄関ドアが外を向いている方角＝ドアを開けて外に出る方角）から自動的に算出される
- 「向」＝ `entrance_facing_dir`（磁北補正後）、「座」＝その正反対の方角
- **重要**：座向きは玄関が家のどの位置にあるか（`entrance_dir`）では決まらない。ドアが実際に開く（外を向く）方角で決まる。例：家の西側の壁に玄関があっても、ドアが南向きに開くなら「向」は南、「座」は北になる

```json
{
  "prefecture": "神奈川県",
  "direction_source": "floor_plan",
  "entrance_dir": "南東",
  "entrance_facing_dir": "南"
}
```
上記の場合、玄関は家の南東の位置にあるが、ドアは南向きに開くため、座向きは「座：北／向：南」として算出される。

## 生成時の注意

- `cover_disclaimer` は省略可。省略した場合、テンプレート側のデフォルト文言（オンライン鑑定の限界を誠実に伝える一文＋巒頭・龍脈をご自身で確認したい方向けの地形図アプリ「スーパー地形」の案内）が自動的に使われる

- `family_members` は入力があった人数分だけ配列要素を増やす。配列が空の場合、ご家族セクション自体を鑑定書から省略する（テンプレート側で自動判定）
- `qimen` は入力がなければJSON全体からキーごと省略する（テンプレート側で有無を判定して章を出し分ける）
- `room_energy_photos` は、アップロードされた写真をClaude自身が`view`ツールで直接閲覧し、その内容を踏まえて生成する。写真がない部屋のエントリは作らない
- `theme_sections` は `concerns` で選ばれた項目の数だけ作る
- `practitioner_name` に系譜名を入れない（TypeBと同じ禁止ワードチェックが生成スクリプトに入っている）
- `rooms` の `direction` が入力フォームで未選択だった部屋は、配列から除外する（無理に埋めない）
- 浴室・トイレ・洗面台など、家の中心付近にある部屋は `direction` に `"中央"` を指定できる。「中央」は方位角を持たないため磁北補正の対象外（`correct_direction_to_magnetic`が素通しする）。中央の部屋を書く際は `references/content_structure_typeA.md` の「部屋が家の中心（中央）にある場合の扱い」を参照し、`fortune` には通常の吉凶ラベルではなく中央特有の柔らかい表現を使う

```json
{"name": "浴室・トイレ・洗面台", "direction": "中央", "fortune": "整えることが大切な場所", "role_note": "...", "commentary": "..."}
```
