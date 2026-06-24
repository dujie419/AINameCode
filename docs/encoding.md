# Encoding Guide

This repository stores source code and documentation as UTF-8.

If Chinese text appears as mojibake in Windows PowerShell, the files are usually still correct. The terminal is reading or writing text with a non-UTF-8 code page.

## Recommended Editor Settings

- Use VS Code or another editor with UTF-8 enabled.
- Keep `files.encoding` set to `utf8`.
- Do not save project files as GBK/ANSI.

## PowerShell

Run this once in a PowerShell session before viewing files or running scripts:

```powershell
.\scripts\use-utf8.ps1
```

If PowerShell script execution is blocked by local policy, paste the equivalent commands manually:

```powershell
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

For `cmd.exe`, run:

```bat
scripts\use-utf8.cmd
```

## Verification

Use Python to verify a file is valid UTF-8:

```powershell
python -c "from pathlib import Path; Path('AInameProject/main.py').read_text(encoding='utf-8'); print('utf-8 ok')"
```
