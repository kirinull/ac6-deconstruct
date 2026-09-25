# M0 启动包：UE5 零基础 → 首个可玩

> **给谁**：一名**从未打开过 UE5** 的大四学生。会 Python、会通用 C++（没用过 UE 框架）、会用 Blender/Maya 建简单模型；不会 UV、不会绑定、不碰过材质编辑器 / HLSL / Niagara。
> **硬件**：台式机强配置，能稳定 60 fps。**时间**：>35 h/周（≈ 5 h/天 × 7 天）。
> **本文档的作用**：把 `docs/02_实施/UE5复刻_实施文档.md` 的 **§7 M0**（项目骨架 + 数据层 + 调参面板）翻译成**日级可执行步骤**。
> **冲突时以谁为准**：以 `docs/02_实施/UE5复刻_实施文档.md` 为准。`docs/04_元分析/` 正在并行更新，本文档不依赖它的具体路线安排。
> **证据等级**：沿用项目约定 —— **A** 官方文档/规格书原文 · **B** paramdex 字段定义 + 本机实测复现 · **C** 合理推断未本地验证 · **D** 不确定/待验证。本文档中我引用的每条数值都带等级与出处章节。
> **诚实声明**：本文档写于无法联网核查 Epic 官网的状态。**所有涉及"菜单具体位置"的地方我都用"搜索框 + 判据"的写法**；凡是我不能确定的界面细节，都标了 ⚠️不确定 并给出自验方法。**请不要把本文档当界面手册用**，把它当"路线 + 判据 + 排查表"用。

---

## 0. 开始前 30 分钟：自检与三个决定

### 0.1 先跑这条命令（Windows PowerShell）

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}}
winver
```

**判据（自己核对，不要问我"我这配置行不行"）**：

| 项 | M0 需要 | 不达标怎么办 |
|---|---|---|
| GPU | 支持 **DX12 / Shader Model 6** 的独显。粗判：GTX 10 系 / RX 5000 系及以上 ⚠️不确定（具体型号以厂商规格页的 "Feature Level 12_1/12_2" 为准） | 引擎启动会报 RHI 相关错误 → 先试退回 DX11（见 §1.7 坑 1） |
| 显存 | ≥ 8 GB 更舒服 ⚠️不确定（Epic 官方推荐值随版本变化，去 `dev.epicgames.com/documentation` 搜 "Hardware and Software Specifications" 核对） | 首次编译 shader 会很慢，但不影响 M0 |
| CPU 核心 | 越多越好，因为**首次 shader 编译**是主要瓶颈 | 首次编译预留 40 分钟 |
| 空闲磁盘 | **≥ 250 GB（NVMe SSD）** | 至少 120 GB 并把 DDC 挪到大盘（见 §1.4） |
| 路径 | 项目路径**纯 ASCII、无空格、无中文** | ✅ 已建好：`<UE_PROJECTS>\`（见 §1.4）|

### 0.2 三个决定（第 0 天就定死，中途改代价很大）

| 决定 | 我的建议 | 理由 |
|---|---|---|
| **引擎版本** | 装**一个**当前 Launcher 里最新的**非 Preview 稳定版**；若 5.6 与 5.7 同时可选，**选 5.6** | 见 §1.1 |
| **M0 走蓝图还是 C++** | **M0 全程蓝图，一行 C++ 都不写** | 见 §3.7。C++ 可以第 2 周再开，M0 开 C++ 只会把"环境问题"和"数据问题"混在一起 |
| **解包数据的处置** | **`data/` 目录永不进公开仓库**，只提交 `tools/` 与 `docs/` | 见 §3.4。这是本项目唯一的法律红线（原文档 §0 原则 1、§8 风险） |

---

# 第 1 部分：环境搭建（第 1~2 天）

> ## ⚡ 2026-09 复测：**环境已全部就位——本部分只剩「跑通模板」一件事，其余请跳过**
>
> | § | 内容 | 状态 |
> |---|---|---|
> | §1.1~§1.3 | 选版本 / 装 Launcher / 勾选项 | ✅ **已完成** — UE **5.8.2** 装在 `<UE_ENGINE>`（31 GB），`UnrealEditor.exe` 就位 |
> | §1.5 | Visual Studio | ✅ **已完成** — VS **Community 2022 17.14** 装在 `<VS2022>`，MSVC 14.44.35207，含 Unreal 集成组件 |
> | §1.4 | 路径与缓存规范 | ✅ **已完成** — 引擎 `<UE_ENGINE>` / 工程根 `<UE_PROJECTS>` / DDC `<UE_DDC>`（环境变量已设并复核） |
> | §1.6 | 跑通一个模板 | ⬜ **没做过 —— 这是你的第 1 件事** |
> | §1.7 / §1.8 | 常见坑 / 第 1~2 天验收 | ⬜ 照做（验收清单已按「环境已完成」重排，见 §1.8） |
>
> **所以：本部分下面 §1.1~§1.3、§1.5 的内容请当"重装/换版本时的参考手册"读，不要照做**（照做 = 白等 1 小时下载）。
> **你要做的只有一件事**：**直接从 §1.6 开始跑模板**（环境、路径、DDC 全部就位）。
> 已装环境的完整核验记录（含端到端编译证据）见 **附三：本机环境实测结果**。

## 1.1 装哪个版本：明确建议

> **对你已不适用** —— 你装的是 **5.8.2**（Release 正式版，非 Preview）。下表保留，用于**将来需要换版本**（例如跟着某套只支持 5.6 的教程）时做判断。

| 选项 | 建议 | 理由 |
|---|---|---|
| **最新的非 Preview 稳定版** | ✅ **主推** | 驱动/新硬件支持最好；你不需要新特性，但你需要"不出错" |
| 5.6 与 5.7 同时可选时 → **选 5.6** | ✅ | 已发布 ≥3 个月 = bug 已被社区踩完；教程、插件、论坛答案覆盖最广。**你的瓶颈是"查不到答案"，不是"功能不够"** |
| 带 `Preview` / `Experimental` 字样的版本 | ❌ | 插件不兼容、崩溃无人答、教程对不上 |
| UE 4.27 | ❌ | Enhanced Input / UMG / Niagara 的差异会让你在"跟着 UE5 教程做却找不到按钮"里烧掉 20 小时 |
| 装两个版本对比 | ❌ | 每个版本 45~60 GB，收益为零 |
| **你在跟一套视频教程** | ✅ **教程用哪个版本就装哪个** | 版本一致性 > "最新"。这是唯一能推翻上面建议的情况 |

⚠️ **不确定项**：我无法联网确认此刻 Epic 提供的确切版本号。用**三个判据**自行确认：① 列表里不带 `Preview`/`Experimental`；② 该版本能在 Epic 官方 Release Notes 页找到正式发布说明；③ 它已经发布 ≥ 3 个月（问一下社区/看发布日期）。

## 1.2 安装步骤（点哪里，看到什么算对）

| 步 | 动作 | 看到什么算对 |
|---:|---|---|
| 1 | 装 **Epic Games Launcher**（`store.epicgames.com` → 右上角下载） | 桌面出现 Launcher 图标，登录 Epic 账号（没有就注册，免费） |
| 2 | Launcher 左侧点 **Unreal Engine** → 顶部切到 **Library（库）** | 页面显示 "Unreal Engine" 标题 + 一个 `+` 按钮 |
| 3 | 点 **`+`** → 下拉里选版本号 | 出现一张带 **Install（安装）** 按钮的卡片 |
| 4 | 点 **Install** → 在弹窗里点 **Browse** 选安装路径 | 路径框显示你选的目录（例：`D:\Epic\UE_5.x`） |
| 5 | 在同一个弹窗里点开 **Options（选项）** 折叠区 | 看到一串复选框（见 §1.3） |
| 6 | 按 §1.3 勾选 → 点 **Install** | 开始下载（进度条 + 剩余时间）。**这一步会跑很久（几十分钟到几小时，取决于网速）** |
| 7 | 下载完 → 卡片上的按钮变成 **Launch（启动）** | 点 Launch 后出现 **Unreal Project Browser（项目浏览器）** |

> 安装期间**不要**做别的大文件 IO；也顺手把杀毒软件的实时防护排除目录加好（§1.7 坑 5）。

## 1.3 安装选项怎么勾

| 选项（名称随版本略有差异） | 勾？ | 理由 / 占用 |
|---|---|---|
| **Engine Source（引擎源码）** | ❌ | +20~30 GB。你不改引擎源码。真想看源码，GitHub 上免费看 |
| **Editor symbols for debugging（调试符号）** | ❌ | **+30~50 GB**。M0 用不到。**M1 以后如果遇到 C++ 崩溃栈看不懂，再回来补装**（Launcher 里右键该版本 → Options 可随时改） |
| **Starter Content（启动内容）** | — | ❌ **UE 5.6 起已彻底移除** —— 5.8 的创建对话框里**根本没有这个勾选框**。源码实证：`TemplateProjectDefs.h:108` → `StarterContent UE_DEPRECATED(5.6, "Ability to add Starter Content has been removed")`；`GameProjectUtils.h:194` → `IsEngineStarterContentAvailable() { return false; }`。**找不到它是正常的**；占位资产改用引擎自带内容（如 `Engine/BasicShapes/`）或自制 |
| **Templates and Feature Packs（模板与功能包）** | ✅ | 你要用 Third Person 模板验证安装成功 |
| Android / iOS / Linux / TVOS 等平台目标 | ❌ | 你是 Windows 单机，勾了纯占空间 |
| **磁盘占用总账** ⚠️不确定（以 Launcher 显示的 Download/Install size 为准） | — | 引擎 + 模板 **≈ 45~60 GB**；调试符号再 +30~50 GB；**DDC 缓存**初始几 GB、长期可涨到 20~50 GB；项目 + Intermediate 5~30 GB → **预留 250 GB 最省心** |

## 1.4 路径与缓存规范

> **★ 这一项已经全部落地（2026-09 复测）。** 用户拍板：**UE 相关的一切都放 J 盘**。

### 你的最终路径方案（照这个建，不要再纠结）

```
<UE_ENGINE>\          ← 引擎（已装，29.9 GB）
<VS2022>\          ← IDE（已装，5.29 GB）
<UE_PROJECTS>\      ← ★ 工程根（已建）
  └─ AC6Proto\      ← ★ M0 项目建在这里
