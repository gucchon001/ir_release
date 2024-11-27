REM save as ANSI/Shift-JIS
@echo off
rem Ensure this file is saved with ANSI/Shift-JIS encoding
@echo off
setlocal enabledelayedexpansion

:: �X�N���v�g���
set "TOOLS_DIR=spec_tools"
set "LOGS_DIR=%TOOLS_DIR%\logs"
set "DOCS_DIR=docs"

:: �w���v���b�Z�[�W
if "%~1"=="" (
    echo �g�p���@:
    echo   spec_tools_run.bat --merge         : merge_files.py �����s
    echo   spec_tools_run.bat --spec          : generate_spec.py �����s
    echo   spec_tools_run.bat --detailed-spec : generate_detailed_spec.py �����s
    echo   spec_tools_run.bat --all           : �S�Ă��ꊇ���s
    echo   spec_tools_run.bat --help          : ���̃w���v��\��
    goto END
)

:: ���z���̃`�F�b�N
if not exist ".\env\Scripts\activate.bat" (
    echo Error: ���z�������݂��܂���Brun.bat �ŉ��z�����쐬���Ă��������B
    goto END
)

call .\env\Scripts\activate

:: �R�}���h�̏���
if "%~1"=="--merge" (
    echo [LOG] merge_files.py �����s��...
    python %TOOLS_DIR%\merge_files.py > %LOGS_DIR%\merge_files.log 2>&1
    if errorlevel 1 (
        echo Error: merge_files.py �̎��s�Ɏ��s���܂����B���O���m�F���Ă��������B
        goto END
    )
    echo [LOG] merge_files.py �̎��s���������܂����B
)

if "%~1"=="--spec" (
    echo [LOG] generate_spec.py �����s��...
    python %TOOLS_DIR%\generate_spec.py > %LOGS_DIR%\generate_spec.log 2>&1
    if errorlevel 1 (
        echo Error: generate_spec.py �̎��s�Ɏ��s���܂����B���O���m�F���Ă��������B
        goto END
    )
    echo [LOG] generate_spec.py �̎��s���������܂����B
)

if "%~1"=="--detailed-spec" (
    echo [LOG] generate_detailed_spec.py �����s��...
    python %TOOLS_DIR%\generate_detailed_spec.py > %LOGS_DIR%\generate_detailed_spec.log 2>&1
    if errorlevel 1 (
        echo Error: generate_detailed_spec.py �̎��s�Ɏ��s���܂����B���O���m�F���Ă��������B
        goto END
    )
    echo [LOG] generate_detailed_spec.py �̎��s���������܂����B
)

if "%~1"=="--all" (
    echo [LOG] �S�ẴX�N���v�g���ꊇ���s��...
    call %0 --merge
    call %0 --spec
    call %0 --detailed-spec
    echo [LOG] �S�ẴX�N���v�g�̎��s���������܂����B
)

if "%~1"=="--help" (
    echo �g�p���@:
    echo   spec_tools_run.bat --merge         : merge_files.py �����s
    echo   spec_tools_run.bat --spec          : generate_spec.py �����s
    echo   spec_tools_run.bat --detailed-spec : generate_detailed_spec.py �����s
    echo   spec_tools_run.bat --all           : �S�Ă��ꊇ���s
    echo   spec_tools_run.bat --help          : ���̃w���v��\��
)

:END
endlocal
