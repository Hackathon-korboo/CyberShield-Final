# PART 01: EXISTING BACKEND AUDIT — COMMANDS AND OUTPUTS

## Command 1: Inspect Root Directory
- **Command:** `Get-ChildItem -Path . -Force`
- **Output:** Empty (no output returned).

## Command 2: Detailed Root Directory Inspection via CMD
- **Command:** `cmd /c "dir /a"`
- **Output:**
```
 Volume in drive D is New Volume
 Volume Serial Number is 908F-96D9

 Directory of D:\Adamas offline Hackathon

11/14/2026  07:39 AM    <DIR>          .
11/14/2026  07:58 AM    <DIR>          ..
               0 File(s)              0 bytes
               2 Dir(s)  72,650,711,040 bytes free
```

## Command 3: Git Status Check & System Investigation
- **Command:** `cmd /c "git status"`
- **Exit Code:** 1
- **Output:**
```
fatal: not a git repository (or any of the parent directories): .git
```
- **Investigation Commands:**
  - `cmd /c "git --version && where git"`: Returned `git version 2.55.0.windows.3` at `C:\Program Files\Git\cmd\git.exe` (Exit Code 0).
  - `Test-Path "D:\Adamas offline Hackathon\.git"`: Returned `False` (Exit Code 0).
  - `cmd /c "git config --list --show-origin"`: Confirmed global Git configuration is intact on the host.
- **Finding:** Git is installed and functional. The exit code 1 is standard Git behavior for uninitialized directories. Repository initialization is intentionally omitted in Phase 01 per Rule 17.

## Command 4: Python Runtime and Path Check
- **Command:** `cmd /c "python --version && where python"`
- **Output:**
```
Python 3.11.9
C:\Users\RUPANJAN\AppData\Local\Programs\Python\Python311\python.exe
C:\Users\RUPANJAN\AppData\Local\Programs\Python\Python313\python.exe
C:\Users\RUPANJAN\AppData\Local\Microsoft\WindowsApps\python.exe
```

## Command 5: Installed Python Package Inventory
- **Command:** `python -m pip list`
- **Output (Relevant Excerpts):**
```
Package            Version
------------------ -----------
fastapi            0.143.0
pydantic           2.14.1
pydantic-settings  2.16.2
uvicorn            0.54.0
starlette          1.8.0
httpx              0.28.1
web3               8.0.0
pytest             9.1.1
pytest-asyncio     1.4.1.post1
python-dotenv      1.2.4
scikit-learn       1.9.1
lightgbm           4.7.0
```
