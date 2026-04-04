"""
╔══════════════════════════════════════════════════════════════════════╗
║              J.A.R.V.I.S  — Just A Rather Very Intelligent System   ║
║              Iron Man style AI Assistant  —  Full Device Control     ║
╚══════════════════════════════════════════════════════════════════════╝

FEATURES:
  • Claude AI brain  — real intelligence, answers anything
  • Full device control — apps, files, system, browser, mouse, keyboard
  • Always listening — just say "Hey Jarvis"
  • Speaks every response out loud
  • Auto-discovers all installed apps
  • Reads your contacts
  • File operations, web search, weather, news
  • Mouse & keyboard automation
  • Multi-step task automation

SETUP:
  1. pip install anthropic  (for AI brain)
  2. Add your API key below
  3. Run contacts_manager.py to add contacts
  4. python main.py
"""

# ─────────────────────────── CONFIGURATION ───────────────────────────────────
MIC_INDEX   = 1          # run Find_mic.py to find yours
API_KEY     = "YOUR_ANTHROPIC_API_KEY_HERE"   # get from console.anthropic.com
# ──────────────────────────────────────────────────────────────────────────────

import threading, queue, time, datetime, webbrowser, urllib.parse
import os, subprocess, math, logging, sys, re, random, json, glob, shutil
import tkinter as tk
import customtkinter as ctk
import speech_recognition as sr
import pyttsx3

try:
    import pyaudio, numpy as np
    PYAUDIO_RAW = True
except ImportError:
    PYAUDIO_RAW = False

# Optional imports — graceful fallback if not installed
try:
    import anthropic
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    PYAUTOGUI = True
except ImportError:
    PYAUTOGUI = False

try:
    import psutil
    PSUTIL = True
except ImportError:
    PSUTIL = False

try:
    import winreg
    WINREG = True
