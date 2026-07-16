#!/bin/bash
# douyin-review-skills 一键安装 / 更新脚本
# 用法：bash install.sh
set -e

SKILL_DIR="$HOME/.workbuddy/skills/douyin-review-skills"
REPO="https://github.com/jiajiehu182-del/douyin-review-skills.git"

if [ -d "$SKILL_DIR/.git" ]; then
  echo "→ 检测到已安装，执行更新 ..."
  git -C "$SKILL_DIR" pull --ff-only
else
  echo "→ 开始安装 douyin-review-skills ..."
  mkdir -p "$HOME/.workbuddy/skills"
  git clone "$REPO" "$SKILL_DIR"
fi

echo ""
echo "✅ 已安装 / 更新到：$SKILL_DIR"
echo "👉 重启或刷新 WorkBuddy 后，在对话中说「做抖音周报 / 数据复盘」即可触发，"
echo "   也可手动 @skill:douyin-review-skills"
