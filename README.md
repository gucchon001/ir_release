## 仕様
# 機能要件仕様書

## 1. システム概要
このプログラムは、EDINET APIを利用して指定された期間内の金融関連の文書を取得し、それをGoogle Driveに保存し、更に内容を要約してSlack通知を行うシステムです。主に金融機関や企業の情報システム部門、または財務分析を行うアナリストを対象にしています。ユーザーはこれにより、日々の業務において必要な金融情報を迅速かつ効率的に入手し、活用することができます。

## 2. 主要機能要件
- **EDINET APIを利用した文書取得**: 
  - 指定された期間内におけるEDINETコードに基づくドキュメントを検索し取得します。
  - 取得した文書はGoogle Driveに保存されます。
- **PDFからのテキスト抽出と要約**:
  - 取得したPDF文書からテキストを抽出し、GPT-4oを用いて要約を作成します。
  - 要約結果はGoogle Driveに保存され、ファイルIDがログシートに記録されます。
- **Slackを用いた通知**:
  - 要約された情報をMarkdown形式でSlackに通知し、関連するIR情報ページのリンクを提供します。
- **スプレッドシートのデータ処理**:
  - Google Sheetsのスプレッドシートから情報を取得し、EDINET APIを呼び出すための各種操作を行います。

## 3. 非機能要件
- **パフォーマンス要件**:
  - 文書取得、要約、通知の各プロセスは並列処理で行い、処理時間を短縮しています。
- **セキュリティ要件**:
  - 環境変数や設定ファイルにAPIキーやサービスアカウント情報を格納し、機密情報の漏洩を防ぎます。
  - Google Drive APIとSlack APIを利用する際には、OAuth 2.0認証を使用しています。
- **可用性**:
  - Google DriveとSlackへのアクセスが可能であれば、プログラムは通常通り動作します。
  - ログファイルによるエラートラッキングと、Slackへのエラーメッセージ通知が可能です。

## 4. 技術要件
- **開発環境およびシステム環境**:
  - Python 3.8以上が必要です。
  - Google API、OpenAI API、Slack APIを使用するための適切な設定と認証情報が必要です。
- **必要なライブラリ**:
  - `requests`: HTTPリクエストの送信。
  - `google-api-python-client`: Google DriveとSheets APIへのアクセス。
  - `pymupdf`: PDFからのテキスト抽出。
  - `openai`: テキスト要約のためのGPT-4oモデルの使用。
  - `slack-sdk`: Slackへのメッセージ送信。
  - `dotenv`: 環境変数のロード。

各機能は、モジュール化されたPythonスクリプトとして実装されており、設定ファイルや環境変数を通じて柔軟に構成できます。これにより、ユーザーの業務プロセスに合わせたカスタマイズが可能です。 

---

## フォルダ構成
プロジェクトのフォルダ構成は以下の通りです。

```plaintext
```
ir_release
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
│   ├── detailed_spec.txt
│   ├── merge.txt
│   └── requirements_spec.txt
├── downloads
│   ├── E04796_S100UPBR_20241111.pdf
│   ├── E04823_S100URPY_20241114.pdf
│   ├── E04824_S100UPMY_20241113.pdf
│   ├── E04850_S100UPQI_20241113.pdf
│   ├── E04981_S100USJE_20241118.pdf
│   ├── E04991_S100UR84_20241114.pdf
│   ├── E05011_S100UOHD_20241111.pdf
│   ├── E05024_S100UIEO_20241010.pdf
│   ├── E05028_S100UMLK_20241106.pdf
│   ├── E05030_S100UORB_20241114.pdf
│   ├── E05524_S100UNLM_20241107.pdf
│   ├── E07801_S100UOGD_20241111.pdf
│   ├── E21514_S100UPZH_20241114.pdf
│   ├── E37221_S100UPOF_20241112.pdf
│   └── E39165_S100URQR_20241114.pdf
├── logs
├── prompt
├── requirements.txt
├── run.bat
├── run_dev.bat
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
    ├── test_logging.py
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
.\run_dev.bat
```

- 仮想環境が存在しない場合、自動的に作成されます。
- 必要なパッケージは `requirements.txt` から自動インストールされます。

仮想環境を手動で有効化する場合：
```bash
.\env\Scripts Activate
```

---

### 2. メインスクリプトの実行
デフォルトでは `src\main.py` が実行されます。他のスクリプトを指定する場合は、引数にスクリプトパスを渡します。

```bash
.\run_dev.bat src\your_script.py
```

環境を指定する場合、`--env` オプションを使用します（例: `development`, `production`）。

```bash
.\run_dev.bat --env production
```

---

### 3. 仕様書生成ツールの使用
仕様書生成スクリプトは `spec_tools_run.bat` を使用して実行できます。

- **merge_files.py の実行**:
  ```bash
  .\spec_tools_run.bat --merge
  ```

- **仕様書生成**:
  ```bash
  .\spec_tools_run.bat --spec
  ```

- **詳細仕様書生成**:
  ```bash
  .\spec_tools_run.bat --detailed-spec
  ```

- **すべてを一括実行**:
  ```bash
  .\spec_tools_run.bat --all
  ```

---

### 4. 本番環境の実行
タスクスケジューラ等で設定をする際には、'run.bat'を利用してください。（パラメータ無しでproduction環境の実行をします）

```bash
.\run.bat
```


## 注意事項

1. **仮想環境の存在確認**:
   `run.bat` / `run_dev.bat` または `spec_tools_run.bat` を初回実行時に仮想環境が作成されます。既存の仮想環境を削除する場合、手動で `.\env` を削除してください。

2. **環境変数の設定**:
   APIキーなどの秘密情報は `config\secrets.env` に格納し、共有しないよう注意してください。

3. **パッケージのアップデート**:
   必要に応じて、`requirements.txt` を更新してください。更新後、`run_dev.bat` を実行すると自動的にインストールされます。

---