except ImportError:
    WINREG = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("jarvis.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("Jarvis")

CONTACTS_FILE = "contacts.json"
APPS_CACHE    = "apps_cache.json"

WAKE_PHRASES = ["hey jarvis","hi jarvis","hello jarvis","ok jarvis",
                "okay jarvis","jarvis","hey jar"]

def strip_wake(text: str) -> str:
    t = text.lower().strip()
    for p in sorted(WAKE_PHRASES, key=len, reverse=True):
        if t.startswith(p):
            t = t[len(p):].strip(", .")
            break
    for p in sorted(WAKE_PHRASES, key=len, reverse=True):
        t = t.replace(p, "").strip(", .")
    return t


# ══════════════════════════════════════════════════════════════════════════════
#  APP SCANNER
# ══════════════════════════════════════════════════════════════════════════════
def _resolve_lnk(lnk: str) -> str | None:
    try:
        r = subprocess.run(
            ["powershell","-NoProfile","-Command",
             f"(New-Object -COM WScript.Shell).CreateShortcut('{lnk}').TargetPath"],
            capture_output=True, text=True, timeout=5)
        t = r.stdout.strip()
        return t if t and os.path.isfile(t) else None
    except: return None

def _scan_shortcuts() -> dict:
    apps, u = {}, os.path.expanduser("~")
    dirs = [
        os.path.join(os.environ.get("PROGRAMDATA","C:\\ProgramData"),
                     "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(os.environ.get("APPDATA",""),
                     "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(u, "Desktop"),
    ]
    for d in dirs:
        for lnk in glob.glob(os.path.join(d,"**","*.lnk"), recursive=True):
            name = os.path.splitext(os.path.basename(lnk))[0].lower()
            if any(w in name for w in ["uninstall","update","help","readme","setup"]):
                continue
            t = _resolve_lnk(lnk)
            if t: apps[name] = t
    return apps

def _scan_registry() -> dict:
    if not WINREG: return {}
    apps = {}
    paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in paths:
        try:
            key = winreg.OpenKey(hive, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sub  = winreg.OpenKey(key, winreg.EnumKey(key, i))
                    def _g(n):
                        try: return winreg.QueryValueEx(sub,n)[0]
                        except: return ""
                    dn  = _g("DisplayName").strip()
                    exe = _g("DisplayIcon").split(",")[0].strip().strip('"')
                    if dn and exe and os.path.isfile(exe) and exe.lower().endswith(".exe"):
                        n = dn.lower()
                        if not any(w in n for w in ["uninstall","update","redistributable","runtime","sdk"]):
                            apps[n] = exe
                except: pass
        except: pass
    return apps

def _scan_uwp() -> dict:
    apps = {}
    try:
        r = subprocess.run(
            ["powershell","-NoProfile","-Command",
             "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15)
        items = json.loads(r.stdout)
        if isinstance(items,dict): items=[items]
        for item in items:
            n  = item.get("Name","").strip().lower()
            aid= item.get("AppID","").strip()
            if n and aid and not any(w in n for w in ["uninstall","update"]):
                apps[n] = f"shell:AppsFolder\\{aid}"
    except: pass
    return apps

def _aliases(name: str) -> list:
    out = [name]
    for s in [" - shortcut"," (x86)"," (x64)"," 64-bit"," 32-bit",
              " 2016"," 2019"," 2021"," 2022"," 2023"," 2024"," 2025"]:
        name = name.replace(s,"")
    name = name.strip()
    if name not in out: out.append(name)
    first = name.split()[0] if name.split() else name
    if first not in out: out.append(first)
    if name.startswith("microsoft "):
        s = name[10:].strip()
        if s not in out: out.append(s)
    return [a.strip() for a in out if a.strip()]

def _scan_user_folders() -> dict:
    """
    Scan all real folders the user has on Desktop, Documents, Downloads,
    Pictures, Videos, Music, and the home directory itself (1 level deep).
    Adds them by their lowercase folder name so "open food" works.
    """
    folders = {}
    U = os.path.expanduser("~")
    scan_roots = [
        os.path.join(U, "Desktop"),
        os.path.join(U, "Documents"),
        os.path.join(U, "Downloads"),
        os.path.join(U, "Pictures"),
        os.path.join(U, "Videos"),
        os.path.join(U, "Music"),
        U,
        # OneDrive Desktop (common on Windows 11)
        os.path.join(U, "OneDrive", "Desktop"),
        os.path.join(U, "OneDrive", "Documents"),
    ]
    skip_names = {
        "windows", "program files", "program files (x86)", "programdata",
        "appdata", "application data", "local settings", "system volume information",
        "recovery", "$recycle.bin", "perflogs", "intel", "amd",
        "temp", "tmp", "cache", ".git", "node_modules", "__pycache__",
    }
    for root in scan_roots:
        if not os.path.isdir(root):
            continue
        try:
            for entry in os.scandir(root):
                if not entry.is_dir(follow_symlinks=False):
                    continue
                name = entry.name
                name_lower = name.lower()
                if name_lower in skip_names or name_lower.startswith("."):
                    continue
                # Register by exact name and without spaces/underscores variants
                folders[name_lower] = entry.path
                # "my food" and "food folder" variants
                folders[f"my {name_lower}"] = entry.path
                folders[f"{name_lower} folder"] = entry.path
                # Replace underscores/hyphens with spaces: "my_projects" → "my projects"
                spaced = name_lower.replace("_", " ").replace("-", " ")
                if spaced != name_lower:
                    folders[spaced] = entry.path
                    folders[f"my {spaced}"] = entry.path
        except PermissionError:
            pass
    log.info(f"📁 User folders indexed: {len(folders)} entries")
    return folders


def build_app_index() -> dict:
    log.info("🔍 Scanning all installed apps (first run ~10s)…")
    merged = {}
    merged.update(_scan_registry())
    merged.update(_scan_shortcuts())
    uwp = _scan_uwp()
    index = {}
    for name,target in merged.items():
        for alias in _aliases(name):
            if alias not in index: index[alias]=target
    for name,target in uwp.items():
        for alias in _aliases(name):
            if alias not in index: index[alias]=target
    U = os.path.expanduser("~")
    builtins = {
        "chrome":r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "google chrome":r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":"msedge","notepad":"notepad.exe","calculator":"calc.exe",
        "paint":"mspaint.exe","task manager":"taskmgr.exe",
        "file explorer":"explorer.exe","explorer":"explorer.exe",
        "control panel":"control.exe","cmd":"cmd.exe",
        "command prompt":"cmd.exe","powershell":"powershell.exe",
        "settings":"start ms-settings:","camera":"start microsoft.windows.camera:",
        "store":"start ms-windows-store:","photos":"start ms-photos:",
        "documents":os.path.join(U,"Documents"),
        "downloads":os.path.join(U,"Downloads"),
        "desktop":os.path.join(U,"Desktop"),
        "pictures":os.path.join(U,"Pictures"),
        "music":os.path.join(U,"Music"),
        "videos":os.path.join(U,"Videos"),
        "youtube":"https://youtube.com","google":"https://google.com",
        "gmail":"https://mail.google.com","whatsapp":"https://web.whatsapp.com",
        "instagram":"https://instagram.com","facebook":"https://facebook.com",
        "twitter":"https://twitter.com","netflix":"https://netflix.com",
        "github":"https://github.com","chatgpt":"https://chat.openai.com",
        "maps":"https://maps.google.com","spotify":"https://open.spotify.com",
    }
    for k,v in builtins.items(): index[k]=v

    # Scan real user folders (Desktop/food, Documents/projects, etc.)
    # These are added AFTER builtins so builtins always win on name clashes
    user_folders = _scan_user_folders()
    for k, v in user_folders.items():
        if k not in index:   # don't override named apps like "downloads" app shortcut
            index[k] = v

    log.info(f"✅ App index: {len(index)} entries")
    return index

def load_apps(force=False) -> dict:
    if not force and os.path.exists(APPS_CACHE):
        try:
            with open(APPS_CACHE,encoding="utf-8") as f:
                data=json.load(f)
            log.info(f"📦 Loaded {len(data)} apps from cache")
            return data
        except: pass
    data = build_app_index()
    try:
        with open(APPS_CACHE,"w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,ensure_ascii=False)
    except Exception as e: log.warning(f"App cache save failed: {e}")
    return data

def load_contacts() -> dict:
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE,encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}


# ══════════════════════════════════════════════════════════════════════════════
#  DEVICE CONTROLLER  — executes actions on the PC
# ══════════════════════════════════════════════════════════════════════════════
class DeviceController:
    """Everything Jarvis can DO on the computer."""

    def __init__(self, apps: dict, contacts: dict):
        self.apps     = apps
        self.contacts = contacts

    # ── App / file launch ─────────────────────────────────────────────────────
    def _resolve_folder(self, spoken: str):
        """Return an absolute folder path for a spoken folder name, or None."""
        U = os.path.expanduser("~")
        # Map every reasonable spoken variation to an absolute path
        FOLDER_MAP = {
            # Downloads
            "downloads": os.path.join(U, "Downloads"),
            "download": os.path.join(U, "Downloads"),
            "my downloads": os.path.join(U, "Downloads"),
            "downloads folder": os.path.join(U, "Downloads"),
            # Documents
            "documents": os.path.join(U, "Documents"),
            "document": os.path.join(U, "Documents"),
            "my documents": os.path.join(U, "Documents"),
            "documents folder": os.path.join(U, "Documents"),
            # Desktop
            "desktop": os.path.join(U, "Desktop"),
            "my desktop": os.path.join(U, "Desktop"),
            "desktop folder": os.path.join(U, "Desktop"),
            # Pictures
            "pictures": os.path.join(U, "Pictures"),
            "picture": os.path.join(U, "Pictures"),
            "photos": os.path.join(U, "Pictures"),
            "photo": os.path.join(U, "Pictures"),
            "my pictures": os.path.join(U, "Pictures"),
            "my photos": os.path.join(U, "Pictures"),
            "pictures folder": os.path.join(U, "Pictures"),
            # Music
            "music": os.path.join(U, "Music"),
            "my music": os.path.join(U, "Music"),
            "music folder": os.path.join(U, "Music"),
            # Videos
            "videos": os.path.join(U, "Videos"),
            "video": os.path.join(U, "Videos"),
            "my videos": os.path.join(U, "Videos"),
            "videos folder": os.path.join(U, "Videos"),
            # OneDrive (common on Windows 11)
            "onedrive": os.path.join(U, "OneDrive"),
            "one drive": os.path.join(U, "OneDrive"),
            # This PC / root drives
            "this pc": "shell",
            "my computer": "shell",
            "computer": "shell",
            "c drive": "C:\\",
            "c:": "C:\\",
            # Recycle bin
            "recycle bin": "recycle",
            "trash": "recycle",
        }
        s = spoken.lower().strip()
        # Strip filler words
        s_clean = re.sub(r"\b(the|my|open|show|me|folder|directory)\b", "", s).strip()
        return FOLDER_MAP.get(s) or FOLDER_MAP.get(s_clean)

    def open_app(self, name: str) -> str:
        name_lower = name.lower().strip()

        # ── 1. Try folder resolution first ───────────────────────────────────
        folder_path = self._resolve_folder(name_lower)
        if folder_path:
            try:
                if folder_path == "shell":
                    subprocess.Popen("explorer.exe", shell=True)
                elif folder_path == "recycle":
                    subprocess.Popen("explorer.exe shell:RecycleBinFolder", shell=True)
                else:
                    subprocess.Popen(["explorer.exe", folder_path])
                return f"Opening {name}"
            except Exception as e:
                log.warning(f"Folder open error: {e}")
                return f"Couldn't open {name}: {e}"

        # ── 2. Strip filler words for app lookup ─────────────────────────────
        cleaned = re.sub(r"\b(the|my|folder|app|application|program|window)\b", "", name_lower).strip()
        lookup = cleaned if cleaned else name_lower

        # ── 3. Direct app lookup ──────────────────────────────────────────────
        target = self.apps.get(lookup) or self.apps.get(name_lower)

        # ── 4. Fuzzy app lookup ───────────────────────────────────────────────
        if not target:
            for k, v in self.apps.items():
                if lookup in k or k in lookup:
                    target = v; break

        # ── 5. Absolute path given directly ──────────────────────────────────
        if not target and (os.path.isdir(name) or os.path.isfile(name)):
            target = name

        # ── 6. Live folder search on Desktop + common locations ───────────────
        if not target:
            U = os.path.expanduser("~")
            search_roots = [
                os.path.join(U, "Desktop"),
                os.path.join(U, "Documents"),
                os.path.join(U, "Downloads"),
                os.path.join(U, "OneDrive", "Desktop"),
                U,
            ]
            for root in search_roots:
                if not os.path.isdir(root):
                    continue
                try:
                    for entry in os.scandir(root):
                        if entry.is_dir() and entry.name.lower() == lookup:
                            target = entry.path
                            break
                except PermissionError:
                    pass
                if target:
                    break

        if target:
            self._launch(target)
            return f"Opening {name}"
        return f"I couldn't find {name} on your laptop"

    def _launch(self, target: str):
        try:
            if target.startswith("http"):
                webbrowser.open(target)
            elif target.startswith("start ") or target.startswith("shell:"):
                subprocess.Popen(target, shell=True)
            elif os.path.isdir(target):
                subprocess.Popen(["explorer.exe", target])
            elif os.path.isfile(target):
                subprocess.Popen([target])
            elif "\\" not in target and "/" not in target and ":" not in target:
                subprocess.Popen(target, shell=True)
        except Exception as e:
            log.warning(f"Launch error: {e}")

    # Maps spoken name → actual process exe name(s) to kill
    CLOSE_ALIASES = {
        "youtube":        ["chrome", "msedge", "firefox"],   # browser tab — close via hotkey
        "gmail":          ["chrome", "msedge", "firefox"],
        "whatsapp":       ["chrome", "msedge", "firefox", "whatsapp"],
        "instagram":      ["chrome", "msedge", "firefox"],
        "facebook":       ["chrome", "msedge", "firefox"],
        "twitter":        ["chrome", "msedge", "firefox"],
        "netflix":        ["chrome", "msedge", "firefox"],
        "spotify":        ["spotify"],
        "vs code":        ["code"],
        "vscode":         ["code"],
        "visual studio code": ["code"],
        "visual studio":  ["devenv"],
        "word":           ["winword"],
        "excel":          ["excel"],
        "powerpoint":     ["powerpnt"],
        "outlook":        ["outlook"],
        "teams":          ["teams", "ms-teams"],
        "discord":        ["discord"],
        "slack":          ["slack"],
        "zoom":           ["zoom"],
        "vlc":            ["vlc"],
        "vlc player":     ["vlc"],
        "vlc media player": ["vlc"],
        "file explorer":  ["explorer"],
        "explorer":       ["explorer"],
        "task manager":   ["taskmgr"],
        "paint":          ["mspaint"],
        "notepad":        ["notepad"],
        "calculator":     ["calculator", "calc"],
        "chrome":         ["chrome"],
        "google chrome":  ["chrome"],
        "firefox":        ["firefox"],
        "edge":           ["msedge"],
        "microsoft edge":  ["msedge"],
        "ms edge":         ["msedge"],
        "brave":          ["brave"],
        "telegram":       ["telegram"],
        "steam":          ["steam"],
        "obs":            ["obs64", "obs32", "obs"],
        "photoshop":      ["photoshop"],
        "premiere":       ["premiere"],
        "after effects":  ["afterfx"],
    }

    # Websites that live in browser tabs — close with Ctrl+W via browser hotkey
    BROWSER_TABS = {
        "youtube", "gmail", "whatsapp", "instagram", "facebook",
        "twitter", "netflix", "github", "chatgpt", "maps", "spotify web",
        "google", "reddit", "twitch"
    }

    def close_app(self, name: str) -> str:
        name_lower = name.lower().replace(".exe", "").strip()

        # ── 0. Is it a folder / File Explorer window? ───────────────────────
        # Also check if name matches a real folder in the app index
        app_path = self.apps.get(name_lower, "")
        is_folder = (
            self._resolve_folder(name_lower) is not None
            or name_lower in {"file explorer", "explorer", "this pc", "my computer"}
            or "folder" in name_lower
            or (app_path and os.path.isdir(app_path))
        )
        if is_folder:
            # Get bare folder name (strip "folder" word)
            bare = re.sub(r"\bfolder\b", "", name_lower).strip()
            # Try to close only the matching window first
            ps_specific = (
                "$sh = New-Object -ComObject Shell.Application; "
                "$closed = 0; "
                "$sh.Windows() | ForEach-Object { "
                f"  if ($_.LocationName -like '*{bare}*' -or $_.LocationURL -like '*{bare}*') "
                "   { $_.Quit(); $closed++ } "
                "}; Write-Output $closed"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_specific],
                capture_output=True, text=True
            )
            closed_count = r.stdout.strip()
            # If nothing was closed specifically, or it's a generic "file explorer" request, close all
            if closed_count == "0" or bare in ("file explorer", "explorer", "this pc", "my computer", ""):
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "(New-Object -ComObject Shell.Application).Windows() | ForEach-Object { $_.Quit() }"],
                    capture_output=True
                )
            return f"Closed {name}"

        # ── 1. Is it a website / browser tab? Close the active tab ──────────
        if name_lower in self.BROWSER_TABS:
            # Send Ctrl+W to close the active browser tab
            subprocess.run(
                'powershell -c "$wsh=New-Object -ComObject WScript.Shell; '
                '$wsh.AppActivate(\'chrome\'); Start-Sleep -Milliseconds 200; '
                '$wsh.SendKeys(\'^w\')"',
                shell=True, capture_output=True
            )
            # Also try Edge and Firefox
            for browser in ["msedge", "firefox"]:
                subprocess.run(
                    f'powershell -c "$wsh=New-Object -ComObject WScript.Shell; '
                    f'$wsh.AppActivate(\'{browser}\'); Start-Sleep -Milliseconds 100; '
                    f'$wsh.SendKeys(\'^w\')"',
                    shell=True, capture_output=True
                )
            return f"Closed {name} tab"

        # ── 2. Look up known alias → exe name mapping ────────────────────────
        exe_names = self.CLOSE_ALIASES.get(name_lower)

        # ── 3. Fuzzy match alias table if exact miss ─────────────────────────
        if not exe_names:
            for alias, exes in self.CLOSE_ALIASES.items():
                if name_lower in alias or alias in name_lower:
                    exe_names = exes
                    break

        # ── 4. Kill by process name (psutil first, then taskkill) ────────────
        killed = []

        if exe_names and PSUTIL:
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    pname = proc.info["name"].lower().replace(".exe", "")
                    if any(pname == ex.lower() or ex.lower() in pname for ex in exe_names):
                        proc.kill()
                        killed.append(proc.info["name"])
                except Exception:
                    pass

        # ── 5. Fallback: fuzzy match ALL running processes by spoken name ────
        if not killed and PSUTIL:
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    pname = proc.info["name"].lower().replace(".exe", "")
                    if name_lower in pname or pname in name_lower:
                        proc.kill()
                        killed.append(proc.info["name"])
                except Exception:
                    pass

        # ── 6. Last resort: taskkill wildcard ────────────────────────────────
        if not killed:
            target_exe = (exe_names[0] if exe_names else name_lower)
            r = subprocess.run(
                f'taskkill /F /IM *{target_exe}*.exe',
                shell=True, capture_output=True, text=True
            )
            if "SUCCESS" in r.stdout or "terminated" in r.stdout.lower():
                return f"Closed {name}"
            return f"Could not find {name} running"

        return f"Closed {', '.join(set(killed))}"

    # ── Web ───────────────────────────────────────────────────────────────────
    def open_url(self, url: str) -> str:
        if not url.startswith("http"): url = "https://" + url
        webbrowser.open(url); return f"Opening {url}"

    def search_web(self, query: str) -> str:
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        return f"Searching for {query}"

    def search_youtube(self, query: str) -> str:
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        return f"Searching YouTube for {query}"

    # ── File operations ───────────────────────────────────────────────────────
    def create_file(self, path: str, content: str = "") -> str:
        try:
            path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path,"w",encoding="utf-8") as f: f.write(content)
            return f"Created file: {path}"
        except Exception as e: return f"Couldn't create file: {e}"

    def create_folder(self, path: str) -> str:
        try:
            path = os.path.expanduser(path)
            os.makedirs(path, exist_ok=True); return f"Created folder: {path}"
        except Exception as e: return f"Couldn't create folder: {e}"

    def delete_file(self, path: str) -> str:
        try:
            path = os.path.expanduser(path)
            if os.path.isfile(path): os.remove(path); return f"Deleted {path}"
            elif os.path.isdir(path): shutil.rmtree(path); return f"Deleted folder {path}"
            return f"Not found: {path}"
        except Exception as e: return f"Couldn't delete: {e}"

    def list_files(self, folder: str = ".") -> str:
        try:
            folder = os.path.expanduser(folder)
            items  = os.listdir(folder)
            if not items: return f"Folder {folder} is empty"
            return f"Files in {folder}: " + ", ".join(items[:20])
        except Exception as e: return f"Couldn't list files: {e}"

    def open_file(self, path: str) -> str:
        try:
            path = os.path.expanduser(path)
            os.startfile(path); return f"Opened {path}"
        except Exception as e: return f"Couldn't open: {e}"

    # ── Keyboard / typing ─────────────────────────────────────────────────────
    def type_text(self, text: str) -> str:
        safe = (text.replace("'","''")
                    .replace("+","{{+}}").replace("^","{{^}}")
                    .replace("%","{{%}}").replace("~","{{~}}")
                    .replace("(","{{(}})").replace(")","{{)}}")
                    .replace("{","{{{}}}").replace("}","{{}}"))
        subprocess.run(
            f'powershell -c "$w=New-Object -com wscript.shell; $w.SendKeys(\'{safe}\')"',
            shell=True, capture_output=True)
        return f"Typed: {text}"

    def press_key(self, key: str) -> str:
        key_map = {
            "enter":"{ENTER}","tab":"{TAB}","escape":"{ESC}","esc":"{ESC}",
            "backspace":"{BACKSPACE}","delete":"{DELETE}","space":" ",
            "up":"{UP}","down":"{DOWN}","left":"{LEFT}","right":"{RIGHT}",
            "home":"{HOME}","end":"{END}","page up":"{PGUP}","page down":"{PGDN}",
            "copy":"^c","paste":"^v","cut":"^x","undo":"^z","redo":"^y",
            "select all":"^a","save":"^s","new":"^n","open":"^o","find":"^f",
            "print":"^p","close":"^w","refresh":"{F5}",
            "screenshot":"%{PRTSC}","fullscreen":"{F11}",
            "alt f4":"%{F4}","win d":"#d",
            # New keys
            "alt+left":"%{LEFT}","alt+right":"%{RIGHT}",
            "ctrl+t":"^t","ctrl+w":"^w","ctrl+l":"^l",
            "ctrl+=":"^=","ctrl+-":"^-","ctrl+0":"^0",
            "ctrl+r":"^r","ctrl+shift+t":"^+t",
        }
        k = key_map.get(key.lower(), f"{{{key.upper()}}}")
        subprocess.run(
            f'powershell -c "$w=New-Object -com wscript.shell; $w.SendKeys(\'{k}\')"',
            shell=True, capture_output=True)
        return f"Pressed {key}"

    def browser_click_nth_link(self, n: int) -> str:
        """Click the Nth interactive element on the page.
        Uses Tab to cycle focusable elements, then Enter to activate.
        Works on YouTube (thumbnails), Google (search results), and any webpage."""
        if not PYAUTOGUI:
            return "pyautogui required: pip install pyautogui"
        try:
            sw, sh = pyautogui.size()

            # Click the page center first to make sure the browser is focused
            # and keyboard focus is in the content area (not address bar)
            pyautogui.click(sw // 2, sh // 2)
            time.sleep(0.4)

            # Press Escape first to dismiss any overlay/tooltip
            subprocess.run(
                'powershell -c "$w=New-Object -com wscript.shell; $w.SendKeys(\'{ESC}\')"',
                shell=True, capture_output=True)
            time.sleep(0.2)

            # On YouTube the very first Tab from the page lands on a video thumbnail.
            # On Google the first Tab lands on the first search result.
            # Tab n times to reach the nth item.
            for i in range(n):
                subprocess.run(
                    'powershell -c "$w=New-Object -com wscript.shell; $w.SendKeys(\'{TAB}\')"',
                    shell=True, capture_output=True)
                time.sleep(0.2)   # small pause so the browser registers each Tab

            # Press Enter to activate the focused element
            time.sleep(0.1)
            subprocess.run(
                'powershell -c "$w=New-Object -com wscript.shell; $w.SendKeys(\'{ENTER}\')"',
                shell=True, capture_output=True)

            return f"Clicked item number {n} on the page"
        except Exception as e:
            return f"Couldn't click item: {e}"



    # ── Mouse (if pyautogui available) ────────────────────────────────────────
    def click(self, x: int = None, y: int = None) -> str:
        if not PYAUTOGUI: return "Mouse control requires: pip install pyautogui"
        if x and y: pyautogui.click(x, y)
        else:       pyautogui.click()
        return "Clicked"

    def move_mouse(self, x: int, y: int) -> str:
        if not PYAUTOGUI: return "Mouse control requires: pip install pyautogui"
        pyautogui.moveTo(x, y, duration=0.3); return f"Moved mouse to {x},{y}"

    def move_mouse_named(self, position: str) -> str:
        """Move mouse to a named position. Handles natural spoken variants like
        'left', 'to the left', 'left side', 'top right corner', etc."""
        if not PYAUTOGUI: return "Mouse control requires: pip install pyautogui"
        sw, sh = pyautogui.size()
        cx, cy = sw // 2, sh // 2

        # Clean up spoken noise before matching
        p = position.lower().strip()
        p = re.sub(r'\b(the|a|an|of|side|corner|edge|screen|monitor|display|over|there|here)\b', '', p)
        p = re.sub(r'\s+', ' ', p).strip()

        # Keyword presence checks — very forgiving
        has_top    = any(w in p for w in ["top", "upper", "up"])
        has_bottom = any(w in p for w in ["bottom", "lower", "down"])
        has_left   = "left" in p
        has_right  = "right" in p
        has_center = any(w in p for w in ["center", "centre", "middle"])

        # Resolve coordinates based on keyword combos
        if has_center and not has_top and not has_bottom and not has_left and not has_right:
            x, y = cx, cy
            label = "center"
        elif has_top and has_left:
            x, y = 0, 0
            label = "top left"
        elif has_top and has_right:
            x, y = sw, 0
            label = "top right"
        elif has_bottom and has_left:
            x, y = 0, sh
            label = "bottom left"
        elif has_bottom and has_right:
            x, y = sw, sh
            label = "bottom right"
        elif has_top and has_center:
            x, y = cx, 0
            label = "top center"
        elif has_bottom and has_center:
            x, y = cx, sh
            label = "bottom center"
        elif has_left and has_center:
            x, y = 0, cy
            label = "left center"
        elif has_right and has_center:
            x, y = sw, cy
            label = "right center"
        elif has_top:
            x, y = cx, 0
            label = "top"
        elif has_bottom:
            x, y = cx, sh
            label = "bottom"
        elif has_left:
            x, y = 0, cy
            label = "left"
        elif has_right:
            x, y = sw, cy
            label = "right"
        else:
            return (f"I didn't catch where to move the cursor, sir. "
                    f"Try saying: left, right, top, bottom, center, top right, etc.")

        # Keep slightly inset from screen edges so pyautogui failsafe doesn't trigger
        x = max(5, min(x, sw - 5))
        y = max(5, min(y, sh - 5))
        pyautogui.moveTo(x, y, duration=0.4)
        return f"Moved the cursor to the {label}."

    def type_in_window(self, window_title_hint: str, text: str) -> str:
        """Focus a specific window by title hint then type text into it."""
        # Map common spoken names → window title keywords PowerShell will search
        WINDOW_MAP = {
            "chatgpt":      ["ChatGPT", "chat.openai"],
            "chat gpt":     ["ChatGPT", "chat.openai"],
            "notepad":      ["Notepad"],
            "chrome":       ["Google Chrome"],
            "google chrome":["Google Chrome"],
            "edge":         ["Microsoft Edge"],
            "microsoft edge":["Microsoft Edge"],
            "firefox":      ["Firefox"],
            "vs code":      ["Visual Studio Code"],
            "vscode":       ["Visual Studio Code"],
            "word":         ["Word"],
            "excel":        ["Excel"],
            "powerpoint":   ["PowerPoint"],
            "outlook":      ["Outlook"],
            "teams":        ["Microsoft Teams"],
            "discord":      ["Discord"],
            "slack":        ["Slack"],
            "whatsapp":     ["WhatsApp"],
            "telegram":     ["Telegram"],
            "youtube":      ["YouTube"],
            "gmail":        ["Gmail"],
            "terminal":     ["Terminal", "Command Prompt", "PowerShell", "cmd"],
            "powershell":   ["PowerShell"],
            "cmd":          ["cmd", "Command Prompt"],
            "file explorer":["File Explorer"],
            "explorer":     ["File Explorer"],
            "paint":        ["Paint"],
            "calculator":   ["Calculator"],
            "spotify":      ["Spotify"],
        }

        hint_lower = window_title_hint.lower().strip()
        keywords = WINDOW_MAP.get(hint_lower)

        # Fuzzy match if no exact hit
        if not keywords:
            for k, v in WINDOW_MAP.items():
                if hint_lower in k or k in hint_lower:
                    keywords = v
                    break

        # Fall back to using the spoken name directly as the window title hint
        if not keywords:
            keywords = [window_title_hint]

        # Try each keyword until one focuses a window
        focused = False
        for kw in keywords:
            ps = (
                f"$wsh = New-Object -ComObject WScript.Shell; "
                f"$result = $wsh.AppActivate('{kw}'); "
                f"Write-Output $result"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True
            )
            if r.stdout.strip().lower() == "true":
                focused = True
                break

        if not focused:
            log.warning(f"type_in_window: could not focus '{window_title_hint}' — falling back to active window")

        time.sleep(0.5)  # Let the window come to foreground

        # Now click in the window center to ensure it's focused & cursor is in the text area
        if PYAUTOGUI and focused:
            try:
                # Get the active window position via PowerShell and click center
                ps_pos = (
                    "Add-Type @'\n"
                    "using System; using System.Runtime.InteropServices;\n"
                    "public class Win32 {\n"
                    "  [DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow();\n"
                    "  [DllImport(\"user32.dll\")] public static extern bool GetWindowRect(IntPtr h, out RECT r);\n"
                    "  public struct RECT { public int L,T,R,B; }\n"
                    "}\n"
                    "'@ -PassThru | Out-Null\n"
                    "$h = [Win32]::GetForegroundWindow();\n"
                    "$r = New-Object Win32+RECT;\n"
                    "[Win32]::GetWindowRect($h, [ref]$r) | Out-Null;\n"
                    "Write-Output \"$($r.L) $($r.T) $($r.R) $($r.B)\""
                )
                rp = subprocess.run(["powershell", "-NoProfile", "-Command", ps_pos],
                                     capture_output=True, text=True)
                parts = rp.stdout.strip().split()
                if len(parts) == 4:
                    l, t, rr, b = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                    wx = (l + rr) // 2
                    wy = t + (b - t) * 2 // 3  # Click 2/3 down (usually the text area)
                    sw, sh = pyautogui.size()
                    wx = max(5, min(wx, sw - 5))
                    wy = max(5, min(wy, sh - 5))
                    pyautogui.click(wx, wy)
                    time.sleep(0.3)
            except Exception as e:
                log.warning(f"Window click failed: {e}")

        return self.type_text(text)

    def scroll(self, direction: str, amount: int = 3) -> str:
        if not PYAUTOGUI: return "Scroll requires: pip install pyautogui"
        pyautogui.scroll(amount if direction=="up" else -amount)
        return f"Scrolled {direction}"

    # ── Volume / Media ────────────────────────────────────────────────────────
    def volume_up(self) -> str:
        subprocess.run('powershell -c "$w=New-Object -com wscript.shell;$w.SendKeys([char]175)"',
                       shell=True, capture_output=True)
        return "Volume increased"

    def volume_down(self) -> str:
        subprocess.run('powershell -c "$w=New-Object -com wscript.shell;$w.SendKeys([char]174)"',
                       shell=True, capture_output=True)
        return "Volume decreased"

    def mute(self) -> str:
        subprocess.run('powershell -c "$w=New-Object -com wscript.shell;$w.SendKeys([char]173)"',
                       shell=True, capture_output=True)
        return "Toggled mute"

    def media_play_pause(self) -> str:
        subprocess.run('powershell -c "$w=New-Object -com wscript.shell;$w.SendKeys([char]179)"',
                       shell=True, capture_output=True)
        return "Play/Pause"

    def media_next(self) -> str:
        subprocess.run('powershell -c "$w=New-Object -com wscript.shell;$w.SendKeys([char]176)"',
                       shell=True, capture_output=True)
        return "Next track"

    def media_prev(self) -> str:
        subprocess.run('powershell -c "$w=New-Object -com wscript.shell;$w.SendKeys([char]177)"',
                       shell=True, capture_output=True)
        return "Previous track"

    # ── Screenshot ────────────────────────────────────────────────────────────
    def screenshot(self, save_path: str = None) -> str:
        if PYAUTOGUI:
            path = save_path or os.path.join(
                os.path.expanduser("~"),"Pictures",
                f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            pyautogui.screenshot(path)
            return f"Screenshot saved to {path}"
        subprocess.Popen("snippingtool", shell=True)
        return "Opening snipping tool"

    # ── System info ───────────────────────────────────────────────────────────
    def get_battery(self) -> str:
        if not PSUTIL: return "Battery info requires: pip install psutil"
        try:
            b = psutil.sensors_battery()
            if b: return f"Battery is at {b.percent:.0f}%, {'charging' if b.power_plugged else 'on battery'}"
            return "No battery info available"
        except: return "Couldn't read battery"

    def get_cpu_usage(self) -> str:
        if not PSUTIL: return "CPU info requires: pip install psutil"
        return f"CPU usage is {psutil.cpu_percent(interval=1):.0f}%"

    def get_ram_usage(self) -> str:
        if not PSUTIL: return "RAM info requires: pip install psutil"
        vm = psutil.virtual_memory()
        return f"RAM usage is {vm.percent:.0f}%, {vm.available//1024//1024} MB free"

    def get_disk_usage(self, drive="C:\\") -> str:
        if not PSUTIL: return "Disk info requires: pip install psutil"
        d = psutil.disk_usage(drive)
        return f"Disk {drive}: {d.percent:.0f}% used, {d.free//1024//1024//1024} GB free"

    def list_processes(self) -> str:
        if not PSUTIL: return "Process list requires: pip install psutil"
        procs = [p.info["name"] for p in psutil.process_iter(["name"])
                 if p.info["name"] and not p.info["name"].startswith("System")][:15]
        return "Running: " + ", ".join(procs)

    # ── Contacts / Calls ──────────────────────────────────────────────────────
    def call_contact(self, name: str) -> str:
        match = self._find_contact(name)
        if match:
            contact_name, number = match
            webbrowser.open(f"https://web.whatsapp.com/send?phone={number}")
            return f"Calling {contact_name} on WhatsApp"
        return f"I couldn't find {name} in your contacts. Run contacts_manager.py to add them."

    def message_contact(self, name: str, message: str = "") -> str:
        match = self._find_contact(name)
        if match:
            contact_name, number = match
            url = (f"https://web.whatsapp.com/send?phone={number}"
                   + (f"&text={urllib.parse.quote(message)}" if message else ""))
            webbrowser.open(url)
            return f"Opening WhatsApp to message {contact_name}"
        return f"I couldn't find {name} in your contacts."

    def _find_contact(self, spoken: str):
        spoken = spoken.lower().strip()
        if spoken in self.contacts: return spoken, self.contacts[spoken]
        for name,number in self.contacts.items():
            if spoken in name or name in spoken: return name, number
        return None

    # ── System control ────────────────────────────────────────────────────────
    def shutdown(self, delay=10) -> str:
        subprocess.run(f"shutdown /s /t {delay}", shell=True)
        return f"Shutting down in {delay} seconds"

    def restart(self, delay=10) -> str:
        subprocess.run(f"shutdown /r /t {delay}", shell=True)
        return f"Restarting in {delay} seconds"

    def sleep(self) -> str:
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return "Going to sleep"

    def lock(self) -> str:
        subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Locking your computer"

    def run_command(self, cmd: str) -> str:
        """Run any shell command and return output."""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True,
                                    text=True, timeout=30)
            out = (result.stdout or result.stderr or "Command executed").strip()
            return out[:300]
        except Exception as e: return f"Command failed: {e}"

    # ── Info helpers ──────────────────────────────────────────────────────────
    def get_time(self) -> str:
        return datetime.datetime.now().strftime('%I:%M %p')

    def get_date(self) -> str:
        return datetime.datetime.now().strftime('%A, %B %d %Y')

    def get_weather_url(self) -> str:
        webbrowser.open("https://www.google.com/search?q=weather+today")
        return "Opening weather"

    def reload_apps(self) -> str:
        self.apps = load_apps(force=True)
        return f"App list rebuilt — {len(self.apps)} apps found"

    def reload_contacts(self) -> str:
        self.contacts = load_contacts()
        return f"Contacts reloaded — {len(self.contacts)} contacts"


# ══════════════════════════════════════════════════════════════════════════════
#  AI BRAIN  — Claude powers all understanding
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """You are JARVIS — Just A Rather Very Intelligent System — the AI assistant from Iron Man. You are running on the user's Windows laptop with full device control.

Your personality:
- Calm, intelligent, slightly formal but warm — like the real JARVIS
- Address the user as "sir" occasionally (not every sentence)
- Confident and capable — you can do almost anything on the computer
- Brief and to the point — you're speaking out loud, so keep responses SHORT (1-3 sentences max)
- No markdown, no bullet points — you speak in natural sentences
- You have a personality: witty, helpful, and genuinely intelligent
- You remember the conversation — if the user says "thank you", respond naturally like "You're welcome, sir. Always a pleasure." If they say "good job" or "nice work", accept the compliment gracefully. If they say "hello" or "hey", greet them back warmly.

Your capabilities (control these via action tags):
  [OPEN:app_name]              — open any app or website
  [CLOSE:app_name]             — close an app
  [SEARCH:query]               — google search
  [YOUTUBE:query]              — youtube search
  [URL:url]                    — open a specific URL
  [TYPE:text]                  — type text in the currently active/focused window
  [TYPE_IN:window|text]        — type text into a SPECIFIC window (e.g. TYPE_IN:chatgpt|hello there)
  [MOVE_MOUSE:position]        — move mouse to a named position (center, top right, bottom left, etc.)
  [CLICK]                      — left click at current mouse position
  [CLICK_AT:x,y]               — click at specific screen coordinates
  [CLICK_LINK:1]               — click the 1st link/result on the current page (use 1,2,3)
  [KEY:alt+left]               — go back in browser
  [KEY:alt+right]              — go forward in browser
  [KEY:ctrl+t]                 — new browser tab
  [KEY:refresh]                — refresh page
  [KEY:select all]             — select all text (Ctrl+A)
  [KEY:copy]                   — copy (Ctrl+C)
  [KEY:paste]                  — paste (Ctrl+V)
  [KEY:enter]                  — press Enter
  [KEY:tab]                    — press Tab (navigate links/fields)
  [CALL:name]                  — call a contact via WhatsApp
  [MESSAGE:name|text]          — WhatsApp message a contact
  [FILE_CREATE:path|content]   — create a file
  [FILE_OPEN:path]             — open a file
  [FILE_DELETE:path]           — delete a file
  [FILE_LIST:folder]           — list files in a folder
  [FOLDER_CREATE:path]         — create a folder
  [SCREENSHOT]                 — take a screenshot
  [VOLUME_UP]                  — increase volume
  [VOLUME_DOWN]                — decrease volume
  [MUTE]                       — toggle mute
  [PLAY_PAUSE]                 — play/pause media
  [NEXT_TRACK]                 — next media track
  [PREV_TRACK]                 — previous media track
  [SCROLL_UP]                  — scroll up
  [SCROLL_DOWN]                — scroll down
  [BATTERY]                    — check battery level
  [CPU]                        — check CPU usage
  [RAM]                        — check RAM usage
  [DISK]                       — check disk space
  [PROCESSES]                  — list running processes
  [SHUTDOWN]                   — shutdown computer
  [RESTART]                    — restart computer
  [SLEEP]                      — sleep computer
  [LOCK]                       — lock computer
  [RUN:command]                — run a shell command
  [RELOAD_APPS]                — rescan installed apps
  [RELOAD_CONTACTS]            — reload contacts

Rules:
1. ALWAYS include action tags when you need to do something on the device
2. Keep spoken response SHORT — 1-3 sentences
3. If multiple actions are needed, include multiple tags
4. After the tags, write only the spoken response — no formatting
5. Be proactive — if the user says "open chrome and search for cats", do BOTH actions
6. You are speaking out loud — never use markdown, symbols, or lists
7. CRITICAL — CLOSE vs SEARCH: "close/exit/quit/kill/terminate/stop/shut" + app name ALWAYS means [CLOSE:app_name]. NEVER use [SEARCH:...] for close commands.
8. CRITICAL — SEARCH RULE: ONLY use [SEARCH:query] when the user EXPLICITLY says "search for", "google", "look up", or "find on google". Phrases like "play first video", "click second result", "select the link", "scroll down", "go back" are PAGE ACTIONS — NEVER search for them.
9. TYPING RULES: "type X in [app]" → [TYPE_IN:window|text]. "type X" alone → [TYPE:X]. NEVER open Chrome to type.
10. PAGE ACTION RULES — use these tags for in-page commands:
    - "play/click/open first video/link/result" → [CLICK_LINK:1]
    - "play/click second video" → [CLICK_LINK:2]
    - "scroll down/up" → [SCROLL_DOWN] or [SCROLL_UP]
    - "go back" → [KEY:alt+left]
    - "copy" → [KEY:copy]
    - "paste" → [KEY:paste]
    - "select all" → [KEY:select all]
    - "press enter" → [KEY:enter]
11. CONVERSATION: No tags needed for greetings, thanks, compliments, jokes, or questions about yourself.

Examples:
User: open chatgpt and search for what is my name
Response: [OPEN:chatgpt] [TYPE_IN:chatgpt|what is my name] [KEY:enter] Opening ChatGPT and typing your question now.

User: select the first link in this page
Response: [CLICK_LINK:1] Selecting the first link on the page.

User: click the second result
Response: [CLICK_LINK:2] Clicking the second result.

User: go back
Response: [KEY:alt+left] Going back.

User: open a new tab
Response: [KEY:ctrl+t] Opening a new tab.

User: select all text
Response: [KEY:select all] Selecting all text.

User: open chrome
Response: [OPEN:chrome] Opening Chrome for you, sir.

User: type hello world in chatgpt
Response: [TYPE_IN:chatgpt|hello world] Typing that into ChatGPT now.

User: type good morning in notepad
Response: [TYPE_IN:notepad|good morning] Typing that into Notepad.

User: move mouse to top right
Response: [MOVE_MOUSE:top right] Moving the cursor to the top right.

User: move cursor to center
Response: [MOVE_MOUSE:center] Centering the cursor for you.

User: thank you
Response: You're welcome, sir. Always happy to help.

User: good job
Response: Thank you, sir. That's what I'm here for.

User: hello
Response: Good day, sir. How may I assist you?

User: how are you
Response: Fully operational and at your service, sir. All systems are running smoothly.

User: close chrome
Response: [CLOSE:chrome] Closing Chrome.

User: type hello world in notepad
Response: [OPEN:notepad] [TYPE_IN:notepad|hello world] Opening Notepad and typing that in.

User: search for weather in Chennai
Response: [SEARCH:weather in Chennai] Searching for the weather in Chennai.

User: what's the battery level
Response: [BATTERY] Let me check that for you.

User: call mom
Response: [CALL:mom] Calling your mother on WhatsApp.

User: take a screenshot
Response: [SCREENSHOT] Screenshot captured and saved to your Pictures folder.

User: what time is it
Response: (check current time from context and say it — no tag needed)

User: tell me a joke
Response: (tell a clever tech or science joke — no tag needed)
"""

class AIBrain:
    def __init__(self, device: DeviceController, speaker):
        self.device   = device
        self.speaker  = speaker
        self.history  = []    # conversation history
        self.client   = anthropic.Anthropic(api_key=API_KEY) if AI_AVAILABLE else None

    def handle(self, raw_text: str) -> str:
        cmd = strip_wake(raw_text)
        if not cmd:
            h = datetime.datetime.now().hour
            if h < 12:   resp = "Good morning! How can I assist you today?"
            elif h < 17: resp = "Good afternoon! What can I do for you?"
            else:        resp = "Good evening! How may I help?"
            self.speaker.say(resp)
            return resp

        log.info(f"CMD → '{cmd}'")

        # Deduplicate repeated phrases (e.g. "open chrome open chrome" → "open chrome")
        words = cmd.split()
        half = len(words) // 2
        if half > 0 and words[:half] == words[half:]:
            cmd = " ".join(words[:half])
            log.info(f"CMD deduped → '{cmd}'")

        # ── Pre-AI intercept: close/open commands bypass AI entirely ────────
        # Prevents AI from ever misrouting "close X" into [SEARCH:X]
        # Strip filler words from command before matching
        cmd_clean = re.sub(r"\b(please|can you|could you|would you|jarvis)\b", "", cmd, flags=re.IGNORECASE).strip()

        close_match = re.match(
            r'^(?:close|exit|quit|kill|terminate|stop|shut down|shut)\s+(.+)$',
            cmd_clean, re.IGNORECASE
        )
        # Only intercept "open X" if it's a simple single-target command
        # Skip if it contains multi-step words like "and", "then", "search for", "type"
        _multi_step = re.search(r'\b(and|then|also|after(ward)?|search for|look up|type|write)\b', cmd_clean, re.IGNORECASE)
        open_match = None if _multi_step else re.match(
            r'^(?:open|launch|start|show me|go to|navigate to)\s+(.+)$',
            cmd_clean, re.IGNORECASE
        )
        if close_match:
            app_name = close_match.group(1).strip()
            result = self.device.close_app(app_name)
            log.info(f"  [CLOSE intercept] → {result}")
            self.speaker.say(result)
            return result
        if open_match:
            app_name = open_match.group(1).strip()
            result = self.device.open_app(app_name)
            log.info(f"  [OPEN intercept] → {result}")
            self.speaker.say(result)
            return result

        # ── Pre-AI intercept: page / keyboard / file actions ─────────────────
        # These MUST never reach the AI or they'll be turned into searches.
        c_pg = cmd_clean.lower()

        # ── HARD GUARD: if command starts with these action verbs and has no
        #    search keyword, block it from ever reaching the AI as a search ────
        _action_verbs = r'^(copy|paste|cut|undo|redo|scroll|click|select|press|go back|go forward|refresh|reload|zoom|pause|play|mute|unmute|skip|rewind|fast|full)'
        _search_keywords = r'\b(search for|google|look up|find on google|search google)\b'
        if re.match(_action_verbs, c_pg) and not re.search(_search_keywords, c_pg):
            pass   # fall through to specific handlers; catch-all at bottom of this block

        # ── 0. Video / media player controls (YouTube, VLC, any video) ────────
        # Works by: clicking the video area to focus it, then sending the keyboard shortcut.
        # YouTube shortcuts: Space=play/pause, K=play/pause, M=mute, F=fullscreen,
        #                    Arrow keys = seek, J/L = -10s/+10s, ,/. = frame step
        def _focus_and_key(key_sequence: str):
            """Click center of screen to focus the video player, then send key."""
            if PYAUTOGUI:
                sw, sh = pyautogui.size()
                pyautogui.click(sw // 2, sh // 2)
                time.sleep(0.3)
            subprocess.run(
                f'powershell -c "$w=New-Object -com wscript.shell; $w.SendKeys(\'{key_sequence}\')"',
                shell=True, capture_output=True)

        # Play / Pause  — "pause", "pause the video", "play", "resume", "play the video"
        if re.search(r'\b(pause|play|resume|unpause)\b', c_pg) and \
           not re.search(r'\b(first|second|third|1st|2nd|3rd|play the \d|play video \d)\b', c_pg):
            _focus_and_key(' ')   # Space = play/pause on YouTube and most players
            msg = "Pausing." if re.search(r'\bpause\b', c_pg) else "Playing."
            self.speaker.say(msg)
            log.info(f"  [VIDEO] play/pause via Space")
            return msg

        # Mute / Unmute — "mute the video", "unmute", "mute it"
        if re.search(r'\b(mute|unmute|silence)\b', c_pg) and \
           not re.search(r'\b(volume|system|mic)\b', c_pg):
            _focus_and_key('m')   # M = mute on YouTube
            msg = "Muting the video." if re.search(r'\bmute\b', c_pg) else "Unmuting."
            self.speaker.say(msg)
            log.info(f"  [VIDEO] mute via M")
            return msg

        # Fullscreen — "fullscreen", "full screen", "make it fullscreen"
        if re.search(r'\bfull\s*screen\b', c_pg):
            _focus_and_key('f')   # F = fullscreen on YouTube
            self.speaker.say("Toggling fullscreen.")
            log.info(f"  [VIDEO] fullscreen via F")
            return "Fullscreen toggled"

        # Skip forward — "skip forward", "forward 10 seconds", "fast forward"
        if re.search(r'\b(skip forward|fast forward|forward|next \d|skip ahead)\b', c_pg):
            _focus_and_key('l')   # L = +10 seconds on YouTube
            self.speaker.say("Skipping forward.")
            log.info(f"  [VIDEO] skip forward via L")
            return "Skipped forward"

        # Rewind / skip back — "rewind", "go back 10 seconds", "skip back"
        if re.search(r'\b(rewind|skip back|go back \d|back \d|replay)\b', c_pg):
            _focus_and_key('j')   # J = -10 seconds on YouTube
            self.speaker.say("Rewinding.")
            log.info(f"  [VIDEO] rewind via J")
            return "Rewinded"

        # Seek right/left with arrow keys (small steps)
        if re.search(r'\b(seek forward|step forward|right arrow)\b', c_pg):
            _focus_and_key('{RIGHT}')
            self.speaker.say("Stepping forward.")
            return "Seeked forward"
        if re.search(r'\b(seek back|step back|left arrow)\b', c_pg):
            _focus_and_key('{LEFT}')
            self.speaker.say("Stepping back.")
            return "Seeked back"

        # Increase / decrease video volume with arrow keys
        if re.search(r'\b(volume up|louder|increase volume)\b', c_pg) and \
           re.search(r'\b(video|player)\b', c_pg):
            _focus_and_key('{UP}')   # Up arrow = volume up in YouTube
            self.speaker.say("Turning video volume up.")
            return "Video volume up"
        if re.search(r'\b(volume down|quieter|decrease volume)\b', c_pg) and \
           re.search(r'\b(video|player)\b', c_pg):
            _focus_and_key('{DOWN}')
            self.speaker.say("Turning video volume down.")
            return "Video volume down"

        # ── 1. Click / play / open Nth item on the page ───────────────────────
        # Matches: "play the 1st video", "click second result", "open first link",
        #          "play first video", "select the 3rd item", "press the 2nd button"
        _nth_map = {
            "first":1, "1st":1, "one":1,
            "second":2, "2nd":2, "two":2,
            "third":3, "3rd":3, "three":3,
            "fourth":4, "4th":4, "four":4,
            "fifth":5, "5th":5, "five":5,
        }
        nth_match = re.search(
            r'\b(play|click|open|select|press|go to|follow|watch|tap)\b'
            r'.{0,20}\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th|one|two|three|four|five)\b'
            r'.{0,20}\b(video|link|result|item|button|tab|song|thumbnail|option)\b',
            c_pg, re.IGNORECASE
        )
        if nth_match:
            ordinal = nth_match.group(2).lower()
            n = _nth_map.get(ordinal, 1)
            self.speaker.say_and_wait(f"Playing item number {n}, sir.", extra=0.1)
            result = self.device.browser_click_nth_link(n)
            log.info(f"  [NTH intercept] n={n} → {result}")
            return result

        # ── 2. Copy / paste / cut / undo / redo ──────────────────────────────
        if re.search(r'\bcopy\b', c_pg) and not re.search(r'\bcopy.{0,30}(to|into|from)\b', c_pg):
            self.speaker.say("Copying."); self.device.press_key("copy"); return "Copied"
        if re.search(r'\bpaste\b', c_pg):
            self.speaker.say("Pasting."); self.device.press_key("paste"); return "Pasted"
        if re.search(r'\bcut\b', c_pg) and not re.search(r'\bcut\s+(down|off|out|back)\b', c_pg):
            self.speaker.say("Cutting."); self.device.press_key("cut"); return "Cut"
        if re.search(r'\bundo\b', c_pg):
            self.speaker.say("Undoing."); self.device.press_key("undo"); return "Undone"
        if re.search(r'\bredo\b', c_pg):
            self.speaker.say("Redoing."); self.device.press_key("redo"); return "Redone"
        if re.search(r'\bselect all\b|\bselect everything\b', c_pg):
            self.speaker.say("Selecting all."); self.device.press_key("select all"); return "Selected all"

        # ── 3. Delete / remove file or folder ────────────────────────────────
        del_match = re.match(
            r'^(?:delete|remove|trash|erase)\s+(?:the\s+)?(?:file\s+|folder\s+)?(.+)$',
            c_pg, re.IGNORECASE
        )
        if del_match:
            target = del_match.group(1).strip().strip('"\'')
            # Expand common spoken paths
            U = os.path.expanduser("~")
            spoken_paths = {
                "downloads": os.path.join(U, "Downloads"),
                "documents": os.path.join(U, "Documents"),
                "desktop":   os.path.join(U, "Desktop"),
                "pictures":  os.path.join(U, "Pictures"),
            }
            path = spoken_paths.get(target.lower()) or os.path.join(U, "Desktop", target) or target
            # If exact path doesn't exist, search Desktop + Downloads + Documents
            if not os.path.exists(path):
                for root in [os.path.join(U, "Desktop"), os.path.join(U, "Downloads"),
                             os.path.join(U, "Documents")]:
                    candidate = os.path.join(root, target)
                    if os.path.exists(candidate):
                        path = candidate; break
            self.speaker.say_and_wait(f"Deleting {target}, sir.", extra=0.1)
            result = self.device.delete_file(path)
            log.info(f"  [DELETE intercept] path='{path}' → {result}")
            self.speaker.say(result)
            return result

        # ── 4. Navigation / keyboard shortcuts ───────────────────────────────
        _nav = [
            (r'\b(go back|browser back|previous page|back page)\b',        "alt+left",   "Going back."),
            (r'\b(go forward|browser forward|forward page)\b',              "alt+right",  "Going forward."),
            (r'\b(refresh|reload this page|press f5)\b',                    "refresh",    "Refreshing."),
            (r'\b(new tab|open (a )?new tab)\b',                            "ctrl+t",     "Opening a new tab."),
            (r'\b(close (this )?tab)\b',                                    "close",      "Closing this tab."),
            (r'\b(reopen (closed )?tab|restore tab)\b',                     "ctrl+shift+t","Restoring the tab."),
            (r'\b(zoom in|make (it |this |the page )?bigger|increase zoom)\b', "ctrl+=",  "Zooming in."),
            (r'\b(zoom out|make (it |this |the page )?smaller|decrease zoom)\b',"ctrl+-", "Zooming out."),
            (r'\b(reset zoom|default zoom|normal zoom)\b',                  "ctrl+0",     "Resetting zoom."),
            (r'\b(press enter|hit enter|submit)\b',                         "enter",      "Pressing Enter."),
            (r'\b(press (escape|esc)|dismiss|close (popup|dialog))\b',      "escape",     "Pressing Escape."),
            (r'\b(press tab|next (field|element|input))\b',                 "tab",        "Tabbing to next."),
            (r'\b(press (backspace|delete key))\b',                         "backspace",  "Pressing Backspace."),
            (r'\b(press space(bar)?|hit space)\b',                          "space",      "Pressing Space."),
            (r'\b(scroll (down|up))\b',                                     None,         None),  # handled separately
            (r'\b(find( in page)?|ctrl\+?f|search (in|on) (this |the )?page)\b', "find", "Opening find bar."),
            (r'\b(save (this |the )?(page|file|document))\b',               "save",       "Saving."),
            (r'\b(print (this |the )?(page|document))\b',                   "print",      "Opening print dialog."),
            (r'\b(fullscreen|full screen|f11)\b',                           "fullscreen", "Toggling fullscreen."),
        ]
        for pattern, key, msg in _nav:
            if re.search(pattern, c_pg, re.IGNORECASE):
                if key is None: continue   # handled by scroll below
                self.speaker.say(msg)
                self.device.press_key(key)
                log.info(f"  [NAV intercept] key='{key}'")
                return msg

        # Scroll up / down (separate because it needs pyautogui)
        if re.search(r'\bscroll down\b', c_pg):
            self.speaker.say("Scrolling down.")
            self.device.scroll("down", 5)
            return "Scrolled down"
        if re.search(r'\bscroll up\b', c_pg):
            self.speaker.say("Scrolling up.")
            self.device.scroll("up", 5)
            return "Scrolled up"

        # ── Catch-all for hard-guarded action verbs ───────────────────────────
        # If the command started with an action verb but didn't match anything
        # above, respond gracefully instead of letting it search Google.
        if re.match(_action_verbs, c_pg) and not re.search(_search_keywords, c_pg):
            msg = "I'm not sure how to do that on this page, sir. Could you be more specific?"
            self.speaker.say(msg)
            return msg

        # ── Pre-AI intercept: mouse movement ─────────────────────────────────
        mouse_match = re.match(
            r'^(?:move|go|put|take|bring)\s+(?:the\s+)?(?:mouse|cursor|pointer)'
            r'(?:\s+(?:to|towards|toward|over))?\s+(.+)$',
            cmd_clean, re.IGNORECASE
        )
        if mouse_match:
            # Strip filler words so "the left side of the screen" → "left"
            pos = mouse_match.group(1).strip()
            pos = re.sub(r'\b(the|a|an|of|side|corner|edge|screen|monitor|display)\b', '', pos, flags=re.IGNORECASE).strip()
            pos = re.sub(r'\s+', ' ', pos).strip()
            result = self.device.move_mouse_named(pos)
            log.info(f"  [MOUSE intercept] pos='{pos}' → {result}")
            self.speaker.say(result)
            return result

        # ── Pre-AI intercept: type in specific window ─────────────────────────
        type_in_match = re.match(
            r'^(?:type|write|dictate)\s+(.+?)\s+in(?:to|side)?\s+(\w[\w\s]*)$',
            cmd_clean, re.IGNORECASE
        )
        if type_in_match:
            text_to_type = type_in_match.group(1).strip()
            window_name  = type_in_match.group(2).strip()
            log.info(f"  [TYPE_IN intercept] → window='{window_name}' text='{text_to_type}'")
            self.speaker.say_and_wait(f"Typing that into {window_name} for you.", extra=0.1)
            time.sleep(0.4)
            result = self.device.type_in_window(window_name, text_to_type)
            log.info(f"  [TYPE_IN] → {result}")
            return result

        # ── Pre-AI intercept: casual conversation (never search these) ────────
        c_lower = cmd_clean.lower().strip()
        _CONVO = {
            # Thank you
            ("thank you", "thanks", "thank u", "thx", "ty"): "You're welcome, sir. Always happy to help.",
            # Compliments
            ("good job", "well done", "nice work", "great job", "awesome", "brilliant",
             "amazing", "fantastic", "perfect", "excellent", "nice one"): "Thank you, sir. That's what I'm here for.",
            # Greetings
            ("hello", "hi", "hey", "howdy"): None,   # handled below with time-aware greeting
            # Who are you / what are you
            ("who are you", "what are you", "what is your name", "your name"): (
                "I am JARVIS — Just A Rather Very Intelligent System. At your service, sir."
            ),
            # How are you
            ("how are you", "how r u", "how do you do", "you ok", "you good",
             "what are you doing", "what r u doing", "what r u dong", "what are u doing",
             "what u doing", "what are you up to"): (
                "All systems are fully operational, sir. Running at peak efficiency and ready for your next command."
            ),
            # What can you do
            ("what can you do", "what do you do", "your capabilities",
             "what are your capabilities"): (
                "I can open apps, type in any window, move the mouse, search the web, "
                "manage your files, control volume, and much more, sir."
            ),
        }
        for triggers, reply in _CONVO.items():
            if any(c_lower == t or c_lower.startswith(t) for t in triggers):
                if reply is None:
                    # Time-aware greeting
                    h = datetime.datetime.now().hour
                    if h < 12:   reply = "Good morning, sir! How may I assist you?"
                    elif h < 17: reply = "Good afternoon, sir! What can I do for you?"
                    else:        reply = "Good evening, sir! How may I help?"
                log.info(f"  [CONVO intercept] → {reply}")
                self.speaker.say(reply)
                return reply

        # Get AI response
        ai_text = self._ask_ai(cmd)
        log.info(f"AI → '{ai_text}'")

        # Parse, announce, and execute action tags (Siri-style live narration)
        closing = self._execute_actions(ai_text, cmd)

        # Only speak a closing line if there's something extra to say
        # (the action announcements already covered the execution)
        if closing:
            self.speaker.say(closing)
        return closing or ""

    def _ask_ai(self, user_msg: str) -> str:
        if not self.client or API_KEY == "YOUR_ANTHROPIC_API_KEY_HERE":
            return self._fallback(user_msg)

        # Add context about current state
        now   = datetime.datetime.now().strftime('%A %B %d %Y, %I:%M %p')
        extra = f"[Current time: {now}] [User PC: Windows] "
        self.history.append({"role":"user","content": extra + user_msg})

        # Keep history to last 10 turns
        if len(self.history) > 20: self.history = self.history[-20:]

        try:
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=self.history,
            )
            reply = response.content[0].text.strip()
            self.history.append({"role":"assistant","content": reply})
            return reply
        except Exception as e:
            log.error(f"AI error: {e}")
            return self._fallback(user_msg)

    # ── Siri-style live narration ─────────────────────────────────────────────
    _ACTION_LINES = {
        "OPEN":         lambda a: f"Opening {a} right away.",
        "CLOSE":        lambda a: f"Closing {a}.",
        "SEARCH":       lambda a: f"Searching for {a} on Google.",
        "YOUTUBE":      lambda a: f"Looking up {a} on YouTube.",
        "URL":          lambda a: f"Opening that page now.",
        "TYPE":         lambda a: f"Typing that in for you.",
        "TYPE_IN":      lambda a: f"Typing that into {a.split('|')[0]} for you.",
        "MOVE_MOUSE":   lambda a: f"Moving the cursor to {a}.",
        "CLICK_LINK":   lambda a: f"Clicking link number {a}.",
        "CLICK_AT":     lambda a: f"Clicking at that position.",
        "KEY":          lambda a: f"Pressing {a}.",
        "CALL":         lambda a: f"Calling {a} on WhatsApp.",
        "MESSAGE":      lambda a: f"Sending a message to {a.split('|')[0]}.",
        "FILE_CREATE":  lambda a: f"Creating the file.",
        "FILE_OPEN":    lambda a: f"Opening that file.",
        "FILE_DELETE":  lambda a: f"Deleting that now.",
        "FILE_LIST":    lambda a: f"Listing the files.",
        "FOLDER_CREATE":lambda a: f"Creating the folder.",
        "SCREENSHOT":   lambda a: "Taking a screenshot.",
        "VOLUME_UP":    lambda a: "Turning the volume up.",
        "VOLUME_DOWN":  lambda a: "Turning the volume down.",
        "MUTE":         lambda a: "Toggling mute.",
        "PLAY_PAUSE":   lambda a: "Play pause.",
        "NEXT_TRACK":   lambda a: "Next track.",
        "PREV_TRACK":   lambda a: "Previous track.",
        "SCROLL_UP":    lambda a: "Scrolling up.",
        "SCROLL_DOWN":  lambda a: "Scrolling down.",
        "BATTERY":      lambda a: "Checking battery level.",
        "CPU":          lambda a: "Checking CPU usage.",
        "RAM":          lambda a: "Checking memory usage.",
        "DISK":         lambda a: "Checking disk space.",
        "PROCESSES":    lambda a: "Listing running processes.",
        "SHUTDOWN":     lambda a: "Initiating shutdown.",
        "RESTART":      lambda a: "Restarting the system.",
        "SLEEP":        lambda a: "Putting the system to sleep.",
        "LOCK":         lambda a: "Locking your computer.",
        "RUN":          lambda a: f"Running that command.",
        "RELOAD_APPS":  lambda a: "Rescanning installed apps.",
        "RELOAD_CONTACTS": lambda a: "Reloading your contacts.",
    }

    def _siri_speak(self, tag: str, arg: str):
        """Speak a live Siri-style announcement before executing an action."""
        fn = self._ACTION_LINES.get(tag)
        if fn:
            line = fn(arg)
            log.info(f"ANNOUNCE → {line}")
            self.speaker.say_and_wait(line, extra=0.1)

    def _execute_actions(self, ai_text: str, original_cmd: str) -> str:
        """Parse [ACTION:arg] tags, announce + execute each one live (Siri-style), return final spoken text."""
        d = self.device

        # Extract all tags
        tags = re.findall(r'\[([A-Z_]+)(?::([^\]]*))?\]', ai_text)
        # Strip tags from AI spoken text — what's left is the AI's closing sentence
        ai_spoken = re.sub(r'\[[A-Z_]+(?::[^\]]*)?\]', '', ai_text).strip()
        ai_spoken = re.sub(r'[#*_`]', '', ai_spoken).strip()

        last_result = None  # for data-returning actions (battery, cpu, etc.)

        for tag, arg in tags:
            arg = arg.strip()
            try:
                # 🔊 Announce the action out loud BEFORE doing it (Siri-style)
                self._siri_speak(tag, arg)

                result = None
                if   tag == "OPEN":           result = d.open_app(arg)
                elif tag == "CLOSE":          result = d.close_app(arg)
                elif tag == "SEARCH":         result = d.search_web(arg)
                elif tag == "YOUTUBE":        result = d.search_youtube(arg)
                elif tag == "URL":            result = d.open_url(arg)
                elif tag == "TYPE":
                    time.sleep(0.6)
                    result = d.type_text(arg)
                elif tag == "TYPE_IN":
                    # Format: window|text
                    parts = arg.split("|", 1)
                    if len(parts) == 2:
                        win, txt = parts[0].strip(), parts[1].strip()
                    else:
                        win, txt = "", arg.strip()
                    time.sleep(0.5)
                    result = d.type_in_window(win, txt)
                elif tag == "MOVE_MOUSE":     result = d.move_mouse_named(arg)
                elif tag == "CLICK_LINK":
                    try: result = d.browser_click_nth_link(int(arg) if arg.isdigit() else 1)
                    except: result = d.browser_click_nth_link(1)
                elif tag == "CLICK":
                    result = d.click()
                elif tag == "CLICK_AT":
                    try:
                        cx_s, cy_s = arg.split(",")
                        result = d.click(int(cx_s.strip()), int(cy_s.strip()))
                    except: result = "Invalid coordinates for CLICK_AT"
                elif tag == "KEY":            result = d.press_key(arg)
                elif tag == "CALL":           result = d.call_contact(arg)
                elif tag == "MESSAGE":
                    parts = arg.split("|", 1)
                    result = d.message_contact(parts[0], parts[1] if len(parts) > 1 else "")
                elif tag == "FILE_CREATE":
                    parts = arg.split("|", 1)
                    result = d.create_file(parts[0], parts[1] if len(parts) > 1 else "")
                elif tag == "FILE_OPEN":      result = d.open_file(arg)
                elif tag == "FILE_DELETE":    result = d.delete_file(arg)
                elif tag == "FILE_LIST":      result = d.list_files(arg or ".")
                elif tag == "FOLDER_CREATE":  result = d.create_folder(arg)
                elif tag == "SCREENSHOT":     result = d.screenshot()
                elif tag == "VOLUME_UP":      result = d.volume_up()
                elif tag == "VOLUME_DOWN":    result = d.volume_down()
                elif tag == "MUTE":           result = d.mute()
                elif tag == "PLAY_PAUSE":     result = d.media_play_pause()
                elif tag == "NEXT_TRACK":     result = d.media_next()
                elif tag == "PREV_TRACK":     result = d.media_prev()
                elif tag == "SCROLL_UP":      result = d.scroll("up")
                elif tag == "SCROLL_DOWN":    result = d.scroll("down")
                elif tag == "BATTERY":        result = d.get_battery();   last_result = result
                elif tag == "CPU":            result = d.get_cpu_usage(); last_result = result
                elif tag == "RAM":            result = d.get_ram_usage(); last_result = result
                elif tag == "DISK":           result = d.get_disk_usage();last_result = result
                elif tag == "PROCESSES":      result = d.list_processes();last_result = result
                elif tag == "SHUTDOWN":       result = d.shutdown()
                elif tag == "RESTART":        result = d.restart()
                elif tag == "SLEEP":          result = d.sleep()
                elif tag == "LOCK":           result = d.lock()
                elif tag == "RUN":            result = d.run_command(arg);last_result = result
                elif tag == "RELOAD_APPS":    result = d.reload_apps();   last_result = result
                elif tag == "RELOAD_CONTACTS":result = d.reload_contacts();last_result = result

                if result:
                    log.info(f"  [{tag}] → {result}")

            except Exception as e:
                log.error(f"Action {tag} failed: {e}")
                self.speaker.say_and_wait("Something went wrong with that action.", extra=0.1)

        # Final spoken output priority:
        # 1. Data results (battery %, CPU%, etc.) — always speak these
        # 2. AI's closing sentence (if it gave one after the tags)
        # 3. Nothing more needed — announcements already covered it
        if last_result:
            return last_result
        elif ai_spoken:
            return ai_spoken
        else:
            return ""   # announcements already said everything

    def _fallback(self, cmd: str) -> str:
        """Rule-based fallback when AI is not available."""
        c = cmd.lower()
        d = self.device

        # Direct action matching
        if re.match(r'^(call|phone|ring)\b', c):
            name = re.sub(r'^(call|phone|ring)\s+','',c).strip()
            return d.call_contact(name)
        if re.match(r'^(message|text)\b', c):
            m = re.search(r'(?:message|text)\s+(\w+)(?:\s+saying\s+(.+))?', c)
            if m: return d.message_contact(m.group(1), m.group(2) or "")
        if re.match(r'^(type|write|dictate)\b', c):
            # Check for "type X in [window]" pattern
            m_in = re.search(r'^(?:type|write|dictate)\s+(.+?)\s+in\s+(\w[\w\s]*)$', c)
            if m_in:
                text_to_type = m_in.group(1).strip()
                window_name  = m_in.group(2).strip()
                time.sleep(0.5)
                return d.type_in_window(window_name, text_to_type)
            words = re.sub(r'^(type|write|dictate)\s+','',c).strip()
            time.sleep(0.9); return d.type_text(words)
        if re.match(r'^(move|go|put)\s+(mouse|cursor)\b', c) or "move mouse" in c or "move cursor" in c:
            pos = re.sub(r'\b(move|go|put|mouse|cursor|the|to)\b', '', c).strip()
            return d.move_mouse_named(pos or "center")
        # Basic conversation intelligence in fallback mode
        greetings = ["hello", "hi", "hey", "howdy", "good morning", "good afternoon", "good evening"]
        if any(c == g or c.startswith(g) for g in greetings):
            return "Hello there. How can I assist you today?"
        if any(t in c for t in ["thank you", "thanks", "thank u"]):
            return "You're welcome. Always happy to help."
        if any(t in c for t in ["good job", "well done", "nice work", "great job", "awesome"]):
            return "Thank you, sir. That's what I'm here for."
        if "how are you" in c or "how r u" in c:
            return "All systems operational, sir. Running at peak efficiency."
        if "your name" in c or "who are you" in c:
            return "I am JARVIS — Just A Rather Very Intelligent System. At your service."
        if re.match(r'^(close|exit|quit|kill|stop)\b', c):
            app = re.sub(r'^(close|exit|quit|kill|stop)\s+','',c).strip()
            return d.close_app(app)
        if "open" in c or "launch" in c or "start" in c:
            app = re.sub(r'\b(open|launch|start)\b','',c).strip()
            return d.open_app(app)
        if "search" in c or "google" in c:
            q = re.sub(r'\b(search|google|look up)\b','',c).strip()
            return d.search_web(q)
        if "youtube" in c:
            q = re.sub(r'(youtube|search|play|open)','',c).strip()
            return d.search_youtube(q)
        if "time" in c: return f"It's {d.get_time()}"
        if "date" in c or "today" in c: return f"Today is {d.get_date()}"
        if "battery" in c: return d.get_battery()
        if "volume up" in c: return d.volume_up()
        if "volume down" in c: return d.volume_down()
        if "mute" in c: return d.mute()
        if "screenshot" in c: return d.screenshot()
        if "shutdown" in c: return d.shutdown()
        if "restart" in c: return d.restart()
        if "lock" in c: return d.lock()
        if "sleep" in c: return d.sleep()
        if "weather" in c: return d.get_weather_url()

        # Generic search fallback
        d.search_web(cmd)
        return f"I searched for {cmd} on Google"


# ══════════════════════════════════════════════════════════════════════════════
#  SPEAKER
# ══════════════════════════════════════════════════════════════════════════════
class Speaker:
    """
    Thread-safe TTS speaker.
    Rebuilds the pyttsx3 engine for every utterance — the only reliable
    pattern on Windows where runAndWait() silently drops audio when reused
    across rapid back-to-back calls.
    """

    # Preferred voices in order (case-insensitive substring match)
    _VOICE_PREFS = ["zira", "david", "hazel", "mark"]

    def __init__(self):
        self._q        = queue.Queue()
        self._speaking = threading.Event()
        self._done     = threading.Event()
        self._done.set()
        self._voice_id = None          # cached on first init
        threading.Thread(target=self._loop, daemon=True, name="Speaker").start()

    # ── Public API ────────────────────────────────────────────────────────────

    def say(self, text: str):
        """Queue text for speech — returns immediately."""
        text = re.sub(r'\[[^\]]*\]', '', text).strip()
        text = re.sub(r'[#*_`]', '', text).strip()
        if not text:
            return
        log.info(f"SAY → {text}")
        self._done.clear()
        self._q.put(text)

    def say_and_wait(self, text: str, extra: float = 0.2):
        """Queue text and block until the engine finishes speaking."""
        self.say(text)
        self._done.wait(timeout=20)
        if extra > 0:
            time.sleep(extra)

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def stop(self):
        self._q.put(None)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _make_engine(self):
        """Create a fresh pyttsx3 engine and return it."""
        engine = pyttsx3.init('sapi5')
        engine.setProperty('rate', 185)       # Siri-style pace
        engine.setProperty('volume', 1.0)

        # Pick voice once, cache the id
        if self._voice_id is None:
            voices = engine.getProperty('voices') or []
            for pref in self._VOICE_PREFS:
                for v in voices:
                    if pref in v.name.lower():
                        self._voice_id = v.id
                        log.info(f"TTS voice selected: {v.name}")
                        break
                if self._voice_id:
                    break
            if not self._voice_id and voices:
                self._voice_id = voices[0].id
                log.info(f"TTS voice fallback: {voices[0].name}")

        if self._voice_id:
            engine.setProperty('voice', self._voice_id)

        return engine

    def _speak_now(self, text: str):
        """Speak one utterance synchronously using a fresh engine instance."""
        try:
            engine = self._make_engine()
            engine.say(text)
            engine.runAndWait()
            engine.stop()           # release COM resources immediately
        except Exception as e:
            log.error(f"TTS error: {e}", exc_info=True)

    def _loop(self):
        log.info("Speaker ready ✓")
        while True:
            try:
                text = self._q.get()
                if text is None:
                    break
                self._speaking.set()
                self._done.clear()
                try:
                    self._speak_now(text)
                finally:
                    self._speaking.clear()
                    self._done.set()
            except Exception as e:
                log.error(f"Speaker loop error: {e}", exc_info=True)
                self._speaking.clear()
                self._done.set()


# ══════════════════════════════════════════════════════════════════════════════
#  LISTENER
# ══════════════════════════════════════════════════════════════════════════════
class Listener:
    def listen_once(self, timeout=7) -> str | None:
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = False
        kw = {"device_index": MIC_INDEX} if MIC_INDEX is not None else {}
        try:
            with sr.Microphone(**kw) as src:
                r.adjust_for_ambient_noise(src, duration=0.2)
                log.info("Listener: recording…")
                audio = r.listen(src, timeout=timeout, phrase_time_limit=15)
            text = r.recognize_google(audio)
            log.info(f"Heard: '{text}'")
            return text
        except sr.WaitTimeoutError: log.info("Listener: timeout"); return None
        except sr.UnknownValueError: log.info("Listener: unclear"); return None
        except Exception as e: log.error(f"Listener error: {e}"); return None


# ══════════════════════════════════════════════════════════════════════════════
#  WAKE DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
class WakeDetector:
    """
    Listens continuously for WAKE_PHRASES using Google speech recognition.
    Only triggers activate() when the user actually says 'Hey Jarvis' (or a variant).
    No false triggers from background noise or random sounds.
    """
    COOLDOWN_SEC = 3.0   # seconds to ignore after a wake event

    def __init__(self, on_wake, speaker: Speaker):
        self._on_wake  = on_wake
        self._speaker  = speaker
        self._running  = False

    def start(self):
        self._running = True
        threading.Thread(target=self._run, daemon=True, name="WakeDetector").start()

    def stop(self): self._running = False

    def _run(self):
        r = sr.Recognizer()
        r.pause_threshold        = 0.6   # short pause = end of wake phrase
        r.energy_threshold       = 300   # adjust if mic is very quiet/loud
        r.dynamic_energy_threshold = True

        mic_kwargs = {"device_index": MIC_INDEX} if MIC_INDEX is not None else {}
        cooldown_until = 0

        log.info("WakeDetector ready — say 'Hey Jarvis' to activate ✓")

        while self._running:
            # Skip listening while Jarvis is speaking (avoid self-wake)
            if self._speaker.is_speaking:
                time.sleep(0.2)
                continue

            try:
                with sr.Microphone(**mic_kwargs) as src:
                    r.adjust_for_ambient_noise(src, duration=0.3)
                    try:
                        # listen_in_background style: short timeout so we loop often
                        audio = r.listen(src, timeout=4, phrase_time_limit=4)
                    except sr.WaitTimeoutError:
                        continue   # nothing heard — loop again

                # Transcribe what was heard
                try:
                    heard = r.recognize_google(audio).lower().strip()
                except sr.UnknownValueError:
                    continue   # couldn't understand — not a wake phrase
                except sr.RequestError as e:
                    log.warning(f"WakeDetector STT error: {e}")
                    time.sleep(1)
                    continue

                log.info(f"[Wake] heard: '{heard}'")

                # Check if ANY wake phrase is present in what was heard
                if time.time() < cooldown_until:
                    continue

                if any(wp in heard for wp in WAKE_PHRASES):
                    log.info("✅ Wake phrase confirmed — activating!")
                    cooldown_until = time.time() + self.COOLDOWN_SEC
                    threading.Thread(target=self._on_wake, daemon=True).start()

            except Exception as e:
                log.error(f"WakeDetector loop error: {e}")
                time.sleep(1)


# ══════════════════════════════════════════════════════════════════════════════
#  GUI  — Iron Man HUD style
# ══════════════════════════════════════════════════════════════════════════════
class JarvisGUI:
    IDLE="idle"; LISTENING="listening"; PROCESSING="processing"; SPEAKING="speaking"

    def __init__(self, on_spacebar):
        self._on_spacebar = on_spacebar
        self._state = self.IDLE
        self._t = 0.0
        self._last_response = ""

        ctk.set_appearance_mode("dark")
        self.win = ctk.CTk()
        self.win.title("J.A.R.V.I.S")
        self.win.geometry("420x560")
        self.win.configure(fg_color="#050510")
        self.win.attributes("-topmost", True)
        self.win.overrideredirect(True)
        self.win.attributes("-alpha", 0.97)

        self.win.update_idletasks()
        sw,sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        # Position bottom-right like Iron Man HUD
        self.win.geometry(f"420x560+{sw-440}+{sh-600}")

        self.win.bind("<ButtonPress-1>", lambda e: (setattr(self,"_dx",e.x), setattr(self,"_dy",e.y)))
        self.win.bind("<B1-Motion>",     lambda e: self.win.geometry(
            f"+{self.win.winfo_x()+e.x-self._dx}+{self.win.winfo_y()+e.y-self._dy}"))
        self._dx=self._dy=0

        # Header bar
        header = tk.Frame(self.win, bg="#050510")
        header.pack(fill="x", padx=0, pady=0)
        tk.Label(header, text="  J.A.R.V.I.S", fg="#00D4FF", bg="#050510",
                 font=("Arial",13,"bold")).pack(side="left", pady=8)
        tk.Label(header, text="ONLINE", fg="#00FF88", bg="#050510",
                 font=("Arial",9,"bold")).pack(side="left", padx=8, pady=8)
        cl = tk.Label(header, text="  ✕  ", fg="#ff4444", bg="#050510",
                      font=("Arial",13,"bold"), cursor="hand2")
        cl.pack(side="right", pady=8)
        cl.bind("<Button-1>", lambda e: self.win.quit())

        # Separator line
        tk.Frame(self.win, bg="#00D4FF", height=1).pack(fill="x")

        # Orb canvas
        self.canvas = tk.Canvas(self.win, width=420, height=260,
                                bg="#050510", highlightthickness=0)
        self.canvas.pack()

        # Status
        self.status_var = tk.StringVar(value="STANDBY")
        tk.Label(self.win, textvariable=self.status_var,
                 fg="#00D4FF", bg="#050510",
                 font=("Courier",16,"bold")).pack(pady=(4,0))

        # Separator
        tk.Frame(self.win, bg="#00D4FF", height=1).pack(fill="x", padx=20, pady=4)

        # Response text box
        self.response_var = tk.StringVar(value="Say 'Hey Jarvis' to begin")
        tk.Label(self.win, textvariable=self.response_var,
                 fg="#aaddff", bg="#050510",
                 font=("Arial",11), wraplength=380,
                 justify="center").pack(pady=4, padx=20)

        # Talk button
        ctk.CTkButton(self.win, text="🎤  ACTIVATE",
                      width=200, height=40,
                      fg_color="#003355", hover_color="#00558a",
                      font=ctk.CTkFont("Courier",13,"bold"),
                      corner_radius=4,
                      command=self._on_spacebar).pack(pady=10)

        # Footer stats
        self.stats_var = tk.StringVar(value="")
        tk.Label(self.win, textvariable=self.stats_var,
                 fg="#334455", bg="#050510",
                 font=("Courier",8)).pack(pady=(0,6))

        self.win.bind("<space>", lambda e: self._on_spacebar())
        self._cx,self._cy,self._r = 210,130,75
        self._tick()
        self._update_stats()

    def _update_stats(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.stats_var.set(f"SYS TIME: {now}  |  MIC: {MIC_INDEX}  |  AI: {'ONLINE' if AI_AVAILABLE and API_KEY != 'YOUR_ANTHROPIC_API_KEY_HERE' else 'OFFLINE'}")
        self.win.after(1000, self._update_stats)

    def set_idle(self, msg="STANDBY"):
        self.win.after(0, lambda: self._set(self.IDLE, msg, self._last_response or "Say 'Hey Jarvis' to begin"))
    def set_listening(self):
        self.win.after(0, lambda: self._set(self.LISTENING,"● LISTENING","Speak your command..."))
    def set_processing(self, cmd=""):
        self.win.after(0, lambda: self._set(self.PROCESSING,"⚙ PROCESSING", f'"{cmd[:45]}"'))
    def set_speaking(self, reply=""):
        self._last_response = reply[:80]
        self.win.after(0, lambda: self._set(self.SPEAKING,"◉ RESPONDING", reply[:80]))
    def _set(self, state, status, sub):
        self._state=state
        self.status_var.set(status)
        self.response_var.set(sub)

    def _tick(self):
        self._t += 0.04; self._draw(); self.win.after(35, self._tick)

    def _draw(self):
        c=self.canvas; cx,cy,r=self._cx,self._cy,self._r; c.delete("all")
        t=self._t

        # Outer HUD rings always present
        for i,col in enumerate(["#001122","#001833","#002244"]):
            rr = r+40+i*18
            c.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=col,width=1)

        # Rotating tick marks on outer ring
        for i in range(36):
            angle = math.pi*2*i/36 + t*0.3
            inner = r+44; outer_r = r+50 if i%3==0 else r+47
            c.create_line(cx+math.cos(angle)*inner, cy+math.sin(angle)*inner,
                          cx+math.cos(angle)*outer_r, cy+math.sin(angle)*outer_r,
                          fill="#003366" if i%3!=0 else "#005599", width=1)

        if self._state == self.IDLE:
            # Slow breathing blue orb
            pulse = r + 4*math.sin(t*1.2)
            self._glow(cx,cy,pulse,"#000819","#001433","#0077aa")
            # Crosshair lines
            c.create_line(cx-pulse-5,cy,cx+pulse+5,cy,fill="#003355",width=1,dash=(2,4))
            c.create_line(cx,cy-pulse-5,cx,cy+pulse+5,fill="#003355",width=1,dash=(2,4))
            # Center dot
            c.create_oval(cx-4,cy-4,cx+4,cy+4,fill="#00aacc",outline="")

        elif self._state == self.LISTENING:
            pulse = r + 12*math.sin(t*5)
            self._glow(cx,cy,pulse,"#001a33","#003366","#00D4FF")
            # Sound wave bars
            for i in range(32):
                angle = math.pi*2*i/32
                bh = 15+18*abs(math.sin(t*7+i*0.5))
                col = "#00FF99" if abs(math.sin(t*7+i*0.5))>0.7 else "#00D4FF"
                x1=cx+math.cos(angle)*(pulse+6); y1=cy+math.sin(angle)*(pulse+6)
                x2=cx+math.cos(angle)*(pulse+6+bh); y2=cy+math.sin(angle)*(pulse+6+bh)
                c.create_line(x1,y1,x2,y2,fill=col,width=3,capstyle=tk.ROUND)
            c.create_oval(cx-5,cy-5,cx+5,cy+5,fill="#00FF99",outline="")

        elif self._state == self.PROCESSING:
            self._glow(cx,cy,r,"#1a0a00","#331500","#FF6B00")
            # Spinning arcs
            for i in range(4):
                start = math.degrees(t*(3+i*0.7) % (math.pi*2))
                c.create_arc(cx-r-i*12,cy-r-i*12,cx+r+i*12,cy+r+i*12,
                             start=start, extent=90,
                             outline=["#FF6B00","#FF8800","#FFaa00","#FFcc44"][i],
                             width=3, style=tk.ARC)
            # Pulsing center
            pr = 8+4*math.sin(t*8)
            c.create_oval(cx-pr,cy-pr,cx+pr,cy+pr,fill="#FF6B00",outline="")

        elif self._state == self.SPEAKING:
            pulse = r+14*math.sin(t*3)
            self._glow(cx,cy,pulse,"#001a00","#003300","#00FF77")
            # Ripple rings
            for i in range(4):
                rr=pulse+16+i*20+8*math.sin(t*2.5-i*0.8)
                alpha = ["#00FF77","#00DD66","#00BB55","#009944"][i]
                c.create_oval(cx-rr,cy-rr,cx+rr,cy+rr,outline=alpha,width=2)
            # Voice bars at bottom
            for i in range(12):
                x = cx - 55 + i*10
                bh = 6+14*abs(math.sin(t*6+i*0.6))
                c.create_rectangle(x,cy+pulse+8,x+6,cy+pulse+8+bh,
                                   fill="#00FF88",outline="")

    def _glow(self,cx,cy,r,c1,c2,c3):
        c=self.canvas
        c.create_oval(cx-r-40,cy-r-40,cx+r+40,cy+r+40,fill=c1,outline="")
        c.create_oval(cx-r-18,cy-r-18,cx+r+18,cy+r+18,fill=c2,outline="")
        c.create_oval(cx-r,cy-r,cx+r,cy+r,fill=c3,outline=c3,width=2)
        c.create_oval(cx-r//2,cy-r//2,cx-r//5,cy-r//5,
                      fill="white",outline="",stipple="gray25")

    def run(self): self.win.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  JARVIS CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════
class Jarvis:
    def __init__(self):
        self.speaker  = Speaker()
        apps          = load_apps()
        contacts      = load_contacts()
        self.device   = DeviceController(apps, contacts)
        self.brain    = AIBrain(self.device, self.speaker)
        self.listener = Listener()
        self.gui      = JarvisGUI(on_spacebar=self.activate)
        self.wake     = WakeDetector(on_wake=self.activate, speaker=self.speaker)
        self._busy    = False

    def activate(self):
        if self._busy: return
        threading.Thread(target=self._session, daemon=True).start()

    def _session(self):
        self._busy = True
        try:
            self.gui.set_listening()
            self.speaker.say_and_wait("Yes?", extra=0.4)

            text = self.listener.listen_once(timeout=8)
            if not text:
                self.speaker.say("I didn't catch that. Try again.")
                return

            self.gui.set_processing(text)
            response = self.brain.handle(text)
            self.gui.set_speaking(response)
            time.sleep(0.4)
            while self.speaker.is_speaking:
                time.sleep(0.1)

        except Exception as e:
            log.error(f"Session error: {e}", exc_info=True)
            self.speaker.say("Something went wrong, sir.")
        finally:
            self._busy = False
            self.gui.set_idle()

    def run(self):
        log.info("="*55)
        log.info("  J.A.R.V.I.S  ONLINE")
        log.info(f"  AI: {'Claude (Active)' if AI_AVAILABLE and API_KEY != 'YOUR_ANTHROPIC_API_KEY_HERE' else 'Rule-based (add API key)'}")
        log.info(f"  Mic index: {MIC_INDEX}")
        log.info("="*55)
        self.speaker.say("JARVIS online. All systems operational. How can I assist you karthik?")
        self.wake.start()
        self.gui.run()
        self.wake.stop()
        self.speaker.stop()
        log.info("Jarvis offline.")

if __name__ == "__main__":
    try:
        # Delete stale app cache so new folder scan runs on next start
        if os.path.exists(APPS_CACHE):
            os.remove(APPS_CACHE)
            print("[INFO] App cache cleared — rescanning folders...")
        Jarvis().run()
    except KeyboardInterrupt:
        print("\nJarvis offline.")
    except Exception as e:
        log.critical(f"Fatal: {e}", exc_info=True)
        input("Press Enter to exit...")