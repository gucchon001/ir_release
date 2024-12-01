## 仕様
[spec] 

---

## フォルダ構成
プロジェクトのフォルダ構成は以下の通りです。

```plaintext
[tree]
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
