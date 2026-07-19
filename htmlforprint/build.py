#!/usr/bin/env python3
"""
date archive 建置腳本。

流程：
  1. 讀 news.md（唯一要編輯的檔案）
  2. 產生 index.html（版本 B：mesh 圖當背景浮水印）
  3. 產生 qr/*.png 和 qr/manifest.json

用法：
  改完 news.md 之後，跑一次：
      python3 build.py
  然後把整個資料夾 git push 到 GitHub Pages。

第一次使用前：把下面的 BASE_URL 改成你的 GitHub Pages 網址（結尾要有斜線）。
需要：pip install "qrcode[pil]"
"""

import re
import json
import sys
from pathlib import Path

# ========= 只有這一行要改 =========
BASE_URL = "https://github.com/planetmarsno34-maker/d.git/"   # repo 名越短，QR 越好掃
# =================================

HERE = Path(__file__).parent
NEWS = HERE / "news.md"
OUT_HTML = HERE / "index.html"
QR_DIR = HERE / "qr"


def parse_news(text):
    """把 news.md 拆成 entry 清單。"""
    entries = []
    # 依 "## id 日期" 切段
    blocks = re.split(r'^##\s+', text, flags=re.M)[1:]
    for b in blocks:
        lines = [l.rstrip() for l in b.splitlines()]
        header = lines[0].split()
        eid, date = header[0], header[1]
        # 剩下的非空行：標題、脈絡、來源連結
        body = [l for l in lines[1:] if l.strip()]
        # 來源是最後一個 markdown 連結
        source, url = "", ""
        title_lines, context_lines = [], []
        for l in body:
            m = re.match(r'\[(.+?)\]\((.+?)\)', l.strip())
            if m:
                source, url = m.group(1), m.group(2)
            elif not title_lines:
                title_lines.append(l.strip())
            else:
                context_lines.append(l.strip())
        entries.append({
            "id": eid,
            "date": date,
            "title": " ".join(title_lines),
            "context": " ".join(context_lines),
            "source": source,
            "url": url,
        })
    return entries


def check(entries):
    """基本檢查：id 不重複、日期格式、連結存在。"""
    ids, dates_ok = set(), True
    for e in entries:
        if e["id"] in ids:
            sys.exit(f"錯誤：id 重複 -> {e['id']}")
        ids.add(e["id"])
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', e["date"]):
            sys.exit(f"錯誤：{e['id']} 日期格式要 YYYY-MM-DD -> {e['date']}")
        if not e["title"]:
            sys.exit(f"錯誤：{e['id']} 沒有標題")
    print(f"檢查通過：{len(entries)} 則，id 無重複")


def build_qr(entries):
    try:
        import qrcode
    except ImportError:
        sys.exit('缺少 qrcode，請先跑： pip install "qrcode[pil]"')
    QR_DIR.mkdir(exist_ok=True)
    for old in QR_DIR.glob("*.png"):
        old.unlink()
    manifest = []
    for e in entries:
        url = f"{BASE_URL}#{e['id']}"
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4, border=0,
        )
        qr.add_data(url)
        qr.make(fit=True)
        if qr.version > 3:
            sys.exit(f"錯誤：{e['id']} 的 URL 太長 (v{qr.version})，請縮短 BASE_URL")
        img = qr.make_image(fill_color="black", back_color="white")
        if img.size[0] > 128:
            sys.exit(f"錯誤：{e['id']} QR {img.size[0]}px 超過 128px")
        img.save(QR_DIR / f"{e['id']}.png")
        manifest.append({"id": e["id"], "date": e["date"], "url": url,
                         "file": f"qr/{e['id']}.png", "px": img.size[0]})
    (QR_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"QR 產生完成：{len(manifest)} 張（都在 128px 內）")


HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex">
<title>date archive</title>
<style>
  :root {
    --paper: #f7f6f3;
    --ink: #141414;
    --meta: #8a8a86;
    --red: #8b0f1e;
    --mono: ui-monospace, "SF Mono", "Cascadia Mono", "Roboto Mono", Menlo, monospace;
    --body: -apple-system, "Helvetica Neue", Arial, sans-serif;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { background: var(--paper); }
  body {
    font-family: var(--body);
    color: var(--ink);
    max-width: 26rem;
    margin: 0 auto;
    padding: 3rem 1.5rem 6rem;
    line-height: 1.7;
    position: relative;
    -webkit-font-smoothing: antialiased;
  }
  body::before {
    content: "";
    position: fixed;
    inset: 0;
    background: url("form.png") center 34% / min(80vw, 26rem) auto no-repeat;
    opacity: 0.30;
    pointer-events: none;
    z-index: -1;
  }
  .back {
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.14em;
    color: var(--meta);
    text-decoration: none;
    display: inline-block;
    margin-bottom: 2.5rem;
  }
  .back:hover, .back:focus-visible { color: var(--red); outline: none; }
  .stamp {
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    color: var(--meta);
    text-transform: uppercase;
  }
  .date {
    font-family: var(--mono);
    font-size: clamp(2.2rem, 10vw, 3rem);
    font-weight: 400;
    letter-spacing: 0.04em;
    margin-top: 0.75rem;
    font-variant-numeric: tabular-nums;
  }
  .tear {
    height: 9px;
    margin: 2rem 0;
    background:
      linear-gradient(-45deg, transparent 6px, var(--ink) 0) 0 0 / 12px 9px repeat-x,
      linear-gradient(45deg, transparent 6px, var(--ink) 0) 6px 0 / 12px 9px repeat-x;
    opacity: 0.12;
  }
  h2.headline {
    font-size: 1.1rem;
    font-weight: 600;
    line-height: 1.55;
    margin-bottom: 1.1rem;
  }
  .context { font-size: 0.9rem; color: #3c3c3a; margin-bottom: 2rem; }
  .source {
    font-family: var(--mono);
    font-size: 0.75rem;
    letter-spacing: 0.04em;
  }
  .source a {
    color: var(--red);
    text-decoration: none;
    border-bottom: 1px solid currentColor;
    padding-bottom: 1px;
  }
  .source a:focus-visible { outline: 2px solid var(--red); outline-offset: 3px; }
  footer {
    margin-top: 4.5rem;
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.14em;
    color: var(--meta);
  }
  nav.index { margin-top: 0.5rem; }
  nav.index a {
    display: block;
    padding: 1.1rem 1.6rem 1.1rem 0;
    border-top: 1px solid rgba(20,20,20,0.14);
    color: var(--ink);
    text-decoration: none;
    position: relative;
    transition: background 0.15s ease;
  }
  nav.index a:last-child { border-bottom: 1px solid rgba(20,20,20,0.14); }
  nav.index a::after {
    content: "\2192";
    font-family: var(--mono);
    position: absolute;
    right: 0.1rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--meta);
    transition: color 0.15s ease, right 0.15s ease;
  }
  nav.index a:hover, nav.index a:focus-visible {
    background: rgba(247,246,243,0.6);
    outline: none;
  }
  nav.index a:hover::after, nav.index a:focus-visible::after {
    color: var(--red);
    right: 0;
  }
  nav.index .d {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--red);
    display: block;
    margin-bottom: 0.2rem;
    font-variant-numeric: tabular-nums;
  }
  nav.index .t { font-size: 0.88rem; line-height: 1.5; display: block; }
  @media (prefers-reduced-motion: reduce) {
    nav.index a, nav.index a::after { transition: none; }
  }
</style>
</head>
<body>
<div id="app"></div>
<script>
const ENTRIES = __DATA__;

function fmt(d) { return d.replaceAll("-", "."); }

function renderEntry(e) {
  const srcLine = e.url
    ? `<a href="${e.url}" target="_blank" rel="noopener">${e.source} \u2197</a>`
    : `<span>${e.source}</span>`;
  const ctx = e.context ? `<p class="context">${e.context}</p>` : "";
  return `
    <a class="back" href="#">\u2190 all dates</a>
    <p class="stamp">no. ${e.id}</p>
    <h1 class="date">${fmt(e.date)}</h1>
    <div class="tear" role="presentation"></div>
    <h2 class="headline">${e.title}</h2>
    ${ctx}
    <p class="source">${srcLine}</p>
    <footer>printed elsewhere. kept here.</footer>
  `;
}

function renderIndex() {
  const sorted = [...ENTRIES].sort((a, b) => b.date.localeCompare(a.date));
  const items = sorted.map(e =>
    `<a href="#${e.id}"><span class="d">${fmt(e.date)}</span><span class="t">${e.title}</span></a>`
  ).join("");
  return `
    <p class="stamp">index \u00b7 ${sorted.length} dates</p>
    <div class="tear" role="presentation"></div>
    <nav class="index">${items}</nav>
  `;
}

function route() {
  const id = location.hash.slice(1);
  const entry = ENTRIES.find(e => e.id === id);
  document.getElementById("app").innerHTML = entry ? renderEntry(entry) : renderIndex();
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", route);
route();
</script>
</body>
</html>
'''


def build_html(entries):
    data = json.dumps(entries, ensure_ascii=False, indent=2)
    OUT_HTML.write_text(HTML.replace("__DATA__", data))
    print(f"index.html 產生完成")


def main():
    if not NEWS.exists():
        sys.exit("找不到 news.md")
    entries = parse_news(NEWS.read_text())
    check(entries)
    build_html(entries)
    build_qr(entries)
    print("\n完成。git push 後就會更新網站。")


if __name__ == "__main__":
    main()