<UE_DDC>\          ← ★ 派生数据缓存（已建 + 环境变量已设）
```

| 项 | 规定 | 你的实测现状 |
|---|---|---|
| 引擎路径 | 纯 ASCII、短、非 C 盘 | ✅ **`<UE_ENGINE>`** — 已满足（无中文、无空格） |
| 工程路径 | 纯 ASCII、无空格、无中文、总长留余量 | ✅ **`<UE_PROJECTS>\AC6Proto`**（≈26 字符，余量充足） |
| 绝对不要 | `C:\Users\你\OneDrive\桌面\我的项目\...` | ① 中文/空格 → Python、UBT、命令行工具集体出错；② OneDrive 会锁文件、拖慢编译、甚至改坏 `.uasset` |
| **DDC 缓存** | 用户环境变量 **`UE-LocalDataCachePath`** | ✅ **已设** = `<UE_DDC>`（写入 `HKCU\Environment`，已从注册表独立复核） |
| 杀毒排除 | 排除：引擎目录、工程目录、DDC 目录 | ⬜ **只剩这一项**，建议做，实测提速 2~5 倍（首次 shader 编译尤其明显） |

**DDC 已替你设好**，记录的原始命令如下（将来换盘时照做，**改完要重启所有 Epic / UE 进程**才生效）：

```powershell
New-Item -ItemType Directory -Force '<UE_DDC>' | Out-Null
[Environment]::SetEnvironmentVariable('UE-LocalDataCachePath', '<UE_DDC>', 'User')
[Environment]::GetEnvironmentVariable('UE-LocalDataCachePath', 'User')   # 应回显 <UE_DDC>
```

> **怎么确认它真的生效**：跑完第一次 shader 编译后，去 `<UE_DDC>` 看有没有长出 `UnrealEngine\Common\DerivedDataCache` 之类的目录；同时确认 `<HOME>\AppData\Local\UnrealEngine\Common\DerivedDataCache` **没有被创建**。
> **Editor Preferences 里的入口**（编辑器内搜索 `Derived Data`）只在单次会话内可靠；**环境变量是唯一跨项目、跨版本都稳的方式**。

### 为什么 J 盘够用（以及什么时候要警惕）

| 项 | 约占用 |
|---|---|
| 引擎 + VS（**已占用**） | 35 GB |
| M0 原型工程（Intermediate + Saved + Binaries） | 3~8 GB |
| DDC（初始 → 长期） | 2~5 GB → 20~50 GB |
| 打包产物 | 1~3 GB |
| **M0 阶段合计新增** | **≈ 10~20 GB** |
| 到 M2（作品集完整项目 + 素材） | 累计 ≈ 80~150 GB |

**J 盘可用 332 GB → M0 阶段绰绰有余，整个作品集周期也够。** 但注意 J 盘还装着 SteamLibrary（79 GB）、ASMR（345 GB）、ww（116 GB）等其他数据——**如果那些目录继续增长，J 盘会先被它们吃紧**。养成习惯：每完成一个里程碑看一眼 `J:` 剩余空间（资源管理器底部就显示）。

## 1.5 Visual Studio：什么时候装、勾哪些

| 问题 | 答案 |
|---|---|
| **现状** | ✅ **已装好**：`<VS2022>` = VS Community 2022 **17.14.37628.2**，MSVC **14.44.35207**，含 `Component.Unreal.Ide` + `Component.Unreal.Debugger`。**不用再装**。下面表格留作重装参考 |
| M0 需要吗 | **不需要**（M0 全蓝图）。但**已经装完了** —— M1 想写 C++ 时不会卡住 |
| 装哪个 | **Visual Studio 2022 Community（免费）最新 17.x** ← 你装的就是 17.14 |
| ⚠️ **实测补充** | 你这台机器**同时**有 VS2026 BuildTools（`C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools`，MSVC 14.50）。**UE5.8 默认选它**；想强制用 VS2022 编译要加 `-Compiler=VisualStudio2022`。**两者共存无冲突**，详见附三 |
| 工作负载（Workloads） | ✅「**使用 C++ 的游戏开发**」<br>✅「**使用 C++ 的桌面开发**」<br>✅「**.NET 桌面开发**」（UE 的构建工具 UBT/UAT 是 C# 写的，很多人漏掉这项然后报奇怪的错） |
| 单个组件（Individual components） | ✅ `MSVC v143 - VS 2022 C++ x64/x64 生成工具`<br>✅ `Windows 11 SDK`（10.0.22621 或更高）<br>✅ `C++ 分析工具`<br>（可选）`适用于 Windows 的 C++ CMake 工具` |
| ❌ 不要装 | 任何 "UWP / 移动开发 / Unity 工作负载" —— 与 UE 无关，纯占空间 |
| ⚠️ 不确定项 | Epic 对每个引擎版本有**最低 VS 版本**要求。核对方法：去 `dev.epicgames.com/documentation` 搜 **"Setting Up Visual Studio Development Environment for Unreal Engine"**，看它列的最低版本号 |
| 验证装对了 | 新建一个 C++ 空项目（VS 里选「空项目」）→ 能 F5 编译运行 → 说明 MSVC 与 SDK 正常。**这一步 5 分钟，能省掉 M1 的一整天** |

## 1.6 跑通一个模板（点哪里 → 看到什么）

> **不要**"先看两天教程再动手"。**先看到东西动起来**，再回头补知识。
>
> ⚠️ **本节已按你机器上的 UE 5.8.2 逐项核对**（读的是引擎源码，不是猜的）。旧版写的是 Launcher 老流程，5.8 已换成新的项目浏览器。

### 你现在停在哪

那个窗口是 **Unreal Project Browser（项目浏览器）的「首页」**——展示教程卡片，**不是**创建项目的地方。

| 左侧栏项 | 作用 |
|---|---|
| **新建项目** | ★ **你要点这个** |
| 我的项目 | 已建好的本地项目列表 |
| 首页 / 新闻 / 入门 / 示例项目 | 教程与官方示例 —— **先别看**，会掉进"看教程黑洞" |
| 论坛 / 文档 / 教程 / 开发路线图 / 版本说明文档 | 外部链接，用不上 |

### 第 1~8 步：填完对话框

点 **新建项目** → 左侧出现分类列表 → 选 **游戏**。

| 步 | 动作 | 填什么 / 看到什么算对 |
|---:|---|---|
| 1 | 左侧分类点 **游戏** | 右侧出现模板卡片网格 |
| 2 | 点 **第三人称模板** | 卡片高亮，出现底部选项面板 |
| 3 | 类型分段控件选 **`C++`**（不是 `BLUEPRINT`） | 见下方「为什么改成 C++」 |
| 4 | **目标平台** → **桌面** | 选项只有 `桌面` / `移动`（源码枚举 `EHardwareClass`） |
| 5 | **质量预设** → **最高质量** | 选项只有 `最高质量` / `可扩展`（源码枚举 `EGraphicsPreset`）。你 RTX 4080S，吃得下 Lumen/Nanite 全效果 |
| 6 | **项目位置** → 点选择按钮 → 选 **`<UE_PROJECTS>`** | 必须是这个（纯 ASCII、非 C 盘、空间足） |
| 7 | **项目名称** → 填 **`AC6Proto`** | 全英文、无空格 |
| 8 | 点 **创建项目** | 进度条 →（C++ 版会先编译几分钟）→ 编辑器主界面 |

> **没有「Starter Content / 初学者内容包」勾选框 —— 这是对的。** 它在 **UE 5.6 就被移除了**（源码 `TemplateProjectDefs.h:108`）。老版本 M0 让你勾它，**现在找不到不是你的错**。

**关于「变体（Variant）」下拉**：据模板定义文件，**C++ 版没有这个下拉**（它直接包含全部三套变体内容）；**蓝图版才有**，选项为：格斗游戏模板 / 平台跳跃游戏模板 / 横版卷轴游戏模板 / 全部。⚠️若你实际看到下拉，随便选即可，C++ 版都含全部内容。

### 为什么改成 C++（我推翻了早期决定，理由在下面）

M0 早期版本定的是"全程蓝图、一行 C++ 不写"。**看完 5.8 模板的真实内容后我建议改成 C++ 版**：

| 理由 | 证据 |
|---|---|
| **C++ 版直接送一套可用的战斗原型** | 模板含 `CombatDummy`（可受伤的靶子）、`CombatEnemy`、`CombatLifeBar`、`AnimNotify_DoAttackTrace`、`AnimNotify_CheckCombo`、`AnimNotify_CheckChargedAttack` —— **几乎就是 M0 要做的"能移动 + 能打 + 会僵直的靶子"**，而且是能直接读的 C++ 源码 |
| **C++ 版包含全部变体内容** | `Templates/TP_ThirdPerson/Content/` 下同时有 `Variant_Combat`、`Variant_Platforming`、`Variant_SideScrolling`；蓝图版只能选一套 |
| **这个选择几乎不可逆** | 蓝图 → C++ 要在项目里加模块（新手经典卡点）；C++ → 蓝图 随便加 |
| **借这次创建做"编辑器内"的最终工具链验证** | 已经用 `ToolchainCheck` 验证过 UBT+MSVC（UBT 9.2 s、编译 79 s 均 Succeeded），这次是在真实项目上再走一遍 |
| **你的长期路线就是 C++ 优先** | 见 `P20` 周路线：UE5 C++ 优先 + 蓝图做胶水 |

> **代价**：首次创建会先编译（几分钟，会弹进度窗口）。**这不是卡死**，等它走完。
> **M0 仍然"只写蓝图"** —— 上面说的是**项目类型**，不是让你现在写 C++。项目是 C++ 类型，你照样用蓝图做 M0 的内容；将来想改代码时不用返工。

### 进编辑器之后（验收动作）

| 步 | 动作 | 看到什么算对 |
|---:|---|---|
| 9 | **等**。看编辑器右下角 | 有 **"Compiling Shaders: N"** 计数在跳。**首次可能 10~40 分钟**。等它降到 0 或消失再继续。**不要强杀进程**（会留下半成品 DDC，下次更慢） |
| 10 | 左上角 **▶ Play** 按钮（或按 **Alt+P**） | 视口进入 PIE 模式。**这就是"能 PIE"** |
| 11 | 按 **W/A/S/D** 走、动**鼠标**转视角、按 **空格**跳 | 一个第三人称角色在地上跑、跳 |
| 12 | 按 **`~`**（Esc 下面那个键）打开控制台 → 输入 `stat fps` 回车 | 左上角出现 **FPS 数字**。再输入 `stat unit` → 出现 Frame/Game/Draw/GPU 四个数 |

**快捷键（已从引擎源码逐条核对，不是记忆）**：

| 键 | 作用 | 源码 |
|---|---|---|
| **Alt+P** | 开始 PIE（与上次相同模式） | `DebuggerCommands.cpp:344` |
| **Alt+S** | Simulate（不接管角色，只跑逻辑） | `:342` |
| **Esc** | **停止 PIE** | `:358` |
| **F8** | Possess / Eject 玩家（弹出相机，像飞一样飘） | `:365` |
| **Shift+F1** | PIE 中取回鼠标指针 | `:362` |
| **`~`** | 打开/关闭控制台 | `BaseInput.ini:16` `+ConsoleKeys=Tilde` |

## 1.7 常见坑（症状 → 原因 → 处理）

| # | 症状 | 原因 | 处理 |
|---:|---|---|---|
| 1 | 启动引擎/项目时报 RHI、D3D12、SM6、显卡不支持之类的错 | 显卡驱动太旧，或显卡不满足 DX12/SM6 | ① 去 NVIDIA/AMD 官网下**最新官方驱动**（别用 Windows Update 推的旧版）② 仍失败则退回 DX11：**Edit → Project Settings → 搜索框里搜 `RHI`**（或在 `Platforms → Windows` 里找 `Default RHI` 下拉）改成 DX11 相关项 ⚠️具体项名随版本变化，**搜索框是唯一可靠入口** |
| 2 | 编译/打开项目报 `The following modules are missing or built with a different engine version` | 项目是 C++ 类型但模块没编译成功，或引擎版本与项目不匹配 | ① 右键 `.uproject` → **Generate Visual Studio project files**（⚠️用 `tools/launch_net_clean.ps1` 启动，见附三坑 0）② 用 VS 打开 `.sln` 编译 ③ 仍不行：删掉 `Binaries/`、`Intermediate/`、`Saved/` 后重来 ④ 确认只开着一个引擎版本 |
| 3 | 首次打开卡在 `Compiling Shaders` 很久，看起来像死了 | 首次要编译几千个 shader，**这是正常的** | 看右下角计数是否还在跳。想加速：① 把 DDC 放到 SSD；② 杀毒排除；③ Editor Preferences 搜索框搜 `Shader`，把后台/异步编译相关开关打开 ⚠️选项名随版本变化 |
| 4 | 项目建在中文/空格路径下，报"找不到文件""导入失败" | UE 的中间文件与 Python/UBT 对非 ASCII 路径容忍度低 | **把整个项目目录移到纯 ASCII 短路径**（`<UE_PROJECTS>\AC6Proto`）。改路径后要重新生成 VS 工程文件（若用了 C++） |
| 5 | 编辑器偶尔卡死几秒、编译特别慢 | 杀毒实时扫描在扫 DerivedDataCache / Intermediate | 杀毒软件里把引擎目录、项目目录、DDC 目录加入**排除** |
| 6 | shader 编译中途屏幕黑一下、驱动重启、引擎崩溃 | Windows 的 **TDR**（显卡超时恢复）把长时间占用的 GPU 判死 | ① 优先：改用后台编译（同坑 3）② 进阶：把 TDR 延时调大（注册表 `TdrDelay`，**改注册表前先备份/建还原点**）⚠️这是有风险的改动，不确定就别做 |
| 7 | 编辑器面板关掉了找不回来 | 误关窗口 | **Window 菜单** → 里面有 Content Browser / Output Log / Details / Place Actors 等所有面板。**卡住时先怀疑"窗口被我关了"** |

## 1.8 第 1~2 天验收（全勾才算过，见第 6 部分）

- [ ] 能双击 `<UE_PROJECTS>\AC6Proto\AC6Proto.uproject` 直接打开编辑器，**Output Log 无红色 `Error:` 行**
- [ ] 能 **Alt+P** 进入 PIE，用 WASD+鼠标+空格操作角色
- [ ] 控制台输入 `stat fps` 能出数字，且 ≥ 60
- [ ] 能说出 Content Browser / World Outliner / Details 三个面板各在哪里、各干什么
- [ ] VS 2022 已装好，能编译一个空 C++ 项目（为 M1 铺路，不是 M0 必需）

---

# 第 2 部分：UE5 最小必要知识（第 3~5 天，只学 M0 用得到的）

## 2.1 总表：不用学 / 必须学 / 学到什么程度

**一页版（打印出来贴墙上，越界就回来看这张）**

| ❌ 你不需要学（M0 阶段） | ✅ 你必须学 | 🎯 学到什么程度够用 |
|---|---|---|
| Niagara 粒子 · HLSL/材质编辑器 · 骨骼动画/AnimBP/Control Rig/IK · Motion Matching · Lumen/Nanite/光追 · 后处理调优 · 音频 MetaSounds/Wwise · 网络复制/联机 · 行为树/黑板/EQS/NavMesh · 打包发布 · World Partition/地形 · 自定义 AnimNode/.Build.cs · 物理资产/破碎 · MetaHuman/Sequencer · UMG 动画与复杂样式 · 蓝图接口/事件分发器 | ① 五大面板<br>② Actor 与 Component<br>③ 蓝图：变量/事件/函数<br>④ Struct + DataTable<br>⑤ Data Asset / Curve<br>⑥ UMG 基础<br>⑦ 材质实例（一个参数）<br>⑧ 调试三件套<br>⑨ 不缓存数值的原则<br>⑩ 项目设置最小集（Input / Plugins） | ① 能说出资产在哪、场景有什么、属性在哪改、怎么放东西<br>② 能各举一个 M0 里的例子说明两者区别<br>③ 能写出"BeginPlay 打印 / Tick 转方块 / 按键切换"<br>④ 能建结构体 → 导 CSV → 读行 → 改表重导后值变化<br>⑤ 各建一个并在蓝图里读到<br>⑥ 能做出"滑条 + 文本 + 按钮"并能驱动世界<br>⑦ 能用 Dynamic Material Instance 改一个参数<br>⑧ 能定位"值没传进来"vs"传进来但表现不对"<br>⑨ 能解释为什么 BeginPlay 不能缓存表值<br>⑩ 能绑一个键并在蓝图响应 |

> 下面两张表是**展开版**（含"什么时候才需要"与"花多久"）。**一页版说不用学的，就别学。**

### A. 你**不需要**学什么（M0 阶段，碰了就是范围爆炸）

| 不学 | 现在不学的理由 | 什么时候才需要 |
|---|---|---|
| Niagara 粒子 / VFX | M0 只做数值可视化，不需要任何特效 | M4（反馈系统） |
| HLSL / 自定义材质函数 / 材质层 | M0 只碰**材质实例的一个参数** | M7（表现力打磨）、P2 涂装 |
| 骨骼动画 / AnimBlueprint / Control Rig / IK / Motion Matching | M0 没有角色动画 | M1 末 ~ M6 |
| Lumen / Nanite / 光追 / 后处理调优 | M0 画面越丑越好（越丑越容易看清数值在动） | M7 |
| 音频（MetaSounds / Wwise） | M0 不需要声音 | M4 / 音频模块 |
| 网络复制 / RPC / 联机 | 原文档 §1.2 明确"不做联网" | 永不做 |
| 行为树 / 黑板 / EQS / NavMesh | M0 没有 AI | M6 |
| 打包发布（Packaging / Shipping Build） | M0 只在编辑器里演示，录像即可 | 作品集上线前 |
| World Partition / Level Streaming / Landscape | M0 就一个空关卡 | 关卡模块 |
| 自定义 C++ AnimNode / 模块构建（.Build.cs） | 这是 P20 项目 B 的内容 | 第 2 个月 |
| 物理资产 / Chaos 破碎 | 不是 M0 的关键路径 | 视需要 |
| MetaHuman / Sequencer / 过场 | 与机甲主题无关，且资产成本极高 | 不做 |
| UMG 动画 / 复杂 UI 样式 | M0 的面板丑一点没关系 | 装配界面阶段 |
| Git LFS 深入使用 | M0 项目还没大资产 | 有 100 MB+ 二进制资产时 |
| 编辑器扩展（Editor Utility Widget）深入 | **M0 是"可选加分项"**，不是必做 | M0 的 Tier 2（见 §3.12） |
| 蓝图接口 / 事件分发器 / 网络同步变量 | M0 用不到 | 需要时再学 |

### B. 你**必须**学什么（学不到就会卡死）

| # | 知识点 | 学到什么程度够用（可观察判据） | 花多久 |
|---:|---|---|---:|
| 1 | **五大面板**：Content Browser / World Outliner / Details / Viewport / Place Actors | 能说出"资产在哪找、场景里有什么、选中后在哪改属性、怎么往关卡里放东西" | 1 h |
| 2 | **Actor 与 Component 的区别** | 能回答："一个 Actor 是一个可以放进关卡的物体；Component 是挂在 Actor 上的一块功能。移动 Actor = 整体移动；移动 Component = 相对 Actor 的偏移。" 能在 Outliner 看到层级 | 2 h |
| 3 | **蓝图基础**：变量（类型/默认值/Instance Editable）、事件（BeginPlay / Tick / 自定义事件 / 按键事件）、函数 vs 宏、Cast、Gate / DoOnce、ForEachLoop、Set Timer by Event | 能自己写："BeginPlay → Print String"；"Tick → 让一个方块按变量速度旋转"；"按 F → 调一个自定义事件" | 1 天 |
| 4 | **Struct + DataTable**（M0 的心脏） | 能建一个 User Defined Struct → 手写 3 行 CSV → 导入成 DataTable → 用 `Get Data Table Row` 读出并打印；改 CSV 重导后值变化 | 1 天 |
| 5 | **Data Asset / Curve Asset** | 知道"单行全局配置放 Data Asset，数值曲线放 UCurveFloat"，能各建一个并在蓝图里读到 | 2 h |
| 6 | **UMG 基础**：Widget Blueprint、Canvas Panel / Vertical Box / Horizontal Box / Slider / Text / Button / ProgressBar、Create Widget → Add to Viewport、输入模式 | 能做出"三个滑条 + 三个显示文本 + 一个按钮"的面板，且拖动滑条能让世界里的东西变化 | 1 天 |
| 7 | **材质实例（只学一个参数）** | 能从引擎自带材质创建 Material Instance → 改一个 Vector/Scalar 参数 → 用 Dynamic Material Instance + Set Vector Parameter Value 用滑条改颜色。<br>**用什么父材质**：内容浏览器齿轮 → 勾 **Show Engine Content** → 到 `Engine/BasicShapes/` 找 **`BasicShapeMaterial`**（实测含 Vector + Scalar 参数）。⚠️**不要**找 Starter Content —— UE 5.6 起已移除 | 2 h |
| 8 | **调试三件套**：Print String / 断点 / Stat 命令 | 能定位"值没传进来"和"值传进来了但表现不对"这两类问题（见 §2.3） | 2 h |
| 9 | **不缓存数值的原则** | 能说出："表里的值要在用的时候读，不要 BeginPlay 抄进变量到处用" | 30 min |
| 10 | **项目设置最小集**：Input（按键映射）、Plugins（Python / Editor Scripting）、Project Name/路径 | 能加一个 `TogglePanel` 按键映射并在蓝图中响应 | 1 h |

> **总量核算**：以上 10 项 ≈ 3 天（按你 >35 h/周 的强度，D3~D5 正好）。**不要在这一步加料。**

## 2.2 三天跟做练习（D3~D5，每天 3~4 个，每个都有判据）

> 全部在 §1.6 创建的 `AC6Proto` 里做，做完**不要删**——它们就是 M0 靶子的雏形。

| 天 | 练习 | 具体动作（点哪里） | 看到什么算对 |
|---|---|---|---|
| **D3** | ① Actor vs Component | 内容浏览器右键 → **Blueprint Class** → 父类选 **Actor** → 命名 `BP_TestCube` → 打开 → 左上 **Add** → 加 `StaticMesh`，Details 里 Static Mesh 选 `Cube`；再加一个 `PointLight`（Component） | 关卡里能看到方块 + 灯；在 Outliner 里展开这个 Actor 能看到两个 Component；**移动 Actor 是整体移动，改 Component 的 Relative Location 是相对偏移** |
| **D3** | ② 变量 + 事件 + Tick | Event Graph：`Event BeginPlay` → `Print String`（写 "Hello M0"）；新建 float 变量 `SpinSpeed` 默认 400，勾 **Instance Editable**；`Event Tick` → `AddActorLocalRotation`（Z = `SpinSpeed * DeltaSeconds`） | PIE 里方块匀速自转；在 Details 里改 `SpinSpeed` 到 4000 立刻变快；Output Log 里有 "Hello M0" |
| **D3** | ③ 按键事件 | Project Settings → 搜索框搜 `Input` → **Engine → Input → Action Mappings** → 加一个 `ToggleSpin`，绑到 **F** 键；蓝图里加 `InputAction ToggleSpin` → `FlipFlop` → 一个分支停转、一个分支转 | 按 F 能在"转/停"之间切换 |
| **D4** | ④ 手写 CSV → DataTable | ① 内容浏览器右键 → **Create Advanced Asset → Blueprints → Structure**（⚠️找不到就找带 `Structure` 字样的项）→ 命名 `S_TestRow` → 加两个变量：`DisplayName`（String）、`Value`（Float）<br>② 用 VSCode 写 `<UE_PROJECTS>\AC6Proto\data\test.csv`：<br>`Name,DisplayName,Value`<br>`T1,Test One,1.5`<br>`T2,Test Two,2.5`<br>③ 把 CSV 拖进内容浏览器 → 弹出对话框选 Row Struct = `S_TestRow` | 内容浏览器出现一个方格图标的 **DataTable** 资产；双击能看到 2 行 × 3 列 |
| **D4** | ⑤ 读表 + 打印 | 蓝图里：`Get Data Table Row`（Data Table 选刚建的，Row Name 填 `T1`）→ 把 `Out Row` 的 `Value` 接到 `Print String`；**同时接上 `Found` 布尔量做判断** | PIE 时 Output Log 打印 `1.5`。**故意把 Row Name 改成 `T9`（不存在）→ Found = false，打印 0** —— 这个体验是你以后排查"数据没进来"的第一把钥匙 |
| **D4** | ⑥ 热重载初体验 | 把 CSV 里 `Value` 从 `1.5` 改成 `9.9` 并保存 → 内容浏览器里**右键该 DataTable → Reimport** → 重启 PIE | Output Log 打印 `9.9`。**"改 CSV → 生效"这条链路，你今天就走通了**（M0 的主验收线就是它） |
| **D4** | ⑦ 遍历全表 | `Get Data Table Row Names` → `ForEachLoop` → `Get Data Table Row` → `Print String`（用 `Append` 把名字和值拼起来） | 打印出 `T1 = 9.9`、`T2 = 2.5`。**这就是调参面板能"表里加一行、面板自动多一行"的原理** |
| **D5** | ⑧ UMG 最小面板 | 内容浏览器右键 → **Create Advanced Asset → User Interface → Widget Blueprint** → `WBP_Test` → Designer 里拖一个 **Vertical Box** → 里面放 **Slider** + **Text**；Event Graph 里 `Slider OnValueChanged` → `SetText` | 编译后在关卡蓝图 PIE 前：`Create Widget` → `Add to Viewport`；PIE 里能看到滑条，拖动时 Text 数字跟着变 |
| **D5** | ⑨ 面板控制世界 | 把面板的**目标**指向 D3 那个方块：`Get All Actors Of Class (BP_TestCube)` → `Set SpinSpeed`（需要把变量勾 `Instance Editable`，并在蓝图里暴露一个 Setter 或直接 Set） | **拖滑条 → 方块转速立刻变**。这一刻你就拥有了"调参面板"的全部原理 |
| **D5** | ⑩ 鼠标能点面板 | 蓝图里：`Set Input Mode Game and UI` + `Set Show Mouse Cursor`（True） | 面板出现后**鼠标能点滑条**。⚠️这是 90% 新手的第一坑：不设它，鼠标会被锁在角色视角里，感觉"面板是坏的" |
| **D5** | ⑪ 材质实例 | ① 内容浏览器**齿轮图标** → 勾 **Show Engine Content** ② 到 `Engine/BasicShapes/` 找 **`BasicShapeMaterial`**（⚠️**不是** `M_Basic_Wall` —— 那是 Starter Content 的资产，UE 5.6 起已随它一起移除）③ 右键 **Create Material Instance** → 打开它 → 勾一个参数（Base Color / Roughness）④ 蓝图里 `Create Dynamic Material Instance` → `Set Vector Parameter Value` | 滑条能改方块颜色。**M0 只需要这一招**，不要展开学材质编辑器 |
| **D5** | ⑫ 调试三件套 | **断点**：蓝图节点右键 → `Add Breakpoint`（或选中节点按 F9）→ PIE → 命中后看变量面板；**Print String** 打印每个关键节点；**控制台**：`~` 后输入 `stat fps` / `stat unit` / `slomo 0.2`（慢动作） | 能用断点看清"变量到底是多少"。⚠️控制台命令太多记不住 → **在控制台里打前几个字母按 Tab 补全**，这是最可靠的发现方式 |

## 2.3 调试：三条命令 + 三个动作就够 M0 用

| 工具 | 怎么用（点哪里） | 用途 |
|---|---|---|
| **Print String** | 节点搜索框输 `Print String`；勾上 `Print to Screen` 和 `Print to Log` | 最笨最有效。**每加一条 Print 就是在缩小范围** |
| **断点** | 蓝图节点右键 → `Add Breakpoint`（F9 切换）→ PIE 命中后，看 **Debug** 标签的调用栈 + 变量值 | 读"这一刻变量的真实值" |
| **Watch Value** | My Blueprint 面板里对变量右键 → `Watch this value` | PIE 时持续显示某变量的值 |
| **`~` 控制台** | `stat fps`（帧率） / `stat unit`（Frame/Game/Draw/GPU 分解，**判断瓶颈在 CPU 还是 GPU**） / `stat game`（游戏线程细分） / `slomo 0.2`（慢动作，看瞬时效果） / Tab 补全发现更多 | 性能与瞬时行为 |
| **Output Log** | **Window → Output Log**；上方有过滤器（搜索框）和**输入下拉**（可切到 `Cmd` / `Python`） | 所有警告与错误的唯一权威来源 |
| **读到 Warnings / Errors 的自查顺序** | ① 只看带 `Error:` 的行 ② 找**第一条**而不是最后一条 ③ 看它指的文件与行号 ④ 复制那行去搜 | 见 §5.1 五步法 |

> **⚠️ 血泪纪律**：`Get Data Table Row` 的 `Found` 一定要接。**不接 Found，出错时你不会得到报错，只会得到一堆 0** —— 这是"数据没进来"最难查的原因。

---

# 第 3 部分：M0 任务书（第 1 周后半 ~ 第 3 周）

## 3.1 M0 是什么、验收线在哪

原文档 §7 对 M0 的定义：**项目骨架 + 数据层 + 调参面板**；验收 = 能演示**改 CSV → 运行时生效**；建议周期 1 周。§4.4 补充说明调参面板应具备：实时改参 / 数据表热重载 / 曲线编辑 / **导出为 DataTable 行** / 预设切换。

**对零基础读者，我把 M0 收敛成 4 条硬验收**：

| # | 验收 | 判据（可观察） |
|---:|---|---|
| 1 | **项目骨架** | 双击 `.uproject` 能进编辑器；目录结构按 §3.4 建好；Git 有 ≥ 6 次有意义的 commit |
| 2 | **数据层** | `Content/AC6/Data/Tables/` 下有 ≥ 5 个 DataTable；每张表打开能看到行；行名保留 AC6 溯源信息（如 `BST_G2_P04`） |
| 3 | **热重载** | 改 CSV 里 `QBReloadTimeSec`（0.30 → 0.91）→ Reimport → **不重启编辑器、不重编译**，PIE 里冷却条时长肉眼变长。**目标 ≤ 15 s（Tier 2 做到 ≤ 5 s）** |
| 4 | **调参面板** | 4 个滑条能实时改变 4 个可视靶子的行为；面板显示"参数名 + 当前值 + 单位 + 来源字段名" |

> **⚠️ 与原文档的口径差异（诚实标注）**：原文档 §7 写"改 CSV → 运行时生效"，P20 写"<2 s 生效"。零基础读者用"手动 Reimport + 重开 PIE"的实际耗时是 **5~15 s**。**我按 15 s 设验收线**；想做到 <2 s 需要 Tier 2（Python 一键重导 + 面板每帧读表），那是加分项不是必做项。

## 3.2 日历（D6~D17 + 2 天缓冲）

| 天 | 目标 | 产出物 |
|---|---|---|
| D6 | 创建正式项目 + 目录结构 + Git 初始化 | `AC6Proto.uproject`、目录树、首次 commit |
| D7 | 定义 4 个 Struct | `S_BoosterRow` / `S_ProtectorRow` / `S_AttackRow` / `S_CombatSettings` |
| D8 | 生成/整理 CSV → 导入 DataTable | `DT_Booster` 等 ≥ 5 张表 |
| D9 | 写数据访问层（不缓存原则） | `BP_DataHub`（读取函数 + Print 校验） |
| D10 | 搭调参靶场关卡（4 个可视靶子） | `L_TuningRange` |
| D11 | UMG 调参面板 v0（滑条 → 运行时值） | `WBP_TuningPanel` |
| D12 | 热重载 Tier 1 + 导出按钮 | "重新读取" / "导出当前值" 两个按钮可用 |
| D13 | 预设切换（轻/中/重三套）+ Python 校验脚本 | `PresetLight/Std/Heavy`、`AC6Proto/tools/check_csv.py` |
| D14 | Tier 2（可选）+ 数组遍历（表加一行面板自动多一行） | Editor Utility Widget 或 Python 一键重导 |
| D15 | 录 60~90 秒演示视频 + 写 `AC6Proto/docs/参数表_v1.md` | 视频 + 参数表 |
| D16 | 写 README（让人 3 分钟跑起来）+ 找同学复现测试 | README + 复现记录 |
| D17 | 补漏 + 第 6 部分清单逐条打勾 | M0 完成 |
| +2 缓冲 | 环境问题、报错、状态差的那些天 | — |

> **>35 h/周 的排法**：每天 5 h 里留 **1 h 专门用来"卡住与排错"**。你一定会卡，把它写进计划就不会崩溃。

## 3.3 D6 当天：项目就位确认（**不再重复创建**）

> ⚠️ **原文这一节叫「创建正式项目」，与 §1.6 重复了，而且用的是旧路径 `<UE_PROJECTS>`。已修正。**
> **项目在 §1.6 就建好了，不要再建第二个** —— 两个项目会让你后面分不清在改哪一个。

| 步 | 动作 | 判据 |
|---:|---|---|
| 1 | 确认 `<UE_PROJECTS>\AC6Proto\AC6Proto.uproject` 在 | 双击它能在 30 秒内进编辑器 |
| 2 | 编辑器里 **File → Open Level** → 打开模板自带的第三人称关卡 | 视口里能看到角色和地面 |
| 3 | 按 **Alt+P** 跑一次 | 角色能跑能跳（§1.6 已验过，这里只确认环境没坏） |
| 4 | 按 §3.4 建目录骨架 | Content 下出现 `AC6/Core`、`AC6/Data/...` 等文件夹 |
| 5 | 把 **Output Log** 停靠到底部 | 后面所有报错都从这里读 |

> **为什么用第三人称模板而不是 Blank**：① 第一天就能 PIE 到「能动的东西」；② 它自带一个可用关卡（M0 的靶场可以先复制它）；③ 等 M1 做自己的 `BP_ACPawn` 时再删掉模板角色，成本很低。
> **不要**为了「干净」改用 Blank 模板 —— 你会多花一天在「搭一个能玩的地面」上。

## 3.4 目录结构与 Git

```
<UE_PROJECTS>\AC6Proto\
├─ AC6Proto.uproject
├─ .gitignore                 ← 用 GitHub 的 UnrealEngine.gitignore 模板
├─ README.md                  ← 5 步跑起来（D16 写）
├─ Config\                    ← 引擎自动生成，可提交
├─ Content\
│   └─ AC6\
│       ├─ Core\              ← GameMode / PlayerController / GameInstance（M0 可空）
│       ├─ Data\
│       │   ├─ Structs\       ← S_BoosterRow 等结构体资产
│       │   ├─ Tables\        ← DT_Booster / DT_Protector / DT_Attack / DT_CombatSettings
│       │   ├─ Curves\        ← C_*.uasset（M0 可空，M1 用）
│       │   └─ Settings\      ← DA_CombatSettings（单行全局配置）
│       ├─ Tuning\            ← WBP_TuningPanel / BP_TuningRig / BP_DataHub / BP_Target*
│       ├─ Maps\              ← L_TuningRange
│       ├─ Art\               ← 占位材质/网格（方块、箭头、球即可）
│       └─ Debug\             ← BP_PrintRow（一键打印某行全部字段）
├─ data\                      ← 源 CSV（**不进公开仓库**）
│   ├─ ue_datatables\         ← 由 tools/export_ue_datatables.py 生成
│   └─ injected\              ← 你自己手改的 M0 用表（如 DT_CombatSettings.csv）
├─ tools\                     ← Python 脚本（可公开）
└─ docs\                      ← 参数表_v1.md / M0验收.md（可公开）
```

**Git 三条纪律**：

| 纪律 | 具体做法 |
|---|---|
| `.gitignore` 必须有 | 至少忽略 `Binaries/`、`DerivedDataCache/`、`Intermediate/`、`Saved/`、`*.sln`、`*.VC.db`。直接抄 GitHub 的 **UnrealEngine.gitignore** 模板 |
| **`data/` 与解包产物绝不 push** | 在 `.gitignore` 里加：<br>`data/ue_datatables/`<br>`data/injected/`<br>`*.param`<br>`regulation.bin*`<br>README 里也要写一句："本仓库仅含机制分析与自制资产，不含任何游戏原始数据文件" |
| commit 纪律 | 每条 commit 对应**一个可验收产出**（例：`feat(data): DT_Booster 导入并跑通 GetDataTableRow`）。**连续 3 天不 commit = 你在裸奔** |

## 3.5 数据层 Step 1：CSV 从哪来（工具已经写好了）

**好消息**：项目里已经有一个**可直接跑的导出器**：`tools/export_ue_datatables.py`。它把解包出来的 `.param` 转成 **UE5 可以直接导入的 CSV + 一份 `.struct.txt`（结构体定义）**。

```bash
cd <repo>
python tools/export_ue_datatables.py --starter
```

**我已在临时目录复跑过这条命令，产物与仓库里的 `data/ue_datatables/` 逐字节一致**（2026-09 复核）。实际输出（这就是你应该看到的）：

| CSV | 行数 | 列数（不含 Name） | 尺寸校验 |
|---|---:|---:|---|
| `EquipParamWeapon.csv` | 284 | 6 | MATCH |
| `EquipParamProtector.csv` | 121 | 12 | MATCH |
| `EquipParamBooster.csv` | 23 | 15 | MATCH |
| `EquipParamGenerator.csv` | 24 | 6 | MATCH |
| `EquipParamFcs.csv` | 19 | 6 | MATCH |
| `AtkParam_Pc.csv` | 712 | 10 | MATCH |
| `Bullet.csv` | 568 | 7 | MATCH |
| `NpcParam.csv` | 1232 | 10 | MATCH |

**M1 会用到、现在可以顺手导出的表**（同一条命令，加表名参数）：

| 命令 | 产出 | 用途 |
|---|---|---|
| `python tools/export_ue_datatables.py ChrActTurnParam` | 258 行 × 27 列 | **转向参数**（400 deg/s / 坦克 230） |
| `python tools/export_ue_datatables.py MovementAcTypeParam` | 19 行 × 184 列 | 腿型 → 移动参数 |
| `python tools/export_ue_datatables.py TentativePlayerParam` | 2 行 × 404 列 | **重力 120 m/s²**、锁定参数 |
| `python tools/export_ue_datatables.py JigglerBehaviorParam JigglerBehaviorSlideParam` | 49 行 × 12 列 / 33 行 × 16 列 | **Jiggler 双求解器** |
| `python tools/export_ue_datatables.py GameSystemParam` | 1 行 × 161 列 ⚠️ `.param` 尺寸校验 **−8 B**（单行表行宽不可信，原文档附录 C.3 铁律 5） | `DamageImpactLifeTimeSec` |
| `python tools/export_ue_datatables.py --list` | 打印脚本支持的 26 张表 | 找不到表名时用 |

**导出器做的三件聪明事**（你要理解它，否则出问题不会修）：

1. **字段名转 PascalCase**（`QB_ReloadTimeSec` → `QBReloadTimeSec`），因为 UE 的资产与变量命名规范是 PascalCase，且列名不能带下划线以外的怪字符；
2. **剪掉全零列**（原文档 §4.1：武器表 389 个槽里 133 个全零）——这是"不要照搬字段"的直接落实；
3. **行名优先用 paramdex 的开发者行名**（`BST_G2_P04`），拿不到才退回 `Row_<ID>` —— **保留了溯源能力**，这是你面试时能讲的点。

> ⚠️ **占位行警告**：导出结果里混着**不是真实部件的行**。必须在导入后认出它们，否则你会在 M1 里被"某把武器重量 = 1"坑死：
> - `EquipParamBooster`：13 行真实玩家件 + **7 行 `*_Inherited` 占位行**（Weight=1、QBEndSpeedKMH=500）+ 3 行 `TANK_BUILT_IN_*`（Weight=0）
> - `EquipParamFcs`：10 行真实件 + **8 行 `*_Inherited` 占位行**（三个提前量参数全 0）+ 1 行 Escape_Mission 特殊件
> - 判据：**行名里带 `Inherited` / `NPC_` / `Damaged` / `Test` 的一律先当占位**，用值域合理性复核。

## 3.6 数据层 Step 2：CSV 表头格式规范

### A. 八条硬规则（违反任何一条都会导入失败或静默出错）

| # | 规则 | 说明 |
|---:|---|---|
| 1 | **第一列必须叫 `Name`** | 它是行名（主键），不是数据。部分版本也接受 `RowName` ⚠️；导出器已经写成 `Name`，手写 CSV **照抄不要改** |
| 2 | 其余列名 = **Struct 里变量名，大小写敏感、不能有空格** | UE 会按列名找结构体字段，找不到就报 `Property not found` |
| 3 | 类型要能解析 | float 写 `1.5`；int 写 `100`；**bool 写 `True`/`False`**（不是 1/0）⚠️不确定：若 1/0 报错就换成 True/False；字符串可加引号 |
| 4 | 分隔符是**英文逗号** | 值里含逗号要用英文双引号包住 |
| 5 | **编码 UTF-8，不要用 Excel 另存** | Excel 会加 BOM、按系统区域改小数点、把逗号变分号。**用 VSCode 或 Python 写** |
| 6 | 行名必须唯一 | 重复行名 = 后者覆盖前者（还可能有警告） |
| 7 | 单元格不要有前后空格 | ` 100` 会导致解析失败 |
| 8 | 列顺序无关；多余列会警告但被忽略 | 少列 = 用结构体默认值 |

> **万能自验法**（比问我可靠 100 倍）：内容浏览器里对任何 DataTable **右键 → Export as CSV → 存到临时目录 → 用 VSCode 打开看它的表头长什么样**。UE 自己写出来的格式就是"官方认可的格式"，照着对齐即可。

### B. 已生成的表头（照抄即可）

```
# EquipParamBooster.csv —— 推进器（M0 主力表）
Name,Weight,ConsumeEN,ConsumeENBoostUp,ConsumeFixedENQB,QBEndSpeedKMH,QBAccelTimeF30,DashBoostEndSpeedKMH,FlyBoostEndSpeedKMH,QBStartAddSpeedKMH,FlyBoostUpperAccelMPSS,FlyBoostUpperMaxSpeedKMH,QBReloadTimeSec,FlyBoostDownMaxSpeedKMH,UpperBoostMaxSpeedKMPH,UpperBoostStartAccelMPSS

