#!/usr/bin/env python3
"""BO4E-Schema-Viewer – erzeugt eine eigenständige HTML-Datei aus conuti-gmbh/bo4e-schema.

Quelle (Standard): GitHub conuti-gmbh/bo4e-schema@master.
  - Der aktuelle Commit wird über die GitHub-API geprüft; nur bei neuem Commit wird das Archiv geladen
    (schemas/, translation/, docs/examples/) und unter cache/<sha>/ abgelegt.
  - Ohne Verbindung: letzter Cache-Stand, sonst eine lokale Kopie (MACOAPP/bo4e-schema-master oder
    ../bo4e-schema bzw. ../bo4e-schema-master neben diesem Ordner, oder settings.json "bo4e_local_path").
Token ist optional (Repo öffentlich), hilft aber gegen das Rate-Limit (60 Abfragen/h anonym):
  BO4E_GITHUB_TOKEN, GITHUB_TOKEN, GH_TOKEN, settings.json "github_token" oder `gh auth token`.

Aufruf:
  python build_viewer.py                 # GitHub (Fallback Cache / lokal)
  python build_viewer.py --quelle lokal  # nur lokale Kopie
  python build_viewer.py --ref <branch|tag|commit> --out <datei.html>

Nur Python-Standardbibliothek.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MACOAPP = HERE.parent.parent  # wenn das Tool unter MACOAPP/Tools/<Tool> liegt


def default_local() -> Path:
    """Lokale Kopie des Schema-Repos: neben MACOAPP/Tools oder neben diesem Repo (z. B. Github-Repos/bo4e-schema)."""
    candidates = (MACOAPP / "bo4e-schema-master", HERE.parent / "bo4e-schema", HERE.parent / "bo4e-schema-master")
    for p in candidates:
        if (p / "schemas" / "v1").exists():
            return p
    return candidates[0]


DEFAULT_LOCAL = default_local()
CACHE = HERE / "cache"
TEMPLATE = HERE / "template.html"
LOGO = HERE / "conuti-logo.png"
DEFAULT_OUT = HERE / "output" / "BO4E-Schema-Viewer.html"
API = "https://api.github.com"
KINDS = ("bo", "com", "enum", "cdoc")
KEEP = ("schemas/", "translation/", "docs/examples/")


def log(msg: str):
    print(msg, flush=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_settings() -> dict:
    p = HERE / "settings.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log(f"Hinweis: settings.json nicht lesbar ({e})")
    return {}


# ----------------------------------------------------------------------------- GitHub

class GitHub:
    def __init__(self, repo: str, ref: str, token: str | None):
        self.repo, self.ref, self.token = repo, ref, token

    def _get(self, url: str, timeout: int = 30) -> bytes:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "BO4E-Schema-Viewer",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 401 and self.token:  # ungültiger Token -> anonym weiter (Repo ist öffentlich)
                log("Hinweis: Token wurde abgelehnt (401) – versuche es ohne Token.")
                self.token = None
                return self._get(url, timeout)
            raise

    def latest(self) -> dict:
        d = json.loads(self._get(f"{API}/repos/{self.repo}/commits/{self.ref}"))
        c = d.get("commit") or {}
        return {"sha": d["sha"], "commit_date": (c.get("committer") or {}).get("date", ""),
                "commit_message": (c.get("message") or "").split("\n")[0][:200]}

    def download(self, sha: str, target: Path):
        raw = self._get(f"{API}/repos/{self.repo}/zipball/{sha}", timeout=180)
        tmp = target.parent / f".tmp-{target.name}-{int(time.time())}"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        n = 0
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for info in z.infolist():
                parts = info.filename.split("/", 1)  # erster Ordner = <owner>-<repo>-<sha>/
                if len(parts) < 2 or info.is_dir():
                    continue
                rel = parts[1]
                if not rel.startswith(KEEP) or ".." in Path(rel).parts:
                    continue
                dest = tmp / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(info))
                n += 1
        if n == 0 or not (tmp / "schemas" / "v1").exists():
            shutil.rmtree(tmp, ignore_errors=True)
            raise RuntimeError("Archiv enthält kein schemas/v1")
        shutil.rmtree(target, ignore_errors=True)
        os.replace(tmp, target)


def find_token(settings: dict) -> str | None:
    t = (os.environ.get("BO4E_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
         or settings.get("github_token") or None)
    if not t and shutil.which("gh"):
        try:
            r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
            t = r.stdout.strip() if r.returncode == 0 else None
        except Exception:  # noqa: BLE001
            t = None
    return t or None


def cache_current() -> dict | None:
    p = CACHE / "current.json"
    if p.exists():
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
            if (CACHE / c["dir"] / "schemas" / "v1").exists():
                return c
        except Exception:  # noqa: BLE001
            pass
    return None


def resolve_source(args, settings) -> tuple[Path, dict]:
    """Liefert (Wurzelordner mit schemas/v1, Quell-Info)."""
    local = Path(args.lokal or settings.get("bo4e_local_path") or DEFAULT_LOCAL)
    quelle = args.quelle or settings.get("quelle") or "github"
    repo = args.repo or settings.get("bo4e_repo") or "conuti-gmbh/bo4e-schema"
    ref = args.ref or settings.get("bo4e_ref") or "master"

    def local_info(hinweis=""):
        if not (local / "schemas" / "v1").exists():
            sys.exit(f"FEHLER: lokale Kopie nicht gefunden: {local}")
        return local, {"art": "lokal", "pfad": str(local), "hinweis": hinweis}

    if quelle == "lokal":
        return local_info()

    gh = GitHub(repo, ref, find_token(settings))
    try:
        log(f"Prüfe GitHub {repo}@{ref} …")
        latest = gh.latest()
        CACHE.mkdir(parents=True, exist_ok=True)
        cur = cache_current()
        d = latest["sha"][:12]
        if not (cur and cur["sha"] == latest["sha"] and (CACHE / d / "schemas" / "v1").exists()):
            log(f"Lade Stand {d} ({latest['commit_date']}) …")
            gh.download(latest["sha"], CACHE / d)
            info = {**latest, "dir": d, "repo": repo, "ref": ref, "fetched_at": now_iso(),
                    "previous_sha": (cur or {}).get("sha", "")}
            (CACHE / "current.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
            keep = {d} | ({cur["dir"]} if cur else set())
            for p in CACHE.iterdir():
                if p.is_dir() and p.name not in keep:
                    shutil.rmtree(p, ignore_errors=True)
            cur = info
        else:
            log(f"Stand {d} ist bereits im Cache.")
        return CACHE / d, {"art": "github", **{k: cur[k] for k in ("repo", "ref", "sha", "commit_date",
                                                                   "commit_message", "fetched_at")}}
    except Exception as e:  # noqa: BLE001  (offline, Proxy, Rate-Limit …)
        msg = f"{type(e).__name__}: {e}"
        if isinstance(e, urllib.error.HTTPError):
            msg = f"GitHub HTTP {e.code}" + {403: " (Rate-Limit? Token hinterlegen)",
                                              404: " (Repo/Ref nicht gefunden)"}.get(e.code, "")
        log(f"WARNUNG: GitHub nicht erreichbar – {msg}")
        cur = cache_current()
        if cur:
            log(f"→ verwende letzten Cache-Stand {cur['dir']} vom {cur['commit_date']}")
            return CACHE / cur["dir"], {"art": "cache", **{k: cur[k] for k in (
                "repo", "ref", "sha", "commit_date", "commit_message", "fetched_at")},
                "hinweis": f"GitHub nicht erreichbar ({msg}) – letzter geladener Stand"}
        log(f"→ verwende lokale Kopie {local}")
        return local_info(f"GitHub nicht erreichbar ({msg}) – lokale Kopie")


# ----------------------------------------------------------------------------- Schema lesen

REF_RE = re.compile(r"^(?:\.\./(bo|com|enum|cdoc)/)?([A-Za-z0-9_]+)\.schema\.json$")


def as_list(t) -> list:
    return t if isinstance(t, list) else ([t] if t else [])


def parse_ref(ref: str, own_kind: str) -> str | None:
    m = REF_RE.match(ref or "")
    return f"{m.group(1) or own_kind}/{m.group(2)}" if m else None


def parse_type(spec: dict, own_kind: str, problems: list, where: str) -> dict:
    types = as_list(spec.get("type"))
    arr = "array" in types
    tgt = (spec.get("items") or {}) if arr else spec
    out: dict = {}
    if arr:
        out["arr"] = 1
    if "null" in types or "null" in as_list(tgt.get("type")):
        out["null"] = 1
    ref = tgt.get("$ref") or (spec.get("$ref") if not arr else None)
    if ref:
        r = parse_ref(ref, own_kind)
        if r:
            out["ref"] = r
        else:
            out["b"] = "?"
            out["raw"] = ref
            problems.append(f"{where}: $ref nicht auflösbar: {ref}")
    else:
        base = [x for x in as_list(tgt.get("type")) if x not in ("null", "array")]
        out["b"] = base[0] if base else ("array" if arr else "any")
        fmt = tgt.get("format") or (spec.get("format") if not arr else None)
        if fmt:
            out["f"] = fmt
    en = tgt.get("enum") or spec.get("enum")
    if en:
        out["e"] = en
    return out


def read_schemas(root: Path) -> tuple[dict, dict, list]:
    base = root / "schemas" / "v1"
    objects, raw, problems = {}, {}, []
    for kind in KINDS:
        folder = base / kind
        if not folder.exists():
            continue
        for f in sorted(folder.glob("*.schema.json"), key=lambda p: p.name.lower()):
            name = f.name[: -len(".schema.json")]
            key = f"{kind}/{name}"
            text = f.read_text(encoding="utf-8")
            try:
                d = json.loads(text)
            except Exception as e:  # noqa: BLE001
                problems.append(f"{key}: JSON nicht lesbar ({e})")
                continue
            raw[key] = text
            o: dict = {"k": kind, "n": name}
            if d.get("title") and d["title"] != name:
                o["title"] = d["title"]
            if d.get("description"):
                o["d"] = d["description"].strip()
            if d.get("x-descriptions"):
                o["xd"] = d["x-descriptions"]
            if "enum" in d:
                o["v"] = d["enum"]
            if "properties" in d or kind != "enum" and "enum" not in d:
                req = set(d.get("required") or [])
                props = []
                for pn, ps in (d.get("properties") or {}).items():
                    p = {"n": pn, "t": parse_type(ps, kind, problems, f"{key}.{pn}")}
                    if ps.get("description"):
                        p["d"] = ps["description"].strip()
                    if ps.get("x-descriptions"):
                        p["xd"] = ps["x-descriptions"]
                    if "default" in ps:
                        p["def"] = ps["default"]
                    if ps.get("$comment"):
                        p["c"] = ps["$comment"]
                    if ps.get("faker"):
                        p["fk"] = ps["faker"]
                    if pn in req:
                        p["req"] = 1
                    props.append(p)
                o["p"] = props
            objects[key] = o
    # Verweise auf fehlende Objekte melden
    for key, o in objects.items():
        for p in o.get("p", []):
            r = p["t"].get("ref")
            if r and r not in objects:
                problems.append(f"{key}.{p['n']}: verweist auf fehlendes Objekt {r}")
    return objects, raw, problems


def read_examples(root: Path) -> dict:
    out = {}
    ex = root / "docs" / "examples"
    if not ex.exists():
        return out
    for kind in KINDS:
        for f in sorted((ex / kind).glob("*.json")) if (ex / kind).exists() else []:
            try:
                out[f"{kind}/{f.stem}"] = json.dumps(json.loads(f.read_text(encoding="utf-8")),
                                                     ensure_ascii=False, indent=2)
            except Exception:  # noqa: BLE001
                pass
    return out


TR_LINE = re.compile(r"^\s+(\"[^\"]+\"|'[^']+'|[^\s#:'\"][^:#]*?)\s*:\s*(\"[^\"]*\"|'[^']*'|[^#]*?)\s*(?:#.*)?$")


def read_translation(root: Path) -> dict:
    f = root / "translation" / "v1" / "DE_to_EN.yaml"
    tr = {}
    if not f.exists():
        return tr
    for line in f.read_text(encoding="utf-8").splitlines():
        m = TR_LINE.match(line)
        if not m:
            continue
        k, v = (s.strip().strip("\"'") for s in m.groups())
        if k and v:
            tr[k] = v
    return tr


# ----------------------------------------------------------------------------- HTML

def build_html(data: dict, out: Path):
    tpl = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    logo = ("data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode()) if LOGO.exists() else ""
    html = tpl.replace("/*__DATA__*/null", payload, 1).replace("__LOGO__", logo)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(html, encoding="utf-8")
    os.replace(tmp, out)


def main():
    ap = argparse.ArgumentParser(description="BO4E-Schema-Viewer erzeugen")
    ap.add_argument("--quelle", choices=("github", "lokal"))
    ap.add_argument("--repo")
    ap.add_argument("--ref", help="Branch, Tag oder Commit (Standard master)")
    ap.add_argument("--lokal", help=f"Pfad der lokalen Kopie (Standard {DEFAULT_LOCAL})")
    ap.add_argument("--out", help=f"Ausgabedatei (Standard {DEFAULT_OUT.relative_to(HERE)})")
    args = ap.parse_args()
    settings = load_settings()

    root, src = resolve_source(args, settings)
    objects, raw, problems = read_schemas(root)
    examples = read_examples(root)
    tr = read_translation(root)
    src["built_at"] = now_iso()

    counts = {k: sum(1 for o in objects.values() if o["k"] == k) for k in KINDS}
    data = {"src": src, "objects": objects, "raw": raw, "examples": examples, "tr": tr, "problems": problems}
    out = Path(args.out) if args.out else DEFAULT_OUT
    build_html(data, out)

    log(f"Objekte: {counts['bo']} BO, {counts['com']} COM, {counts['enum']} ENUM, {counts['cdoc']} CDOC · "
        f"{len(examples)} Beispiele · {len(tr)} Übersetzungen")
    for p in problems:
        log(f"  Hinweis: {p}")
    log(f"Fertig: {out}  ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
