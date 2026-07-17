#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
douyin_export.py — 抖音创作者后台「半自动」数据导出脚本
=====================================================

用途：
    自动打开抖音创作者后台（creator.douyin.com），等你扫码登录后，
    把【周维度整体数据】和【近 7 天每条视频的完整明细数据】抓取并备份到本地。

为什么是"半自动"：
    抖音后台只能扫码 / 手机验证码登录，这一步必须你本人操作。
    脚本会弹出浏览器并停在该步骤，你扫码后脚本自动继续。

导出内容：
    output/<日期>/
        overview/
            overview.png        # 数据总览整页截图（含周维度指标）
            overview.html       # 整页 HTML 源码（备用解析）
        videos/
            <序号>_<标题>/
                detail.png      # 单条视频数据详情页截图（含全部指标）
                detail.html     # 详情页 HTML 源码
        tables/
            *.xlsx              # 若页面含 <table> 则尽力解析成 Excel
        manifest.json           # 本次导出清单（日期 / 视频数 / 文件列表）

依赖安装（首次运行前，在你的终端执行）：
    pip install playwright
    playwright install chromium
    pip install pandas openpyxl lxml

运行：
    python douyin_export.py
    可选参数：
        --headless     后台无头运行（仅在你已登录过、cookie 复用时效内可用）
        --out DIR      指定输出根目录（默认 ./douyin_export_output）
        --no-tables    跳过表格解析（纯截图 + HTML 备份）

说明 / 已知限制（务必读完）：
    1. 抖音后台是强反爬 SPA，页面结构可能随版本变化。脚本用「可见中文文案」
       做定位，比 CSS 选择器稳，但仍可能在抖音改版后失效，届时需要微调。
    2. 时间范围选择（近 7 日）脚本会先尝试自动点击「近7日 / 最近7天」按钮；
       若页面文案不一致找不到，会暂停让你手动选，回车继续。
    3. 导出的是截图 + HTML 源码，能直接喂给数据分析流程（Read 工具看图即取数）。
       若页面用标准 <table> 渲染，会额外解析成 Excel 方便后续处理。