# EquipParamProtector.csv —— 护甲（头/核心/手臂/腿四类同表）
Name,Weight,PartsDamageRate,CorectSARecover,AssembleMenuCategory,Ap,Stability,ArmMaxWeight,LegsPayload,LegsBoosterId,LegsMovementParamId,LegsTurnParamId,IsHeavyWeightAddAnim

# EquipParamWeapon.csv —— 武器（注意：这里的 attackBase* 不是最终伤害）
Name,Weight,AttackBasePhysics,AttackBaseMagic,AttackBaseFire,AttackBaseThunder,AttackBaseStamina

# AtkParam_Pc.csv —— 攻击参数（真正的伤害/冲击力在这张表）
Name,HitStopTime,AtkPhys,AtkFire,AtkStam,ImpactPower,StaggerCriticalRatePhys,StaggerCriticalRateMag,StaggerCriticalRateFire,StaggerCriticalRateThun,ResidualImpactPower

# EquipParamGenerator.csv —— 发电机
Name,Weight,EnergyMax,EnergyRecoveryPerSec,EnergyRecoveryDelayTimeSec,EnergyRecoveryDelayTimeForEmptySec,EnergyRecoverValForEmpty

# EquipParamFcs.csv —— 火控
Name,Weight,PredictionShootBulletSpeedMPS,PredictionShootMaxShootOffset,PredictionShootStartPredDist,MissileLockTimeRate,MissileMultiLockTimeRate

