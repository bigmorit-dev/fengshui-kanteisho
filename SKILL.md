---
name: fengshui-kanteisho
description: 地理風水（巒頭法・玄空飛星・奇門遁甲・八宅法）の鑑定データから、装飾デザイン付きの鑑定書PDFを自動生成する。2種類の鑑定書に対応：TypeB=現地調査メモ・巒頭分析を含む本格鑑定（4ページ程度）、TypeA=ネット上の入力フォームで集めたデータのみで作る鑑定（写真解析・家族分の命卦判定を含み10ページ以上）。ユーザーが現地調査メモ・鑑定データ・方位情報・依頼主情報などを渡してきたら、または「鑑定書を作って」「鑑定書PDFにして」「ネット鑑定の鑑定書を作って」「風水鑑定の結果をまとめて」と言われたら必ずこのスキルを使う。巒頭・玄空飛星・八宅法・龍脈・砂・水法・明堂・飛星盤・東四命・西四命・命卦などの風水専門用語が現地調査データや入力フォームデータに含まれる場合も積極的にこのスキルを検討する。
---

# 地理風水鑑定書 生成スキル

鑑定データを受け取り、ブランド統一されたデザインの鑑定書PDFを自動生成する。**TypeA（ネット鑑定）とTypeB（現地調査＋巒頭分析）の2種類**があり、それぞれ章立て・テンプレート・データスキーマが異なる。

## TypeA と TypeB の違い

| 項目 | TypeA（ネット鑑定） | TypeB（現地調査） |
|---|---|---|
| データの出所 | Webの入力フォーム（`assets/typeA_intake_form.html`） | 現地調査メモ・鑑定士の観察 |
| 巒頭分析 | なし（アップロード写真からの簡易見立てで代替） | あり（本格的な現地分析、要素カード＋方位コンパス） |
| 命卦・八宅法 | 依頼主＋家族分（人数可変、コンパス図付き） | 依頼主のみが基本（家族追加も可能） |
| 奇門遁甲 | 入力があれば「吉日・タイミング」章を掲載 | 未実装 |
| テーマ別重点解説 | あり（相談内容に応じて可変） | なし |
| ページ数目安 | 10〜14ページ以上（可変） | 10ページ以上（可変） |
| テンプレート | `assets/template_typeA.html` | `assets/template.html` |
| データスキーマ | `references/data_schema_typeA.md` | `references/data_schema.md` |
| 内容構成 | `references/content_structure_typeA.md` | `references/content_structure.md` |

両タイプとも、目次・章番号（`section_numbers`/`toc_items`）・九宮コンパス図（`compass_map`）・九宮飛星図（`xuankong_grid`）は `generate_pdf.py` が入力データから自動生成する。章立ての順序はデータに含まれるキーの有無で動的に決まるため、どの章を何番目に置くかを手動管理する必要はない。

どちらを使うべきか判断に迷う場合は、ユーザーに「現地調査に基づくTypeBか、オンライン入力のTypeAか」を確認する。

## ブランディング上の絶対ルール

**「御堂龍児」およびその系譜名は、生成する鑑定書のいかなる箇所にも一切表示しない。** これはユーザー（ケンタローさん）から明示的に指示されたルール。鑑定士のクレジット欄には、屋号「ガモウ（我望）」を使う（ユーザーから別途指定があればそちらを優先する）。師系・流派の学術的な知識背景としてこのスキル自体が地理風水の巒頭重視の流儀に基づいていることは問題ないが、それを固有名詞として出力に含めてはいけない。

**TypeAの表紙（P1）には、オンライン鑑定であることの限界を伝える一文を必ず入れる。** 巒頭分析を伴う現地鑑定（TypeB）とは異なる点を、卑下せず・かつ誠実に伝える文言とする。あわせて、周辺の地形や龍脈の流れをご自身で確認したい依頼主向けに、地形図アプリ「スーパー地形」（国土地理院データをもとにした地形強調表示アプリ）を紹介する一文も入れる。TypeAでは詳細住所を聞かない設計のため、依頼主自身が関心を持てば地形を調べられるという導線として機能する。テンプレート（`assets/template_typeA.html`）にはデフォルト文言が既に組み込まれているため、通常は追加作業不要。文言を鑑定ごとに変えたい場合のみ、データJSONに `cover_disclaimer` を指定する。

`scripts/generate_pdf.py` には、この禁止ワードが入力データに紛れ込んでいないかの簡易チェックが入っている。エラーになった場合は該当箇所を除去してから再実行すること。

## ワークフロー（共通）

1. **データの受け取りと整理**
   - TypeBの場合：現地調査メモ・鑑定データを読み、`references/data_schema.md` のJSON形式に変換する
   - TypeAの場合：入力フォーム（`assets/typeA_intake_form.html`）から集まったデータを、`references/data_schema_typeA.md` のJSON形式に変換する

2. **【TypeA限定】写真の解析**
   - アップロードされた玄関・リビング・寝室などの写真を、このスキルを実行するClaude自身が`view`ツールで直接閲覧する
   - 採光・動線・物の配置・水回りとの位置関係などから「気の流れ」を見立て、`room_energy_photos` の解説文を書く
   - 断定を避け「拝見する限り」「写っている範囲では」を徹底し、個人が特定できる情報（表札の氏名、車のナンバーなど）が写っていても言及しない
   - 写真がアップロードされていない部屋はエントリを作らない

