#!/bin/bash
# douyin-review-skills 一键安装 / 更新脚本（跨平台 v2.0.0）
# 用法：
#   bash install.sh            # 安装到 WorkBuddy，并在当前目录放出 AGENTS.md / .cursorrules
#   bash install.sh --claude   # 额外把 AGENTS.md 放到 ~/.claude/AGENTS.md（全局）
#   bash install.sh --cursor   # 额外把 .cursorrules 放到当前目录（Cursor 项目级）
set -e

SKILL_DIR="$HOME/.workbuddy/skills/douyin-review-skills"
REPO="https://github.com/jack-jiajie/douyin-review-skills.git"
HERE="$(cd "$(dirname "$0")" && pwd)"

# 1) 安装 / 更新 WorkBuddy skill
if [ -d "$SKILL_DIR/.git" ]; then
  echo "→ 检测到已安装，执行更新 ..."
  git -C "$SKILL_DIR" pull --ff-only
else
  echo "→ 开始安装 douyin-review-skills（WorkBuddy）..."
  mkdir -p "$HOME/.workbuddy/skills"
  git clone "$REPO" "$SKILL_DIR"
fi

# 2) 在当前目录放出跨平台指令文件（供其它 agent 软件直接使用）
if [ -f "$HERE/AGENTS.md" ]; then
  cp "$HERE/AGENTS.md" "./AGENTS.md"
  echo "→ 已复制 AGENTS.md 到当前目录（Claude Code / Codex / Cline / Roo / 通用可用）"
fi
if [ -f "$HERE/.cursorrules" ]; then
  cp "$HERE/.cursorrules" "./.cursorrules"
  echo "→ 已复制 .cursorrules 到当前目录（Cursor 可用）"
fi

# 3) 可选：全局 Claude
if [ "$1" = "--claude" ] && [ -f "$HERE/AGENTS.md" ]; then
  mkdir -p "$HOME/.claude"
  cp "$HERE/AGENTS.md" "$HOME/.claude/AGENTS.md"
  echo "→ 已复制 AGENTS.md 到 ~/.claude/AGENTS.md（全局生效）"
fi

echo ""
echo "✅ 已安装 / 更新到：$SKILL_DIR"
echo "👉 重启或刷新 WorkBuddy 后，在对话中说「做抖音周报 / 数据复盘」即可触发，"
echo "   也可手动 @skill:douyin-review-skills"
echo ""
echo "📦 如需使用半自动数据导出脚本（douyin_export.py），另在终端执行一次："
echo "   pip install -r $SKILL_DIR/requirements.txt && playwright install chromium"
echo "   然后运行：python $SKILL_DIR/douyin_export.py"
