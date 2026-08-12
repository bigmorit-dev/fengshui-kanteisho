# fengshui-kanteisho スキル 開発用プロジェクト

地理風水鑑定書PDF自動生成スキル。claude.aiの「スキル」機能で使うための`.skill`パッケージを、このソース一式から生成する。

## セットアップ（初回のみ）

```bash
cd ~/projects/  # 普段のプロジェクト置き場に合わせて調整
unzip fengshui-kanteisho-source.zip
cd fengshui-kanteisho
git init && git add . && git commit -m "初回インポート"

pip install weasyprint jinja2 pyIGRF --break-system-packages
```

## 開発の流れ

1. **Claude Codeで編集**：`assets/template.html`（TypeB）、`assets/template_typeA.html`（TypeA）、`scripts/generate_pdf.py`、`references/*.md` を直接編集する
2. **ローカルでPDF生成して確認**：
   ```bash
   # サンプルデータを用意して試す（references/data_schema*.md にスキーマ例あり）
   python3 scripts/generate_pdf.py sample.json output.pdf --type A
   python3 scripts/generate_pdf.py sample.json output.pdf --type B
   ```
   生成したPDFはFinderやプレビューアプリでそのまま開いて確認できる
3. **問題なければコミット**：`git add -A && git commit -m "変更内容"`
4. **claude.aiにアップロードする形（`.skill`）にパッケージし直す**：
   ```bash
   # skill-creatorのpackage_skillスクリプトを使う（Claude Codeに「.skillにパッケージして」と頼めばよい）
   python3 -m scripts.package_skill /path/to/fengshui-kanteisho
   ```
   生成された `fengshui-kanteisho.skill` を claude.ai の「スキル」画面からアップロードして差し替える

## ディレクトリ構成

```
fengshui-kanteisho/
├── SKILL.md                       # スキル本体の説明・ワークフロー定義
├── scripts/
│   └── generate_pdf.py            # JSON → PDF 変換（--type A/B対応、磁北補正・座向き算出も内包）
├── assets/
│   ├── template.html              # TypeB（現地調査）用テンプレート
│   ├── template_typeA.html        # TypeA（ネット鑑定）用テンプレート
│   ├── typeA_intake_form.html     # TypeA入力フォーム（Web埋め込み用、単独のHTMLファイル）
│   └── igrf14coeffs.txt           # 地磁気モデルの係数ファイル
└── references/
    ├── design_spec.md             # デザイン仕様（カラー・装飾モチーフ）
    ├── content_structure.md       # TypeBの章立て・文章技法
    ├── content_structure_typeA.md # TypeAの章立て・文章技法
    ├── data_schema.md             # TypeB入力JSONスキーマ
    └── data_schema_typeA.md       # TypeA入力JSONスキーマ
```

## Claude Codeに頼むときの例

- 「巒頭分析のカードデザインをもう少し引き締めた雰囲気にして」→ `template.html`のCSSを調整
- 「入力フォームに築年数の必須チェックを追加して」→ `typeA_intake_form.html`を編集
- 「都道府県の偏角テーブルを2025年値に更新して」→ `generate_pdf.py`の`_DECLINATION_2020`を更新
- 「変更したらサンプルPDFを2〜3件生成して見た目を確認して」→ ローカルでそのまま実行・プレビューできる

## 注意点

- `assets/`配下のファイルパスは `generate_pdf.py` が相対参照しているため、フォルダ構成を変えないこと
- 「御堂龍児」等の系譜名を出力に含めないルール、鑑定士クレジット「ガモウ（我望）」の扱いは`SKILL.md`冒頭に明記されている。変更時もこのルールは維持すること
- `.skill`へのパッケージ化はテスト完了後に行う（毎回の細かい修正のたびにパッケージ化する必要はない）
