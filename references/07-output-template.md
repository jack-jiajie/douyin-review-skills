# 输出模板与交付话术

## 一、HTML 文件骨架

单文件 HTML，内联 CSS，图表用 Chart.js CDN：`https://cdn.jsdelivr.net/npm/chart.js`。

建议结构（顺序即报告板块顺序）：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>抖音周度数据复盘_YYYYMMDD-MMDD</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    /* 浅色主题、卡片式；变量见下 */
    :root{ --blue:#2b6cff; --green:#0a9d6b; --orange:#c9871a; --purple:#7a5cff; --bg:#f5f7fb; --card:#fff; --ink:#1d2330; --sub:#6b7280; --line:#e6e9f0; }
    body{ font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:var(--ink); margin:0; padding:24px; }
    .wrap{ max-width:960px; margin:0 auto; }
    section{ background:var(--card); border-radius:14px; padding:20px 22px; margin-bottom:18px; box-shadow:0 1px 3px rgba(20,30,60,.06); }
    h2{ font-size:19px; margin:0 0 12px; display:flex; align-items:center; gap:10px; }
    h2 .n{ width:26px; height:26px; border-radius:8px; background:var(--blue); color:#fff; font-size:14px; display:grid; place-items:center; }
    .kpi{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
    .kpi>div{ background:#fbfcfe; border:1px solid var(--line); border-radius:10px; padding:12px 14px; }
    .kpi .t{ font-size:12px; color:var(--sub); }
    .kpi .v{ font-size:22px; font-weight:700; margin:4px 0; }
    .chartbox{ margin-top:16px; }
    .note{ font-size:13px; color:var(--sub); margin-top:10px; line-height:1.6; }
    .three{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }
    .why{ background:#f8fafc; border-left:3px solid var(--blue); padding:10px 14px; border-radius:8px; margin-top:10px; font-size:14px; line-height:1.7; }
    .chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .chip{ font-size:12px; padding:4px 10px; border-radius:999px; }
    .chip.r{ background:#e8f6ee; color:#0a7a4a; }
    .chip.s{ background:#fff4e2; color:#a9701a; }
    .chip.b{ background:#fdecec; color:#c0392b; }
  </style>
</head>
<body>
  <div class="wrap">
    <!-- 板块0 指标真相表 -->
    <!-- 板块1 结论速览 -->
    <!-- 板块2 总览 + 趋势图 canvas#trend -->
    <!-- 板块3 关注来源 + canvas#src -->
    <!-- 板块4 单条视频三位一体 -->
    <!-- 板块5 引流直播间 -->
    <!-- 板块6 亮点 -->
    <!-- 板块7 待优化 -->
    <!-- 板块8 优化策略 -->
  </div>
  <script>
    // 趋势图见 references/03-chart-design.md 双 Y 轴示例
    new Chart(document.getElementById('trend'),{ /* ... */ });
  </script>
</body>
</html>
```

---

## 二、给用户的汇报话术骨架

> 报告已生成，预览里可直接看。先说结论：
> 1. 本周内容能力没问题但**供给节奏断档**——前半周爆款、后半周接不住，不是能力问题。
> 2. 涨粉引擎在**换轨**：推荐涨粉走弱，主页+搜索主动触达翻倍成为主引擎。
> 3. 时长回落的根因是**口播留人弱于切片**，已给出"口播切片化"修复动作。
> 数据归属我已先和您核对过（点赞 238 / 评论 13 等均未混淆），可放心引用。

---

## 三、交付动作

- 用 `present_files` 打开 HTML 预览，并附 2-3 条最重要信号（不是只说"报告已生成"）。
- 如封面「直播切片」角标未按截图确认，提示用户目测核对。
