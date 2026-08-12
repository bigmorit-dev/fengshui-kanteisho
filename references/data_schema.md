# 入力データスキーマ

`scripts/generate_pdf.py` に渡すJSONの構造。現地調査メモ・鑑定データからClaudeがこの形式に変換してから生成スクリプトを呼ぶ。

```json
{
  "report_title": "地理風水鑑定書",
  "client_name": "〇〇",
  "report_date": "2026年8月12日",
  "property_label": "〇〇エリアのご自宅",
  "practitioner_name": "鑑定士名またはブランド名（系譜名は入れない）",

  "overview_text": "鑑定概要の文章（3〜5行相当）",

  "luantou_lead": "巒頭分析のリード文",
  "luantou_rows": [
    {"element": "龍脈", "status": "良好", "meaning": "背後の山並みが安定した気の流れを支えています"},
    {"element": "青龍・白虎", "status": "要調整", "meaning": "左右のバランスに軽い偏りがあります"}
  ],
  "luantou_note": "巒頭分析で最も伝えたい一文（任意）",

  "xuankong_lead": "玄空飛星分析のリード文",
  "xuankong_rows": [
    {"direction": "北", "stars": "山星6・向星8・運星9", "fortune": "吉"}
  ],

  "bazhai_lead": "八宅法分析のリード文",
  "bazhai_rows": [
    {"kind": "吉方位（生気）", "direction": "東南", "meaning": "仕事運・対人運を高める方位"},
    {"kind": "凶方位（五鬼）", "direction": "北西", "meaning": "トラブルが起きやすいとされる方位。整理整頓で調整可能"}
  ],

  "scores": [
    {"label": "金運", "value": 70},
    {"label": "健康運", "value": 60},
    {"label": "人間関係運", "value": 80},
    {"label": "仕事運", "value": 65}
  ],

  "actions": [
    {"priority": "高", "text": "玄関の東南に観葉植物または水晶を置く（どちらでも同様の効果が期待できます）"},
    {"priority": "中", "text": "寝室の北西方向を整理整頓し、不要なものを置かない"}
  ],
  "key_message": "開運行動プランの中で最も伝えたい一文（任意）",

  "maxim": "締めの格言・一言",
  "closing_text": "今後の見通し・フォローアップへの導線となる一文"
}
```

## 生成時の注意

- `role_note`（要素・部屋の一般的な役割解説）と `direction`（方位。指定するとコンパス図が表示される）は `luantou_rows` の各要素に任意で追加できる。両方とも省略可能
- `rooms` は任意。現地調査でお部屋ごとの記録がある場合に追加すると「お部屋ごとの方位鑑定」章が自動的に加わる（構造はTypeAの`data_schema_typeA.md`と同じ）
- `era_note`（現在の元運についての一般的な解説）は `xuankong_lead` の下に表示される補足。省略可
- `xuankong_rows` は8方位＋中央の9行すべてを埋めると、九宮飛星図（3×3グリッド）が自動的に描画される。一部の方位のみでも動作するが、全て埋めた方が視覚的に充実する
- `bazhai_rows` の `kind` に「凶」の文字を含めると、対応する方位が凶方位（テラコッタ色）としてコンパス図にまとめて表示される。「凶」を含まない場合は吉方位（ブルー）として扱われる
- `family_members` も任意で追加可能（構造はTypeAと共通）。ただし通常はTypeAの差別化要素として使うことが多く、TypeBでは基本的に依頼主本人のみを扱う運用を推奨

- `practitioner_name` に系譜名（師の名前）を入れない。鑑定書のクレジット欄には屋号「ガモウ（我望）」を使う（ユーザーから別途指定があればそちらを優先する）
- `luantou_rows` / `xuankong_rows` / `bazhai_rows` は行数を必要な分だけ増減してよい
- `property_label` には詳細住所を書かず、エリア程度の抽象化に留める（依頼主のプライバシー保護）
- 文章はすべて references/content_structure.md の「文章技法まとめ」に沿って書く（外部権威に語らせる、ネガティブ要素はポジティブに再解釈、二択フレーム、時系列接続、専門用語への短い注釈）
