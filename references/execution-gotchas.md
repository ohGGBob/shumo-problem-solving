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

## 七、Excel 交付物「行列位」错误（最隐蔽：数值全对、结构全错，自检抓不到）

- **现象**：题目给的 `resultN.xlsx` 模板填完后，**第 1 行时间表头与第 1 列对象标签被数据覆盖、数据整体错位一格、末行/末列留空**。
  按标签读数会把对象整体错位一个（例如"第 51 节"读成"第 50 节"）。**数值全对但交付物不合格**。
- **成因**：误以为模板第 1 行就是数据行。**实际约定**：第 1 行 = 时间/维度表头，第 1 列 = 对象标签，
  **数据从 (行2, 列2) 开始**；且"每对象占几行"要按模板标签列数出来（如位置表是 x/y 两行一组）。
- **对策（三步，缺一不可）**：
  1. **写数据前先看模板**：`python scripts/xlsx_deliverable.py probe 附件/resultN.xlsx`
     —— 它会打印"表头行 / 标签列 / 数据行列区间 / 填值约定"；
  2. 按约定写（对象 i → 行 = 数据首行 + i×K；时间 k → 列 = 数据首列 + k）；
  3. 填完体检：`python scripts/xlsx_deliverable.py check out/resultN.xlsx --sheet 位置 --auto`
     —— 抓"表头被覆盖 / 标签被数值覆盖 / 末行末列空 / 数据区有空洞 / 右侧下方溢出"。
- **为什么自检常抓不到**：自检代码往往复用了**同一套错误约定**去回读，于是"回读一致"但整体错位。
  必须由**独立分支**（不同实现/不同脚本）复核格式，或用上面的 `check` 工具（它按模板结构判定，不依赖你的写入约定）。
- **实测代价**：三个交付文件同时中招，涉及三处写入代码；靠独立复核分支才发现并修复。

## 八、沙箱/环境限制清单（本机实测，开工前先知道）

| 限制 | 现象 | 对策 |
|---|---|---|
| **multiprocessing 不可用** | `Pool` 抛 `PermissionError(13, '拒绝访问')`（禁止命名管道） | 阶段内不要用 Pool；并行改用"多个子代理"或后台作业 |
| **`scipy.optimize.shgo` 崩** | numpy 2.x 下 `float(1-element array)` → `TypeError` | 改"稠密网格扫 + 局部 `minimize_scalar` 精化" |
| **同路径并发写** | `Out-File -FilePath X` 重定向 + 脚本自身也写 `X` → `PermissionError` | 重定向路径与脚本内部日志路径**分开** |
| **孤儿进程** | 子代理已结束，`python` 仍在跑（CPU 累计上千秒） | `Get-Process python \| Select Id,CPU` 查，`Stop-Process` 清理 |
| CIM/WMI 受限 | `Get-CimInstance Win32_Process` 报"无法从客户端访问" | 用 `Get-Process` + 启动时间/CPU 间接判断进程身份 |

> 子代理编排（并行分支、独立复核、提示词模板、失败模式）另见
> `references/subagent-orchestration.md`。

## 九、「判据选择」比「数值精度」更致命（数学层面的坑）

- **现象**：同一问用三种合理方法算出 0.4443 / 0.4596 / 0.527，差 19%。逐段检查后发现**都不是算错**，而是**在算不同的量**。
- **规律**：
  - **端点快照判据**（只看终点是否满足）通常是**必要不充分**，会系统性偏乐观；
  - **跳变判据**（如"首次碰撞半径"在最近对象切换处跳变）**对它插值/二分必偏**；
  - **光滑判据**（如 $\min_r C(p,r)-\text{阈值}$）才良态，残差可达 1e-12。
- **对策**：先问"这个判据与题面要求是否等价"，再谈精度；能用连续量表达的判据就不要用不连续量。
  论文里把"为什么选这个判据"写出来（并给出被弃判据会偏多少），本身就是一条硬核的模型检验。

