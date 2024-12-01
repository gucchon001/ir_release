#test_drive_file.py
import sys
from pathlib import Path

# プロジェクトのルートディレクトリを計算してPythonパスに追加
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))  # srcディレクトリも追加

# modules配下のpdf_mainからインポート
from modules.pdfSummary.pdf_main import test_process_drive_file

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test processing a Google Drive PDF file by its file ID.")
    parser.add_argument("file_id", help="The Google Drive file ID of the PDF to process.")
    parser.add_argument("drive_folder_id", help="The Google Drive folder ID to save the summary.")
    args = parser.parse_args()

    try:
        test_process_drive_file(args.file_id, args.drive_folder_id)
    except Exception as e:
        print(f"エラーが発生しました: {e}")