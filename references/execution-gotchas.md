# 运行踩坑与工具链经验（跑 skill 脚本前扫一眼）

> 这些是在真实 Windows 环境跑 skill 脚本时踩到的坑，记录成因与对策，避免下次再犯。均为实测可复现的经验，非理论推测。

## 一、脚本输出的中文乱码 / UnicodeDecodeError（最常见）

- **现象**：用 `python script.py` 在 Windows 下把输出经管道/子进程捕获时，中文变成乱码；父进程按 UTF-8 解码则抛 `UnicodeDecodeError`。
- **成因**：Windows 默认区域编码是 GBK/cp936；子进程 `stdout` 不是 tty 时按区域编码写出，被调用方以 UTF-8 解释就乱码/报错。
- **对策（其一即可，可靠）**：
  - 运行前 `$env:PYTHONIOENCODING="utf-8"`（PowerShell），或 `python -X utf8 script.py`；
  - 多数 skill 脚本已对 `sys.stdout/stderr` 做 `reconfigure(encoding="utf-8", errors="replace")`，这能让抓到的是 UTF-8，但**调用方**仍应以 UTF-8 解码。
- **核对**：捕获后 `"降 AI 味" in stdout` 是否为 `True`。

## 二、用 PDF 文本喂 dedup_scan / crosscheck 会因页眉误报

- **现象**：`dedup_scan.py` 报"段首 X 字开局 N 段"（如「航空」开局 28 段）、与题干 8 字片 100% 重合。
- **成因**：用 PyMuPDF 等把 PDF 抽成文本时，`\fancyhf` 逐页页眉/页脚（如"航空安全风险分析和飞行技术评估"）会被当成正文，每页出现一次。
- **对策**：**优先用 `.tex`/`.md` 源码分析**；若只能用 PDF 文本，加
  `dedup_scan.py 论文.txt 题干.txt --drop-repeat 5`（删出现 ≥5 次的重复行，即页眉），或 `--strip-header "页眉文字"` 精确删除。
- **性质**：这类报"抄题/模板化"是版式噪音，不是真实问题；须剔除后再下结论。

## 三、xelatex 不在 PATH：TeX Live 需手动加 bin

- **现象**：`xelatex` 命令找不到（`Get-Command xelatex` 为空）。
- **成因**：TeX Live 位于 `C:\texlive\<年份>\bin\windows\`，默认不在 PATH。
- **对策**（在 `paper/` 目录跑两遍解析交叉引用）：
  ```pwsh
  $env:PATH = "C:\texlive\2025\bin\windows;" + $env:PATH
  Set-Location <项目>\paper
  xelatex -interaction=nonstopmode -halt-on-error main.tex   # 第 1 遍
  xelatex -interaction=nonstopmode -halt-on-error main.tex   # 第 2 遍
  ```
- **中文排版本**：`ctexart` + `fontset=none`，并用
  `\setCJKmainfont[Path=C:/Windows/Fonts/, BoldFont=simhei.ttf]{simsun.ttc}`
  显式指向系统字体文件最稳（避免某些 TeX 发行版枚举不到 Windows 字体）。

## 四、Python 解释器发现：别只信 `Get-Command python`

- **现象**：`Get-Command python` 为空，或 `python` 指向错误版本。
- **成因**：Windows 常同时装多版本（3.11/3.13/3.14），`python` 未必在 PATH；且某版本目录可能只有目录没有 `python.exe`（半截安装）。
- **对策**：`py -0p` 列出所有版本；找不到就从 `C:\Users\<用户>\AppData\Local\Programs\Python\Python3xx\python.exe` 取；若某版目录下无 `python.exe` 就换下一版。

## 五、改已有文件前先 read 再 edit（文件策略）

部分文件工具要求先 `read` 目标文件才能 `edit`（fs-observation-policy）。对已存在文件做改动前，先 read 一次；否则 `edit` 报"需要先读文件"。

## 六、降 AI 味的高杠杆点（写稿就规避，别事后补）

- **最大收益**：打破**僵化排比**——如摘要"对于问题一……对于问题二……"五连排比，改"问题一：用……／问题二先把……／问题三就……"；模型评价"第一……第六……"机械枚举改流动叙述。
- **其它**：删"具有重要意义/至关重要"零信息句；把"采用……方法"换成"用最小二乘拟合得 b=−0.83"这类带数字的写法；敢写负结果（50% 漏报、偏 R²=0.0085）既是加分项也更像人写。
- **诚实边界**：AI 检测工具（Turnitin/ZeroGPT 等）对纯人写文本也常报高比例假阳性，不可当判据；2026 国赛对 AI 是"要求**披露**"而非"禁用"，隐瞒 + 不核验才是一票否决红线。要的是真实写作质量，不是"伪装成人类"。