# NpcParam.csv —— 敌人
Name,PhysGuardCutRate,MagGuardCutRate,FireGuardCutRate,ThunGuardCutRate,DefMag,DefFire,HitStopTime,ReceiveDmgHitStopType,EnableImpactGaugeFE,StabilityVal
```

### C. AC6 原字段名 ↔ CSV 列名 ↔ 中文 ↔ 出处（要引用数值时必须能对上）

| AC6 原字段名 | CSV 列名 | 类型 | 含义 | 出处（原文档 / 字段参考） |
|---|---|---|---|---|
| `weight` | `Weight` | float | 重量 [kg] | §4.1 / 字段参考 |
| `consumeFixedEN_QB` | `ConsumeFixedENQB` | int32 | 【QB】瞬间消费 EN | §5.1 |
| `QB_EndSpeedKMH` | `QBEndSpeedKMH` | float | QB 终端速度 [km/h] | §5.1 |
| `QB_AccelTimeF30` | `QBAccelTimeF30` | float | QB 喷射时间 [1/30 s] | §5.1 / §5.8.9 |
| `QB_ReloadTimeSec` | `QBReloadTimeSec` | float | **QB 再使用时间（冷却）[s]** | §5.1 |
| `consumeEN` | `ConsumeEN` | int32 | 常态 EN 消费 [/s] | §5.1 |
| `ap` | `Ap` | int32 | AP（机体耐久） | §5.6（偏移 412） |
| `stability` | `Stability` | int32 | **姿态稳定（阈值）** | §5.3 / §5.6（偏移 488） |
| `legs_payload` | `LegsPayload` | int32 | 腿部载重上限 [kg] | §5.6.1 |
| `armMaxWeight` | `ArmMaxWeight` | float | **手臂载重上限 [kg]（第二道门）** | §5.6 / 装配界面规格书 tail 572 |
| `assembleMenuCategory` | `AssembleMenuCategory` | int32 | 槽位类型（1 头 / 2 核心 / 3 手臂 / 4 腿） | §5.6 |
| `partsDamageRate` | `PartsDamageRate` | float | 部位伤害倍率（全表恒 1.5） | §5.6 |
| `corectSARecover` | `CorectSARecover` | float | 姿态回复时间修正（−0.33） | §5.6.3 |
| `legs_MovementParamId` | `LegsMovementParamId` | int32 | → `MovementAcTypeParam` 行 ID | §5.6.1 |
| `legs_TurnParamId` | `LegsTurnParamId` | int32 | → `ChrActTurnParam` 行 ID（10000000 等） | §5.6.1 |
| `legs_boosterId` | `LegsBoosterId` | int32 | 坦克腿内置推进器 ID（其余 = −1） | §5.6.1 |
| `attackBasePhysics` | `AttackBasePhysics` | int32 | 实弹攻击力**基本值**（≈占位，非最终伤害） | 字段参考 @200 |
| `atkPhys` | `AtkPhys` | int32 | **实弹攻击力（真正的伤害量级）** | §5.3（AtkParam @84） |
| `impactPower` | `ImpactPower` | int32 | **冲击力（打姿态用，与伤害是两条线）** | §5.3（@528） |
| `residualImpactPower` | `ResidualImpactPower` | int32 | 残留冲击 | §5.3（@988） |
| `hitStopTime` | `HitStopTime` | float | 顿帧时长 [s]（近战才非零） | §5.4 / 字段参考 |
| `staggerCriticalRate_*` | `StaggerCriticalRatePhys/Mag/Fire/Thun` | int32 | 直击补正 [%] | §5.3.1（@840/842/844/846） |
| `Damage_ImpactLifeTimeSec` | `DamageImpactLifeTimeSec`（在 `GameSystemParam`，需单独导出） | float | **冲击衰减寿命 1.5 s** | §5.3 |
| `MovementGravity` | `MovementGravity`（在 `TentativePlayerParam`，需单独导出） | float | **重力 120 m/s²** | §5.8.7 |
| `baseTurnSpeedDPS` | `BaseTurnSpeedDPS`（在 `ChrActTurnParam`，需单独导出） | float | 基准转向速度 [deg/s] | §5.1 |
| `turnAccelDPSS` | `TurnAccelDPSS`（同上） | float | 角加速度 [deg/s²] | §5.1 / §5.6.2⑤ |
| `rotAccelScaleX` | `RotAccelScaleX`（在 `JigglerBehaviorParam`） | float | Jiggler 旋转力 | §5.8.4 |
| `moveAccelScaleX` | `MoveAccelScaleX`（在 `JigglerBehaviorSlideParam`） | float | Jiggler 平移力 | §5.8.4 |

⚠️ **两个已知的命名坑**：
1. 原文档 §5.1 写的 `lookTargetModeTurnSpeedDPSAtLowDiff`，在 paramdex 导出里叫 **`LookTargetModeTurnSpeedDPSAtLowDeltaAngle`**。**引用时以 CSV 里的实际列名为准**（导出器是从 paramdex 直接生成的）。
2. `CorectSARecover` 保留源数据的拼写错误（少一个 `r`），**不要"顺手改对"**，否则列名找不到。

### D. M0 真正要你手写的只有一张表：全局配置

前面 8 张表都是脚本生成的，**你只需要手写这一张**（因为它跨表、是"全局常数"，不属于任何一张源表）：

```csv
Name,ImpactLifeTimeSec,PartsDamageMult,GravityMPSS,StaggerDurationSec,DirectHitMultPercent,BaseTurnSpeedDPS,TankTurnAccelDPSS
Default,1.5,1.5,120.0,1.2,100,400,230
```

- 值全部来自 §4 的"直接抄"表（1.5 / 1.5 / 120 / 400 / 230 均为 **B** 级）；
- `StaggerDurationSec = 1.2` 与 `DirectHitMultPercent = 100` 是**占位**：AC6 的硬直时长随速度变化（§5.6.1，`minStiffTimeSec`/`maxStiffTimeSec`），文档没有给单一常数 —— **这是你要自己标定的两个数**，标 C/D 级写进 `AC6Proto/docs/参数表_v1.md`。

## 3.7 数据层 Step 3：Struct 怎么定义

### 路线 A（**M0 推荐**）：蓝图结构体，零编译

| 步 | 动作 | 判据 |
|---:|---|---|
| 1 | 内容浏览器右键 → **Create Advanced Asset → Blueprints → Structure** ⚠️不同版本菜单层级略有差异，找不到就在右键菜单里找带 `Structure` 字样的项 | 出现 "Structure" 选项 |
| 2 | 命名 `S_BoosterRow` | 资产出现在 `Content/AC6/Data/Structs/` |
| 3 | 双击打开 → **+ Add Variable**，逐个加变量 | 变量名**必须与 CSV 列名逐字符一致**（`QBReloadTimeSec`、`ConsumeFixedENQB`…） |
| 4 | 变量类型：CSV 里带小数点的用 **Float**，整数用 **Integer** | 类型错了会导入失败或静默变 0 |
| 5 | 重复建 `S_ProtectorRow`（12 个变量）、`S_AttackRow`（10 个）、`S_CombatSettings`（7 个） | 4 个结构体齐全 |
| 6 | 改完结构体后 → 已有的 DataTable 需要 **Reimport**（UE 可能提示"有行无效"） | 表能正常打开、无红字警告 |

**优点**：不装 VS、不编译、改一行存一下就行（热迭代最快）。
**缺点**：不能写 C++ 逻辑；M1 之后如果要在 C++ 里用这些数据，需要重写成 `USTRUCT`。

### 路线 B（M1 之后再切）：C++ `USTRUCT`

导出器已经替你写好了 —— 每个 CSV 旁边都有一个 **`.struct.txt`**，内容就是可直接粘贴的 C++：

```cpp
// 摘自 data/ue_datatables/EquipParamBooster.struct.txt（节选，注释是我加的）
// paramdex 结构 384 字节 vs 实际 384 字节 -> MATCH
USTRUCT(BlueprintType)
struct FEquipParamBoosterRow : public FTableRowBase   // ★ 必须继承 FTableRowBase
{
    GENERATED_BODY()