3. **文章の作成**
   - TypeB: `references/content_structure.md` の8ブロック構成と文章技法に従う
   - TypeA: `references/content_structure_typeA.md` の12ブロック構成と文章技法に従う。フォームの「ご相談内容」を鑑定概要・テーマ別重点解説の両方で拾い、パーソナライズ感を出す
   - デザイン面のトーンは共通で `references/design_spec.md` を参照

4. **JSONデータファイルの作成**
   - 該当するスキーマに沿ってJSONファイルを作成し、作業ディレクトリに保存する
   - TypeAで家族構成の入力があれば `family_members` を人数分配列に、なければキーごと省略する
   - TypeAで奇門遁甲（吉日）の入力があれば `qimen` オブジェクトを含め、なければキーごと省略する
   - TypeAでは `prefecture`（都道府県）・`direction_source`・`entrance_facing_dir` を必ず含める（次項参照）

4.5. **【TypeA限定・重要】磁北補正と座向きの算出**
   - 一般的な間取り図に記載されている方位は**真北**基準だが、風水の方位判定は**磁北**基準で行うべきものなので、この差を補正する
   - `references/data_schema_typeA.md` の「磁北補正・座向きの算出について」を必ず確認し、`prefecture`（都道府県、必須）・`direction_source`（間取り図基準か実測コンパス基準か）・`entrance_facing_dir`（玄関ドアが外を向く方角）をJSONに含める
   - **精度向上のため、可能な限り `latitude` / `longitude`（緯度・経度）も含めること。** 依頼主の市区町村がわかっている場合、Claude自身がweb検索でその市区町村役場（または大まかな中心地）の緯度経度を調べてJSONに追加する。これにより、都道府県代表値ではなく市区町村レベルの精度で偏角を計算できる（IGRF地磁気モデルを使用、国土地理院公表値との誤差0.1度以内を確認済み）
   - `latitude`/`longitude` が無い場合は、都道府県代表値（`PREFECTURE_DECLINATION`テーブル）に自動フォールバックする。都道府県が広い、または離島を含む場合（北海道・鹿児島県など）は特に、市区町村レベルの緯度経度を調べることを優先する
   - 座向きの「向」は玄関の壁面の位置ではなく、**玄関ドアが実際に開く（外を向く）方角**で決まる。「座」はその正反対。これらは `generate_pdf.py` が `entrance_facing_dir` から自動算出するため、`facing`/`sitting` を手動で計算する必要はない

5. **PDF生成**
   ```bash
   pip install weasyprint jinja2 pyIGRF --break-system-packages  # 未インストールの場合のみ
   python3 <skill_dir>/scripts/generate_pdf.py <input.json> <output.pdf> --type A   # ネット鑑定
   python3 <skill_dir>/scripts/generate_pdf.py <input.json> <output.pdf> --type B   # 現地調査（デフォルト）
   ```
   - `<skill_dir>` はこのスキルがインストールされているディレクトリ（`scripts/generate_pdf.py` が `assets/` 配下のテンプレートや同梱のIGRF係数ファイルを相対パスで参照するため、絶対パスで呼び出すこと）
   - `pyIGRF` の pip配布物には地磁気モデルの係数ファイルが同梱されていないことがあるが、`generate_pdf.py` が起動時に `assets/igrf14coeffs.txt`（このスキルに同梱済み）を自動的に補完するため、追加作業は不要
   - `--type` を省略した場合は B（現地調査）として扱われる
   - スクリプトが禁止ワードのエラーを出したら、JSONを修正して再実行する
   - TypeAでは `rooms` / `family_members` の方角情報から、九宮コンパス図（`compass_map`）と玄空飛星の九宮飛星図（`xuankong_grid`）、章番号・目次（`section_numbers` / `toc_items`）が自動的に生成される。これらのキーを手動で作る必要はない

6. **納品**
   - 生成したPDFをユーザーに提示する（`present_files` などのファイル共有手段があれば使う）
   - 内容について「このトーンでよいか」「開運行動プランの提案内容は実行しやすいか」を確認する。フィードバックがあれば、JSONを修正して再生成する（ゼロから作り直す必要はない）

## ファイル構成

```
fengshui-kanteisho/
├── SKILL.md
├── scripts/
│   └── generate_pdf.py            # JSON → PDF 変換スクリプト（--type A/B対応）
├── assets/
│   ├── template.html              # TypeB用 Jinja2 + CSS テンプレート
│   ├── template_typeA.html        # TypeA用 Jinja2 + CSS テンプレート
│   ├── typeA_intake_form.html     # TypeAの入力フォーム（Web埋め込み用）
│   └── igrf14coeffs.txt           # IGRF-14地磁気モデルの係数ファイル（磁北補正の精密計算用）
└── references/
    ├── design_spec.md             # カラーパレット・装飾モチーフ・レイアウト原則（共通）
    ├── content_structure.md       # TypeB：8ブロック構成と文章技法
    ├── content_structure_typeA.md # TypeA：12ブロック構成と文章技法
    ├── data_schema.md             # TypeB：入力JSONのスキーマ
    └── data_schema_typeA.md       # TypeA：入力JSONのスキーマ
```

## 章立てのカスタマイズ

- TypeBに巒頭分析以外の章を追加する場合は `assets/template.html` にセクションを追加し、`references/data_schema.md` にデータ項目を追記する
- TypeAの入力フォーム自体に項目を追加する場合は `assets/typeA_intake_form.html` を編集し、`references/data_schema_typeA.md` にも対応するキーを追記する