"""

import argparse
import datetime as dt
import json
import os
import sys
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    sys.exit("❌ 未安装 playwright，请先执行：pip install playwright && playwright install chromium")

import pandas as pd

# ---------------------------------------------------------------------------
# 配置区（可按需修改）
# ---------------------------------------------------------------------------
CREATOR_HOME = "https://creator.douyin.com/creator-micro/home"
PROFILE_DIR = os.path.expanduser("~/.douyin_export_profile")  # 登录态持久化目录
DATE_RANGE_LABELS = ["近7日", "最近7天", "近 7 日", "7天", "近七天"]  # 时间范围候选文案
LOGIN_WAIT_SECONDS = 180  # 扫码登录最长等待时间
PAGE_WAIT = 2.5           # 页面切换后的缓冲等待（秒）

# 视频列表页 / 详情页 的候选入口文案
VIDEO_LIST_LABELS = ["作品数据", "作品分析", "内容数据", "视频数据"]
DETAIL_LABELS = ["查看数据分析", "数据分析", "详情", "数据详情"]


def log(msg):
    print(f"[douyin_export] {msg}", flush=True)


def safe_name(s: str, max_len=40) -> str:
    """把视频标题转成安全的文件名。"""
    bad = '/\\:*?"<>|'
    for c in bad:
        s = s.replace(c, "_")
    return s[:max_len].strip() or "untitled"


def wait_for_login(page):
    """检测是否已登录；若未登录则等待用户扫码。"""
    log("检测登录态 ...")
    # 已登录特征：URL 进入 home 且出现「数据总览」之类入口；未登录则停留登录页
    try:
        page.wait_for_url("**/creator-micro/**", timeout=8000)
    except Exception:
        pass

    # 尝试判断是否有二维码（未登录标志）
    qr = page.query_selector('img[src*="qrcode"], .qrcode, canvas')
    if qr is not None:
        log("=" * 60)
        log("请使用「抖音 App」扫描浏览器中的二维码完成登录 ...")
        log(f"等待登录中（最长 {LOGIN_WAIT_SECONDS} 秒）...")
        log("=" * 60)
        # 轮询：出现退出头像 / 数据入口即视为登录成功
        deadline = time.time() + LOGIN_WAIT_SECONDS
        while time.time() < deadline:
            if page.query_selector('text=数据总览') or page.query_selector('text=作品数据'):
                log("✅ 检测到已登录（出现数据入口）。")
                return True
            time.sleep(2)
        log("❌ 登录等待超时，请重新运行脚本并扫码。")
        return False
    log("✅ 似乎已处于登录态（未发现二维码）。")
    return True


def try_set_date_range(page):
    """尝试自动把时间范围切成『近 7 日』；失败则暂停人工选择。"""
    log("尝试设置时间范围为『近 7 日』...")
    for label in DATE_RANGE_LABELS:
        try:
            btn = page.locator(f"text={label}").first
            if btn.count() and btn.is_visible(timeout=1500):
                btn.click()
                page.wait_for_timeout(PAGE_WAIT * 1000)
                log(f"✅ 已点击时间范围：{label}")
                return True
        except Exception:
            continue
    # 没找到对应文案 → 人工选择
    log("⚠️ 未自动匹配到『近7日』按钮（抖音文案可能变了）。")
    log("请在浏览器里手动把时间范围选成『近 7 日 / 最近 7 天』，")
    input("  选好后回到这里按回车继续 >>> ")
    return True


def capture_overview(page, out_dir):
    """抓取数据总览页（周维度整体指标）。"""
    log("进入数据总览页 ...")
    try:
        page.locator("text=数据总览").first.click(timeout=8000)
    except Exception:
        log("⚠️ 未找到『数据总览』入口，尝试直接等待页面加载。")
    page.wait_for_timeout(PAGE_WAIT * 1000)
    try_set_date_range(page)
    page.wait_for_timeout(PAGE_WAIT * 1000)

    ov_dir = os.path.join(out_dir, "overview")
    os.makedirs(ov_dir, exist_ok=True)
    png = os.path.join(ov_dir, "overview.png")
    html = os.path.join(ov_dir, "overview.html")
    page.screenshot(path=png, full_page=True)
    html_path = page.content()
    with open(html, "w", encoding="utf-8") as f:
        f.write(html_path)
    log(f"📸 总览截图：{png}")
    return png, html


def goto_video_list(page):
    """进入作品 / 视频列表页。"""
    log("进入视频列表页 ...")
    for label in VIDEO_LIST_LABELS:
        try:
            el = page.locator(f"text={label}").first
            if el.count() and el.is_visible(timeout=1500):
                el.click()
                page.wait_for_timeout(PAGE_WAIT * 1000)
                log(f"✅ 已进入：{label}")
                return True
        except Exception:
            continue
    log("⚠️ 未自动匹配到视频列表入口，请手动进入后按回车。")
    input("   进入视频列表页后按回车继续 >>> ")
    return True


def collect_video_entries(page):
    """从列表页收集视频条目（标题 + 进入详情的入口元素）。"""
    log("扫描视频列表 ...")
    entries = []
    # 视频卡片常见形态：含封面图 + 标题文字的容器
    cards = page.locator("a[href*='video'], div[class*='card'], li[class*='item']").all()
    seen = set()
    for card in cards:
        try:
            title_el = card.locator("text=/./").first
            title = title_el.inner_text(timeout=800).strip()
        except Exception:
            title = ""
        if not title or title in seen:
            continue
        # 只保留近 7 天（列表通常按时间倒序，取前若干；这里保守收集全部，详情页再校验）
        seen.add(title)
        entries.append({"title": title, "element": card})
    log(f"📋 扫描到 {len(entries)} 个视频条目。")
    return entries


def capture_video_detail(page, entry, out_dir, index):
    """进入单条视频详情页，抓取全部指标。"""
    title = entry["title"]
    folder = os.path.join(out_dir, "videos", f"{index:02d}_{safe_name(title)}")
    os.makedirs(folder, exist_ok=True)
    log(f"→ 抓取视频 [{index}] {title}")

    try:
        entry["element"].click(timeout=5000)
    except Exception:
        log("  ⚠️ 点击卡片失败，尝试查找『数据分析』入口。")
        try:
            entry["element"].locator(f"text={'/'.join(DETAIL_LABELS)}").first.click(timeout=5000)
        except Exception:
            log("  ⚠️ 无法进入详情，跳过该视频。")
            return None

    page.wait_for_timeout(PAGE_WAIT * 1000)
    # 若进入了列表内弹层而非新页，尝试点『数据分析』
    try:
        dl = page.locator(f"text=/({'|'.join(DETAIL_LABELS)})/").first
        if dl.count() and dl.is_visible(timeout=1500):
            dl.click()
            page.wait_for_timeout(PAGE_WAIT * 1000)
    except Exception:
        pass

    png = os.path.join(folder, "detail.png")
    html = os.path.join(folder, "detail.html")
    page.screenshot(path=png, full_page=True)
    with open(html, "w", encoding="utf-8") as f:
        f.write(page.content())
    log(f"  📸 详情截图：{png}")
    return png, html


def extract_tables(html_path, xlsx_path):
    """尽力把页面中的 <table> 解析为 Excel。返回是否成功。"""
    try:
        tables = pd.read_html(html_path)
        if not tables:
            return False
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            for i, t in enumerate(tables):
                t.to_excel(writer, sheet_name=f"table_{i}", index=False)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description="抖音创作者后台半自动数据导出")
    ap.add_argument("--headless", action="store_true", help="无头运行（需已登录 cookie 有效）")
    ap.add_argument("--out", default="./douyin_export_output", help="输出根目录")
    ap.add_argument("--no-tables", action="store_true", help="跳过表格解析")
    args = ap.parse_args()

    today = dt.date.today().isoformat()
    out_dir = os.path.join(os.path.abspath(args.out), today)
    os.makedirs(out_dir, exist_ok=True)
    tables_dir = os.path.join(out_dir, "tables")
    os.makedirs(tables_dir, exist_ok=True)

    manifest = {"date": today, "overview": None, "videos": [], "tables": []}

    with sync_playwright() as p:
        log("启动浏览器 ...")
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=args.headless, args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(CREATOR_HOME, wait_until="domcontentloaded")
        page.wait_for_timeout(PAGE_WAIT * 1000)

        if not wait_for_login(page):
            context.close()
            sys.exit(1)

        # 1) 周维度整体数据
        ov_png, ov_html = capture_overview(page, out_dir)
        manifest["overview"] = {"png": ov_png, "html": ov_html}

        # 2) 近 7 天每条视频明细
        goto_video_list(page)
        entries = collect_video_entries(page)
        for i, entry in enumerate(entries, start=1):
            res = capture_video_detail(page, entry, out_dir, i)
            if res:
                manifest["videos"].append({"index": i, "title": entry["title"],
                                           "png": res[0], "html": res[1]})

        # 3) 表格解析（尽力）
        if not args.no_tables:
            log("解析页面表格为 Excel ...")
            if manifest["overview"]:
                x = os.path.join(tables_dir, "overview.xlsx")
                if extract_tables(manifest["overview"]["html"], x):
                    manifest["tables"].append(x)
            for v in manifest["videos"]:
                x = os.path.join(tables_dir, f"{v['index']:02d}_{safe_name(v['title'])}.xlsx")
                if extract_tables(v["html"], x):
                    manifest["tables"].append(x)

        context.close()

    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    log("=" * 60)
    log(f"✅ 导出完成！输出目录：{out_dir}")
    log(f"   周维度总览：{len([1]) and '1' } 份")
    log(f"   视频明细：{len(manifest['videos'])} 条")
    log(f"   解析表格：{len(manifest['tables'])} 个")
    log(f"   清单文件：{manifest_path}")
    log("=" * 60)
    log("下一步：把 output/<日期>/ 里的截图直接发给我，我会按 douyin-review-skills 标准出报告。")


if __name__ == "__main__":
    main()