    /** 重量[kg]  (offset 12) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float Weight = 0;

    /** 【QB】瞬間消費EN[point]  (offset 84) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32 ConsumeFixedENQB = 0;

    /** QB終端速度[km/h]  (offset 88) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float QBEndSpeedKMH = 0;

    /** QB再使用時間[s]  (offset 132) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float QBReloadTimeSec = 0;
    // …其余字段照抄 .struct.txt
};
```

**三条 C++ 侧的注意**：
1. `FTableRowBase` 是硬要求，不继承就不能当 DataTable 的行类型；
2. 结构体必须放在**能被反射的头文件**里（`#include "Engine/DataTable.h"`），且项目要有 C++ 模块 —— 也就是说**走路线 B 就等于开了 C++ 模块**（M0 不想面对的那些问题会全部回来）；
3. `.struct.txt` 顶部的 `paramdex 结构 X 字节 vs 实际 Y 字节` 若显示 **DIFF**（如 `GameSystemParam` 是 −8），**该表字段偏移可能不可靠，先跑 `python tools/paramdex_audit.py` 核对再用**（原文档附录 C.3 铁律 5）。

> **决策建议**：M0 走 A，M1 需要写移动逻辑时再一次性切 B（那时你已经有 3 天经验，切过去只要半天）。

## 3.8 数据层 Step 4：导入 DataTable（点哪里 + 报错对照表）

| 步 | 动作 | 判据 |
|---:|---|---|
| 1 | 把 `data/ue_datatables/*.csv` **复制**到 `<UE_PROJECTS>\AC6Proto\data\ue_datatables\` | 项目自包含（源 CSV 与资产都在一起） |
| 2 | 在内容浏览器里进入 `Content/AC6/Data/Tables/` | 路径对了 |
| 3 | 从资源管理器**拖** `EquipParamBooster.csv` 进内容浏览器 | 弹出对话框，问 **Row Struct / Row Type** |
| 4 | 选 `S_BoosterRow` → OK/Apply | 出现一个**方格图标**的资产 `EquipParamBooster` |
| 5 | 重命名成 `DT_Booster`（右键 → Rename） | 命名规范统一（见附录 B） |
| 6 | 双击打开 | 看到 23 行；点某行右侧 Details 显示字段值 |
| 7 | 对其余 CSV 重复（`EquipParamProtector`→`DT_Protector`；`AtkParam_Pc`→`DT_Attack`；`EquipParamWeapon`→`DT_Weapon`；`EquipParamGenerator`→`DT_Generator`；`EquipParamFcs`→`DT_Fcs`；`NpcParam`→`DT_Enemy`；手写的全局表→`DT_CombatSettings`） | ≥ 8 张表 |

**导入报错对照表**（出现这些字样时按右列处理）：

| 报错/症状 | 原因 | 处理 |
|---|---|---|
| `Property not found` / 某列被忽略 | CSV 列名与结构体变量名不一致（大小写/空格/拼写） | 逐个字符比对（`CorectSARecover` 这种拼写错误也要照样抄） |
| 导入后某列全 0 | 类型不匹配（float vs int），或该列真的空 | 检查结构体变量类型；用内容浏览器**导出为 CSV** 对比格式 |
| `Failed to find row struct` / 没有行类型可选 | 结构体没建成 Structure 资产，或名字不对 | 确认 `Content/AC6/Data/Structs/` 下有 `S_*` 结构体 |
| 第一列没被识别成行名 | 第一列标题不是 `Name`/`RowName`，或文件有 BOM | 用 VSCode 另存为 **UTF-8（无 BOM）**；标题改 `Name` |
| 整表导入失败，无详细信息 | 编码/分隔符问题（Excel 另存的锅） | 用 Python 重写该 CSV（`csv.writer`，`encoding='utf-8'`, `newline=''`） |
| 中文注释乱码 | 文件被当成 ANSI 读 | 我们生成的 CSV **没有中文**，出现中文说明你自己的表混入了中文，删掉即好 |

## 3.9 数据层 Step 5：读取层（M0 最重要的一条纪律）

**纪律：不要在 `BeginPlay` 把表里的值抄进成员变量然后到处用。**

| 做法 | 评价 |
|---|---|
| ✅ 每次需要时 `Get Data Table Row` 现读 | 表一改就生效（M0 验收线的技术基础） |
| ⚠️ `BeginPlay` 读一次存到变量 | 能用，但热重载后不更新 —— **M0 阶段会让你的验收失败**，而且你会花 2 小时怀疑"Reimport 坏了" |
| ❌ 手动在蓝图里写死数值 | 直接违反 §4.4 与 §7 的核心要求（"硬编码 = 返工"） |

**蓝图节点清单（M0 只用这几个）**：

| 节点 | 用途 | 注意 |
|---|---|---|
| `Get Data Table Row` | 按行名取一行 | **必须接 `Found`**，否则失败时静默返回全 0 |
| `Get Data Table Row Names` | 取所有行名（数组） | 用来做"表加一行、面板自动多一行" |
| `Get Data Table Column as String` | 调试用：按列名取整列字符串 | 排查列名问题时很好用 |
| `Make Literal Name` / 变量 | 拼行名 | 行名建议暴露成 `Instance Editable` 变量，方便 PIE 里现场换行 |
| `ForEachLoop` | 遍历行名 | — |
| `Print String` | 打印 `行名 + 字段名 + 值` | **验收证据的来源** |

**建议写一个 `BP_DataHub`（Actor 或 Game Instance Subsystem 的蓝图版）**：里面每张表有一个"取行"函数（`GetBooster(QBReloadTimeSec)` 之类），所有其他蓝图都从这里拿数。**M0 的架构一句话：只有 DataHub 认识 DataTable，别人只认识 DataHub。**

## 3.10 调参面板：先设计"看得见什么"，再写代码

原文档 §4.4 说得很清楚：**这个面板本身就是作品集里最有说服力的一件东西** —— 它证明你理解的是参数空间，不是抄了一组数字。
所以 M0 的面板必须"看得见效果"，而不是"数字在变"。**四个可视靶子**（都在 `L_TuningRange` 里，用方块/箭头/球即可，不需要任何美术）：

| 靶子 | 长什么样 | 面板滑条 | 验收现象（这就是可演示的证据） | 对应原文档 |
|---|---|---|---|---|
| **T1 转速靶** | 一个方块 + 一个锥体（当指针），要转到场景里的目标点 | `BaseTurnSpeedDPS`（范围 230~400） | 滑到 **230**：指针像"开船"，明显追不上目标；滑到 **99999**：瞬间对准（"变人形"） | §5.1 转向表 / §5.6.2⑤（B） |
| **T2 姿态靶** | 一个靶子方块 + 头顶一根进度条 | 按 **F** 累计 `ImpactPower`；滑条改 `Stability`（范围 600~1500）与 `ImpactLifeTimeSec`（0.5~3.0） | 打满 → 变红 + 停 1.2 s（硬直）；把寿命改成 **0.5 s** → **几乎打不出硬直**（这是原文档 P20 点名的演示） | §5.3 / §5.8.10（B） |
| **T3 QB 冷却灯** | 一个灯 + 一个冷却条 | 按 **Q** 触发；滑条改 `QBReloadTimeSec`（0.30~0.91）与 `QBAccelTimeF30`（8~16.5） | 灯亮 **0.27~0.55 s** 后灭；之后再按 Q 在冷却期内**无效**；面板改 0.91 → 冷却条肉眼变长 | §5.1（B） |
| **T4 重力靶** | 一个球从 10 m 高空落下 | 滑条改 `GravityMPSS`（9.8~120） | 120 时"砸下来"，9.8 时"飘下来"；落地时间能读出差异 | §5.8.7（B） |

**面板规格表**（写进 `AC6Proto/docs/参数表_v1.md` 的原始格式）：

| 面板行 | 显示文本 | 滑条范围 | 数据来源 | 滑条范围从哪来 |
|---|---|---|---|---|
| 1 | `BaseTurnSpeedDPS` | 230 ~ 400 | `DT_CombatSettings.BaseTurnSpeedDPS` | **值域从数据推导**（§4），不是 0~1 自由滑 |
| 2 | `Stability` | 600 ~ 1500 | `DT_Protector[选中的腿].Stability` | 腿部实测值域 618~1500（§5.6） |
| 3 | `ImpactLifeTimeSec` | 0.5 ~ 3.0 | `DT_CombatSettings` | 中位 1.5 的上下 2 倍区间 |
| 4 | `QBReloadTimeSec` | 0.30 ~ 0.91 | `DT_Booster[选中的推进器].QBReloadTimeSec` | **逐部件实测值域**（§5.1） |
| 5 | `GravityMPSS` | 9.8 ~ 120 | `DT_CombatSettings` | 地球重力 ↔ AC6 实测（§5.8.7） |
| — | 底部：`重新读取数据表` 按钮 / `导出当前值` 按钮 / `预设` 下拉 | — | — | — |

> **★ TA 式的一个小设计**：每行滑条右边显示 **`当前值 (单位) ← 字段名`**，例如 `0.91 s ← DT_Booster[BUERZEL_21D].QBReloadTimeSec`。
> 这一行字让面试官 3 秒钟看懂"你不是在拖滑条，你在改一个数据契约"。

## 3.11 调参面板实现（点哪里）

**① 面板骨架（Designer）**

| 步 | 动作 | 判据 |
|---:|---|---|
| 1 | 内容浏览器右键 → **Create Advanced Asset → User Interface → Widget Blueprint** → `WBP_TuningPanel` ⚠️菜单层级随版本变化，找不到就找 `Widget Blueprint` | 打开 Designer |
| 2 | 拖 **Canvas Panel** 到根 → 里面拖一个 **Vertical Box** → `Details → Slot → Position/Size` 调到左上角 | 布局住下了 |
| 3 | Vertical Box 里放：5 组「**Horizontal Box**（Text + Slider + Text）」+ 1 个 Horizontal Box（Button + Button + ComboBox） | 结构像一张表 |
| 4 | 每个 Slider：`Details → Appearance → Min Value / Max Value` 按 §3.10 规格填；`Step Size` 设成合适粒度（如 0.01） | 滑条范围与数据值域一致 |
| 5 | 每个 Slider/Text **命名**（`Slider_TurnSpeed`、`Text_TurnSpeedValue`…） | 命名规范，否则后面连线会疯 |

**② 打开面板（别跳过输入模式）**

在关卡蓝图（或 GameMode）里：

```
Event BeginPlay
  → Create Widget (Class = WBP_TuningPanel)
  → Add to Viewport
  → Set Input Mode Game and UI        ← 少了这条，鼠标点不到滑条
  → Set Show Mouse Cursor (true)      ← 少了这条，看不见鼠标
```

**③ 滑条 → 运行时值**

```
Slider_TurnSpeed → OnValueChanged (float Value)
  → Get All Actors Of Class (BP_TuningRig)
  → Set BaseTurnSpeedDPS (Value)
  → Text_TurnSpeedValue → Set Text (Value + " deg/s ← DT_CombatSettings")
```

**④ 打开/关闭面板的快捷键**

| 方案 | 步骤 | 何时用 |
|---|---|---|
| **旧版 Input Action（M0 最省时间）** | Project Settings → 搜索 `Input` → **Engine → Input → Action Mappings** → `+` 加 `TogglePanel` → 绑 **Tab** → 蓝图里 `InputAction TogglePanel` → `FlipFlop` → 一个分支 `Add to Viewport`，另一个 `Remove from Parent` | M0 直接用。⚠️UE5 里它是 deprecated API（会有警告），但可用 |
| Enhanced Input（UE5 默认体系） | 建 `IA_TogglePanel` + `IMC_Default` → PlayerController 里 `Add Mapping Context` | M2 迁移，不要在 M0 折腾 |

## 3.12 热重载与导出（M0 的灵魂，分两级做）

### Tier 1（**必做**）：手动 Reimport

| 步 | 动作 | 判据 |
|---:|---|---|
| 1 | 用 VSCode 打开 `<UE_PROJECTS>\AC6Proto\data\ue_datatables\EquipParamBooster.csv`，把 `IA_C01B_GILLS` 行的 `QBReloadTimeSec` 从 `0.3` 改成 `0.91`，保存 | 文件真的变了（看文件修改时间） |
| 2 | 内容浏览器里**右键 `DT_Booster` → Reimport**（或双击打开后在工具栏上找 `Reimport`）⚠️入口位置随版本变化，找不到就在资产右键菜单里找 `Reimport` | 表里的值变成 0.91；Output Log 可能有 Reimport 记录 |
| 3 | PIE 里按面板上的 **`重新读取数据表`** 按钮（按钮 → 调 `BP_DataHub` 的刷新函数 → 重新 `Get Data Table Row` → 更新靶子与文本） | T3 冷却条肉眼变长 |
| 4 | 计时 | **从存盘到看见变化 ≤ 15 s，且全程没重启编辑器、没重编译** |

### Tier 2（**加分**）：Python 一键重导（你 Python 底子在，这步性价比极高）

启用插件：**Edit → Plugins → 搜索框搜 `Python`** → 勾 **Python Editor Script Plugin**；同时勾 **Editor Scripting Utilities** → 重启编辑器。
打开 **Window → Output Log** → 把输入框左边的下拉从 `Cmd` 切到 **`Python`**（⚠️下拉里没有 Python = 插件没启用）→ 粘贴：

```python
# 一键重导 /Game/AC6/Data/Tables 下所有 DataTable
import unreal
paths = unreal.EditorAssetLibrary.list_assets('/Game/AC6/Data/Tables', recursive=False, include_folder=False)
print('待重导：', len(paths), '个资产')
# ★ 先确认 API 名字（不要背 API，让它自己告诉你）
print([m for m in dir(unreal.EditorAssetLibrary) if 'eimport' in m.lower()])
```

**第一行输出的函数名列表里应该有类似 `reimport_asset` / `reimport_assets` 的东西** —— 用列出来的真名去调：

```python
import unreal
for p in unreal.EditorAssetLibrary.list_assets('/Game/AC6/Data/Tables', recursive=False, include_folder=False):
    ok = unreal.EditorAssetLibrary.reimport_asset(p)     # ← 用上一步打印出的真实函数名
    print(p, ok)
```

⚠️ **诚实标注**：`reimport_asset` 这个具体名字/签名在不同版本可能不同（也可能要配合 `AssetImportTask` + `AssetToolsHelpers`）。**上面那段 `dir()` 打印就是防我记错的保险**。别的方案：`unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])` 配合 `unreal.AssetImportTask`（`replace_existing=True`）。

**把 Tier 2 做成面板上的一个按钮**：按钮 → Python（或 Editor Utility Widget）→ 重导 → 回写 `上次重导时间 → 读到的新值`。**这是你 M0 最值钱的一件交付物。**

### 导出（原文档 §4.4 的"导出为 DataTable 行"）

| 做法 | 实现 | 说明 |
|---|---|---|
| 最简 | 面板上 `导出当前值` 按钮 → `Print String` 打印一行 CSV 格式文本 → 你复制粘贴回 CSV | 3 分钟做完，M0 够用 |
| 进阶 | 用 Python 写文件（Python 侧 `open().write()` 天然会做） | ⚠️蓝图侧的"写文件"节点在不同版本里名字/可用性不一（在节点搜索框里输 `Save String` 看有什么可用），**不确定就用 Python** |

## 3.13 M0 验收演示脚本（90 秒，照着录）

| 秒 | 做什么 | 观众看到什么 |
|---:|---|---|
| 0-10 | 双击 `.uproject` 打开编辑器 → 打开 `L_TuningRange` | 能进项目 |
| 10-25 | PIE → 按 Tab 打开面板 → 拖 `BaseTurnSpeedDPS` 从 400 到 230 再到 99999 | 指针从"开船"变"瞬间对准" |
| 25-45 | 按 F 打姿态靶 → 打满 → 变红硬直 → 硬直期间伤害数字变大 | 完整的"积累 → 硬直 → 爆发" |
| 45-60 | 把 `ImpactLifeTimeSec` 从 1.5 拖到 0.5 | 姿态条几乎涨不起来，**打不出硬直** |
| 60-75 | 按 Q 触发 QB → 灯亮 → 冷却条 → 在冷却中再按 Q 无效；把 `QBReloadTimeSec` 改成 0.91 | "资源 + 冷却"双闸门 |
| 75-90 | 切到 VSCode 改 CSV 一行 → 回编辑器点 `重新读取` → 面板数字与靶子行为同步变化 | **改 CSV → 运行时生效** |

## 3.14 M0 之后立刻做什么（给 M1 留接口）

| 预留 | 现在怎么做（成本很低） |
|---|---|
| 移动参数 | `MovementAcTypeParam` / `ChrActTurnParam` 提前导出成 DataTable（命令见 §3.5），M1 直接用行 ID 关联 |
| 腿型外键 | `DT_Protector.LegsTurnParamId` 已经是 **DataTable 行名引用**，M1 用 `Get Data Table Row` 二次查表即可。**不要写 `switch(legType)`**（原文档 §5.6 明确要求） |
| 单位换算 | 面板上把"数据单位"和"游戏单位"分开显示（`km/h ↔ m/s` ×0.27778；`1/30 s ↔ s` ×0.0333）——原文档 §5.6.2⑧ 证明 AC6 自己就是这么做的 |
| 占位行 | 现在就在表里给占位行打标记（或建一个 `DT_PartBlacklist`），M1 才不会选到 `*_Inherited` |

---

# 第 4 部分：第一批可用的真实数值（拿来就能填）

## 4.1 读表须知

| 事项 | 说明 |
|---|---|
| **证据等级定义** | **A** 官方文档原文 · **B** paramdex 字段定义 + 本机实测复现 · **C** 合理推断但未本地验证 · **D** 不确定/待验证（原文档 §0、附录 C） |
| **这些是"起点"不是"标准答案"** | 原文档 §0 原则 3 原文：*"本文档里的数字都是'起点'而不是'标准答案'……照着起步、然后按自己的手感调"* |
| **引用时必须带口径** | 同一个字段不同口径会得出不同中位数（原文档附录 C.3.2）。下表所有"中位"都标了口径 |
| **数值会随补丁变化** | 原文档附录 C.4：数据取自本机特定版本，量级可靠、精确值可能已变 |
| **本表已做的额外验证** | 标 ✅复现 的行，我用本机 `data/ue_datatables/*.csv` 重算过，与原文档一致 |

## 4.2 ★ 主表：M0 起步数值（直接抄）

| # | 参数（人话） | 真实字段名 | **起步值** | 单位 | 出处（原文档） | 等级 | M0 填到哪 |
|---:|---|---|---|---|---|---|---|
| 1 | **QB 冷却** | `QB_ReloadTimeSec` | **0.30 / 0.56 / 0.91**（轻/中/重三档）；值域 0.30~0.91 ✅复现 | s | **§5.1** 推进器真实数值表 | **B** | `DT_Booster` 一列 |
| 2 | **QB 末速** | `QB_EndSpeedKMH` | **257 ~ 377**（13 个玩家件）；特殊行到 **425** ✅复现 | km/h | **§5.1** | **B** | `DT_Booster` |
| 3 | **QB 瞬间耗 EN** | `consumeFixedEN_QB` | **480 ~ 1100** ✅复现 | point | **§5.1** | **B** | `DT_Booster` |
| 4 | QB 喷射时长 | `QB_AccelTimeF30` | **8 ~ 16.5** → 约 **0.27~0.55 s** ✅复现（8~16.5） | 1/30 s | 字段值域 **§5.1**（B）；÷30 的换算见 **§5.8.9**（该节自称 **D**） | **B**（换算部分 D） | `DT_Booster` |
| 5 | 常态 EN 消耗 | `consumeEN` | **130 ~ 480** | /s | **§5.1** | **B** | `DT_Booster` |
| 6 | 空中上升加速度 | `flyBoostUpperAccelMPSS` | **45 ~ 70** | m/s² | **§5.1** | **B** | `DT_Booster` |
| 7 | **姿态稳定**（阈值） | `stability` | **0 ~ 1500，逐部件**；头 **201~536** / 核心 **278~641** / **手臂恒为 0** / 腿 **618~1500** ✅复现 | 点 | **§5.3** ACS 表 + **§5.6** 按类别实测表 | **B** | `DT_Protector` |
| 8 | **冲击力** | `impactPower` | **0 ~ 6000**；**中位 315**（⚠️口径：剔除 −1 哨兵后的 **447** 行）；仅正数 **395** 行中位 **500** ✅复现（447/315、395/500） | 点 | **§5.3** + **附录 C.3.2** | **B** | `DT_Attack` |
| 9 | **冲击衰减寿命** | `Damage_ImpactLifeTimeSec` | **1.5** | s | **§5.3** | **B** | `DT_CombatSettings` |
| 10 | **重力** | `MovementGravity` | **120**（≈ 12 g） | m/s² | **§5.8.7** | **B** | `DT_CombatSettings` |
| 11 | **基准转向速度** | `baseTurnSpeedDPS` | 中位 **400**（⚠️口径：**仅正数 201 行**；全体中位 320）；二足/逆关节/四足固定行 = **360** ✅复现（360） | deg/s | **§5.1** 转向表 + **附录 C.3.2** | **B** | `DT_CombatSettings` / M1 的 `DT_Turn` |
| 12 | **坦克角加速度** | `turnAccelDPSS` | 坦克行 **230**（另两行 350 / 450）；**其余腿型 9999999 ≈ 瞬时** | deg/s² | **§5.1** 表述修正 + **§5.6.2⑤** | **B** | M1 |
| 13 | Jiggler 旋转力 | `rotAccelScaleX` / `rotDecayValueX` | 中位 **20**（上限 115）；阻尼中位 **5** | 无量纲 | **§5.8.4** / **§5.1.1** | **B**（"平移是旋转 5 倍"这个**倍数结论是 C**） | M1（M0 只登记） |
| 14 | Jiggler 平移力 | `moveAccelScaleX` | 中位 **330**（上限 580） | 无量纲 | **§5.8.4** | **B** | M1 |
| 15 | Jiggler 生效区间 | `minAccelMPSS` / `maxAccelMPSS` | **50 ~ 300**；限位反弹 **0.1~0.2**；角度硬限位 **±45°** | m/s²、比率、度 | **§5.8.4** | **B** | M1 |
| 16 | 部位伤害倍率 | `partsDamageRate` | **1.5**（全表恒为 1.5，做成全局常数） | × | **§5.6** | **B** | 全局 |
| 17 | 硬直阈值阶梯 | `DamageLevelConvThresholdParam` | `[150, 1600, 1600, 2000, 7500, 9000, 13000]` → DL1~DL6 | 点 | **§5.8.10** | 字段存在 **B**；**"这串数就是硬直阈值"的语义是 C/D** ⚠️需自验 | M3 |
| 18 | **手臂载重上限**（第二道门） | `armMaxWeight` | 手臂实测 **10520 ~ 21300 kg**（20 行）✅复现；腿/头/核心该列为 0 | kg | **§5.6** + **装配界面规格书**（tail 572 → 起始 568） | **B** | `DT_Protector`（M5 装配时才是硬约束，M0 先登记） |

**怎么用这张表（三步）**：

1. 把第 7/8/9/10/11 条填进 `DT_CombatSettings.csv`（§3.6 D 给了模板），其余填进对应部件表；
2. 每条在 `AC6Proto/docs/参数表_v1.md` 里**照抄"出处 + 等级"两列**（这是你面试时唯一能立刻掏出来的东西）；
3. **面板滑条的范围用这些值域**（§3.10），不要写 0~1。

## 4.3 附：本机可复现的样例行（拿来当"三档预设"）

> ✅ 以下数值**我已用本机 `data/ue_datatables/*.csv` 逐行复现**，行名就是真实开发者行名。可以直接抄进 `DT_Booster` / `DT_Protector` 当"轻/中/重"三套预设。

**推进器（`DT_Booster`）**

| 行名 | Weight | ConsumeFixedENQB | QBEndSpeedKMH | QBAccelTimeF30 | QBReloadTimeSec | 特点 |
|---|---:|---:|---:|---:|---:|---|
| `BC_0400_MULE` | 970 | 670 | 298 | 14 | 0.58 | **最轻**（值域下限） |
| `BST_G1_P10` | 1300 | 480 | 299 | 11.7 | 0.60 | **QB 消耗最低**（480，值域下限） |
| `IA_C01B_GILLS` | 1590 | 620 | 320 | 8.5 | **0.30** | **冷却最快**（值域下限） |
| `IB_C03B_NGI_001` | 1930 | 740 | **377** | 13 | 0.63 | **末速最高**（值域上限） |
| `BUERZEL_21D` | **2240** | 630 | 307 | 8 | **0.91** | **最重 + 冷却最慢**（值域上限） |
| `AB_J_137_KIKAKU_Escape_Mission_Variant` | 1620 | **1100** | **257** | 11.5 | 0.60 | **QB 消耗最高 / 末速最低**（值域另一端） |

**腿（`DT_Protector`，`AssembleMenuCategory=4`）**

| 行名 | Weight | Ap | Stability | LegsPayload | LegsMovementParamId | LegsTurnParamId | LegsBoosterId |
|---|---:|---:|---:|---:|---:|---:|---:|
| `LEGS_EL_TL_10_FIRMEZA` | 11200 | 3600 | 737 | 52100 | **0** | **10000000** | −1 |
| `LEGS_KASUAR_42Z` | 16510 | 3580 | 686 | 49280 | **500** | **11000000** | −1 |
| `LEGS_LG_022T_BORNEMISSZA` | 49800 | **9240** | **1500** | **100300** | **300** | **13000000** | **63300000** |
| `LEGS_EL_TL_11_FORTALEZA` | 23650 | 5100 | 842 | 69300 | **320** | **13200000** | **63360000** |

→ **一眼可见的三件事**：① `legs_MovementParamId` / `legs_TurnParamId` / `legs_boosterId` 都是**外键**（`legs_boosterId` 只有坦克腿非 −1，与 §5.6.1 一致 ✅复现）；② 坦克腿用 AP 9240 与稳定 1500 换来"转不动"；③ 腿是防御主力。

**护甲四类的实测值域**（✅ 我用 121 行全量重算，与 §5.6 完全一致）：

| `AssembleMenuCategory` | 部位 | 行数 | AP | 姿态稳定 | 重量 |
|---:|---|---:|---|---|---|
| 1 | 头 | 24 | 300 ~ 1250 | 201 ~ 536 | 1050 ~ 4600 |
| 2 | 核心 | 19 | 2400 ~ 4320 | 278 ~ 641 | 9700 ~ 23600 |
| 3 | 手臂 | 20 | 1000 ~ 2970 | **全 0** | 8480 ~ 26740 |
| 4 | 腿 | 26 | 2000 ~ 9240 | 618 ~ 1500 | 11200 ~ 49800 |

**发电机（`DT_Generator`，样例）**

| 行名 | Weight | EnergyMax | EnergyRecoveryPerSec | EnergyRecoveryDelayTimeSec | EnergyRecoveryDelayTimeForEmptySec | EnergyRecoverValForEmpty |
|---|---:|---:|---:|---:|---:|---:|
| `AG_J_098_JOSO` | 3420 | 2300 | 2600 | 1.3 | 2.0 | 400 |
| `DF_GN_02_LING_TAI` | 3860 | 2240 | 2340 | 0.5 | 1.2 | 280 |
| `DF_GN_08_SAN_TAI` | 10060 | **4420** | 3210 | 0.98 | 1.9 | 620 |
| `VP_20S` | 3800 | 2620 | **3400** | 1.12 | 2.3 | **1200** |

→ **两段式 EN 回复**（正常延迟 vs "借金"延迟）在数据里是两列，M1 直接用。

**FCS（`DT_Fcs`）—— 一个值得注意的实测事实**

| 分组 | 行数 | BulletSpeedMPS / MaxShootOffset / StartPredDist |
|---|---:|---|
| 真实件 | 10 | **350 / 80 / 390（三者全同）** |
| 占位行 `*_Inherited` | 8 | 0 / 0 / 0 |
| 特殊件 `FCS_G1_P01_Escape_Mission` | 1 | 800 / 35 / 250 |

→ 即：**大部分 FCS 的"提前量三参数"是同一套值**，玩家能感知的差异主要来自 `MissileLockTimeRate`（实测 0.72~1.55）。**这是"表里有这列 ≠ 这列在做区分"的一个活例子**（对应原文档 §5.6.2⑩ 的"4 行曲线是死的"）。

## 4.4 两条口径警告（引用数字时必须一起说）

| # | 警告 | 具体 |
|---:|---|---|
| 1 | **统计口径** | `impactPower`：**剔除 −1 哨兵后 447 行中位 315**；若按"仅正数"算是 **395 行中位 500**；按"非零含 −1"算是 **660 行中位 68.5**。**写文档时三者必带其一**。`baseTurnSpeedDPS` 同理（全体中位 320 / 仅正数 400） |
| 2 | **单位换算** | 速度 `km/h → m/s`：**÷3.6**（§5.1 给过锚点：500 km/h ≈ 139 m/s）；时间 `F30 → 秒`：**按 1/30 算**（§5.8.9，该节自称 **D 级**：F30 是参数单位、不等于 tick 频率）。**换算写在代码里的地方要注释来源**，否则半年后你自己都不敢改 |

## 4.5 明确**不要**照抄的四样东西

| ❌ 不要抄 | 为什么 | 正确做法 |
|---|---|---|
| 伤害公式里的**"防御中性点 1000"** | 原文档 §5.3 已把它从 B 降级为 **C**："防御 1227"在 257 张表里零命中，无法本地复现 | 用它的**公式形式**起步，自己拿 5 组 (防御, 伤害) 数据拟合中性点 |
| **`defensePhysics / defenseMagic / ...`** | **死字段**：89 个真实部件的值全为 0（32 个占位行是 100）。AC6 真正的防御是"逐伤害类型的格挡减伤率 + AP + 姿态稳定"（§5.3 / §5.6） | 建表时**直接不导出这些列**（导出器的全零剪枝已经替你做了） |
| **武器表的 `attackBasePhysics`** | 它是"基本值"，游戏里大量行是 100/110 这种占位量级；**真正的伤害在 `AtkParam_Pc.atkPhys`**（非零 314/712，中位 **1300** ✅复现） | 武器表与攻击表**分开建**，靠 ID 关联（§4.2 的 DataTable 划分就是这么设计的） |
| ❌ 顺带一条 | Jiggler 的"**平移力是旋转力的 5 倍**" | 原文档标 **C**：两表量纲可能不同，中位比是 16.5 倍、上限比是 5.0 倍 | 只用定性结论"**平移项的参数空间明显更大**"，不报倍数 |

---

# 第 5 部分：卡住时怎么办

## 5.1 通用排查五步法（背下来，比任何教程都值钱）

| 步 | 动作 | 说明 |
|---:|---|---|
| 1 | **先看日志，不看画面** | `Window → Output Log`。只看带 `Error:` 的行 |
| 2 | **找第一条错误，不是最后一条** | 后面的错误往往是第一条的连锁反应 |
| 3 | **复制报错原文去搜** | 搜索时**带上 UE 版本号**（搜 `UE5.6 xxx` 比搜 `UE5 xxx` 准得多）。⚠️AI/搜索给的答案要先在**最小复现**里验证再用 |
| 4 | **做最小复现** | 新建一个**空关卡 / 空 Actor / 空项目**，只放"可能出错的那一件事"。能在空项目里复现 = 是引擎/版本问题；不能在空项目里复现 = 是你的项目里的东西在干扰 |
| 5 | **二分法定位** | 把节点/代码**注释掉一半**，看还坏不坏。坏 → 问题在被注释掉之后那半；不坏 → 问题在这半。**重复 3~4 次就能精确到一个节点** |

> **黄金法则**：**先证明"数据到了"，再怀疑"表现不对"**。
> 例：面板拖滑条没反应 → 先 `Print String` 打印滑条的 `OnValueChanged` 的 `Value`（证明滑条在工作）→ 再打印目标 Actor 的变量（证明赋值成功）→ 最后才怀疑靶子逻辑。

## 5.2 五类最常见的"新手卡死"

### 卡点 1：环境与启动（装完打不开 / 打开就崩 / 慢到怀疑人生）

| 项 | 内容 |
|---|---|
| **典型症状** | 报 RHI/D3D12/SM6；卡在 `Compiling Shaders` 一小时；驱动重启后崩溃；打开项目转圈 |
| **30 秒判断** | 看 Output Log 最后 20 行 + 看右下角是否有 shader 计数在动。**计数在动 = 正常，等着**；计数不动 + 无日志 = 真卡死 |
| **排查路径** | ① 显卡驱动是否为厂商官网最新 ② 显存/内存是否被其他程序吃满（任务管理器看）③ 试着新建一个**空项目**能否打开（能 → 是你的项目坏了；不能 → 是引擎/驱动问题）④ 引擎版本 Launcher 里 **Verify** 一次（修复损坏安装） |
| **最小复现** | 新建一个 Blank 空白项目能否秒开 |
| **去哪查** | Epic 官方论坛 / UE 的 AnswerHub 归档 / 报错原文搜索（带版本号） |
| **不要做** | ❌ 不要反复强杀进程重开（半成品 DDC 会让下次更慢）；❌ 不要一上来就重装引擎（先 Verify） |

### 卡点 2：蓝图报错（编译错误 / `Accessed None` / 运行时红字）

| 项 | 内容 |
|---|---|
| **典型症状** | 编译按钮变红带数字；PIE 时屏幕左上角红字 `Blueprint Runtime Error: ... Accessed None trying to read property ...` |
| **30 秒判断** | `Accessed None` = **你在用一个"空引用"**。90% 是：Actor 不存在、`Get All Actors Of Class` 返回空数组、`Create Widget` 失败、Cast 失败 |
| **排查路径** | ① 双击编译错误 → 跳到出问题的节点 ② 对每个引用加 `Is Valid` 判断 + `Print String` 打印它是空还是有效 ③ Cast 节点后接 `Cast Failed` 分支打印日志 ④ 确认 `Get All Actors Of Class` 的类选对了（选了基类会拿到一堆不想要的东西） |
| **最小复现** | 新建空关卡 → 只放一个 Actor → 只跑那一段节点 |
| **去哪查** | 报错原文 + 类名搜索；蓝图节点文档 |
| **不要做** | ❌ 不要用"多试几次/重启"当解法；❌ 不要忽略黄色警告（它们经常是 bug 的前身） |

### 卡点 3：CSV 导入 / DataTable（列没了、全 0、行名乱）

| 项 | 内容 |
|---|---|
| **典型症状** | 导入后某列全 0；某列在表里看不到；导入直接失败；行名变成一串数字 |
| **30 秒判断** | 用内容浏览器**导出该 DataTable 为 CSV** 看"官方格式"，与你的源 CSV 逐列对比 |
| **排查路径** | ① 列名逐字符比对（大小写/下划线/拼写错误都要一致）② 类型比对（float vs int）③ 编码（UTF-8 无 BOM，别用 Excel 存）④ 第一列是否叫 `Name` ⑤ 行名唯一性 |
| **最小复现** | 手写 2 行 × 2 列的 CSV（`Name,Value`）导入看能否成功 |
| **去哪查** | UE 文档搜 `DataTable CSV`；本项目 `tools/export_ue_datatables.py` 的输出格式就是标准答案 |
| **不要做** | ❌ 不要在 Excel 里编辑 CSV（BOM/小数点/分隔符三个坑同时来） |

### 卡点 4：PIE 里改了值没反应（"我改了啊"）

| 项 | 内容 |
|---|---|
| **典型症状** | CSV/面板改了，PIE 里靶子不动；重启 PIE 才好；有时好有时坏 |
| **30 秒判断** | **是否在 BeginPlay 缓存了值？** 这是第一嫌疑 |
| **排查路径** | ① 在读取处 `Print String` 打印**真实读到的值** ② 确认 Reimport 是否成功（表里能看到新值）③ 确认读的是**资产**不是**拷贝**（DataTable 资产在 PIE 里是共享的，但你自己抄进变量的副本不是）④ 面板滑条是否真的连到了目标 Actor（`Is Valid` + 打印目标引用）⑤ 输入模式是否被锁（鼠标点不到 = `Set Input Mode` 没设） |
| **最小复现** | 空 Actor + `Get Data Table Row` + `Print String`，改 CSV 重导后看打印 |
| **去哪查** | 本项目 §3.9 的"不缓存原则"；DataTable 的 Reimport 文档 |
| **不要做** | ❌ 不要"重启一下试试"——先搞清楚是哪一层断的（文件 → 资产 → 读取 → 使用） |

### 卡点 5：C++ / 编译环境（你迟早会撞上，M1 前解决）

| 项 | 内容 |
|---|---|
| **典型症状** | `The following modules are missing or built with a different engine version`；`Unable to find MSVC`；`Cannot open include file`；`LNK` 链接错误 |
| **30 秒判断** | 报错里出现 `MSVC` / `v143` / `Windows SDK` → 组件没勾齐；出现 `different engine version` → 项目与引擎版本不匹配 |
| **排查路径** | ① VS Installer 里核对 §1.5 的组件清单 ② 右键 `.uproject` → **Generate Visual Studio project files** ③ 删掉 `Binaries/`、`Intermediate/`、`Saved/` 后重生成 ④ 确认**项目路径全 ASCII** ⑤ 确认不是开着两个引擎版本 |
| **最小复现** | 新建 C++ 空项目能否编译（不能 = 环境问题；能 = 是这个项目的问题） |
| **去哪查** | Epic 文档 "Setting Up Visual Studio..."；报错原文（带 `UE5.x` 与 VS 版本号） |
| **不要做** | ❌ M0 阶段根本不要开 C++（这就是本文档把 M0 定为纯蓝图的原因）。撞上了就先退回蓝图项目把 M0 做完 |

## 5.3 明确**不要**做什么（违反一条，你的 M0 就会变成 M∞）

| # | 不要做 | 理由（出处） |
|---:|---|---|
| 1 | 第一个月就做 Niagara 大特效 | M0/M1 的目标是"能演示"，不是"好看"。原文档 §1.1 的顺序：先做穿 L1 |
| 2 | 一开始就写**自定义 AnimNode** | 那是 P20 项目 B（第 2 个月）的内容。M0 阶段你连骨架都没有 |
| 3 | 过早做**多人联机** | 原文档 §1.2 明确不做（`MultiPlayCorrectionParam` 相关一律跳过） |
| 4 | 涂装 / 贴花 / 徽章编辑器 | 原文档 §1.2 明确不做（除非你专攻 UI/图形） |
| 5 | 复刻**全部武器** | 原文档 §1.2：3~4 把覆盖三种伤害类型即可 |
| 6 | 照搬 **389 个字段** | 原文档 §4.1：真正要建模的浮点量约 15 个。你的结构体 20~30 个字段就够 |
| 7 | **从零猜数值** | 原文档第 4 章给了 B 级量级，照抄起步比猜快得多 |
| 8 | 用 **root motion** 驱动位移 | 原文档 §5.8.1（B 级三重证据）：AC6 不是根运动。M1 会用到，现在记住即可 |
| 9 | 只用**一个伤害值** | 原文档 §5.3：伤害与冲击力必须两条线，否则装配系统直接失去一半乐趣 |
| 10 | 把参数**硬编码**进蓝图 | 原文档 §7：硬编码 = 返工。"参数可在面板实时调"是每个里程碑的通用验收 |
| 11 | 在 M0 追求**美术资产** | 用方块/箭头/球。M0 的观众是"看数值在动"，不是"看画面" |
| 12 | 把**解包原始数据**提交到公开仓库 | 原文档 §0 原则 1 / §8：只提取结构与数值规律，不分发原始数据文件 |
| 13 | 连续 3 天不 commit / 不产出可展示物 | P20 的纪律："没有产出的一周就是不存在的周" |
| 14 | 边学边等"学完再做" | 本文档每一节的结尾都是"看到什么算对"。**每天必须有 1 个可见产出** |
| 15 | 同时开 3 个方向（学材质 + 学动画 + 学数据） | M0 只需要 §2.1 的 10 项。**范围爆炸是这类项目的第一杀手**（原文档 §8 风险表首行） |

## 5.4 时间安排上的现实提示

| 提示 | 说明 |
|---|---|
| 每天留 1 h 给"卡住" | >35 h/周 的强度下，卡住不是意外而是常态 |
| D10~D12 最容易崩 | 蓝图的引用/Cast 问题会在搭靶场时集中爆发。**崩了就用 §5.1 的五步法，不要重装编辑器** |
| 如果 D9 结束还没跑通"改 CSV → 生效" | **停下来**，只做这一件事。它是 M0 的唯一命门，别的都可以砍 |
| 可以砍的 | 靶子 4（重力）、预设切换、Tier 2、面板美化 |
| **不能砍的** | 数据层能打通 + 面板能实时改一个值 + 能录像演示 |

---

# 第 6 部分：M0 完成的判定清单

> **每条都是可观察的事实**，不是感觉。勾不上的一条都不许写进作品集。

## 6.1 硬清单

### A. 项目与环境

- [ ] 双击 `<UE_PROJECTS>\AC6Proto\AC6Proto.uproject` **30 秒内**能进入编辑器；Output Log **无 `Error:`**
- [ ] 路径里**没有中文、空格**（截图证明）
- [ ] PIE 里能操作（WASD+鼠标+空格 至少一个能动的对象）
- [ ] `stat fps` 在 M0 场景下 **≥ 60**，且打开/关闭调参面板的帧率差 **< 5 fps**

### B. 目录与版本管理

- [ ] 目录结构里有 `Content/AC6/Data/{Structs,Tables}`、`Tuning`、`Maps`、`data`、`tools`、`docs`
- [ ] `.gitignore` 里包含 `Binaries/ Intermediate/ Saved/ DerivedDataCache/` **且包含 `data/ue_datatables/`**
- [ ] `git log --oneline` 有 **≥ 6 条**有意义的 commit，每条对应一个产出
- [ ] `git ls-files | findstr /i ".param"` **输出为空**（证明没把原始数据提交进去）

### C. 数据层

- [ ] `Content/AC6/Data/Structs/` 下有 **≥ 4 个**结构体（Booster / Protector / Attack / CombatSettings）
- [ ] `Content/AC6/Data/Tables/` 下有 **≥ 5 个** DataTable，双击都能打开且**无红字警告**
- [ ] 每张表的**行名保留 AC6 溯源信息**（例：`DT_Booster` 里能看到 `BST_G2_P04`）
- [ ] 你能**指认出** `DT_Booster` 里的占位行（7 行 `*_Inherited`）并说出为什么它们是占位行（Weight=1 / QBEndSpeedKMH=500）
- [ ] `DT_Protector` 里 `AssembleMenuCategory=3`（手臂）的 `Stability` **全部为 0**（与原文档 §5.6 一致）
- [ ] `DT_Protector` 里**只有 3 行**的 `LegsBoosterId ≠ −1`（坦克腿）
- [ ] PIE 里能打印出形如 `DT_Booster[BST_G1_P10].QBReloadTimeSec = 0.6` 的一行（截图/录像）

### D. 调参面板

- [ ] 按一个键（Tab）能**打开/关闭**面板；打开后**鼠标能点滑条**
- [ ] 面板有 **≥ 4 个滑条**，每个都**真的改变**世界里某个东西的行为（不是只改数字）
- [ ] 每个滑条**范围来自数据推导**（截图证明：如 `QBReloadTimeSec` 是 0.30~0.91，不是 0~1）
- [ ] 每行显示 **参数名 + 当前值 + 单位 + 来源字段名**（例：`0.91 s ← DT_Booster[BUERZEL_21D].QBReloadTimeSec`）
- [ ] 「转速靶」把 `BaseTurnSpeedDPS` 从 400 拖到 230，能让第三人描述出"变笨重了"（录 5 秒对比）
- [ ] 「姿态靶」改 `ImpactLifeTimeSec` 1.5 → 0.5 后**几乎打不出硬直**（录 10 秒对比）
- [ ] 「QB 冷却灯」在冷却期内**按 Q 无效**（录 10 秒）

### E. 热重载（M0 的唯一命门）

- [ ] 改 `EquipParamBooster.csv` 一行 → Reimport → **不重启编辑器、不重编译** → PIE 里行为/数字变化
- [ ] 全过程**计时 ≤ 15 s**（Tier 2 做到 ≤ 5 s 加分）
- [ ] 面板上的 `重新读取数据表` 按钮可用（不是靠重启 PIE）
- [ ] 面板上的 `导出当前值` 按钮能打印出一行可粘贴回 CSV 的文本

### F. 文档与合规

- [ ] `AC6Proto/docs/参数表_v1.md` 里**每一条数值都带"出处章节 + 证据等级"**两列
- [ ] `AC6Proto/docs/参数表_v1.md` 里**至少 2 条标了 C/D**（证明你会区分"验证过的"和"猜的"）
- [ ] `README.md` 里有 **5 步跑起来**的说明（含路径、引擎版本、要装什么）
- [ ] **一个没参与的人**按 README 能在 10 分钟内打开项目并看到面板（找同学做，记录结果）
- [ ] 仓库里**没有任何解包原始文件**（`*.param`、`regulation.bin`）；README 有一句"机制分析与技术复刻，非资产复制"
- [ ] 有 **60~90 秒**的 M0 演示录像，按 §3.13 的脚本走完

### G. 你自己的能力（自评，用可观察的方式）

- [ ] 能不看笔记说出 **Actor 与 Component 的区别**（并各举一个 M0 里的例子）
- [ ] 能说出 `Get Data Table Row` 的 `Found` 为什么必须接
- [ ] 能说出"**为什么不把表值缓存进 BeginPlay**"
- [ ] 能在报错时**独立走完 §5.1 的五步法**（找个真报错演示一遍）

## 6.2 三条负向测试（**能定位 = 真的会了**）

| # | 故意搞坏 | 你应该能说出 |
|---:|---|---|
| 1 | 把 CSV 里某个列名改错一个字母（`QBReloadTimeSec` → `QBReloadTimeSecc`）再 Reimport | 报错长什么样；为什么值变成 0 而不是报错 |
| 2 | 把 `Get Data Table Row` 的 Row Name 改成一个不存在的行名 | 为什么**不会崩**、只会得到全 0；`Found` 在这里的作用 |
| 3 | 在 `BeginPlay` 把表值抄进变量，然后再改 CSV + Reimport | 为什么这次**不生效**（这就是"缓存"的代价） |

## 6.3 一句话验收台词 + 交付物清单

**台词（面试/汇报用，30 秒版）**：
> "我把一款商业游戏的 257 张二进制数据表，收敛成了 UE5 里 5 张可热重载的 DataTable，并做了一个调参面板：**改一行 CSV，不用重编译、不用重启，波形立刻变。** 每条数值我都标了来源章节和证据等级 —— 我知道哪些是我验证过的，哪些是我猜的。"

**交付物清单**：

| # | 交付物 | 状态 |
|---:|---|---|
| 1 | `AC6Proto` 项目（蓝图，可双击打开） | ☐ |
| 2 | Git 仓库 + `.gitignore` + ≥ 6 次 commit + README | ☐ |
| 3 | `Content/AC6/Data/` 下 ≥ 4 Struct + ≥ 5 DataTable | ☐ |
| 4 | `WBP_TuningPanel` + `L_TuningRange`（4 个可视靶子） | ☐ |
| 5 | `AC6Proto/docs/参数表_v1.md`（带出处 + 等级） | ☐ |
| 6 | 60~90 秒演示录像 | ☐ |
| 7 | （加分）Tier 2 一键重导 + 表加一行 → 面板自动多一行 | ☐ |

---

# 附录 A. 命令速查（本项目内已验证）

```bash
# 0) 项目数据终校：当前实际输出 203 / 203 通过
#    ⚠️ 断言数会随着脚本扩充而增长。以「实跑结果」为准，不要在文档里硬写死数字；
#       历史文档里若出现 141/167/175/180 等，都是早期版本的过期值。
cd <repo>
python tools/verify_doc.py

# 1) 导出 UE5 可导入的 CSV（M0 主命令）
python tools/export_ue_datatables.py --starter
#    → data/ue_datatables/*.csv + *.struct.txt
#    → 我在临时目录复跑过：与仓库内现有产物逐字节一致

# 2) 列出脚本支持的表名（找不到表名时用）
python tools/export_ue_datatables.py --list

# 3) 补导 M1 要用的表
python tools/export_ue_datatables.py ChrActTurnParam MovementAcTypeParam TentativePlayerParam
python tools/export_ue_datatables.py JigglerBehaviorParam JigglerBehaviorSlideParam

# 4) 保留全部列（不剪全零列）—— 想让 UE 表"忠实反映源数据"时用
python tools/export_ue_datatables.py --keep-all --prune-const

# 5) 单字段现场取证（同时打印"全体/非零"两种口径，防口径陷阱）
python tools/check_field.py EquipParamProtector EquipParamProtector legs_boosterId
#    → 121 行 / 行宽 900 B / 偏移 584 / s32
#    → 唯一值 [-1, 63300000, 63340000, 63360000]

# 6) 位域字段专用（按整字节读会得到完全相反的结论）
python tools/check_bit.py Bullet BulletParam isEnableAutoHoming
```

**判据**：命令 1 的输出里每行都应该有 `-> xxx.csv`；若某表显示 `跳过`，说明 paramdex 无该表定义或数据里无此表。

# 附录 B. 命名规范（M0 就定死，后期免重构）

| 类型 | 前缀 | 示例 |
|---|---|---|
| 结构体 | `S_` | `S_BoosterRow` |
| DataTable | `DT_` | `DT_Booster` |
| Data Asset | `DA_` | `DA_CombatSettings` |
| 曲线资产 | `C_` | `C_TurnRate` |
| 蓝图 Actor | `BP_` | `BP_TuningRig` |
| UMG 控件 | `WBP_` | `WBP_TuningPanel` |
| 关卡 | `L_` | `L_TuningRange` |
| 材质 / 材质实例 | `M_` / `MI_` | `MI_Placeholder` |
| 函数/变量 | PascalCase，**不加类型前缀**（UE 惯例） | `BaseTurnSpeedDPS` |

**DataTable 行名规范**：**优先沿用 AC6 行名**（`BST_G2_P04` / `LEGS_KASAR_42Z`）——这是你的溯源能力，别改成 `Row1`。

# 附录 C. 本文档的不确定项汇总（照这个清单自己核实）

| # | 我说的 | 不确定点 | 怎么自验 |
|---:|---|---|---|
| 1 | 装哪个 UE 版本 | 我无法联网确认此刻 Epic 提供的确切版本 | Launcher 列表看是否带 `Preview`；查 Release Notes 发布日期 |
| 2 | 安装选项名称与勾选框 | 各版本命名有差异 | 以弹窗实际显示为准；任何项都能事后在 Launcher 改 |
| 3 | 磁盘占用数字 | 我只给了量级 | 以 Launcher 显示的 Download/Install Size 为准 |
| 4 | 项目模板列表（Third Person 变体） | 新版本可能新增 `Motion Matching` 等 | 选最普通那个；判据是能 PIE 到角色 |
| 5 | VS 最低版本要求 | 随引擎版本变化 | Epic 文档 "Setting Up Visual Studio…" |
| 6 | DDC 设置入口 | 菜单路径随版本变化 | 用 Editor Preferences 的**搜索框**搜 `Derived Data`；或改用环境变量 `UE-LocalDataCachePath` |
| 7 | Reimport 按钮位置 | 有的在资产右键菜单，有的在打开的编辑器工具栏 | 两处都找；判据是点了之后表里的值真的变 |
| 8 | 蓝图侧写文件节点 | 节点名/可用性随版本变化 | 节点搜索框输 `Save String` 看有什么 |
| 9 | `reimport_asset` Python API 名 | 可能改名或需要 `AssetImportTask` | 已在 §3.12 给了 `dir()` 打印脚本 —— **先跑它，别背 API** |
| 10 | Output Log 的 Python 下拉 | 需先启用 Python 插件并重启 | 下拉里没有 Python = 插件没启用 |
| 11 | CSV 里 bool 的写法 | 我建议 `True/False` | 若报错就换成 `True/False`，或在结构体侧改用 int |
| 12 | 第一列标题 `Name` vs `RowName` | 版本差异 | 导出器已用 `Name`；真出错就试 `RowName`；或**导出引擎自己的 CSV 看格式** |
| 13 | 退 DX11 的具体设置项名 | 路径随版本变化 | Project Settings 里**搜索 `RHI`** |
| 14 | 硬直阈值表的语义 | 原文档未标等级（字段存在是 B，语义是 C/D） | 用 `tools/check_field.py` + 游戏内实测交叉验证 |

---

## 附：本文档对原文档的三处显式偏差（诚实记录）

| # | 原文档说 | 本文档说 | 为什么 |
|---:|---|---|---|
| 1 | §7：M0 验收"改 CSV → 运行时生效" | 量化为 **≤ 15 s 且不重编译/不重启**（Tier 2 ≤ 5 s） | 零基础读者用"手动 Reimport"的实际耗时做不到 <2 s；把验收线定到可实现的范围。**✅ 用户已确认（2026-09-11）** |
| 2 | §7：M0 建议周期 1 周 | **D6~D17 ≈ 2 周**（含 D1~D5 基础共约 3 周） | 读者 UE5 熟练度为 0，1 周不现实；本文档把"1 周"理解为**已有 UE 基础的人**的估计。**✅ 用户已确认（2026-09-11）** |
| 3 | 本文与 README/§C.1 的断言数 | **203/203（实测）** | 已由主 agent 统一为 180 |

---


---

## 附三：本机环境实测结果（2026-09-11 22:20，父 agent 实际跑出来的）

> **这一节的每个结论都是实测的**，不是建议或推测。你的环境已经搭好了。

### 已安装的东西

| 组件 | 路径 | 版本 | 状态 |
|---|---|---|---|
| **UE5.8** | `<UE_ENGINE>` | **5.8.2**（CL 56702186，Release 正式版） | ✅ 已下载完成（31 GB） |
| **VS2022 Community** | `<VS2022>` | **17.14**（MSVC **14.44.35207**） | ✅ 本次新装（5.29 GB） |
| VS2026 BuildTools | `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools` | 18.5（MSVC 14.50.35717） | ✅ 你原有的，**也在用** |
| Windows SDK | `C:\Program Files (x86)\Windows Kits\10` | **10.0.26100.0** | ✅ 已满足 UE5.8 要求 |

### UE5.8 的官方要求 vs 你的环境（已逐条核对）

来源：`<UE_ENGINE>\Engine\Config\Windows\Windows_SDK.json`

| 要求项 | UE5.8 要求 | 你的环境 | 结论 |
|---|---|---|---|
| VS2022 最低版本 | **17.8** | 17.14 | ✅ |
| VS2026 最低版本 | **18.0** | 18.5 | ✅ |
| 必需工作负载 | `NativeDesktop` + `NativeGame` | 都已安装 | ✅ |
| UE 集成组件 | `Component.Unreal.Ide` + `Component.Unreal.Debugger` | 已装（`VC.Ide.UnrealEngineTools.Interfaces` / `CodeLens` / Unreal 项目模板都在） | ✅ |
| VS2022 工具集 | `VC.14.44.17.14` | **14.44.35207** | ✅ |
| Windows SDK | ≥ 0xA00 (Win10) | 10.0.26100.0 | ✅ |

### ★ 一个重要发现：UE5.8 默认用 VS2026 编译，不是 VS2022

实测编译日志（父 agent 建了个最小 C++ 项目真编译过）：

```
# 默认情况 —— UBT 自动选了 VS2026
Using Visual Studio 14.50.35730 toolchain
  (C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717)

# 加 -Compiler=VisualStudio2022 —— 才用你新装的 VS2022
Using Visual Studio 2022 14.44.35228 toolchain
  (<VS2022>\VC\Tools\MSVC\14.44.35207)
```

**这意味着什么**：
- **编译器你早就有**（VS2026 BuildTools 一直能编译 UE）——所以之前"没装 VS2022"并不影响编译
- **VS2022 的价值在 IDE**：`devenv.exe`、调试器、Unreal 项目模板、CodeLens 导航、蓝图调试关联。这些是 BuildTools **没有**的
- **日常不需要管这个**：UBT 自动选哪个都能编过（两条路都实测通过）
- 只有当你**明确要用 VS2022 的编译器**时，才加参数：`-Compiler=VisualStudio2022`

### 工具链已验证可用（端到端）

父 agent 建了一个最小 C++ 项目 `J:\UE_test\ToolchainCheck`，完整跑通了：

| 步骤 | 命令 | 结果 |
|---|---|---|
| 生成项目文件 | `UnrealBuildTool.dll -ProjectFiles -Project=...` | ✅ `Result: Succeeded`（9.2 秒），生成 `.sln` + `.slnx` |
| 编译（默认工具链） | `UnrealBuildTool.dll ToolchainCheckEditor Win64 Development -Project=...` | ✅ `Result: Succeeded`（**79 秒**，7 个 action） |
| 编译（强制 VS2022） | 同上 + `-Compiler=VisualStudio2022` | ✅ 通过，用 14.44 工具链 |

**产物**：`UnrealEditor-ToolchainCheck.dll` 已生成。

> **这个测试项目保留着**，以后想验证"环境还正常吗"可以直接重跑：
> ```bash
> cd /j/UE_5.8
> Engine/Binaries/ThirdParty/DotNet/10.0/win-x64/dotnet.exe \
>   Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll \
>   ToolchainCheckEditor Win64 Development \
>   -Project="J:\UE_test\ToolchainCheck\ToolchainCheck.uproject" -WaitMutex
> ```

### ⚠️ 坑 0：从某些终端启动 VS2022 会直接崩溃（2026-09-11 实测并定位）

**症状**：

> 由于出现错误，无法启动 Visual Studio。
> `System.ArgumentException: 已添加项。字典中的关键字:"no_proxy"所添加的关键字:"NO_PROXY"`

**这不是你的 VS 装坏了。** 是**启动它的那个终端**往里传了一份含重复键的环境变量。

**根因**（有代码位置）：DSH 宿主加载的 `@deepseek-ai/dsh-http-proxy` 会**故意**把代理变量按大小写各写一份——

```js
// node_modules/@deepseek-ai/dsh-http-proxy/lib/index.js:31-32
noProxy: ["no_proxy", "NO_PROXY"],          // 成对写入，为了兼容只认某一种大小写的库
// lib/index.js:368-369
process.env[name] = value;                   // ← 于是 http_proxy 与 HTTP_PROXY 同时存在
```

Windows 的环境变量**查起来大小写不敏感**，但**可以同时存两个大小写不同的条目**。.NET 在构建环境字典时用大小写不敏感的哈希表 → 撞上重复键 → 抛异常。VS 启动时正好要读这个字典，**必崩**。

**怎么判断你会不会中招**：

| 启动方式 | 环境块 | 结果 |
|---|---|---|
| 桌面/开始菜单双击、任务栏 | 继承 explorer，**干净** | ✅ 正常 |
| 编辑器/IDE 里直接运行 | 取决于父进程 | ✅ 一般正常 |
| **某个被注入了代理变量的终端**（如 DSH 的 bash 工具） | **有重复键** | ❌ **崩溃** |

**一条命令自检**——如果这条命令报 `已添加项`，你所在的终端就有这个问题：

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -match 'proxy' }
```

**如果你想从这个终端启动 VS**，用附带的清理启动器（`tools/launch_net_clean.ps1`）：

```powershell
# 清掉重复的大小写变量后再启动（代理仍然生效，只去掉歧义的那一份）
powershell -NoProfile -File tools\launch_net_clean.ps1 `
  -Exe '<VS2022>\Common7\IDE\devenv.exe'
```

**同样的坑还会影响**（凡是会构建大小写不敏感环境字典的 .NET 程序）：
- `devenv.exe`（VS2022）—— **实测会崩**
- PowerShell 自己的 `Env:` 驱动器 —— **实测会崩**
- `UnrealVersionSelector.exe`（右键 `.uproject` → Generate Visual Studio project files 用它）—— 未实测，但同属 .NET Framework，**建议也走启动器**
- ❌ **不受影响**：`MSBuild.exe`（实测正常）、`UnrealBuildTool.exe`（.NET 8，此前端到端编译已成功）、`UnrealEditor.exe`（原生 C++）

> **实测对照（同一台机器、同一个时刻）**：
> ① DSH bash 直接 `Start-Process devenv.exe` → **崩溃**（弹错误框）
> ② 经 explorer 启动 → **正常**
> ③ 用 `tools/launch_net_clean.ps1` 清理后启动 → **正常**（进程健康、无错误框、`IsHungAppWindow=False`）

### 所以你现在可以直接开始 直接从第 2 部分（最小必要知识）开始，然后进第 3 部分的 M0 任务书。

**唯一要注意的**：UE5.8 首次打开编辑器会**编译着色器**，可能卡 5~20 分钟（进度条不动是正常的）。之后就好了。

## 附二：数据合规（用户已确认 2026-09-11）

**用户已确认：解包派生数据写死 .gitignore，不 push。**

项目根目录已放置 `.gitignore`，其中明确排除：

| 类别 | 排除内容 |
|---|---|
| ① 游戏原始数据 | `*.param` / `*.paramdef` / `*.dcx` / `*.bnd` / `*.bdt` / `*.bin` / `regulation*`、`unpacked/`、`regulation-bin/`、`pdef/` |
| ② 数据派生内容 | **`data/ue_datatables/`**（UE 导入用的 CSV）、`data/injected/` |
| ③ 过程产物 | `_scratch/`、`__pycache__/`、`*.pyc` |
| ④ UE5 工程产物 | `Binaries/` `Build/` `DerivedDataCache/` `Intermediate/` `Saved/` `.vs/` `*.sln` |

**仍可提交的**（是结构与统计，不含原始资产）：`param_tables_*.csv`（行数/行宽）、`param_系统映射.md`、`字段参考.md`、`装配界面规格书.md`、`tools/`、`data/`、`docs/`、`prompts/`。

**作品集里的说明话术**（建议直接抄）：
> 「本项目是对《装甲核心6》**机制与数据结构**的分析与技术复刻实践。所有游戏数据仅在本机用于学习研究，未随项目分发；作品集展示的是我自建的解析工具、分析文档与 UE5 实现，不含任何 FromSoftware 的资产、音频或文本。」
