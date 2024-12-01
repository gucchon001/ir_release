## 仕様
## 機能要件仕様書

### 1. システム概要
- **目的**: 本プログラムは、EDINET APIを利用して日本の有価証券報告書や四半期報告書を自動的に取得し、PDF形式のドキュメントを処理して要約を生成、それをGoogle Driveに保存し、Slackに通知します。金融機関や企業のIRチームが、効率的に報告書を管理し、関係者に迅速に情報を共有することを支援します。
- **対象ユーザー**: 金融機関のアナリスト、企業のIR担当者、投資家。

### 2. 主要機能要件
- **EDINETからのドキュメント取得**: EDINETのAPIを使用して、指定された期間内の報告書を取得。ユーザーはスプレッドシートを通じて取得するEDINETコードを指定可能。
- **PDFからのテキスト抽出と要約**: PyMuPDFを使用してPDFからテキストを抽出し、OpenAIのAPIを用いてテキストを要約。要約結果はGoogle Driveに保存。
- **Google Drive管理**: Google Drive APIを利用して、PDFと要約をクラウドにアップロードし、フォルダ管理を行う。
- **Slack通知**: 要約された情報をMarkdown形式でSlackに通知。事前に設定したSlackチャンネルに投稿。
- **スプレッドシートの管理**: Google Sheets APIを活用し、処理したデータのログをスプレッドシートに記録。ユーザーはスプレッドシートで処理対象を管理。

### 3. 非機能要件
- **パフォーマンス**: 並列処理を用いて、指定期間内のドキュメントを迅速に取得。最大スレッド数は10。
- **セキュリティ**: Googleサービスとの接続にはサービスアカウントを利用し、機密情報は`.env`ファイルで管理。
- **可用性**: エラーハンドリングを強化し、障害発生時に詳細なログを記録。ログは日次でローテーション。
- **スケーラビリティ**: スプレッドシートやAPIの設定を変更することで、新たな報告書や企業を簡単に追加可能。

### 4. 技術要件
- **プログラミング言語**: Python 3.8以上
- **外部ライブラリ**: `requests`, `google-api-python-client`, `PyMuPDF`, `openai`, `slack-sdk`, `tiktoken`, `sentence-transformers`, `dotenv`
- **実行環境**: 
  - OS: クロスプラットフォーム（Windows, macOS, Linux）
  - Google Cloudサービスと連携するため、インターネット接続が必要
- **依存関係の管理**: `requirements.txt`を使用してパッケージを管理
- **設定ファイル**: `settings.ini`と`secrets.env`でAPIキーや各種パラメータを管理

## 注意事項
- ソースコードを適切に配置し、`config`, `src`, `tests`ディレクトリを使用してプロジェクトを構成します。
- `.env`および設定ファイルのセキュリティを確保し、アクセス権を制限してください。

---

## フォルダ構成
プロジェクトのフォルダ構成は以下の通りです。

```
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
- **最終更新日**: [YYYY-MM-DD]
