## 仕様
# 機能要件仕様書

## 1. システム概要
- **プログラムの全体的な目的と対象のユーザー**:
  - このプログラムは、EDINET APIを利用して有価証券報告書などの財務書類を取得し、その内容をPDFとして保存し、要約を生成してGoogle Driveに保存します。また、生成された要約をSlackを通じて通知します。対象ユーザーは、企業の財務情報を迅速に把握したい投資家やアナリスト、企業内の財務担当者です。

## 2. 主要機能要件
- **EDINET APIからの文書取得**:
  - 指定された日付範囲内でEDINET APIを通じて財務文書を取得します。取得した文書はEDINETコードに基づいてフィルタリングされます。

- **PDFのテキスト抽出と要約**:
  - PDFからテキストを抽出し、OpenAIのAPIを利用してテキストを要約します。要約は複数のチャンクに分割して処理され、最終的に一つの要約としてまとめられます。

- **Google Driveへの保存**:
  - 取得したPDFおよび生成された要約をGoogle Driveに保存します。ファイルは特定のフォルダに整理され、既存の同名ファイルがある場合は上書きを避けます。

- **Slack通知**:
  - 要約が生成されると、Slackを通じて指定されたチャンネルに通知を送信します。通知には要約の内容と関連するIRページへのリンクが含まれます。

- **スプレッドシートのデータ処理**:
  - GoogleスプレッドシートからEDINETコードを取得し、それに基づいて文書の取得と処理を行います。処理結果はスプレッドシートにログとして記録されます。

## 3. 非機能要件
- **パフォーマンス**:
  - 大量のPDFを並列で処理するために、ThreadPoolExecutorを使用しています。これにより、処理速度を向上させています。
  
- **セキュリティ**:
  - APIキーやサービスアカウント情報は環境変数や設定ファイルで管理され、不正アクセスを防ぎます。
  - Slack通知やGoogle Driveへのアクセスは、適切な認証を経て行われます。

- **可用性**:
  - ログを詳細に記録し、エラー発生時には適切にハンドリングすることで、システムの可用性を高めています。

## 4. 技術要件
- **開発環境**:
  - Python 3.xが必要です。
  - 必要な外部ライブラリは`requirements.txt`に記載されており、`pip`でインストール可能です。

- **システム環境**:
  - Google Cloud Platformを利用したGoogle Drive APIおよびGoogle Sheets APIの使用が必要です。
  - OpenAI APIを使用するためのAPIキーが必要です。

- **必要なライブラリ**:
  - `openai`, `google-auth`, `google-api-python-client`, `requests`, `pymupdf`, `slack_sdk`, `dotenv`, `tiktoken`, `sentence_transformers`などが使用されています。

このプログラムは、投資家や企業の財務担当者が迅速かつ効率的に情報を取得し、処理できるよう設計されています。各機能は独立しており、モジュール化されているため、個々の機能の拡張や改善が容易です。 

---

## フォルダ構成
プロジェクトのフォルダ構成は以下の通りです。

```plaintext
```
ir_news_release
├── .gitignore
├── .pytest_cache
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   ├── README.md
│   └── v
│       └── cache
│           ├── lastfailed
│           ├── nodeids
│           └── stepwise
├── .req_hash
├── README.md
├── config
│   ├── boxwood-dynamo-384411-6dec80faabfc.json
│   ├── prompt_financial_report.json
│   ├── secrets.env
│   └── settings.ini
├── docs
│   ├── .gitkeep
│   ├── detail_spec.txt
│   ├── generate_detailed_spec.txt
│   ├── merge.txt
│   └── requirements_spec.txt
├── requirements.txt
├── run.bat
├── spec_tools_run.bat
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── modules
│   │   ├── __init__.py
│   │   ├── edinet
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── operations.py
│   │   ├── pdfSummary
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py
│   │   │   ├── pdf_main.py
│   │   │   ├── process_drive_file.py
│   │   │   ├── summarizer.py
│   │   │   └── tokenizer.py
│   │   ├── setup.py
│   │   ├── slack
│   │   │   └── slack_notify.py
│   │   └── spreadsheet_to_edinet.py
│   └── utils
│       ├── __init__.py
│       ├── date_utils.py
│       ├── drive_handler.py
│       ├── environment.py
│       ├── logging_config.py
│       └── spreadsheet.py
└── tests
    ├── README.md
    ├── __init__.py
    ├── test_drive_file.py
    ├── test_log.py
    ├── test_slack_notify.py
    ├── test_slack_notify_with_file.py
    ├── test_slack_notify_with_markdown.py
    ├── test_spreadsheet.py
    └── test_template.py
```
```

---

## 実行方法

### 1. 仮想環境の作成と有効化
初回実行時には仮想環境を作成します。以下のコマンドを使用してください。

```bash
run.bat
```

- 仮想環境が存在しない場合、自動的に作成されます。
- 必要なパッケージは `requirements.txt` から自動インストールされます。

仮想環境を手動で有効化する場合：
```bash
.\env\Scripts ctivate
```

---

### 2. メインスクリプトの実行
デフォルトでは `src\main.py` が実行されます。他のスクリプトを指定する場合は、引数にスクリプトパスを渡します。

```bash
run.bat src\your_script.py
```

環境を指定する場合、`--env` オプションを使用します（例: `development`, `production`, `test`）。

```bash
run.bat --env production
```

---

### 3. 仕様書生成ツールの使用
仕様書生成スクリプトは `spec_tools_run.bat` を使用して実行できます。

- **merge_files.py の実行**:
  ```bash
  spec_tools_run.bat --merge
  ```

- **仕様書生成**:
  ```bash
  spec_tools_run.bat --spec
  ```

- **詳細仕様書生成**:
  ```bash
  spec_tools_run.bat --detailed-spec
  ```

- **すべてを一括実行**:
  ```bash
  spec_tools_run.bat --all
  ```

---

### 4. テストモード
テストモードでスクリプトを実行するには、`--test` オプションを使用します。

```bash
run.bat --test
```

---

## 注意事項

1. **仮想環境の存在確認**:
   `run.bat` または `spec_tools_run.bat` を初回実行時に仮想環境が作成されます。既存の仮想環境を削除する場合、手動で `.\env` を削除してください。

2. **環境変数の設定**:
   APIキーなどの秘密情報は `config\secrets.env` に格納し、共有しないよう注意してください。

3. **パッケージのアップデート**:
   必要に応じて、`requirements.txt` を更新してください。更新後、`run.bat` を実行すると自動的にインストールされます。

---

## サポート情報

- **開発者**: [yHaraguchi]
- **最終更新日**: 2024-12-01
