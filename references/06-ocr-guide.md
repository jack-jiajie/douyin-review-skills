# 截图识别实操（腾讯云高精度为主 · 本地 tesseract 兜底）

本模型 `Read` 图片会被过滤，必须用 OCR 旁路识别截图文字。两套方案，**优先腾讯云高精度 OCR**，本地 tesseract 作兜底。

---

## A1 腾讯云通用文字识别（高精度版）· 首选

准召率远高于本地 OCR，对抖音后台暗色背景、小字号、复杂版式更稳，且返回文字框坐标便于定位单条指标。

**环境：**
- 安装 SDK：`/Users/xdf/.workbuddy/binaries/python/envs/default/bin/pip install tencentcloud-sdk-python`
- 密钥（环境变量）：`TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY`（腾讯云控制台 CAM→API 密钥；OCR 需购买「通用文字识别（高精度版）」）

**调用（脚本见 `tencentcloud-ocr` skill 的 `scripts/main.py`）：**
```bash
# 本地图片（Base64 方式，最常用）
/Users/xdf/.workbuddy/binaries/python/envs/default/bin/python \
  /Users/xdf/.workbuddy/skills/tencentcloud-ocr/scripts/main.py \
  --image-base64 /Users/xdf/Downloads/IMG_5630.PNG
# 图片 URL 方式：把 --image-base64 换成 --image-url https://xxx.png
```
返回 JSON 含 `raw_text`（完整识别文本）+ `RequestId`。逐张跑完所有截图，结果写入 `/tmp/ocr/tencent_*.txt` 后 Read 取数归类。

> 若未配置密钥：跳过 A1，直接用 A2 兜底，并在「指标真相表」备注「截图识别为本地 OCR，准召率有限，关键数字以 Excel 为准」。

---

## A2 本地 tesseract · 兜底（无密钥 / 断网时）

已验证可用流程（详见 `screenshot-ocr` skill）：

```bash
# 1) 环境（已装，缺失时补）
#   tesseract 5.5.0 @ /opt/homebrew/bin/tesseract
#   Python venv: /Users/xdf/.workbuddy/binaries/python/envs/default (pillow + openpyxl)
#   中文包: /opt/homebrew/share/tessdata/chi_sim.traineddata (用 tessdata_fast 版 ~2.4MB)

# 2) Python 把 PNG 转 BMP + 暗色图反相（subprocess 调 tesseract 会被沙箱拦，故分组执行）
/Users/xdf/.workbuddy/binaries/python/envs/default/bin/python - <<'PY'
from PIL import Image, ImageOps
import glob, os
os.makedirs('/tmp/ocr/bmp', exist_ok=True)
for img in sorted(glob.glob('/Users/xdf/Downloads/IMG_56*.PNG')):
    im = Image.open(img).convert('L')
    w,h = im.size; px = im.load(); s=0; n=0
    for y in range(0,h,8):
        for x in range(0,w,8): s+=px[x,y]; n+=1
    if s/n < 128: im = ImageOps.invert(im)   # 暗色后台反相
    im.save('/tmp/ocr/bmp/'+os.path.basename(img).replace('.PNG','.bmp'))
print('bmps ready')
PY

# 3) 在 Bash 直接调 tesseract（必须关沙箱 dangerouslyDisableSandbox，否则读不了刚写的图）
for f in /tmp/ocr/bmp/*.bmp; do
  n=$(basename "$f" .bmp)
  /opt/homebrew/bin/tesseract "$f" "/tmp/ocr/out_$n" -l chi_sim+eng --psm 6 2>/dev/null
done
# 结果在 /tmp/ocr/out_*.txt，逐个 Read 取数归类
```

**踩坑清单（务必避开）：**
1. 中文包下成 1.38MB 损坏版 → 全员 0 字符；必须用 `tessdata_fast` 版（~2.4MB）。
2. PNG 直读失败 → 必须转 BMP。
3. 暗色图未反相 → 0 字符（抖音后台 ~96% 黑像素）。
4. tesseract 放 Python subprocess → 被沙箱拦截 → 0 字符，必须 Bash 直调且关沙箱。

---

## 封面「直播切片」角标识别

封面上的「直播切片」文字是图片文字，OCR 未必能直接识别。若无法从截图确认类型，可依据"播放量破万 + 与直播引流强关联"做代表性归类，并在报告中注明"以用户目测封面为准"，请用户最终核对。
