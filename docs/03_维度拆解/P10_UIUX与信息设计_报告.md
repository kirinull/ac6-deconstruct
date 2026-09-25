# 《装甲核心6：境界天火》界面与信息设计拆解（P10 · UI/UX + 技术 UI 方向 TA）

> 读者设定：大四，目标技术美术（TA），计划从策划岗入门。
> 证据等级：**A** 游戏内可直接观察 / **B** 官方或社区数据（本机 AC6 专用 paramdex 解出的字段定义 + 对 regulation 数据表的实际取值复核）/ **C** 同类游戏与工程惯例的合理推断 / **D** 不确定（附验证方法）。
> 本报告出现的每一个"表名 · 字段名 · 数值"，都是本机 `<WORKSPACE>/tools/WitchyBND/Assets/Paramdex/AC6/` 的字段定义对上 `<WORKSPACE>/ac6_merge/van/regulation-bin/*.param` 的真实读取结果；命令与原始输出见 **§11 实测证据**。凡是没跑过的，一律标 C/D，不写"实测"。

---

## 0. 结论先行（12 条）

1. **AC6 的 UI 不是"画出来的"，是"配出来的"。** 整套前端由一组 `Menu*` 数据表驱动：`MenuPropertyLayoutParam`（**2512 行 × 32 字节**）用字符串 `LayoutPath` 描述 **125 个界面槽位**，`PropertyID` 指向 `MenuPropertySpecParam`（**508 行 × 108 字节**）里的 **508 条属性定义**。改界面布局 = 改表，不改代码。**[B]**
2. **信息密度的第一手段不是"隐藏"，是"状态驱动显隐 + 边缘化 + 颜色/尺寸分级"。** 屏幕中心只保留"我现在能不能打"（锁定框/准星/伤害数字），机体状态与弹药被推到边缘；脱离战斗后按表里写死的秒数淡出。HUD 的**全部时间常量集中在 `MenuParam` 这一张只有 1 行 × 424 字节的表里**。**[B]**
3. **锁定是"信息即玩法"的最纯样本。** 软锁与硬锁共用一套**屏幕空间候选区**：水平 45%、垂直 55% 的画面比例（`TentativePlayerParam.lockRangeHorizontalScreenRatio / lockRangeVerticalScreenRatio`）。能不能锁上，取决于距离（通常锁 450 m、导弹锁 280 m）与输入长按（0.5 s 进入多锁）。**UI 上"能不能锁"这件事，本质是数值的可见化。** **[B]**
4. **装配界面的实时性来自"引用式数值提取"，不是"复制一份数值"。** `MenuPropertySpecParam` 的 `extract0_Target / extract0_MemberTailOffset / extract0_Operation / extract0_Constant0/1` 五个字段构成一条"取数配方"：从哪张表、哪个字节偏移、套什么公式取值。508 条里 **105 条在使用**（20.7%）。例：`【武器】衝撃力` → `AtkParam @528 impactPower × 100`。**[B] ☜ 本维度最有价值的一条线索**
5. **同一份数据要喂三种精度的界面。** 属性布局里有 **237 行带 `Simple` 前缀**的"精简版"（`Simple HEAD - AP`、`Simple CORE - Weight`…），与全量版并存 → 列表页只显示 3–4 个数，详情页显示十来个。**信息层级是数据层实现的，不是代码分支。** **[B]**
6. **约束可视化是全表最"组件化"的部分。** `【PC】積載限界超過 / 腕部積載限界超過 / 使用不可データ含` 这组警告（PropertyID 29901/29902/29903）在 **4 个不同界面**（布局行 15001/16011/17031/18027）以 `Warn_0/1/2` 三个槽位复用；`TotalWeight`（積載状況）与 `TotalConsumeEN`（EN消費状況）在 **3 个界面**复用。**一个组件，多处挂载——这正是现代 UI 框架的思路。** **[B]**
7. **★ 关键突破：`extract0_MemberTailOffset` 是"字段末尾偏移"，不是"字段起始偏移"。** 取数地址应为 `MemberTailOffset − sizeof(extract0_MemberType)`。按此规则：**105/105 条记录全部落在 paramdex 的真实（非填充）字段上，且 105/105 条声明的原始类型与目标字段类型完全一致**（`u16`↔`u16`、`f32`↔`f32`…）。若按"起始偏移"朴素理解，只有 6/105 落在语义吻合的字段上，其余会读到 `pad*` 填充字段或错位字段。**这是一个真实的 TA 踩坑样本：我第一遍就是按"首偏移"读的，得到"14% 的配方已失效"的错误结论；修正偏移语义后错误率归零。** **[B]**
8. **AC6 没有难度选项，但它有一整套"难度旋钮"藏进玩法与选项里**：`【ゲームオプション】ロックオン自動切換`（自动锁定切换）、`オートパージ`、`アサルトブースト操作`（长按/切换）、自动装配（`【自動アセン】`）。这是"把难度交给玩家自己的配置而不是菜单"的取向。**[B]**
9. **可及性选项的总量是可数的：整个选项菜单 = `MenuPropertySpecParam` 里 PropertyID 落在 90000–91000 区间的 62 条。** 其中与可及性直接相关的只有：字幕显示（`90020` ON/OFF）、HUD 颜色（`90022` 按钮）、HUD 布局（`90023` 按钮）、按键重映射（`90090` 预设 + `90091` 详细）、键鼠设置（`90101–90104`）、操作提示设备（`90100`）。**没有字号设置、没有色盲模式。** **[B]**
10. **HUD 布局编辑器是真实存在的功能，且是数据驱动的。** `MenuInputGestureParam` 里有 `9201 HUD：位置X / 9202 位置Y / 9204 缩放X / 9205 缩放Y / 9206 不透明度` 五个手势条目；`MenuValueTableParam` 里有 `【オプション】HUDレイアウト：デフォルト / カスタム1 / カスタム2 / カスタム3` → **4 个布局槽位，可调位置、缩放、透明度。** **[B]**
11. **菜单本身也要渲染 3D。** `MenuOffscrRendParam`（140 行 × 80 字节）为每个菜单场景配一套**离屏相机**（注视点、距离、FOV、距离/角度限位）；其中 **73 行 GparamID=1010 是 AC6 专有的"机体"用机位**，另 67 行是从魂系继承来的角色预览机位。`MenuPartsModelRendParam`（14 行）给**每个部件类别**配初始模型角度（`10000 AM_M`=右臂 / `20000 BD_M`=机体 / `30000 HD_M`=头 / `40000 LG_M`=腿 / `50000 BS_A`=推进器 / `60000/70000/80000 WP_*`=武器）。**[B]**
12. **TA 在这个体系里的职责不是"画 UI"，是"造管道"**：表结构设计 → 取数配方 → 字段语义注册表 → 布局数据到控件的绑定 → 一致性校验 CI → UI 批处理与 3D 混排。**§10** 给出完整组件实现思路。

---

## 1. 数据驱动 UI 的证据（表清单）

以下全部为 `python tools/paramdex_fields.py <表名>` 的输出（结构大小与实际行宽逐表比对，全部 `SIZE MATCH`）：

| 表名 | 行数 × 行宽 | 作用（从字段名 + 开发者行名推断） | 等级 |
|---|---|---|---|
| `MenuPropertyLayoutParam` | **2512 × 32** | 界面槽位表：`LayoutPath`(16B 定长串) + `PropertyID` + `CaptionTextID` + `HelpTextID` + `DisplayCondition` | B |
| `MenuPropertySpecParam` | **508 × 108** | 属性定义表：文本/图标/优劣判定/格式/编辑类型/取数配方（extract0/1） | B |
| `MenuValueTableParam` | **270 × 12** | 枚举值 → 文本ID 映射（比较类型：相等/大于等于/恒真/定义数） | B |
| `MenuColorTableParam` | **882 × 4** | UI 调色板：RGBA（**225 种不同颜色**） | B |
| `MenuBehaviorParam` | **31 × 32** | **前端画面注册表**（ASSEMBLY / TRIAL FIT / BUY / SELL / OS TUNING / AC TEST / PAINT / DECAL / AC DATA / MISSION / ARENA …）+ 教程ID + 帮助菜单开关 | B |
| `MenuInputGestureParam` | **175 × 16** | 输入手势 → 提示文本 + SE（172/175 条有提示文本，37 条有 SE） | B |
| `MenuOffscrRendParam` | **140 × 80** | 菜单离屏渲染机位（含 3D 预览相机全套参数） | B |
| `MenuPartsModelRendParam` | **14 × 4** | 部件 3D 预览初始角度（按部件类别） | B |
| `MenuFilter` | **28 × 52** | 菜单后处理滤镜（噪点/对比度/中央减淡） | B |
| `KeyAssignDisplayParam` | **58 × 32** | 键位显示项（可解绑 55 / 可改手柄 50 / 可改鼠标 50 / 可进配置菜单 28） | B |
| `KeyAssignMenuItemParam` | **24 × 16** | 键位菜单项 | B |
| `ActionButtonParam` | **144 × 112** | **世界空间动作按钮**（圆柱判定区 + 图标 + 优先级 + 灰化/无效标志） | B |
| `MessageBoxParam` | **141 × 24** | 消息框类别 + 是否暂停 + 单机/联机行为控制 | B |
| `MenuParam` | **1 × 424** | **全局 FE/HUD 时序与阈值单例表** | B |
| `GraphicsParam` | **1 × 200** | 菜单背景模糊淡入淡出、子窗口尺寸 (576×324)、缩放模糊 | B |
| `TutorialParam` | **201 × 48** | 教程弹窗（吐司/模态两种资源类型 + 图片 + 按键引导 4 行 + 解锁 flag） | B |
| `EquipmentMenuManageCategoryParam` | **110 × 32** | 装备列表分类 → `PropertyLayoutID`（**49 个不同布局**） | B |
| `PlayerColoringPresetParam` | **6 × 392** | 涂装预设（6 套；每套 20 个色槽 × 5 通道，另有 14 个 slot 定义） | B |

**架构含义（结论）**：AC6 的前端是 **"表 → 绑定 → 视图"** 的三段式。表里没有任何一个像素坐标（`LayoutPath` 是 `Item_00`、`TopItem_3`、`Warn_0` 这种**语义槽位名**），坐标在引擎侧的界面资源里；表负责的是**"这一屏显示哪些属性、按什么顺序、什么条件下显示、怎么取数"**。这意味着：

- 策划/设计师可以**在不碰引擎工程的前提下**调整属性组合、顺序、显示条件、数值格式；
- 同一份属性定义可以被多个界面复用（`【アイテム共通】重量` 在 95 个槽位出现，`【アイテム共通】消費EN` 93 个，`【射撃攻撃】攻撃性能` 73 个）；
- **代价**是"偏移语义一旦被误解，UI 会安静地显示错数字"（见 §0 第 7 条与 §5.2）。

---

## 2. HUD 元素清单与信息层级

> 说明：**屏幕坐标不在数据表里**（在界面资源中），因此"位置"一列标 A（游戏内可观察）。**更新频率**除有表证据者外标 C（推断）。**可关闭性**来自选项表（B）与 HUD 布局编辑器（B）。

| 元素 | 位置（A） | 更新频率 | 紧急度 | 可关闭性 | 数据来源（B） | 等级 |
|---|---|---|---|---|---|---|
| **AP 条**（机体耐久） | 屏幕角落 | 受击时跳变，1.5 s 后开始淡出 | 高（<30% 触发低血量 FE） | 可调位置/缩放/透明度 | `MenuPropertyID 3000【防具】AP`；`MenuParam.FE_LowHP_rate = 30`（%）；`HpBarFadeOutTime = 1.5 s`；`ZeroHpBarFadeOutTime = 0.3 s` | A/B |
| **姿态/冲击条（ACS 积累）** | 敌我分置，贴近各自机体 | 连续（每帧） | 极高（决定反击窗口） | 部分（同属 HUD 布局体系） | `TentativePlayerParam.bodyTrunk_BodyGaugePoint / bodyTrunk_ActionGaugePoint`；`EnemyCommonParam` 同名；`MenuParam.VolatilizeFadeBeginSec = 0.8 s`（瞬間衝撃ゲージ淡出开始）、`VolatilizeCombineSec = 0.4 s`（结合时间） | B |
| **EN 条 / EN 消费状况** | 边缘，靠近 AP | 连续 | 高 | 同 HUD 布局 | `MenuPropertyID 20012【PC】EN消費`、`20015【PC】EN消費状況`（布局槽位 `TotalConsumeEN`，3 处复用） | B |
| **四武器槽 + 弹药** | 左右下角分组 | 换弹/开火时 | 中高 | 同 HUD 布局 | `MenuEquipCategory` TDF 列出 `機体構成 R-ARM UNIT / L-ARM UNIT / R-BACK UNIT / L-BACK UNIT`；`MenuPropertyID 2000【武器】装弾数`（63 个槽位复用）、`10014【弾丸】弾単価` | B |
| **锁定框 / 锁定站点（ロックサイト）** | 屏幕中心偏上 | 连续（插值 0.15） | 极高 | 不可关（玩法核心） | `TentativePlayerParam.LockSiteWidthScale = 2.0 / LockSiteHeightScale = 1.3`；`lockCamParamLerpRate = 0.15`；每把武器还有自己的 `lockSightWidthScale/HeightScale`（`EquipParamWeapon`） | B |
| **锁定光标（不可射击态）** | 锁定框本体 | 状态切换 | 高 | 不可关 | `MenuParam.DisableLockCursorAlpha = 40`（射不可时的 alpha，0–255 尺度） | B |
| **导弹锁定进度 / 多锁标记** | 锁定框周围 | 长按 0.5 s 后逐格点亮 | 高 | 不可关 | `triggerContinueTimeToMultiLock = 0.5 s`；`missileLock_MaxLockNum = 4`；`multiLockTaretNumMax = 10`；`missileLock_MaxDist = 280 m` | B |
| **目标标记（マーキング）** | 屏幕内敌方机体的浮标 | 捕获/超时 | 中 | 不可关 | `LockTargetMarking_ChachDist = 600 m`、`ChachAngleDeg = 30°`、`TimeOutSec = 2.0 s`、`ForgetDist = 700 m`；屏内绘制范围 `MenuParam.MakerRendRangeWidth = 1650 / Height = 650`（FullHD 基准） | B |
| **索敌状态图标（Search / Battle）** | 敌方标记上 | 状态切换后 2 s | 中 | 不可关 | `MenuParam.TargetStateSearchDurationTime = 2.0 s`、`TargetStateBattleDurationTime = 2.0 s`、`EnemySearchIconFadeOutTime = 1.0 s` | B |
| **雷达 / 迷你地图** | 角落 | 连续 / 可切换间隔 0 s（即常显） | 中 | 同 HUD 布局 | `MiniMap_WorldDispRange = 1200 m`、`MiniMap_RaderRange = 2000 m`、`MiniMap_ChangeInterval = 0.0 s`；3D 小地图各图标缩放（玩家 10 / 目标点 5 / 敌 3 / 补给点 6 / 弹射器 6 / 路线 10 / 塔·城市 0.3） | B |
| **伤害数字** | 命中点/目标身上 | 命中瞬间，**0.5 s 内累积合并** | 中（仅自检输出） | 无独立开关 | `MenuParam.FE_ShowDamageAccumulationTimeSec = 0.5 s`（**累积时间**）、`HitFEViewTime = 1.0 s` | B |
| **被弹警告（Danger）** | 屏幕边缘 | 受击后 2 s | 高 | 无 | `MenuParam.DangerFEViewTime = 2.0 s`；大伤害判定 `FE_LargeDamageDetect_HP_rate = 100 %`、`FE_LargeDamageDetect_CollectTime = 2.0 s` | B |
| **敌方射击预兆（射撃予兆）** | 敌方机体上的 dummy poly 位置 | 开火前 | 极高 | 无 | `AttackActionParam.shootIndicationType`（枚举：なし=0 / **強射撃予兆=1**）、`shootIndicationDmypolyId`（**挂在 dummy poly 上，偏移 80**）；`alertShowType`（トリガー=0 / 出さない=2）、`alertLevel`（小=0 / 大=1） | B |
| **任务目标 / 作战区域线** | 世界空间 + 屏幕 | 连续 | 中高 | 无 | `FE_MissionRegionStartLineDist = 200 m`、`LineDist = 100 m`、`LineHeight = 3 m`、`TexTile = 10 m`、`HeightOffset = 12 m`、`AddBlend = 1`、`UseSfx = 0`；`FE_MissionLine_Width = 300 m` | B |
| **作战区域警告线** | 世界空间 | 进入阈值后 | 高 | 无 | `FE_MissionLineWarningStartLineDist = 200 m`、`WarningLineDist = 100 m`；另 `MiniAreaParam.warningLineStartDisplayDistance / warningLineDisplayDistance` | B |
| **作战区域边缘装饰** | 世界空间 | 连续 | 低 | 无 | `FE_RegionEdgeTexWidth = 30 m`、`Height = 8 m`、`OffsetY = -1`；`FE_RegionEdgeSfxHideDist = 12 m`、`FadeDist = 6 m` | B |
| **区域上下限判定** | 无 UI，纯逻辑 | 连续 | 中（越界惩罚） | 无 | `FE_Region_UpperLimitDist = 50 m`、`LowerLimitDist = 100 m` | B |
| **物品获取日志** | 边缘，逐行滚 | 每行 6 s | 低 | 无 | `MenuParam.ItemGetLogAliveTime = 6.0 s` | B |
| **骇入进度条** | 屏幕中下 | 连续 | 高（仅在骇入场景） | 无 | `MenuParam.HackingGaugeFadeOutTime = 1.0 s` | B |
| **动作面板（ActionPanel）** | 屏幕边缘 | **速度阈值 0.5 m/s 才切换** | 中 | 无 | `MenuParam.ActionPanelChangeThreshold_Vel = 0.5 m/s`、`_PassTime = 0.0 s` | B |
| **世界动作按钮（拾取/骇入/补给）** | 世界空间，附着在目标上 | 进入圆柱判定区 | 中 | 无 | `ActionButtonParam`：`regionType` 全部为「円柱」、`textBoxType` 全部为「アクションボタン」；`raycastType`：常に判定する 119 / 実行範囲外のみ判定 22 / 判定しない 3；`iconID` 分布：通常 77 / ハッキング 25 / ハッキングLv3 24 / Lv2 17 / 補給 1 | B |
| **コーラル（Coral）演出** | 全屏/局部 | 状态触发 | 中（视觉威胁提示） | 无 | `CoralFeWeak/Strength_FE_*`：滚动速度、显示宽度、淡入时间（**0.3 s**）、RGBA 四通道各有独立字段 | B |
| **画质/亮度选项的 HUD 关联** | — | — | — | 可关 | `90024 HDR`、`90025 輝度調整`、`90026 画質調整` | B |

**信息层级（按"玩家必须看"排）**：中心区 = 锁定框 / 准星 / 射击预兆 / 伤害数字；近中心 = 姿态条（敌我）；边缘 = AP / EN / 弹药 / 雷达；世界空间 = 目标标记 / 区域线 / 动作按钮；全屏 = Coral / Danger 闪边。

---

## 3. 信息密度管理：屏幕同时几十个数字为什么不崩

### 3.1 状态驱动的显隐（时间常量全部集中，可整体调参）

**设计意图**：HUD 不是"常显的仪表盘"，是"事件驱动的提示层"。玩家没有在看的东西，不该占用屏幕。
**实现手段**：所有淡出/停留时长都写在 `MenuParam`（**1 行 × 424 字节**）里，代码只读不写死：

| 通道 | 常量 | 实测值 |
|---|---|---|
| 敌我血条淡出 | `HpBarFadeOutTime` | **1.5 s** |
| 归零血条淡出 | `ZeroHpBarFadeOutTime` | **0.3 s** |
| 瞬间冲击条淡出 / 结合 | `VolatilizeFadeBeginSec` / `VolatilizeCombineSec` | **0.8 s** / **0.4 s** |
| 命中 FE 停留 | `HitFEViewTime` | **1.0 s** |
| 被弹 Danger 停留 | `DangerFEViewTime` | **2.0 s** |
| 索敌图标淡出 | `EnemySearchIconFadeOutTime` | **1.0 s** |
| 伤害数字累积窗口 | `FE_ShowDamageAccumulationTimeSec` | **0.5 s** |
| 物品日志单行 | `ItemGetLogAliveTime` | **6.0 s** |
| 骇入条淡出 | `HackingGaugeFadeOutTime` | **1.0 s** |
| 死亡淡出（单人 / 幽灵队友） | `SoloPlayDeath_ToFadeOutTime` / `PartyGhostDeath_ToFadeOutTime` | **2.5 s** / **2.0 s** |

**可复用结论（TA）**：把"什么时候出现、什么时候消失"从代码搬到表里，是把 UI 从"程序资产"变成"设计资产"的第一道门。代价是——**所有时序必须有一个单一真相源**（这里就是 `MenuParam`），否则时序会散落到几十个蓝图/脚本里再也调不动。

### 3.2 颜色编码（调色板是数据，语义名也是数据）

`MenuColorTableParam` **882 行**，实测 **225 种不同 RGBA**，alpha=255 的占 864 行。开发者行名直接给出了**语义槽位**：

| rid | 开发者行名（节选） | 语义 |
|---|---|---|
| 0 | 使用禁止 | 保留/禁止使用 |
| 1–3 | テキスト：デフォルト / 青 / 赤 | 文本默认、蓝（增益/信息）、红（危险/削减） |
| 4–6 | ミニマップ：敵：通常 / 索敵 / 戦闘 | 雷达上敌人的三态配色 |
| 7–8 | レーダー範囲：通常 / ハッキング後 | 雷达范围环两态 |
| 9 | ミニマップ：敵視界 | 敌人视野扇形 |
| 10–11 | FE：作戦領域 / 警告領域 | 作战区域 / 警告区域 |
| — | 3Dミニマップ：敵密集地帯1..3 | 3D 小地图敌密集度分级 |
| — | アウトライン / アウトライン内塗りつぶし（各 8 / 6 条） | 描边与填充 |
| — | ハッキングライン：ハッキング中 | 骇入连线 |
| — | `0..14：MAIN` 等 20 组 × 20 条 | 20 个色槽 × 20 个用途的矩阵 |

**高频色（实测出现次数）**：`#0C0C0C`(68) · `#686868`(51) · `#3A3A3A`(38) · `#232323`(33) · `#808080`(20) · `#FF2E2E`(19) · `#FFFFFF`(18) · `#AEAEAE`(18) · `#556EFF`(15)。

**读法**：前四种是 UI 底板的**四级灰阶**（在最亮和最暗都被排除后留出对比空间），`#FF2E2E` 是**唯一的警示红**，`#556EFF` 是**唯一的交互蓝**。**"只用一种红、只用一种蓝"是颜色编码不发生歧义的前提**——如果屏幕上有三种红表示三件事，玩家就读不出"红=危险"。**[B]**

**可复用结论**：调色板应该是**表 + 语义名**，不是美术在贴图里选色。语义名让"这个红是敌人红还是警告红"在数据层就可查，也让换皮/色盲模式变成"换一张表"。

### 3.3 尺寸与对比层级

- `LockSiteWidthScale = 2.0 / LockSiteHeightScale = 1.3`（`TentativePlayerParam`）：锁定框不是正方形，是**宽高比 2.0 : 1.3 ≈ 1.54:1 的扁框**，并且**每把武器还能覆盖这个值**（`EquipParamWeapon.lockSightWidthScale/HeightScale`）。这意味着"不同武器的锁定框大小不一样"是数据决定的设计，而不是美术随手的差异。**[B]**
- `DoubleLockSightOffset = 350 px`（`MenuParam`）：双持手枪时锁定站点**从屏幕中心偏移 350 px**——因为双枪的弹道收敛点不在正中。**[B]**
- `MenuOffscrRendParam` 的 `camFov` 实测 **8°–40°**、`camDist` 实测 **1.5–2000**：菜单里的 3D 模型用**长焦小画角**呈现，这正是机库里的机体看起来"没有透视畸变、像工业产品照"的原因。**[B]**

### 3.4 边缘化

**做法**：可配置的 HUD 元素全部走**语义槽位 + 布局编辑器**。`MenuInputGestureParam` 里存在 `HUD：位置X / 位置Y / 缩放X / 缩放Y / 不透明度` 五条手势（rid 9201/9202/9204/9205/9206），`MenuValueTableParam` 里存在 `HUDレイアウト：デフォルト / カスタム1 / カスタム2 / カスタム3` 四槽位，且选项表里 `90023【表示オプション】HUDレイアウト(ボタン)` 是 `EditType=Button`（打开子界面）。

**玩家体验/结果**：默认布局是"开发者认为大多数人在大多数时候需要的分布"，但**你不喜欢，可以自己挪**——把"信息密度"这个问题从"设计者猜"变成"玩家自己调"。
**可复用结论**：**给玩家一个布局编辑器，是信息密度问题的合法逃脱出口**，但前提是元素的语义槽位在数据层是稳定的（否则保存的布局在版本更新后错位）。**[B]**

### 3.5 动效节奏

有表证据的四条：

| 动效 | 常量 | 实测值 | 等级 |
|---|---|---|---|
| 菜单背景模糊淡入 | `GraphicsParam.MenuBackBoke_FadeInTime` | **0.4 s** | B |
| 菜单背景模糊淡出 | `GraphicsParam.MenuBackBoke_FadeOutTime` | **0.1 s** | B |
| 机库界面转场 | `MenuParam.Garage_FadeTime` | **0.18 s** | B |
| 简报界面背景虚化 | `MenuParam.Garage_BriefingBokeTime` / `WaitTime` / `Rate` | **0.5 s** / **2.0 s** / **3.0** | B |
| 作战线淡入 / 淡出 | `FE_MissionLine_FadeInTime` / `FadeOutTime` | **2.0 s** / **0.5 s** | B |
| 子窗口尺寸 | `GraphicsParam.SubWindow_Width / Height` | **576 × 324** | B |
| 菜单噪点刷新间隔 | `MenuFilter.NoiseTexUpdateTime` | **0.05 s**（20/28 行）/ 0（8 行） | B |

**读法**：**淡出永远比淡入快**（0.1 vs 0.4；0.5 vs 2.0）。淡入慢 = 让玩家看清"我进入了新状态"；淡出快 = 让玩家尽快回到操作。这是 UI 动效最基础也最常被忽略的规则。**[C，但两处数据一致支持]**

---

## 4. 锁定反馈：软锁 vs 硬锁的 UI 区分（本维度重点）

### 4.1 三套锁定机制与它们的数值

AC6 的"锁定"其实是**三种不同的东西共用一个视觉符号系统**：

| 机制 | 数据字段（`TentativePlayerParam`，行 0 实测值） | 数值 |
|---|---|---|
| **通常锁（软锁/准星吸附）** | `normalLock_MaxDist` | **450 m** |
| | `normalLock_1stLockDist` | **450 m** |
| | `lockRangeHorizontalScreenRatio` | **0.45**（水平画面占比 → 候选区） |
| | `lockRangeVerticalScreenRatio` | **0.55** |
| | `chrFrontScoreDirectionWeightWhenUnlock` | **9000**（行 0）/ 5000（行 1） |
| | `lockRangeAngleWhenSwitchTarget` | **180°**（行 0）/ 60°（行 1） |
| | `lockRangeDistanceForBackLock` | **400 m**（行 0）/ 130 m（行 1） |
| | `LockOnRangeOutRemineTime` | **1.5 s**（脱离范围后仍保持） |
| | `KeepLockWhenTgtInvisibleTime` | **0.0 s**（遮挡不保持） |
| | `wallThroughLockRange` | **9999 m**（壁越锁定上限 = 实际无限） |
| **导弹锁（多锁）** | `missileLock_MaxDist` | **280 m** |
| | `missileLock_MaxLockNum` | **4**（单次锁 4 个） |
| | `multiLockTaretNumMax` | **10**（总数上限） |
| | `triggerContinueTimeToMultiLock` | **0.5 s**（长按 0.5 s 进多锁） |
| **目标标记（マーキング）** | `LockTargetMarking_ChachDist` | **600 m** |
| | `LockTargetMarking_ChachAngleDeg` | **30°** |
| | `LockTargetMarking_TimeOutSec` | **2.0 s** |
| | `LockTargetMarking_ForgetDist` | **700 m** |
| 其它 | `AimActLockRangeScale` | **2.0**（瞄准时锁定距离翻倍） |
| | `bladeKeepLockTime` | **0.8 s**（近战最短锁定保障） |
| | `lockCamParamLerpRate` | **0.15** |
| | `DeadLockOnDisableWaiteFrame` | **24**（1/30 s 单位 ≈ 0.8 s） |
| | `LockTargetChangeWaitTimeMouse` / `InputCoefficient` | **0.1 s** / **500** |
| | `UnlockAfterCrossingAngleThreshold` | **180°** |
| | `freeCameraMaxOffsetTimeForSemiAutoLock` | **0.5 s** |
| | `DisableLockPrevAutoSightingTargetTime` | **0.2 s** |

**注意两份数据不一样**：`TentativePlayerParam` 有 **2 行**（rid 0 / rid 1），多数字段相同，但 `chrFrontScoreDirectionWeightWhenUnlock`（9000 vs 5000）、`lockRangeAngleWhenSwitchTarget`（180 vs 60）、`lockRangeDistanceForBackLock`（400 vs 130）、`bladehoming_InertiaCondAngleDeg`（30 vs 0）、`bladeHoming_ModelRotAngSpeedDegPerSec`（60 vs −1）不同。**这两行很可能是"两种锁定模式"（例如手动/半自动锁定）或难度/手感档位**——具体是哪一种我未能确认，标 **D**（验证方法：`Names/TentativePlayerParam.txt` 或 `Developer Names/` 若存在行名可直接读到用途；本机该表未见行名文件）。

### 4.2 UI 上如何区分软锁 / 硬锁

| 状态 | UI 表现 | 数据依据 | 等级 |
|---|---|---|---|
| **未锁定（自由视角）** | 屏幕中心只有一个小准星（"射击站点"），不吸附 | `shootTargetOffsetDistanceAtUnlock = 806 m`、`shootTargetLookUpAngAtUnlock`（非锁定时的射击点俯角） | B |
| **软锁/临时锁（仮ロック）** | 准星向候选目标**插值吸附**；目标身上出现标记框 | `lockCamParamLerpRate = 0.15`；`MakerRendRangeW/H`（屏内标记绘制范围） | B |
| **硬锁（持续锁定）** | 目标框**锁定框尺寸随武器变化**、相机跟随 | `LockSiteWidthScale = 2.0 / Height = 1.3`，并被 `EquipParamWeapon.lockSightWidthScale/HeightScale` 逐武器覆盖 | B |
| **不可射击态** | 锁定光标**变半透明**（alpha 40/255 ≈ 15.7%） | `MenuParam.DisableLockCursorAlpha = 40` | B |
| **脱离范围但仍在锁定** | 锁定框保留 1.5 s 后消失 | `LockOnRangeOutRemineTime = 1.5 s` | B |
| **导弹多锁进度** | 长按 0.5 s 后逐格点亮，最多 4 格（同类）；总数上限 10 | `triggerContinueTimeToMultiLock = 0.5 s`、`missileLock_MaxLockNum = 4`、`multiLockTaretNumMax = 10` | B |
| **目标标记（超出视野）** | 屏幕边缘方向标（"这里有敌人"），2 s 后遗忘 / 700 m 后彻底清除 | `LockTargetMarking_TimeOutSec = 2.0 s`、`ForgetDist = 700` | B |
| **敌方开火预兆** | 敌方机体上的特效/图标，**挂在 dummy poly 上** | `AttackActionParam.shootIndicationType = 強射撃予兆`、`shootIndicationDmypolyId` | B |

**为什么这样设计**：AC6 的锁不是"点一下贴上去"，而是**一条连续的、由数值定义的注意力管道**：候选区的屏幕占比（45%/55%）定义"什么算在我视野里"，距离阈值（450/280 m）定义"什么算打得到"，权重（9000）定义"什么算朝前"，超时（1.5 s / 2.0 s）定义"什么时候忘掉"。**UI 只是把这些数值翻译成像素。**

**可复用结论（"信息即玩法"的教科书）**：当一套系统的判定完全由数值组成时，**UI 的正确做法不是"显示判定结果"，而是"显示判定所用的量"**——锁定框的大小写实地反映"我离能锁上还有多远"，玩家就会自然学会 280 m 是导弹锁的分界线，而不需要任何教程文字。

---

## 5. 装配界面（Garage）：高维数值 + 高自由度编辑的信息设计

### 5.1 三种精度并存（信息层级的表实现）

`Names/MenuPropertyLayoutParam.txt` 有 1261 行英文行名，**其中 237 行以 `Simple` 开头**，覆盖 HEAD / CORE / ARMS / LEGS / BOOSTER / FCS / GENERATOR / EXPANSION（4 种）/ 各种武器类别。例：

- `HEAD - AP` / `HEAD - Attitude Stability` / `HEAD - System Recovery` / `HEAD - Scan Distance` / `HEAD - Weight` / `HEAD - EN Load` / `HEAD - Part Info`
- `Simple HEAD - AP` / `Simple HEAD - Attitude Stability` / `Simple HEAD - Weight` / `Simple HEAD - EN Load`

**读法**：列表页（一排部件滚动浏览）显示 `Simple` 子集 3–4 条，进入单部件详情才展开全量。**这是"信息密度管理"最经济的一招——不是"少显示"，而是"分级显示同一份数据"。** 而它由数据表实现，意味着加/减一条属性不需要改代码。**[B]**

**武器类别的属性集也有 148 个不同前缀**（`BASIC GUN` / `CORAL RIFLE` / `CHARGE BLAST LASER` / `MULTI ENERGY RIFLE` / `TANK LEGS` / `AC Specs` / `EXPANSION (PULSE ARMOR)` …）。**每类武器的面板是不一样的**——因为"集弹性能"对霰弹枪有意义、对刀刃没意义。**[B]**

### 5.2 换件前后的差值：引用式取数（本报告最重要的技术线索）

`MenuPropertySpecParam` 的关键字段（paramdex 定义，实测结构 108 字节）：

| 偏移 | 字段 | 含义 | 实测分布 |
|---|---|---|---|
| 12 | `CompareType` | **優劣判定**（0=无 / 1=大者优 / 2=小者优） | 无 260 / 大者优 205 / 小者优 43 |
| 13 | `FormatType` | 显示格式（含 `±数値`、`通貨`、`0以下は-(ハイフン)`、`【オプション】ON・OFF`、`アイコン(PartsSpec)` 等 30+ 种） | 小数点以下切り捨て 168 / 未指定 167 / 0以下はハイフン 47 / 通貨 24 / 小数第一位 10 … |
| 36 | `EditType` | 编辑类型（0 无 / 1 列表 / 2 滑杆 / 3 按钮） | 无 383 / 列表 53 / 滑杆 45 / 按钮 27 |
| 38 | `IndexRefParamID` | 索引引用参数（`Float_00`–`Float_31`） | **83/508 行在用**；`Float_01` 占 65 条 |
| **68/70/71/72/76/80** | **`extract0_Target / _MemberType / _Operation / _MemberTailOffset / _Constant0 / _Constant1`** | **取数配方：从哪张表（枚举 14 种目标表）、什么原始类型、什么公式、什么字节偏移、两个常数** | **105/508 行在用** |
| 88–100 | `extract1_*` | 第二条取数配方（**仅 4 行在用**） | 4 |

**枚举（paramdex TDF，已解出）**：
- `MenuPropertyExtractTargetType`：`None=0, Weapon=1, Armor=2, booster=3, FCS=4, generator=5, Behavior Para=6, Attack Para=7, Bullet Para=8, Child Bullet Para=100, Child Bullet_Attack Para=101, Grand Dangan Para=110, Grand Bullet_Attack Para=111`
- `MenuPropertyExtreactOperationType`：`None=0, Constant0 × Para + Constant1=1, Constant0 ÷ Para + Constant1=2`
- `MenuPropertyExtreactPrimitiveType`：`s8/u8/s16/u16/s32/u32/f32`（7 种）
- `MenuPropertyCmpType`：`----=0, large=1, small=2`

**★★ 必须先讲清楚偏移语义（否则整节都会错）**

`extract0_MemberTailOffset` 的 paramdex 名是 **"メンバ末尾オフセット"（成员末尾偏移）**。实测验证：**取数地址 = `MemberTailOffset − sizeof(extract0_MemberType)`**。

| 规则 | 105 条中落在 paramdex `pad*` 填充字段（=读错）的条数 | 语义比对胜出 |
|---|---|---|
| 按"**起始**偏移"朴素理解（`addr = off`） | **6 / 105（5.7%）** | 5 |
| `addr = off − 4`（固定减 4） | 1 / 105（1.0%） | — |
| **`addr = off − sizeof(type)`（尾偏移，正确）** | **0 / 105（0.0%）** | **42**（另 58 条标签为假名/符号，无法用汉字比对） |
| `addr = off + 4` | 6 / 105（5.7%） | — |

**更强的证据 —— 类型一致性检验**：在尾偏移规则下，**105/105 条记录**声明的原始类型（`extract0_MemberType`：`s8/u8/s16/u16/s32/u32/f32`）**与目标字段在 paramdex 里的声明类型完全一致，0 条不一致**。这基本排除了巧合。

**"首偏移"读法会造成的具体错误（这就是坑）**：

| PropertyID | UI 项 | 若按 `addr = off` 读到的字段（✘） | 按尾偏移读到的字段（✔） |
|---|---|---|---|
| 2013 | 【武器】PA干渉 | `@528 impactPower 衝撃力`（张冠李戴） | **`@526 atkPa PA減衰力`** |
| 2024 | 【武器】弾単価 | `@732`（f32 的半个字，实测仅 0/100 两个值） | **`@730 bulletCost 弾薬費`**（实测 0–1600，184 行非零，29 个不同值） |
| 2025/2026 | 【武器】衝撃力（子/孙弹丸） | `@532 damageLevelConvId` | **`@528 impactPower 衝撃力`** |
| 2027/2028 | 【武器】残留衝撃（子/孙弹丸） | `@992 hit0_sfxmodelId`（SFX 模型 ID，−1/83100） | **`@988 residualImpactPower 非ガード時残留衝撃力`** |
| 3013/3100/3201/3401 | 【防具/HEAD/CORE/脚部】安定性能 | `@492`（实测 121 行**全为 0**） | **`@488 stability 安定性能`**（实测 0–1500，70 个不同值） |
| 3302 | 【ARM】射撃運動性能 | `@488 stability`（错位一格） | **`@484 shootMotionPerf 射撃運動性能`** |
| 3301 | 【ARM】反動制御 | `@500 energyDrain_FourLegFlyMove` | **`@496 recoilCtrl 反動制御`** |
| 3300 | 【ARM】腕部積載許容量 | `@572 AppropriateType_Energy` | **`@568 armMaxWeight`** |
| 3505 | 【GENE】EN武器適正 | `@44 pad_end[14]`（填充字段） | **`@40 AppropriateType_Energy`** |
| 3204 | 【CORE】ラジエーター性能 | `@884 pad_end[16]` | **`@880 generatorCoolPerf`** |
| 2015 | 【武器】チャージ中EN負荷 | `@1120 pad04_2[2]` | **`@1116 consumeEN_Charging`** |
| 2038 | 【武器】二段チャージ時間 | `@1032 pad_05_3[4]` | **`@1028 chargeLv2EndTimeSec`** |
| 3708 | 【ブースター】アサルトブースト消費EN | `@284 pad_2[2]` | **`@280 assaultBoost_DrainEnPointPerSec`** |

**105 条实际配方样本（按尾偏移修正后：`起始地址 = off − sizeof(类型)`）**：

| PropertyID | UI 项 | 参照源表 | 字段起始 | 声明类型 | 表内字段（paramdex） | 公式 | 常数 |
|---|---|---|---|---|---|---|---|
| 2013 | 【武器】PA干渉 | AtkParam | 526 | u16 | `atkPa`（PA减衰力） | ×P+0 | 100, 0 |
| 2024 | 【武器】弾単価 | EquipParamWeapon | 730 | u16 | **`bulletCost`（弾薬費）** | — | — |
| 2025/2026 | 【武器】衝撃力（子/孙弹丸） | AtkParam | 528 | s32 | `impactPower` | — | — |
| 2027/2028 | 【武器】残留衝撃（子/孙弹丸） | AtkParam | 988 | s32 | `residualImpactPower` | — | — |
| 2012 | 【武器】マガジンリロード | EquipParamWeapon | 924 | f32 | `magazineReloadTimeSec` | — | — |
| 2021/2066 | 【武器/护盾】冷却性能 | EquipParamWeapon | 1420 | f32 | `heat_SubValuePerSec` | — | — |
| 2044 | 【武器】緊急冷却性能 | EquipParamWeapon | 1424 | f32 | `heat_OverHeatSubValueScalePercent` | ×P+C | 0.01, 0 |
| 2048 | 【武器】格闘コンボ数 | EquipParamWeapon | 1464 | s8 | **`menu_MeleeComboCount`** | — | — |
| 2060 | 【护盾】ガード範囲 | EquipParamWeapon | 914 | s16 | `guardRangeHorizontalDeg` | ×P+C | 2, 0 |
| 2062/2073 | 【护盾/Scutum】耐衝撃性能 | EquipParamWeapon | 1188 | f32 | `guardImpactCutRatePercent` | — | — |
| 2064/2074 | 【护盾/Scutum】維持時間 | EquipParamWeapon | 1040 | f32 | `justGuardKeepTimeSec` | — | — |
| 2065/2204/2205 | 【护盾/突击装甲】耐久性能 | EquipParamWeapon | 1098 | u16 | `paGaugeMax` | — | — |
| 2069/2071 | 【护盾】初期出力耐衝撃性能 | EquipParamWeapon | 1048 | f32 | `justGuardImpactCutRatePercent` | — | — |
| 2200 | 【突击驱动】使用可能回数 | EquipParamWeapon | 680 | s32 | `totalBulletNum` | — | — |
| 2206 | 【突击驱动】クリティカル適性 | AtkParam | 842 | s16 | `staggerCriticalRate_Mag` | — | — |
| 3050–3082 | 各部位 耐KE/TE/CE装甲 | EquipParamProtector | 612/616/620 | f32 | `ProCutRate_Phys/Mag/Fire` | ×P+C | 10, **150/350/200/300** |
| 3101 | 【HEAD】システム復元性能 | EquipParamProtector | 632 | f32 | `ProCutRate_Burn` | ×P+C | 1, 100 |
| 3103/3104/3105 | 【HEAD】スキャン角度/距離/硬直時間 | EquipParamProtector | 822/824/828 | u16/f32/f32 | `scanAngle` / `scanDist` / `scanTime` | — | — |
| 3200 | 【CORE】ブースターEN伝達効率 | EquipParamProtector | 872 | f32 | `quickBoosterOutputCorrRate` | — | — |
| 3203 | 【CORE】ジェネ出力伝達性能 | EquipParamProtector | 876 | f32 | `generatorOutputCorrRate` | — | — |
| 3204 | 【CORE】ラジエーター性能 | EquipParamProtector | 880 | f32 | `generatorCoolPerf` | — | — |
| 3300 | 【ARM】腕部積載許容量 | EquipParamProtector | 568 | f32 | `armMaxWeight` | — | — |
| 3301 | 【ARM】反動制御 | EquipParamProtector | 496 | f32 | `recoilCtrl` | — | — |
| 3302 | 【ARM】射撃運動性能 | EquipParamProtector | 484 | f32 | `shootMotionPerf` | — | — |
| 3303 | 【ARM】格闘適正 | EquipParamProtector | 576 | f32 | `AppropriateType_Melee` | — | — |
| 3403 | 【脚部】ブレーキ性能 | EquipParamProtector | 476 | f32 | `landBrakeScale` | ×P+C | 100, 0 |
| 3404 | 【脚部】歩行性能 | EquipParamProtector | 840 | f32 | `walkAnimSpeedRate` | ×P+C | 144, 0 |
| 3502 | 【GENE】冷却性能 | EquipParamGenerator | 28 | f32 | `energyRecoveryDelayTimeForEmptySec` | **÷P+C** | 1000, 0 |
| 3503 | 【GENE】緊急冷却性能 | EquipParamGenerator | 32 | f32 | `energyRecoverValForEmpty` | **÷P+C** | 1000, 0 |
| 3504 | 【GENE】緊急時EN回復割合 | EquipParamGenerator | 36 | f32 | `energyRecoverValForEmpty` | — | 100, 0 |
| 3600 | 【FCS】ミサイルロック性能 | EquipParamFcs | 132 | f32 | `missileMultiLockTimeRate` | ×P+C | **−100, 200** |
| 3602 | 【FCS】二次ロック性能 | EquipParamFcs | 144 | f32 | `perfRateSubScale` | ×P+C | 100, 0 |
| 3700 | 【推进器】巡航推力 | EquipParamBooster | 100 | f32 | `QB_StartAddSpeedKMH` | ×P+C | **16.67**, 0 |
| 3704 | 【推进器】QB喷射时间 | EquipParamBooster | 92 | f32 | `dashBoost_EndSpeedKMH` | ×P+C | **0.033**, 0 |
| 3708 | 【推进器】突击推进消费EN | EquipParamBooster | 280 | f32 | `assaultBoost_DrainEnPointPerSec` | — | — |
| 10009 | 【弾丸】射撃反動 | BehaviorParam | 116 | f32 | `lockTimeSec` | — | — |
| 10008 | 【弾丸】最大ロック数 | BehaviorParam | 124 | u8 | `shootEnableLockNum` | — | — |
| 2029/2030/2202 | 【武器/突击驱动】爆発範囲 | BulletParam | 80 | f32 | `hitRadiusMax` | — | — |

**这就是"实时数值对比组件"的真正形态（★ 关键的架构线索）**：

1. UI **不持有任何数值副本**。它持有的是 `(目标表, 字段尾偏移, 原始类型, 公式, 常数0, 常数1)`。
2. 换件时，UI 重新对**新的部件行**执行同一份配方，得到新值；**对比 = 用同一份配方跑两次（当前件 vs 待选件）**，差值符号由 `CompareType`（大者优/小者优）决定颜色。
3. 显示格式由 `FormatType` 决定（`±数値`、`通貨`、`0以下はハイフン`、`小数点切り捨て`…），所以"−12"和"×1.5"这种格式差异也是数据。
4. 常数是**单位换算**：`×16.67` 就是 m/s → km/h（16.67 = 60×60/1000 的近似值，实测 **16.670000076293945**）；`÷1000` 是毫秒→秒；`×100` 是比率→百分比。**换句话说，UI 层负责单位换算，数值表只存引擎单位。**

5. **`EquipParamWeapon` 里的 `menu_SrcGeneration*` 字段（共 30+ 个）就是这条链的上游开关**：`menu_SrcGenerationImpact`（衝撃力参照元）、`menu_SrcGenerationResidualImpact`（蓄積衝撃力参照元）、`menu_SrcGenerationHoming`（誘導性能参照元）、`menu_SrcGenerationRange`（射程限界参照元）… 外加 `_Charge` 后缀的第二套（チャージ後），以及 `menu_ShowConsumeBullet`（消費弾数表示）、`menu_ShowAddHeat`（発熱表示）。

   **实测值分布（`EquipParamWeapon`，284 行）**：
   - `menu_SrcGenerationAtkPower @1446`：0 → **205 行**，1 → 46，2 → 17，4 → 12，3 → 4
   - `menu_SrcGenerationImpact @1453` / `ResidualImpact @1454` / `DirectHit @1452`：**完全相同的分布**（0:205 / 1:46 / 2:17 / 4:12 / 3:4）
   - `menu_SrcGenerationHoming @1456`：0 → 236，1 → 38，2 → 8，4 → 2
   - `menu_SrcGenerationRange @1459`：0 → 251，1 → 25，2 → 8
   - `menu_ShowConsumeBullet @1460` / `menu_ShowAddHeat @1461`：**284 行全部 = 1**

   **读法**：一把武器内部有**多个攻击参数（普通 / 蓄力 / 连段…）**，`menu_SrcGeneration*` 就是告诉 UI "面板上的『冲击力』这一栏，请从第 N 组攻击参数里取"。这是**"显示的数值"与"实际生效的数值"之间的一层间接寻址**——因为一把武器可能有 5 组攻击参数，而面板只能显示一格。`menu_ShowConsumeBullet/ShowAddHeat` 全为 1，说明"是否显示弹数与发热"这个开关对玩家武器**全部打开**，但字段保留了——这是给特殊武器（如刀刃、护盾）留的口子。

**可复用结论（TA）**：**"实时数值对比"的工程量 90% 在"取数层"而不是"显示层"。** 你需要的是：
- 一份**字段地址注册表**（表 + 偏移 + **偏移语义** + 类型），而不是每个属性写一段取值代码；
- 一套**公式 DSL**（这里的 `C0 × P + C1` / `C0 ÷ P + C1` 只有两种，够用）；
- 一个**单位换算层**（把引擎单位翻译成显示单位）；
- 一个**优劣方向标记**（`CompareType`）；
- **一个偏移语义契约**（"这是首偏移还是尾偏移？"必须写死在文档和校验里——本报告第一节就演示了误读它的后果）；
- 以及**全量一致性校验 CI**（见 §10.3）。

### 5.3 约束可视化：警告组件的三槽复用

| 布局行 | 界面 | `Warn_0` | `Warn_1` | `Warn_2` |
|---|---|---|---|---|
| 15001/16011/17031/18027 | 4 个不同界面 | 29901 `【PC】積載限界超過` | 29902 `【PC】腕部積載限界超過` | 29903 `【PC】使用不可データ含`（该行开发者名为"終端"） |

另外三个界面里有 `TotalWeight`（`20014【PC】積載状況`）与 `TotalConsumeEN`（`20015【PC】EN消費状況`）。
`MenuPropertyID` 里还有一组"未满足"提示：`29900【PC】EN出力不足`、`29901【PC】積載限界超過`、`29902【PC】腕部積載限界超過`、`29903【PC】使用不可データ含`。

**读法**：重量超限、EN 不足、腕部超限是**三种不同的失败原因**，但用**同一个组件的三个槽位**呈现。这就是组件化 UI 的最小单元：**不是"三个警告控件"，是"一个警告控件 + 三个数据源"**。**[B]**

### 5.4 试算与预览

`MenuBehaviorParam`（31 行）是前端画面注册表，实测全部内容：

| rid | 画面 | tutorialID | 帮助菜单 |
|---|---|---|---|
| 1000 | **ASSEMBLY** | 2000000 | 1 |
| 1001 | **TRIAL FIT**（试装/试算） | 2002100 | 1 |
| 1002 | BUY | 2002000 | 1 |
| 1003 | SELL | 2002010 | 1 |
| 1004 | **OS TUNING** | 2009000 | 1 |
| 1005 | **AC TEST**（试跑） | 2006000 | 1 |
| 2000 | **PAINT (Top)** | 2003000 | 1 |
| 2001 | **MARKING**（徽章） | 2003100 | 1 |
| 2002 | **DECAL (Top)** | 2003100 | 1 |
| 2003 | **CUSTOM DESIGN (Top)** | 2003300 | 1 |
| 2004 | PAINT (edit) | 0 | 1 |
| 2005 | DECAL (layer editing) | 0 | 1 |
| 2006 | CUSTOM DESIGN (layer editing) | 0 | 1 |
| 2007 | CUSTOM DESIGN (piece editing) | 0 | 1 |
| 3000 | **AC DATA**（配装保存） | 2005000 | 1 |
| 4000 | MISSION | 2001000 | 1 |
| 4001 | REPLAY MISSION | 2001100 | 1 |
| 4002 | ARENA | 2004000 | 1 |
| 4003 | TRAINING | 2007000 | 1 |
| 5000 | PLATE EDIT | 2004140 | 1 |
| 5001 | PLATE SHOP | 2004150 | 1 |
| 5002 | SOLO MATCH | 2004120 | 1 |
| 5003 | TEAM MATCH | 2004130 | 1 |
| 5004 | CUSTOM MATCH | 2004110 | 1 |
| 5005 | YOUR DATA | 0 | 0 |
| 5006 | AC DATA SHARING | 0 | 1 |
| 5007 | CUSTOM DESIGN SHARING | 0 | 1 |
| 5008 | ARCHIVES | 2008000 | 0 |
| 5009 | ONLINE ARENA | 2004101 | 0 |
| 5011 | TIPS | 2008100 | 0 |

**这张表同时回答了三个问题**：(a) 前端有哪 31 个画面；(b) 每个画面首次进入弹哪条教程（`tutorialID` 指向 `TutorialParam` 的 201 行之一）；(c) 每个画面是否有帮助菜单。**帮助菜单的开关也在表里**（`enableHelpMenu`）——**"这个界面要不要新手帮助"是一个策划可调的数值**。

**此外还有"自动装配"（`【自動アセン】`）**：`MenuPropertySpecParam` 里 `59001【自動アセン】脚部タイプ`（列表选择，`FormatType=105 使用种类`）、`59002【自動アセン】アセン傾向`（列表，`106 アセン系統`）、`59050【自動アセン】余剰積載`（滑杆）、`59051【自動アセン】余剰EN`（滑杆）。**这是"给系统两个滑杆和两个下拉，让它替你配一台机"的界面**，是高自由度装配的信息量解法之一。**[B]**

### 5.5 保存、分享与跨玩家编辑

- `3000 AC DATA`：本机配装保存。
- `5006 AC DATA SHARING` / `5007 CUSTOM DESIGN SHARING`：**配装与自定义设计的跨玩家分享**（对应 AC6 的分享码机制）。
- `MenuPropertyID` 里有 `30000【イメージ】作成番号 / 30001【イメージ】作成日 / 30002【イメージ】UgcID / 30010【イメージ】使用ピース数` → **UGC（用户生成内容）有独立的数据模型：编号 + 创建日 + UGC ID + 使用的贴片数量**。**[B]**
- `MenuOffscrRendParam` 里存在 `4000–4033` 共 **14 行** `UGC確認用機体画像 前/後/左/右`，且**按脚部类型分了三套**：普通 / 4 脚（`4010–4013`）/ 坦克（`4020–4023`）/ 浮游（`4030–4033`）。**读法：分享界面要生成"机体的四视图缩略图"，而不同腿部构型的模型包围盒差异很大，所以按腿型各配了 4 个机位。** 这是"UI 需求反向决定渲染资源"的典型例子。**[B]**

### 5.6 涂装 / 贴花 / 徽章编辑器的信息设计

从 `MenuBehaviorParam` 看，这一块是**四个独立画面 + 三个编辑层**：

```
[PAINT 涂装]   Top → edit          （颜色编辑，含 HSV 拾色器）
[MARKING 徽章] Top                 （徽章/标记）
[DECAL 贴花]   Top → layer editing （图层编辑）
[CUSTOM DESIGN 自定义图案] Top → layer editing → piece editing（图层 → 贴片，两级）
```

**颜色编辑器的数据模型**（`MenuPropertyID` 的 40000 段 + `PlayerColoringPresetParam`）：

| PropertyID | 项 | 说明 |
|---|---|---|
| 40200 | color | 颜色项（`LayoutPath` 空） |
| 40301–40303 | 【フォトモード】カラーシフト R/G/B | 照片模式下的颜色偏移 |
| 40001–40003 | 【デカール】基点位置 X/Y/Z | 贴花锚点 |
| 40004–40005 | 【デカール】基点角度 X/Y | 贴花角度 |
| 40006–40007 | 【デカール】贴付方向补正 X/Y | **滑块**（`EditType=2`） |
| 40008 | 【デカール】图像角度 Z | |
| 40009–40012 | 【デカール】图像位置 X/Y、サイズ X/Y | 实测布局行 `100000 Pos/X` → `pid=40009` |
| 40013 | 【デカール】画像反转：左右 | `FormatType=130 【オプション】ON・OFF` |
| 40014 | 【デカール】贴付对象 | 列表选择，`FormatType=100`；布局行 `100200 Mask` |
| 40015 | 【デカール】贴付限界距离 | **滑块** |
| 40100 | 【デカール】使用イメージ数 | 布局行 `100300 TopItem_0` |

**输入手势也是数据**（`MenuInputGestureParam`，实测）：
- `250/251/252` 颜色拾取器 **H / S / V**（三轴分别绑键）
- `1202/1203/1204/1205` 颜色 **复制 / 粘贴 / 重置 / 登录**（带 SE：1100 / 1100 / 1150 / —）
- `9002` 滑块值操作、`9001` 滑块取消、`9000` 初始化
- `9100–9105` 键位解绑（割り当て解除 / 初期化 / 割り当てキャンセル / 前·次类别 / 自定义删除）

**涂装预设**（`PlayerColoringPresetParam`，6 行 × 392 字节）：每个部件有 **20 个 slot**（`slot0`–`slot19`），每 slot 有 `PatternID` + 2 个 `MaterialProperty` + 5 个色通道（`Base` / `Sub` / `Support` / `Optional` / `Device`），每个色通道 **RGBA 四字节**。实测 6 套预设：

| rid | slot0 Base RGBA | slot0 Sub RGBA |
|---|---|---|
| 0 | (128,128,128,255) | (60,60,60,255) |
| 1 | (255,0,0,255) | (60,60,60,255) |
| 2 | (0,0,255,255) | (60,60,60,255) |
| 3 | (255,255,0,255) | (60,60,60,255) |
| 4 | (255,96,160,255) | (60,60,60,255) |
| 5 | (0,255,0,255) | (60,60,60,255) |

**读法**：Primary 是纯色（红/蓝/黄/粉/绿），Secondary 全部固定 `(60,60,60)` 深灰。**预设只改主色、副色锁定深灰**——这是"预设要保证不会太丑"的保守设计。**[B]**

同时实测发现 `MaterialExParam` 里有 `1150–1153` 四条开发者行：**"メニューでカラー変更した場合の明滅_Flickering_Main/Sub/Support/Optional"** —— **在菜单里改颜色时，模型对应部位会闪一下**。这是"编辑即预览反馈"的具体实现：改哪个通道，哪个通道闪。**[B]**

### 5.7 "高维数值 + 高自由度编辑"如何做到实时响应（技术侧结论）

按优先级：

1. **数据侧：不要在编辑时做全量重算。** 这套设计的聪明处在于——UI 显示的每个数字都是**O(1) 的单字段读取 + 一次乘加**。没有"重新编译整机数据"这一步。重算的只有**汇总值**：`TotalWeight`（`20014 積載状況`）、`TotalConsumeEN`（`20015 EN消費状況`）、`AP`（`3000`，可覆盖 + 每部件 KE/TE/CE 三抗）。这些都是**加法聚合**，改一个部件只需要"减去旧件、加上新件"（增量更新），根本不需要遍历整机。**[C，但结构与字段支持该推断]**
2. **视图侧：用语义槽位而不是绝对坐标。** 换件时布局不变（布局在 `MenuPropertyLayoutParam` 里静态描述），只有**值**变。所以"实时响应"退化成"改 N 个文本控件的 string"——这是最便宜的 UI 更新。**[B/C]**
3. **渲染侧：3D 预览走离屏渲染 + 独立机位表。** `MenuOffscrRendParam` 给每个菜单场景一个固定机位（`camAtPos*` / `camDist` / `camRot*` / `camFov`），并且**机位可以通过 `camDistMin/Max`、`camRotXMin/Max` 做限定范围内的玩家旋转**（实测 `camDist 1.5–2000`、`camFov 8–40°`）。`MenuPartsModelRendParam` 的 14 行给每个部件类别一个初始角度（如 `-20, 45`、`20, 0`）→ **换件时模型换成新件 + 应用该类别的初始角度**，这是一个纯数据操作。**[B]**
4. **菜单后处理是共享的。** `MenuFilter` 28 行、`NoiseTexUpdateTime` 实测 **0.05 s**（20 行）→ **菜单有一层 20 Hz 刷新的噪点滤镜**，覆盖在所有菜单之上。这意味着**UI 不是"纯净的"**，它和 3D 场景一起过后处理。**[B]**
5. **性能上真正要做的是"合批 + 少材质"。** 这一层**本机数据里没有直接证据**（DrawCall / 批次数是运行时指标），我标 **C/D**，验证方法见 §12。

---

## 6. 任务流程 UI：简报 → 出击 → 战斗 → 结算 → 商店/机库

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. 任务列表 (MISSION, rid=4000)                                      │
│    决策：选哪个任务 / 看报酬·难度描述 / 重玩 (REPLAY MISSION, 4001)     │
└───────────────┬─────────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. 简报 BRIEFING                                                     │
│    表证据：Garage_BriefingBokeTime=0.5s / WaitTime=2.0s / Rate=3.0    │
│    决策：换装（跳回 ASSEMBLY）/ 直接出击                               │
└───────────────┬─────────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────┐    ┌──────────────────────────────┐
│ 3. 装配 ASSEMBLY (1000)          │◄──►│ TRIAL FIT (1001) 试算         │
│    · 换件 → 增量更新汇总值         │    │ AC TEST (1005) 试跑           │
│    · 约束检查 Warn_0/1/2          │    │ 自动アセン（59001/59002/      │
│    · 保存 AC DATA (3000)          │    │          59050/59051）        │
│    · 涂装 PAINT/MARKING/DECAL/    │    └──────────────────────────────┘
│      CUSTOM DESIGN (2000–2007)   │
└───────────────┬─────────────────┘
                ▼  出击
┌─────────────────────────────────────────────────────────────────────┐
│ 4. 战斗中（HUD 层级见 §2）                                            │
│    信息流：AP/EN/弹药(边缘) · 姿态条(近中心) · 锁定框+导弹多锁(中心)    │
│            射击预兆(敌方 dummy poly) · 目标标记(世界空间)              │
│            作战区域线+警告线(世界空间 200m/100m) · Danger(受击 2.0s)   │
│    决策：打/撤/换目标/用扩展兵装/放弃任务                              │
└───────────────┬─────────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. 结算 RESULT（表证据：MenuPropertyID 80001–80090 + 布局行 80000+）    │
│    · 收入：基本报酬 (80001) / 特別加算合計 (80003) / 特別減算合計 (80004)│
│    · 收入合计 (80019)                                                  │
│    · 费用：修理費 (80020) / 弾薬費 (80021)                             │
│    · 费用合计 (80039)                                                  │
│    · 收支合計 (80090, 布局路径名 totalBalance)                          │
│    决策：看到赤字 → 下次换更便宜的弹药 / 少挨打                        │
└───────────────┬─────────────────────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. 商店 / 机库                                                        │
│    BUY (1002) / SELL (1003) / OS TUNING (1004) / AC DATA (3000)      │
│    ARENA (4002) / TRAINING (4003) / PLATE SHOP (5001)                │
│    决策：钱怎么花（新部件 vs OS 强化 vs 外观）                          │
└─────────────────────────────────────────────────────────────────────┘
```

**结算界面的信息设计要点**：它把"我这局花了多少钱"拆成**可归因的收支项**——修理费（跟我挨了多少打相关）和弹药费（跟我打了多少发相关）。**这是把战斗过程翻译成经济反馈的界面**，也是玩家下一轮决策的直接输入。**[B]**

---

## 7. 可及性（Accessibility）

### 7.1 全部选项（`MenuPropertySpecParam` 中 PropertyID 90000–91000 的 62 条）

| 组 | 项数 | 项 |
|---|---|---|
| 游戏选项 | 6 | 锁定自动切换、手柄振动、推进操作、突击推进操作、限幅器解除操作、自动抛弃 |
| 相机选项 | 4 | 相机上下、相机左右、相机上下重置、相机速度 |
| **显示选项** | **6** | **字幕显示**、**HUD 颜色（按钮）**、**HUD 布局（按钮）**、HDR、亮度调整（按钮）、画质调整（按钮） |
| 音频选项 | 4 | BGM 音量、SE 音量、语音音量、总音量 |
| 亮度调整 | 1 | SDR 亮度 |
| 画质调整 | 3 | HDR 亮度、HDR 最大亮度、HDR 彩度 |
| **按键设定** | **2** | **按键分配（预设/自定义）**、**按键分配详细设定（按钮）** |
| **输入设备设定** | **5** | **操作提示目标设备**、鼠标灵敏度、鼠标左右、鼠标上下、**键位设定** |
| 网络设定 | 7 | 匹配地区、语音聊天、玩家名称显示、标题启动设定、数据使用同意、软件使用条款、隐私政策 |
| 语言设定 | 2 | 文本、语音 |
| 图形设定 | 9 | 屏幕模式、分辨率、自动描画调整、品质设定、详细设定、性能设定、光追（PS5/Scarlett）、FPS 限制、Vsync |
| 图形详细 | 13 | 纹理/AA/SSAO/景深/运动模糊/阴影/光照/特效/体积雾/反射/水面/着色器/光追品质 |

**有表数据支撑的结论**：
- **字幕**：只有 ON/OFF 一个开关（`fmt=130`，`EditType=1 列表选择`）。**没有字号、没有背景框、没有说话人颜色、没有字幕速度**。**[B]**
- **色盲**：选项表里**没有任何 colorblind 条目**。最接近的是 `90022【表示オプション】HUDカラー(ボタン)`——一个打开子界面的按钮，其子界面内容不在本机数据中。**HUD 颜色是否可以设成色盲友好配色，我未能确认，标 D。** **[D]**
- **文本大小**：**无**（选项表内无对应 PropertyID；`FeFreeDialogParam.FontScale = 1` 是全局常量而非玩家选项）。**[B，负面结论]**
- **按键重映射**：**是最完整的一块**。`KeyAssignDisplayParam` 58 行（55 行可解绑、50 行可改手柄、50 行可改鼠标、28 行可进配置菜单），`KeyAssignMenuItemParam` 24 行；`KeyAssignParam` 定义 key 映射（`padKeyId / keyboardModifyKey / keyboardKeyId / mouseModifyKey / mouseKeyId`）；`MenuInputGestureParam` 有 `9100 解绑 / 9101 初始化 / 9102 取消分配 / 9103-9104 上一个·下一个类别 / 9105 删除自定义设定` 五条专门手势。**[B]**
- **操作提示设备**（`90100`）：**可以指定"提示显示哪种设备的按键图标"**——这在纯键鼠/纯手柄/混合三种情形下都重要，很多游戏做不到。**[B]**
- **HUD 布局**：位置 X/Y、缩放 X/Y、不透明度（五个手势），4 个槽位（默认 + 自定义 1/2/3）。**这是本作可及性里最有价值的一项**——对视距/视野受损玩家，能把 HUD 搬到视野内并放大。**[B]**

### 7.2 "没有难度选项"的得与失

**得**：
1. **数值统一，平衡与社区共识只有一份。** 所有玩家的伤害、姿态、弹药都是同一套表值；讨论"这把枪好不好"不需要先说"我开的什么难度"。**[C]**
2. **难度交给了"可配置的玩法旋钮"而不是菜单。** `90000 锁定自动切换`、`90002/90003 推进操作方式`（长按 vs 切换）、`90005 自动抛弃`、`90004 限幅器解除操作`——**这些直接改变操作负荷**；`自動アセン` 让不想研究配装的人也能过关。**[B]**
3. **难度实际由"任务选择 + 配装"承担。** 打不过的关卡可以换装、换武器、换扩展兵装、调 OS——**难度是一个连续可调的曲面，而不是三档台阶**。**[C]**

**失**：
1. **对无法通过"练"来跨越的玩家没有兜底。** 反应速度/手眼协调受限的玩家，只能靠"更硬的配装"或"更简单的任务"绕，而不是"降低敌人伤害 30%"。而这两条路都需要玩家先理解系统。**[C]**
2. **结算经济惩罚放大了失败成本。** 弹药费和修理费是**按实际消耗**扣的（`80020/80021`），**技术差 → 花钱多 → 更买不起好装备 → 更打不过**是一条真实的负反馈循环。**没有难度选项意味着这条循环没有泄压阀。** **[B/C，字段证据 + 推理]**

**TA 视角的补充**：从工程上讲，"没有难度选项"其实**降低**了 UI 复杂度（不需要难度状态在所有界面穿透），但也**把压力转移到了数值配置与 UI 的信息完备性上**——因为玩家必须能从界面上完整理解"我为什么打不过"。**信息设计在这里承担了难度设计的一部分责任。** **[C]**

---

## 8. 反馈一致性：动效时长 / 音效同步 / 警告优先级

### 8.1 时长表（全部有表证据，B）

| 类别 | 项 | 值 |
|---|---|---|
| 菜单转场 | 背景模糊淡入 / 淡出 | 0.4 s / 0.1 s |
| 菜单转场 | 机库淡入 | 0.18 s |
| 菜单转场 | 简报背景虚化 / 等待 / 倍率 | 0.5 s / 2.0 s / 3.0 |
| 菜单输入 | 机库：手柄输入受理等待 | 0.8 s |
| 菜单输入 | 部件模型旋转：判定"无手柄输入"的时间 | 见 `MenuParam.PartsModelRotationInputWaitTimeSec` |
| 战斗 FE | 命中 FE | 1.0 s |
| 战斗 FE | 被弹 Danger | 2.0 s |
| 战斗 FE | 大伤害判定：阈值 100% HP，判定窗口 2.0 s | — |
| 战斗 FE | 瞬间冲击条淡出开始 / 结合 | 0.8 s / 0.4 s |
| 战斗 FE | 伤害数字累积窗口 | **0.5 s** |
| 战斗 FE | 索敌图标停留 / 淡出 | 2.0 s / 1.0 s |
| 战斗 FE | 作战线淡入 / 淡出 | 2.0 s / 0.5 s |
| Coral 演出 | 弱势 / 强势 淡入 | 0.3 s |
| 血条 | 常规淡出 / 归零淡出 | 1.5 s / 0.3 s |
| 死亡 | 单人 / 幽灵 | 2.5 s / 2.0 s |

**一致性规律（3 条）**：
1. **所有"战斗内瞬时反馈"落在 0.3–2.0 s 区间**，中位数约 1.0 s。**超过 2 s 的只有"索敌图标停留"和"作战线淡入"——这两个都是"状态变化"而不是"事件发生"。**
2. **所有"菜单转场"都在 0.5 s 以内**（0.1–0.5 s），因为菜单是**玩家主动**进入的，不需要"说服"。
3. **淡出 > 淡入**（背景模糊 0.4 in / 0.1 out；作战线 2.0 in / 0.5 out）。

### 8.2 音效与 UI 的同步

- `MenuInputGestureParam` **175 行里 37 行带 SE ID**（实测），且**同一手势可绑不同 SE**：如 `Color: 复制`→SE 1100、`Color: 粘贴`→SE 1100、`Color: 重置`→SE 1150；`前のタブ/次のタブ`→SE **500**；`UI表示切替`→SE **400**。
- **读法**：**UI 音效不是"每个按钮一个音效"，而是"按操作类别共用一小撮 SE"**（实测出现的 SE 号集中在 400 / 500 / 1100 / 1150 附近）。这样耳朵能听到的是**操作类别**（"我在切换分类"vs"我在改值"），而不是"我按了第几个按钮"。**[B]**
- `TutorialParam` 有 `OpenSE (offset 28)` / `CloseSE (offset 32)` 两个独立字段 → **教程弹窗的开关音是数据配置的**。**[B]**
- `FeTextEffectParam`（280 行）：`TextID_1st/2nd/3rd/4th` + `SeID` + `DispSlot` → **文本特效（字幕/大字提示）有独立表**，一个资源可对应最多 4 段文本 + 1 个 SE + 1 个显示槽位。**[B]**
- `FeFreeDialogParam`（31 行）：`DialogGroup` / `DisplayTime` / `BaseRect_left/top/w/h` / `BaseColor_rgba` / `FontColor_rgba` / `FontScale` → **自由对话框的框体位置、底色、字色、字号、显示时长全部是表数据**。**这就是"字幕样式"在数据层的实现——但它是全局配置（31 行 = 31 个对话框组），不是玩家选项。** 这解释了 §7 的负面结论：**字幕样式可配置，只是没开放给玩家。** **[B] ★ 这是一条对 TA 很有价值的发现：可及性功能"没做"和"没开放"是两件事。**

### 8.3 警告优先级

有证据的优先级机制：
- `ActionButtonParam.priority`（重叠时优先级）：实测 144 行值域 **0–10**。
- `ActionButtonParam.sameCategoryActionDisplay`（同类别内重叠显示）+ `regionType` 全为圆柱判定 + `raycastType`（常に判定 119 / 実行範囲外のみ 22 / 判定しない 3）→ **世界空间动作按钮有一个"谁盖谁"的排序系统**。
- `ActionButtonParam.invalidFlag` / `grayoutFlag`（实测各只有 1 行非零）→ **无效态与灰化态是两个不同的视觉状态**，可分别配置。
- `MessageBoxParam.requestPause`（实测 17/141 行为 1）→ **消息框分"暂停游戏"和"不暂停"两类**；`singleActivityCtrl` / `multiActivityCtrl` 非零 42 / 88 → **单机与联机行为不同**（联机不能暂停）。
- `MessageBoxAutoNaviControl` TDF：`続行=0 / 中断=1 / Yesで続行=2` → **消息框的自动导航行为有三级**。

**屏幕警告（Danger / 低血 / 大伤害）的优先级顺序**：本机数据没有给出"警告优先级队列"这样一张表，**标 D**。

---

## 9. 分析三问

### 9.1 如果只显示 AP 和锁定框、隐藏其他所有信息会怎样？

**会变成另一个游戏。** 具体拆解（每条对应一个被切断的信息通道）：

| 被隐藏的 | 直接后果 | 机制依据 |
|---|---|---|
| EN 条 | 玩家无法预判"还能不能 QB/AB"，机动从"资源管理"变成"随机失败" | EN 消费是连续值，且 `ActionPanelChangeThreshold_Vel = 0.5 m/s` 说明面板本身是速度驱动的 |
| 弹药 | 80021「弾薬費」的归因链断裂 → 结算赤字变成不可解释 | 弹药费按实际消耗扣除 |
| 姿态条 | **反击窗口不可见** → 战斗从"打崩 → 处决"退化为"互相对射" | `bodyTrunk_BodyGaugePoint`（敌我双方都有） |
| 射击预兆 | 强攻击无法预判 → 只能靠背板 | `shootIndicationType = 強射撃予兆` |
| 目标标记 | 失去"刚才那个敌人在哪" → 战场空间记忆负担转嫁给玩家 | `LockTargetMarking_*` 四个字段 |
| 作战区域线 | **越界惩罚机制失去可视化** → 玩家会在毫无预告的情况下失败 | `FE_MissionLineWarning*` |

**放大/缩小 10 倍实验（定位边界）**：
- 把 `FE_ShowDamageAccumulationTimeSec` 从 0.5 s 放大到 **5 s**：连射伤害数字合并成一个"每 5 秒跳一次的大数字"，手感从"打击感"变成"血条偶尔跳一下"。
- 缩小到 **0.05 s**：每秒 20 个数字独立弹出，屏幕中心被数字淹没 → 这就是"信息密度"崩溃的样子，也解释了为什么需要 0.5 s 这个中间值。
- 把 `HpBarFadeOutTime` 从 1.5 s 缩到 **0.15 s**：血条几乎看不见（因为战斗中血条大部分时间在动 → 一直在重置淡出计时器？不，会频繁消失）→ 玩家会对自己的血量失去感知。
- 把 `MakerRendRangeWidth/Height`（1650/650）缩小 10 倍：屏内标记只出现在最中心的小区域，**敌方标记从"边缘方向提示"退化成"中心遮挡"**。

**它在解决什么问题 / 有没有更简单替代**：核心矛盾是"信息完整性"与"视觉清晰度"不可兼得。**更简单的替代方案是"常显全部信息 + 让玩家自己忽略"**——很多游戏就这么做，代价是视觉噪声长期存在且无法根治。AC6 选了"事件驱动 + 分级显示 + 可自定布局"这条更贵但更干净的路。

### 9.2 如果装配界面不给数值、只给雷达图会怎样？

**会摧毁这个游戏的核心决策循环。** 理由：

1. **AC6 的配装是"约束满足"而不是"偏好选择"。** 三个硬约束（重量上限、EN 供给、腕部载重）是**硬边界**：超了就 `積載限界超過` / `EN出力不足` / `腕部積載限界超過`（三个独立警告），不是"性能下降"。**雷达图无法表达阈值**——你没法从一个五边形上看出"我离超重还差 12"。
2. **数据表本身就证明了设计者的取向**：`MenuPropertySpecParam` 有 `CompareType`（大者优/小者优）字段 **248/508 行在用**，`FormatType` 有 `±数値`、`通貨`、`0以下はハイフン` 等 30+ 种格式——**整套系统是为了显示"精确数字及其优劣方向"而建的**。若设计意图是雷达图，这 248 行的优劣判定毫无意义。
3. **数字是配装社区的语言。** 讨论"这把枪冲击力 1500"是可验证的；讨论"这把枪的橙色区域比较长"不是。

**放大/缩小实验**：把 `Simple` 那 237 行的"精简视图"再砍到 2 个属性（AP + 重量）→ 列表页可用性其实**提升**（扫得快），但玩家必须逐个点进详情页 → 决策变慢。**这就是"更多信息 ≠ 更好"的实证：AC6 自己就用 `Simple` 前缀承认了这一点。**

**有没有更简单的替代**：可以只做"雷达图 + 超限时数字变红"吗？可以，但你仍然需要数字来告诉玩家"超限多少才能修好"。**所以简化方案能省掉"全量属性列表"，但省不掉"约束数字"。**

### 9.3 如果没有伤害数字会怎样？

1. **失去"配装是否生效"的即时验证。** 换了一把新枪，第一枪打出去看到数字从 320 变 480——这是配装的即时奖励。没有数字，玩家要靠"敌人血条掉得快不快"来判断，而血条本身还在淡出（`HpBarFadeOutTime = 1.5 s`），分辨率极低。**[C]**
2. **失去伤害类型的反馈。** AC6 有三属性（KE / TE / CE）与抗性乘算（`ProCutRate_Mag/Fire/Thunder`，UI 侧还要 `×10 + 150/350/200/300` 换算）。**同样的枪打不同敌人数字不同，是玩家学习"这个敌人弱什么"的唯一高速通道。** 没有数字，玩家只能通过"打了多久"来推断，效率下降一个数量级。**[B/C]**
3. **保留下来的是"视觉打击感"通道。** `GraphicsParam` 有 `BulletMultiFrameHitSfxIntervalTimeSec`（多段命中的 SFX 间隔）、`HitInsDamageNearSfxNumMax` / `HitInsDamageNearSfxDist`（命中 SFX 的数量上限与距离限制）→ **即使没有数字，命中的音画反馈仍然丰富**。所以"删掉伤害数字"不会让战斗变哑，只会让**数值学习通道**消失。

**放大/缩小实验**：把数字放大到占屏 1/3（视觉等价于"3 倍字号"）→ 屏幕中心被数字占据，**遮挡锁定框与姿态条**——而锁定框与姿态条是"能不能打"的信息，优先级高于"打了多少"。**这就是为什么伤害数字必须小且必须累积合并（0.5 s）。**

**更有价值的替代方案**：把数字换成"血条上的分段刻度"或"命中瞬间的抗性图标"。**AC6 没有这么做**——它选择了最"土"但也最可比较、最便于社区讨论的方案：**精确数字**。[C]

---

## 10. 技术 UI 的实现（TA 转化）

### 10.1 数据驱动 UI 的架构：表 → 绑定 → 视图

从 AC6 的表结构可以反推出一套标准分层：

```
[数据层]  数值表（EquipParamWeapon / AtkParam / EquipParamProtector …）
              ▲ 只读，引擎单位，不关心 UI
              │
[取数层]  MenuPropertySpecParam.extract0_*   ← 字段地址注册表 + 公式 + 单位换算
          (Target表, 原始类型, 字节偏移, C0×P+C1 / C0÷P+C1)
              ▲
[语义层]  MenuPropertySpecParam.CompareType / FormatType / EditType / IndexRefParamID
          MenuValueTableParam（值→文本ID）
              ▲
[布局层]  MenuPropertyLayoutParam（LayoutPath 语义槽位 + PropertyID + 显示条件）
          EquipmentMenuManageCategoryParam（列表分类 → 布局ID）
              ▲
[视图层]  界面资源（真正的像素/锚点/动画）
          + MenuColorTableParam（调色板）
          + GraphicsParam/MenuFilter（菜单级后处理）
          + MenuOffscrRendParam/MenuPartsModelRendParam（3D 预览机位）
```

**如何避免 UI 与逻辑耦合（4 条具体做法，均可从这份数据里学到）**：

1. **UI 不存数值，只存"取数配方"。** 数值永远从数据层现取。这消除了"UI 显示的数字和实际生效的数字不一致"这一整类 bug——**前提是配方正确**（见 10.3）。
2. **UI 不写死布局，用语义槽位。** `LayoutPath = "Item_00"` 而不是 `x=1240, y=680`。这样不同分辨率/不同平台共用一套布局逻辑。
3. **UI 不判断业务规则，用数据条件。** `DisplayCondition` 字段（`MenuPropertyDisplayConditionType`：`None=0` / `Booster only=1023`）——**"这个属性只在推进器上显示"是一条数据，不是代码里的 if**。实测 2512 行里 12 行非零（全部 = 1023，即 Booster only）。**[B]**
4. **UI 控件类型不写死，用 `EditType`。** `List selection=1 / Slider-=2 / Button=3` ——同一个属性面板，策划把 EditType 从列表改成滑杆，**界面控件就换了，代码没动**。实测 508 行中 125 行有编辑类型。**[B]**

### 10.2 UI 性能：合批 / DrawCall / 材质数 / 动效开销 / 与 3D 混排

**本机数据能支持的（B）**：
- **UI 与 3D 是混排的。** 菜单有一层全局后处理（`MenuFilter`，噪点每 0.05 s 刷新，28 行预设），并且有独立的离屏渲染机位表（`MenuOffscrRendParam` 140 行）。`GraphicsParam.MenuBackBoke_FadeInTime/FadeOutTime`（0.4 / 0.1 s）说明菜单背后是**实时渲染的 3D 场景 + 模糊**，不是静态背景图。**这意味着 UI 的渲染预算里包含"一整个 3D 场景 + 后处理"，UI 优化不能只盯着 UI。**
- **子窗口 576 × 324**（`GraphicsParam.SubWindow_Width/Height`）——UI 里的 3D 预览窗口分辨率是**低于主画面的固定尺寸**，这是一个明确的性能取舍：预览不需要全分辨率。
- **调色板只有 882 行 / 225 色**，且 864/882 行 alpha=255 → **颜色数量受控，利于材质合批**（同材质的 UI 元素可以合并）。**[C]**
- **`MenuOffscrRendParam.GparamID` 只有 7 个值**（10/11/12/13/14/15/1010），140 行机位共享 7 组图形参数 → **同一批菜单共享材质/光照环境，这是批处理的思路**。**[B/C]**
- **模型初始角度只有 14 行**（按部件类别）→ 预览模型的旋转不做逐件调参，**减少资源变体**。

**本机数据不能支持的（C/D，需运行时验证）**：
- 具体 DrawCall 数、UI 图集数量、UI 材质数、UI Canvas 的 Rebuild 频率。
- **验证方法**：PC 版用 RenderDoc / PIX 抓菜单帧，统计 UI pass 的 DrawCall 与状态切换；或把菜单打开时的 GPU 时间与关闭时对比，得到"菜单开销 = 3D 场景 + UI"的拆分比例。

**一般性 TA 原则（C）**：
- **UI 图集按"同屏共存"分组**，而不是按功能分组。换件界面同屏出现的所有部件缩略图应该在**同一张图集**里，才能一次 DrawCall 画完。
- **避免逐元素材质实例。** 颜色应该走顶点色 / 参数，而不是每个元素一个材质实例——AC6 用**一张 882 行的调色板表 + 顶点色/参数**的做法正是这个思路。
- **文字是最大杀手。** 几十个数值文本意味着几十个字体图集页与几十次 DrawCall。用**同字体同字号的 SDF 图集 + 合批**是标准解法。AC6 把属性格式（`FormatType`）收敛成 30 种，也在减少"同一屏出现多种字号/格式"的概率。**[C]**
- **动效开销**：淡入淡出应走 **材质参数/UV 偏移**（一次 DrawCall 内完成），而不是逐帧改 mesh 或逐元素设 alpha。`MenuFilter` 的噪点是**全屏一层后处理**，成本是 O(1) 而不是 O(元素数)——**这是把"每个元素都要有的效果"提到全屏层做的经典优化**。**[B/C]**

### 10.3 一个"实时数值对比"组件的实现思路（可直接落地）

**目标**：策划在 Excel/JSON 里加一行"武器面板显示冲击力"，UI 自动更新；玩家换件时，面板立刻显示"当前值 / 待选值 / 差值"，且差值的颜色由"大者优/小者优"决定。

**关键设计（每条都能在 AC6 数据里找到对应物）**：

```
StatField {
    id:          "weapon_impact"              // 语义 ID，跨表稳定
    sourceTable: "AttackPara"                 // ← MenuPropertyExtractTargetType 枚举
    memberOffset:528                          // ← extract0_MemberTailOffset
    memberType:  "s32"                        // ← extract0_MemberType（8 种原始类型）
    operation:   "MUL_ADD" | "DIV_ADD"        // ← MenuPropertyExtreactOperationType（只有 2 种！）
    c0: 100.0, c1: 0.0                        // ← extract0_Constant0/1（单位换算在这里）
    compare:     "HIGHER_IS_BETTER"           // ← MenuPropertySpecParam.CompareType
    format:      "INT" | "PERCENT" | "CURRENCY" | "PLUS_MINUS" | "DASH_IF_NEGATIVE"
                                              // ← MenuPropertySpecParam.FormatType
    displayCondition: ["BOOSTER_ONLY"]        // ← MenuPropertyLayoutParam.DisplayCondition
    precision:   0
}
```

**取数管线**：
```
resolve(field, partRow) -> raw = readPrimitive(partRow, field.memberOffset, field.memberType)
                        -> val = applyFormula(raw, field.c0, field.c1, field.operation)
                        -> text = format(val, field.format)
```
**对比管线**：
```
delta = resolve(field, candidateRow) - resolve(field, currentRow)
color = (delta > 0) == (field.compare == HIGHER_IS_BETTER) ? GOOD : BAD
```

**为什么这样设计（能力 → 收益）**：
1. **公式只有两种 → 校验简单、策划可读。** AC6 用 `C0×P+C1` 和 `C0÷P+C1` 覆盖了全部 105 条配方。**不要做通用表达式引擎**——那会让"这个数怎么来的"不可审计。
2. **偏移 + 类型 + 公式是可序列化的 → 可以自动生成代码/文档。**
3. **`CompareType` 让"颜色规则"成为数据。** 无需为"重量越小越好"写特例代码。
4. **`FormatType` 让"显示规则"成为数据。** 也无需为"货币"和"百分比"写特例。
5. **差异计算是 O(1) 单字段读取 → 可以每帧算。** AC6 没有"换件时重算整机"的需求，是因为**汇总值（总重/总 EN/AP）是加法聚合，可以增量更新**。

**★ 必须补的一环：一致性校验（AC6 数据给出的真实教训）**

**教训一：偏移语义必须显式契约化。** 我在本项目的第一次统计里把 `extract0_MemberTailOffset` 当成"字段起始偏移"，得到"**15 / 105（14.3%）条取数配方已失效**"的错误结论，并写下"AC6 自己都有 14% 的配方是坏的"。修正为"**尾偏移**"（`addr = off − sizeof(type)`）后，**105/105 位置命中真实字段，105/105 类型完全一致，失效数为 0**。

> **这正好是"数据驱动 UI"最典型的陷阱：偏移语义没有写在类型系统里，读错不会报错，只会安静地显示错误的数字。** 一个真实案例：`【武器】弾単価` 的配方尾偏移是 732 / 类型 u16 → 正确字段是 `bulletCost 弾薬費`（实测 0–1600，184 行非零，29 个不同值）；若按首偏移读 732，拿到的是一个 f32 的半个字（实测只有 0 和 100 两个值）——**面板上会出现一个永远只显示 0 或 100 的"弹药单价"**。

**教训二：冗余字段会掩盖错误。** 同一批 UI 属性在多个界面复用（`【PC】積載状況` 3 处、`Warn_0/1/2` 4 处），**一个取数错误会同时污染多个界面**，而且"看起来一直有值"（比如全 0 被当成合法值）。

**因此 TA 必须提供**：
> 1. **字段语义注册表**（语义 ID → 表 + **偏移语义标签** + 偏移 + 类型 + 公式 + 单位），而不是让每个属性各自硬编码；
> 2. **CI 校验**：构建时遍历所有 StatField —
>    - 计算出的字段起始是否落在该表行宽内；
>    - 该处的 paramdex 声明类型是否与 `MemberType` 一致（AC6 这 105 条是 100% 一致，所以**类型不一致 = 一定是错的**，这是最廉价也最强的断言）；
>    - 该处的字段名是否是 `pad*`（是则告警——意味着偏移语义读错或定义滞后）；
>    - 读取全表该字段的值域，若"全为 0"或"只有 1–2 个不同值"而该属性在 UI 上是个连续量 → 告警（这正是 `@492` 与 `@732` 两个坑的指纹）；
> 3. **变更影响分析**：数值表结构变更时，自动列出受影响的 UI 属性；
> 4. **运行时兜底**：取到全零/越界值时 UI 显示占位而非 0（AC6 是否这么做我无法验证，标 D）。

### 10.4 TA 在这套体系里的职责边界

| 界内（TA 该做） | 界外（不该 TA 做） |
|---|---|
| 表结构设计与字段语义注册表 | 具体某个部件该有多少 AP（数值策划） |
| 取数配方 DSL、单位换算层、`FormatType` 实现 | 某个属性该显示成什么单位（需策划确认） |
| 布局数据 → 控件的运行时绑定系统 | 这个界面该放哪些属性（UI/UX 设计） |
| 一致性校验 CI、类型/值域断言 | 数值平衡 |
| UI 图集策略、合批、材质数、文字渲染 | 单个图标的绘制 |
| UI 与 3D 混排的渲染顺序、后处理接入（`MenuFilter`） | 后处理的美术风格 |
| 离屏渲染机位系统（`MenuOffscrRendParam` 那种） | 机位对应的美术构图 |
| HUD 布局编辑器的数据模型与保存 | 默认布局长什么样 |
| UI 动效时长表（`MenuParam` 那种单例表）与曲线 | 动效是"弹一下"还是"滑一下" |
| 可及性选项的**数据通路**（字号/色板/重映射能不能配） | 开放哪些选项（产品决策） |

**一句话**：**TA 造的是"从表到像素"的管道，以及保证这条管道不会安静地出错。**

---

## 11. 实测证据（命令与原始输出）

> 全部命令在本机 `<repo>` 下执行。工具：`tools/paramdex_fields.py`（paramdex 字段定义 + 行宽比对）、自建 `_p10/dump.py`（按 paramdex 偏移取值）、`_p10/extract_map.py`（extract 配方 → 字段名反查）、`_p10/analyze*.py`（分布统计）。

**（1）表结构 + 行宽比对（paramdex 与实际数据精确吻合）**

```
$ python tools/paramdex_fields.py MenuPropertyLayoutParam
# MenuPropertyLayoutParam  <-  paramdex: MenuPropertyLayoutParam.xml
# 字段数 6, 计算结构大小 32 字节
# 实际: 2512 行 x 32 字节  -> SIZE MATCH
偏移     类型         字段名                                            日文显示名
0      fixstr     LayoutPath[16]                                 レイアウトパス
16     u32        PropertyID                                     プロパティID
20     s32        CaptionTextID                                  項目名テキストID
24     s32        HelpTextID                                     ヘルプテキストID
28     u16        DisplayCondition                               表示条件
```

```
$ python tools/paramdex_fields.py MenuPropertySpecParam
# 字段数 29, 计算结构大小 108 字节
# 实际: 508 行 x 108 字节  -> SIZE MATCH
0      s32        CaptionTextID          4      s32  IconID
8      u32        RequiredPropertyID     12     s8   CompareType        優劣判定
13     u8         FormatType             36     u8   EditType           編集タイプ
38     s16        IndexRefParamID        68     u16  extract0_Target    対象
70     u8         extract0_MemberType    71     u8   extract0_Operation 補正式
72     s32        extract0_MemberTailOffset   76 f32  extract0_Constant0 補正用定数0
80     f32        extract0_Constant1     88-100      extract1_*（同构）
```

其余逐表行宽比对（全部 `SIZE MATCH`）：`MenuParam 1×424`、`MenuValueTableParam 270×12`、`MenuColorTableParam 882×4`、`MenuBehaviorParam 31×32`、`MenuInputGestureParam 175×16`、`MenuOffscrRendParam 140×80`、`MenuPartsModelRendParam 14×4`、`MenuFilter 28×52`、`KeyAssignDisplayParam 58×32`、`KeyAssignMenuItemParam 24×16`、`ActionButtonParam 144×112`、`MessageBoxParam 141×24`、`GraphicsParam 1×200 (SIZE DIFF −4，表尾有 4 字节额外数据)`。
**⚠ 注意**：`GraphicsParam` 是唯一不匹配的表（paramdex 计算 196，实际 200）。引用 `GraphicsParam` 的字段值时我已用 paramdex 偏移读取并复核值域合理（`SubWindow 576×324`、`ZoomBlur_ThresholdSpeedKmH 100`），但**"该表 paramdex 定义可能滞后 4 字节"这一点请保留怀疑，标 D。**

**（2）`MenuParam` 单例表实际取值（FE/HUD 全局时序）**

```
$ python _p10/dump1.py MenuParam van "HpBar|HitFE|Danger|Volatilize|TargetState|LockSite|DoubleLock|MiniMap|Maker|Damage|Garage|DisableLock|LargeDamage|LowHP"
### van/MenuParam  rows=1 rowsize=424
  TargetStateSearchDurationTime      見つかりそうFE：Searchアイコンの表示時間[秒]     = 2.0
  TargetStateBattleDurationTime      見つかりそうFE：Battleアイコンの表示時間[秒]     = 2.0
  VolatilizeFadeBeginSec             FE：瞬間衝撃ゲージフェード時間[秒]              = 0.8
  MakerRendRangeWidth                マーカーの描画範囲幅（FullHD準拠）             = 1650
  MakerRendRangeHeight               マーカーの描画範囲高（FullHD準拠）             = 650
  HpBarFadeOutTime                   体力バーのフェードアウト開始時間[秒]            = 1.5
  ZeroHpBarFadeOutTime               体力0になった時の体力バーフェードアウト開始時間[秒]  = 0.3
  HitFEViewTime                      ヒットFE表示時間[sec]                       = 1.0
  VolatilizeCombineSec               FE：瞬間衝撃ゲージ結合時間[秒]                = 0.4
  MiniMap_WorldDispRange             ミニマップ：ワールド表示範囲[m]                = 1200.0
  MiniMap_RaderRange                 ミニマップ：レーダーの範囲[m]                 = 2000.0
  EnemySearchIconFadeOutTime         索敵FE_探知状態フェードアウト時間[sec]           = 1.0
  LockSite_DisableLockDistance       補完を行なわない…画面座標上の距離              = -1.0
  DangerFEViewTime                   被弾時のDanger表示時間[sec]                 = 2.0
  MiniMap_RepairPointAlphaBeginHeith  ミニマップ：修理ポイント透明化開始高度差[m]       = 600.0
  MiniMap_RepairPointAlphaEndHeith   ミニマップ：修理ポイント透明化完了高度差[m]       = 800.0
  MiniMap_ChangeInterval             ミニマップ：表示切替間隔[sec]                 = 0.0
  DoubleLockSightOffset              二丁拳銃時にロックサイトを中心位置からずらす距離（px） = 350.0
  DisableLockCursorAlpha             射撃不可時のロックカーソルのアルファ値           = 40.0
  ItemGetLogAliveTime                アイテム取得ログ：１行の表示時間[sec]            = 6.0
  FE_LowHP_rate                      HP少の閾値                                = 30
  FE_LowBarrier_rate                 バリア少の閾値                              = 30
  FE_LargeDamageDetect_HP_rate       大ダメージ判定ダメージ量(％)                     = 100
  FE_LargeDamageDetect_CollectTime   大ダメージ判定時間(秒)                         = 2.0
  Garage_FadeTime                    ガレージ：フェード演出時間(秒)                   = 0.18
  Garage_CamPadWaitTime              ガレージ：パッド入力受付待機時間(秒)              = 0.8
  Garage_BriefingBokeTime            ブリーフィング：ぼかし時間                        = 0.5
  Garage_BriefingBokeWaitTime        ブリーフィング：カメラアニメありのときのぼかし待機時間  = 2.0
  Garage_BriefingBokeRate            ブリーフィング：ぼかし率                          = 3.0
  FE_ShowDamageAccumulationTimeSec   ダメージ表示累積時間[sec]                      = 0.5
  HackingGaugeFadeOutTime            ハッキングバーのフェードアウト開始時間[秒]          = 1.0
  CamLockInterpolationFactor         カメラ固定時補間係数                            = 40.0
  CamUnlockInterpolationFactor       カメラ固定解除時補間係数                          = 1.0
  FE_MissionLine_FadeInTime          FE：作戦ラインフェードイン時間[s]                 = 2.0
  FE_MissionLine_FadeOutTime         FE：作戦ラインフェードアウト時間[s]                = 0.5
  FE_MissionLine_Width               FE：作戦ライン表示横幅[m]                      = 300.0
  FE_MissionLineWarningStartLineDist FE：作戦ライン警告表示開始距離[m]                = 200.0
  FE_MissionLineWarningLineDist      FE：作戦ライン警告表示距離[m]                   = 100.0
  FE_MissionRegionStartLineDist      FE：作戦領域線表示開始距離[m]                   = 200.0
  FE_MissionRegionLineDist           FE：作戦領域線表示距離[m]                      = 100.0
  FE_MissionRegionLineHeight         FE：作戦領域線縦幅[m]                         = 3.0
  FE_MissionRegionLineTexTile        FE：作戦領域線タイリングスケール[m]               = 10.0
  FE_MissionRegionLineHeightOffset   FE：作戦領域線高さオフセット[m]                  = 12.0
  FE_MissionRegionLineAddBlend       FE：作戦領域線加算ブレンドにするか               = 1
  FE_MissionRegionLineUseSfx         FE：作戦領域をSFXで表示するか                   = 0
  FE_RegionEdgeTexWidth              FE：作戦領域テクスチャ幅[m]                     = 30.0
  FE_RegionEdgeTexHeight             FE：作戦領域テクスチャ高さ[m]                    = 8.0
  FE_Region_UpperLimitDist           FE：作戦領域上限判定距離[m]                     = 50.0
  FE_Region_LowerLimitDist           FE：作戦領域下限判定距離[m]                     = 100.0
  ActionPanelChangeThreshold_Vel     アクションパネル切り替え判定_プレイヤー速度[m/sec]   = 0.5
  ActionPanelChangeThreshold_PassTime アクションパネル切り替え判定_プレイヤー速度判定時間[sec] = 0.0
  SoloPlayDeath_ToFadeOutTime        ソロプレイ死亡時フェードアウト開始時間[秒]          = 2.5
  PartyGhostDeath_ToFadeOutTime      ホワイト、ブラックゴースト死亡時…[秒]            = 2.0
```

**（3）提取配方统计（`_p10/analyze2.py` + `_p10/extract_map.py`）**

```
== MenuPropertySpecParam: 508 行
CompareType 分布: [(0, 260), (1, 205), (2, 43)]
EditType 分布: [(0,383,'----'), (1,53,'List selection'), (2,45,'Slider-'), (3,27,'Button')]
extract0_Target 分布: [('None',403),('Armor',32),('Weapon',24),('booster',13),('FCS',7),
                       ('Attack',6),('Bullet',6),('Behavior',5),('generator',5),
                       ('ChildBullet_Atk',2),('GrandBullet_Atk',2),('ChildBullet',2),('GrandDangan',1)]
extract0_MemberType 分布: [('invalid',403),('f32',72),('s32',16),('u16',7),('s16',5),('u32',3),('s8',1),('u8',1)]
extract0_Operation 分布: [('None',474),('C0*P+C1',32),('C0/P+C1',2)]
使用 extract0 的行数=105, 使用 extract1 的行数=4
compareType != 0 的行数=248
EditType != 0 的行数=125
IndexRefParamID != -1 的行数 = 83 / 508 ；用到的槽: Float_01(65) Float_00(5) Float_14(2) …
```

**（4）★ 关键：`extract0_MemberTailOffset` 是"尾偏移"的实测证明**

规则检验（脚本：遍历 508 行 `MenuPropertySpecParam`，取 `extract0_Target`/`extract0_MemberType`/`extract0_MemberTailOffset`，在对应 paramdex 表里解析字段）：

```
可判定(有类型)记录 = 105
  off    -> 落在 pad/? 的比例 = 6/105 = 5.7%
  off-4  -> 落在 pad/? 的比例 = 1/105 = 1.0%
  TAIL   -> 落在 pad/? 的比例 = 0/105 = 0.0%     ← addr = off - sizeof(MemberType)
  off+4  -> 落在 pad/? 的比例 = 6/105 = 5.7%

语义比对(汉字二元组重叠): TAIL 胜 42, off 胜 5, 并列/无法比对 58

== TAIL 规则下：类型一致性检验（105 条）==
  解析不到字段 : 0
  落在 pad 字段 : 0
  类型一致(含同宽符号差异) : 105
  类型不一致 : 0
```

**105/105 位置命中真实字段 + 105/105 类型完全一致 + 0 条落到填充字段。** 抽样对照：

```
pid     UI项                       表                      tailoff type  | off 处字段(✘)                    | TAIL 处字段(✔)
2024    【武器】弾単価                 EquipParamWeapon        732    u16   | depletedUraniumToxicPaGuardR…   | bulletCost
2013    【武器】PA干渉                 AtkParam                528    u16   | impactPower                     | atkPa
2025    【武器】衝撃力（子弾丸）           AtkParam                532    s32   | damageLevelConvId               | impactPower
2027    【武器】残留衝撃（子弾丸）          AtkParam                992    s32   | hit0_sfxmodelId                 | residualImpactPower
3013    【防具】安定性能                EquipParamProtector     492    s32   | energyRecoveryDelayTimeForEm…   | stability
3302    【ARM】射撃運動性能              EquipParamProtector     488    f32   | stability                       | shootMotionPerf
3301    【ARM】反動制御                 EquipParamProtector     500    f32   | energyDrain_FourLegFlyMove      | recoilCtrl
3300    【ARM】腕部積載許容量             EquipParamProtector     572    f32   | AppropriateType_Energy          | armMaxWeight
3204    【CORE】ラジエーター性能           EquipParamProtector     884    f32   | pad_end[16]                     | generatorCoolPerf
3505    【GENE】EN武器適正              EquipParamGenerator     44     u32   | pad_end[14]                     | AppropriateType_Energy
2015    【武器】チャージ中EN負荷           EquipParamWeapon        1120   s32   | pad04_2[2]                      | consumeEN_Charging
2038    【武器】二段チャージ時間            EquipParamWeapon        1032   f32   | pad_05_3[4]                     | chargeLv2EndTimeSec
3708    【ブースター】アサルトブースト消費EN    EquipParamBooster       284    f32   | pad_2[2]                        | assaultBoost_DrainEnPointPerSec
2012    【武器】マガジンリロード            EquipParamWeapon        928    f32   | chargeEndTimeSec                | magazineReloadTimeSec
2048    【武器】格闘コンボ数              EquipParamWeapon        1465   s8    | menu_AtkPowerCondType           | menu_MeleeComboCount
3403    【脚部】ブレーキ性能              EquipParamProtector     480    f32   | groundQbAddSpeedKMH             | landBrakeScale
```

**相关字段值域复核（用于交叉验证偏移语义）**：

```
# EquipParamProtector（121 行 × 900 字节，paramdex SIZE MATCH）
Protector @480 landBrakeScale                    min=0.0 max=386.0 非零=23 不同值=22
Protector @484 shootMotionPerf                   min=0   max=160   非零=20 不同值=21
Protector @488 stability                         min=0   max=1500  非零=69 不同值=70
Protector @492 energyRecoveryDelayTimeForEmptySec min=0.0 max=0.0  非零=0  不同值=1   ← 全零，误读的指纹
Protector @496 recoilCtrl                        min=0.0 max=232.0 非零=20 不同值=21

# EquipParamWeapon（284 行 × 1556 字节）
Weapon @728 operationPartsId                     min=0 max=0     非零=0    不同值=1
Weapon @730 bulletCost                           min=0 max=1600  非零=184  不同值=29   ← 真正的"弾薬費"
Weapon @732 depletedUraniumToxicPaGuardResistRate min=0.0 max=100.0 非零=2  不同值=2    ← 误读的指纹

# AtkParam_Pc（712 行 × 1040 字节）
AtkParam_Pc @526 atkPa                           min=0 max=4800  非零=430  中位=89
AtkParam_Pc @528 impactPower                     min=-1 max=6000 非零=660  中位=45
AtkParam_Pc @988 residualImpactPower             min=0 max=3840  非零=233  中位=0
AtkParam_Pc @992 hit0_sfxmodelId                 min=-1 max=83100 非零=712 中位=-1
```

```
# EquipParamWeapon（284 行 × 1556 字节）menu_SrcGeneration* 实测分布
@1446 menu_SrcGenerationAtkPower  : [(0,205),(1,46),(2,17),(4,12),(3,4)]
@1452 menu_SrcGenerationDirectHit : [(0,205),(1,46),(2,17),(4,12),(3,4)]
@1453 menu_SrcGenerationImpact    : [(0,205),(1,46),(2,17),(4,12),(3,4)]
@1454 menu_SrcGenerationResidualImpact: [(0,205),(1,46),(2,17),(4,12),(3,4)]
@1456 menu_SrcGenerationHoming    : [(0,236),(1,38),(2,8),(4,2)]
@1459 menu_SrcGenerationRange     : [(0,251),(1,25),(2,8)]
@1460 menu_ShowConsumeBullet      : [(1,284)]   ← 全部为 1
@1461 menu_ShowAddHeat            : [(1,284)]   ← 全部为 1
@712  assembleMenuCategory        : [(1,'ARM UNIT',95),(0,'表示しない(ダミー)',82),(5,'R BACK UNIT',41),
                                     (4,'L BACK UNIT',40),(2,'BLADE',14),(3,'SHIELD',8),(7,'ASSAULT DRIVE',4)]
```

**（5）布局表的复用度（`_p10/analyze.py`）**

```
== MenuPropertyLayoutParam: 行数=2512, 不同 LayoutPath 数=125
DisplayCondition 非零行数: 12 / 2512   （值分布: {0:2500, 1023:12}）
PropertyID==0 行数: 882
== 出现次数最多的 PropertyID（跨布局复用）==
     101 x101  【アイテム共通】 説明
     103 x95   【アイテム共通】 重量
     122 x93   【アイテム共通】 消費EN
     2090 x73  【射撃攻撃】攻撃性能
     2009 x73  【武器】衝撃値
     2000 x63  【武器】装弾数
     100 x51   【アイテム共通】 名前
     123 x50   【アイテム共通】 カテゴリ名
     1900 x39  【武器】属性_アイコン
```

**（6）调色板（`_p10/analyze3.py`）**

```
== MenuColorTableParam: 882 行, 不同 RGBA 组合=225
   alpha 分布: [(255, 864), (0, 6), (200, 4), (128, 3), (64, 3), (160, 1), (100, 1)]
   最高频 10 色: [('#0C0C0C',255,68), ('#686868',255,51), ('#3A3A3A',255,38), ('#232323',255,33),
                  ('#808080',255,20), ('#FF2E2E',255,19), ('#FFFFFF',255,18), ('#AEAEAE',255,18),
                  ('#556EFF',255,15), ('#DCDCDC',255,15)]
   （开发者行名）4 Minimap: Enemies: Normal / 5 Search / 6 Combat / 7 Radar range normal /
                8 Radar range after hacking / 9 Minimap: Enemy visibility / 10 FE 作戦領域 / 11 FE 警告領域
```

**（7）锁定系统全参数（`TentativePlayerParam`，2 行 × 2112 字节，行 0 实测）**

```
lockRangeHorizontalScreenRatio  = 0.45      lockRangeVerticalScreenRatio = 0.55
normalLock_MaxDist              = 450.0     normalLock_1stLockDist       = 450
missileLock_MaxDist             = 280.0     missileLock_MaxLockNum       = 4
multiLockTaretNumMax            = 10        triggerContinueTimeToMultiLock = 0.5
LockSiteWidthScale              = 2.0       LockSiteHeightScale          = 1.3
lockCamParamLerpRate            = 0.15      LockOnRangeOutRemineTime     = 1.5
KeepLockWhenTgtInvisibleTime    = 0.0       wallThroughLockRange         = 9999.0
LockTargetMarking_ChachDist     = 600.0     LockTargetMarking_ChachAngleDeg = 30.0
LockTargetMarking_TimeOutSec    = 2.0       LockTargetMarking_ForgetDist = 700
AimActLockRangeScale            = 2.0       bladeKeepLockTime            = 0.8
DeadLockOnDisableWaiteFrame     = 24        geomLockEnableRange          = 200.0
chrFrontScoreDirectionWeightWhenUnlock = 9000.0 (行0) / 5000.0 (行1)
lockRangeAngleWhenSwitchTarget  = 180.0 (行0) / 60.0 (行1)
lockRangeDistanceForBackLock    = 400.0 (行0) / 130.0 (行1)
```

**（8）菜单 3D 预览（离屏机位 / 部件角度）**

```
== MenuOffscrRendParam: 140 行, 按 GparamID 分组 = 7 组
  GparamID=10 x3 / 11 x59 / 12 x1 / 13 x1 / 14 x1 / 15 x2  ← 魂系角色预览遗留（67 行）
  GparamID=1010 x73                                        ← AC6 机体用（73 行）
  camDist 值域 1.5 ~ 2000.0 ; camFov 值域 8.0 ~ 40.0 ; legType4Leg/TankRefParamId 各 2 行非零
  开发者行名示例：50 機体フルスクリーン表示用 / 60 機体ビューモード用 /
                 3010 機体データメニュー：サムネイル / 4000-4033 UGC確認用機体画像 前後左右
                 （普通 / 4脚用 / タンク用 / フロート用 各 4 张）

== MenuPartsModelRendParam: 14 行, initModelDegX/Y:
   [(0,0),(0,0),(0,0),(0,0),(0,0),(-20,0),(-20,45),(-20,0),(-20,0),(-20,0),(-20,0),(20,0),(-20,45),(-20,-45)]
  开发者行名：10000 AM_M_XXXX / 20000 BD_M_XXXX / 30000 HD_M_XXXX / 40000 LG_M_XXXX /
             50000 BS_A_XXXX / 60000 WP_A_XXXX / 68960·68970 F.C.S. / 68980·68990 generator /
             69000 LimiterRelease / 70000 WP_L_XXXX / 80000 WP_R_XXX
```

**（9）前端画面注册表（`MenuBehaviorParam` 全 31 行）**

```
0      tut=2000000 help=0  Prohibited from use（使用禁止）
1000   tut=2000000 help=1  ASSEMBLY
1001   tut=2002100 help=1  TRIAL FIT            1002 tut=2002000 help=1 BUY
1003   tut=2002010 help=1  SELL                 1004 tut=2009000 help=1 OS TUNING
1005   tut=2006000 help=1  AC TEST
2000   tut=2003000 help=1  PAINT(Top)           2001 tut=2003100 help=1 MARKING
2002   tut=2003100 help=1  DECAL(Top)           2003 tut=2003300 help=1 CUSTOM DESIGN(Top)
2004   tut=0 help=1        PAINT(edit)          2005 tut=0 help=1 DECAL(layer editing)
2006   tut=0 help=1        CUSTOM DESIGN(layer editing)   2007 tut=0 help=1 CUSTOM DESIGN(piece editing)
3000   tut=2005000 help=1  AC DATA
4000   tut=2001000 help=1  MISSION              4001 tut=2001100 help=1 REPLAY MISSION
4002   tut=2004000 help=1  ARENA                4003 tut=2007000 help=1 TRANING
5000   tut=2004140 help=1  PLATE EDIT           5001 tut=2004150 help=1 PLATE SHOP
5002   tut=2004120 help=1  SOLO MATCH           5003 tut=2004130 help=1 TEAM MATCH
5004   tut=2004110 help=1  CUSTOM MATCH         5005 tut=0 help=0 YOUR DATA
5006   tut=0 help=1        AC DATA SHARING      5007 tut=0 help=1 CUSTOM DESIGN SHARING
5008   tut=2008000 help=0  ARCHIVES             5009 tut=2004101 help=0 ONLINE ARENA
5011   tut=2008100 help=0  TIPS
```

**（10）选项菜单（62 条，PropertyID 90000–91000）**

```
90000 【ゲームオプション】ロックオン自動切換  fmt=130 【オプション】ON・OFF       edit=1 列表
90001 【ゲームオプション】コントローラ振動     fmt=0                          edit=2 滑杆
90002 【ゲームオプション】ブースト操作        fmt=134 ブースト操作タイプ          edit=1
90003 【ゲームオプション】アサルトブースト操作  fmt=135                          edit=1
90004 【ゲームオプション】リミッター解除操作    fmt=136                          edit=1
90005 【ゲームオプション】オートパージ       fmt=130 ON・OFF                  edit=1
90010/90011 【カメラオプション】操作上下/左右  fmt=131 ノーマル・リバース          edit=1
90012 【カメラオプション】カメラ上下リセット  fmt=130 ON・OFF                  edit=1
90013 【カメラオプション】カメラ速度          fmt=0                          edit=2
90020 【表示オプション】字幕表示             fmt=130 ON・OFF                  edit=1
90022 【表示オプション】HUDカラー(ボタン)     fmt=0                          edit=3 按钮
90023 【表示オプション】HUDレイアウト(ボタン)  fmt=139 【オプション】HUDレイアウト     edit=3
90024 【表示オプション】HDR                 fmt=130 ON・OFF                  edit=1
90025/90026 【表示オプション】輝度調整/画質調整(ボタン)  fmt=0               edit=3
90030-90033 【音響オプション】BGM/SE/ボイス/全体音量  fmt=0                  edit=2
90090 【ボタン設定】ボタン割り当て            fmt=132 プリセット・カスタム         edit=1
90091 【ボタン設定】ボタン割り当て詳細設定(ボタン) fmt=0                        edit=3
90100 【入力機器設定】操作ガイド対象デバイス   fmt=137                          edit=1
90101-90103 【入力機器設定】マウス感度/左右/上下  fmt=0 / 131 / 131             edit=2/1/1
90104 【入力機器設定】キー設定               fmt=0                          edit=3
90150/90151 【言語設定】テキスト/ボイス        fmt=110/111 【言語】                edit=3
90200-90222 【グラフィック】15 项 + 【グラフィック詳細】13 项
```

**（11）HUD 布局编辑器（输入手势 + 布局槽位）**

```
$ python _p10/analyze3.py  → MenuInputGestureParam rid>=9000
9201  key=10000  guideText=-1  HUD: Position X -- HUD：位置X
9202  key=10001  guideText=-1  HUD: Position Y -- HUD：位置Y
9204  key=10002  guideText=-1  HUD: Scale X   -- HUD：スケールX
9205  key=10003  guideText=-1  HUD: Scale Y   -- HUD：スケールY
9206  key=10007  guideText=-1  HUD: Opacity   -- HUD：不透明度
250/251/252  カラーピッカー：H / S / V
1202/1203/1204/1205  カラー：コピー / ペースト / リセット / 登録（SE 1100/1100/1150/—）
9100-9105  割り当て解除 / 初期化 / 割り当てキャンセル / 前・次カテゴリ / カスタム設定の削除
$ 开发者行名（MenuValueTableParam）
139 【オプション】HUDレイアウト：デフォルト / カスタム1 / カスタム2 / カスタム3
```

**（12）结算界面字段（`MenuPropertyLayoutParam` 布局路径 + PropertyID）**

```
80000 totalBalance  pid=80090  【リザルト】収支：合計
80001 in_Total      pid=80019  【リザルト】収入：合計
80002 in_0          pid=80001  【リザルト】収入：基本報酬
80003 in_1          pid=80003  【リザルト】収入：特別加算合計
80008 out_2         pid=80004  【リザルト】収入：特別減算合計
80005 out_Total     pid=80039  【リザルト】費用：合計
80006 out_0         pid=80020  【リザルト】費用：修理費
80007 out_1         pid=80021  【リザルト】費用：弾薬費
```

**（13）实战按钮 / 消息框 / 教程的量级**

```
== ActionButtonParam: 144 行
   regionType 分布: [('円柱',144)]   textBoxType: [('アクションボタン',144)]
   raycastType 分布: [('常に判定する',119),('実行範囲外のみ判定',22),('判定しない',3)]
   iconID 分布: [1 通常 x77, 2 ハッキング x25, 6 ハッキングLv3 x24, 5 ハッキングLv2 x17, 3 補給 x1]
   priority 值域 0~10 ; execButtonHoldSec 全 0 ; invalidFlag/grayoutFlag 各 1 行非零
== MessageBoxParam: 141 行, msgCategory 分布: [(204,72),(203,69)]
   requestPause=1 行数=17 ; singleActivityCtrl 非零=42 ; multiActivityCtrl 非零=88
== TutorialParam: 201 行, MenuResourceType 分布:
   105 モーダル：ムービー(インゲーム用) x91
   2   トースト：キーガイド x51
   101 モーダル：画像あり x34
   100 モーダル：画像なし x24
   0   トースト：１行テキスト x1
   有 ImageID 的行=124, 有 Keyguide* 的行=54
```

**（14）涂装预设（`PlayerColoringPresetParam` 6 行 × 392 字节）**

```
rid=0 slot0_PatternID=0 slot0_Base=(128,128,128,255) slot0_Sub=(60,60,60,255)
rid=1 slot0_PatternID=0 slot0_Base=(255,0,0,255)     slot0_Sub=(60,60,60,255)
rid=2 slot0_PatternID=0 slot0_Base=(0,0,255,255)     slot0_Sub=(60,60,60,255)
rid=3 slot0_PatternID=0 slot0_Base=(255,255,0,255)   slot0_Sub=(60,60,60,255)
rid=4 slot0_PatternID=0 slot0_Base=(255,96,160,255)  slot0_Sub=(60,60,60,255)
rid=5 slot0_PatternID=0 slot0_Base=(0,255,0,255)     slot0_Sub=(60,60,60,255)
每行 392 字节 = 20 个 slot × (PatternID + 2×MaterialProperty + 5 通道 × RGBA4)
```

**（15）字幕样式的数据层证据（`FeFreeDialogParam` 31 行 × 64 字节）**

```
0   s32  DialogGroup      ダイアロググループ
4   f32  DisplayTime      表示時間(秒)
8/12/16/20  f32  BaseRect_left/top/w/h   下地の位置(左/上)、幅、高さ
24-27  u8  BaseColor_r/g/b/a             下地色
28-31  u8  FontColor_r/g/b/a             テキスト色
32  f32  FontScale        フォントの大きさ        （实测 = 1）
```

**（16）UI 相关的全球秒表（`GraphicsParam` 1 行 × 200 字节）**

```
SubWindow_Width  = 576        SubWindow_Height = 324
MenuBackBoke_FadeInTime  = 0.4   MenuBackBoke_FadeOutTime = 0.1
ZoomBlur_ThresholdSpeedKmH = 100.0  ZoomBlur_InterpolationTime = 0.4  ZoomBlur_Pow = 0.002
ZoomBlur_CenterOffset = -1.7   ZoomBlur_Contrast = 0.0
ZoomBlur_UVOffsetUp = 0.03     ZoomBlur_UVOffsetDown = 0.03
```

---

## 12. 存疑清单与验证路径

### 12.1 标为 D 级（不确定）的结论 —— 共 9 条

| # | 结论 | 为什么不确定 | 如何验证 |
|---|---|---|---|
| D1 | `TentativePlayerParam` 的 **2 行**分别对应哪种锁定模式/难度档 | 本机该表无 `Names/` 与 `Developer Names/` 行名文件；两行多数字段相同，只有 5 个字段不同 | 查 Smithbox 的 AC6 行名定义；或对比 mod（`mob/`、`reibis/`）中该表是否被改写 |
| D2 | `HUDカラー` 子界面是否包含色盲友好配色 | 选项表只能看到入口按钮（`90023/90022` 均为 `EditType=Button`），子界面内容不在本机提取范围内 | 进游戏打开 `显示选项 → HUD 颜色`，截图记录有哪些可选配色 |
| D3 | 「尾偏移」这一语义是否是引擎的真实读法（本报告的推断基于 105/105 的类型一致性，但仍是从数据反推） | 我没有反编译代码，只能从"位置全中 + 类型全对"反推；理论上仍可能是别的等效读法 | 反汇编/反编译菜单取数函数，确认是 `read(offset - size, type)`；或在 mod 中把某条 tailoffset 改 ±4，观察游戏内该面板数值是否跳变 |
| D4 | `GraphicsParam` paramdex 结构 196 与实际 200 差 4 字节的原因 | 该表是唯一 SIZE DIFF 的表 | 用 Smithbox 重新导出该表定义；或核对表尾 4 字节是否为额外数据 |
| D5 | 屏幕警告（Danger/低血/大伤害）之间的**优先级队列** | 本机数据里没有一个显式的"警告优先级"表 | 同时触发多个警告，观察实际显示顺序；或查 UI 资源里的动画优先级 |
| D6 | UI 的 **DrawCall / 图集数量 / UI 材质数** | 运行时指标，静态数据表无法给出 | PC 版用 RenderDoc 抓一帧菜单，统计 UI pass 的 DrawCall 与状态切换次数 |
| D7 | `MenuFilter` 的 28 个滤镜分别用在哪些界面 | 只读到参数（噪点/对比度/中央减淡），没有"哪个界面用哪个"的映射 | 在游戏内切换各界面，对比是否有噪点/对比度差异；或查界面资源引用 |
| D8 | HUD 各元素的**具体屏幕坐标** | 坐标在界面资源里，不在 param 数据里 | 全屏截图测量像素位置；或用 HUD 布局编辑器读出各元素的默认锚点 |
| D9 | 58 条"标签为假名/符号、无法用汉字比对"的配方是否也全部正确 | 类型一致性已 105/105，但语义只人工核对了约 20 条 | 对 58 条逐条人工比对：进游戏看该面板项名称，回到 paramdex 找对应日文 DisplayName，确认是同一条 |

### 12.2 最值得用本地数据继续挖的 1 条

> **把 105 条取数配方全部还原成"UI 属性 → 数据源字段"的对照表，再与 `MenuPropertyLayoutParam` 的 2512 行槽位表 join，画出"哪个界面显示哪个字段"的全景图。**
> 位置与类型已经 105/105 对齐（见 §11(4)），**缺的是"语义确认"**：把人工核对从约 20 条扩到 105 条，产出一份可直接交付的文档 —— 对复刻/移植是最直接的输入：**你不需要逆向菜单逻辑，只需要知道"这一栏读哪张表的哪个字段、乘以多少、按什么方向判优劣、按什么格式显示"。**
> 具体做法：
> 1. 对每条配方算 `fieldStart = tailOffset − sizeof(memberType)`，读出 paramdex 字段名 + 日文 DisplayName；
> 2. join `MenuPropertyLayoutParam`（`PropertyID` → `LayoutPath`），得到每一屏显示的字段清单；
> 3. 对每个字段跑全表值域统计（min/max/不同值数/非零行数）——**值域退化（全 0 或只有 1–2 个不同值）就是读错的指纹**（`@492` 与 `@732` 两个案例正是如此）；
> 4. 输出 CSV：`界面 | 槽位 | 属性名 | 源表 | 字段 | 类型 | 公式 | C0 | C1 | 优劣方向 | 显示格式 | 值域`。
> 命令起点：`python _p10/extract_map.py`（105 条配方 → 字段名映射）、`python _p10/analyze.py`（布局反查）。
> **这份产物可以直接用于验证/复刻 AC6 的装配界面数值面板。**

### 12.3 其它验证路径（按表）

| 想验证的问题 | 去查哪张表 | 具体字段 |
|---|---|---|
| HUD 有哪些元素可以关 | `MenuPropertySpecParam` + `MenuPropertyLayoutParam` + `MenuInputGestureParam` | PropertyID 90000–90230 段 + `LayoutPath` 含 `HUD` 的行 + rid 9201–9206 |
| HUD 淡出/停留时长 | `MenuParam`（**唯一 1 行表，424 字节**） | `*FadeOutTime` / `*ViewTime` / `*Sec` |
| 锁定距离/角度/超时 | `TentativePlayerParam` | `normalLock_* / missileLock_* / LockTargetMarking_* / LockSite*` |
| 锁定相机手感 | `LockCamParam`（98 行 × 376 字节） | `lockRotChaseRate` / `locksiteMoveFactor` / `lockRotXShiftRatio_*` / `crossingLockRotChaseRate` |
| 装配面板能显示哪些属性 | `MenuPropertyLayoutParam`（2512 行）+ `MenuPropertySpecParam`（508 行）+ `Names/MenuPropertyLayoutParam.txt`（1261 行英文名） | `LayoutPath` / `PropertyID` / `Simple` 前缀行 |
| 面板数值从哪来 | `MenuPropertySpecParam` | `extract0_Target/_MemberType/_Operation/_MemberTailOffset/_Constant0/_Constant1` |
| 武器面板显示哪一组攻击参数 | `EquipParamWeapon` | `menu_SrcGeneration*`（含 `_Charge` 系列）、`menu_ShowConsumeBullet`、`menu_ShowAddHeat` |
| 装配界面的分类与排序 | `EquipmentMenuManageCategoryParam`（110 行）+ `EquipParamWeapon.assembleMenuCategory` | `PropertyLayoutID` / `CategoryNameTextID` / `SortID` |
| 前端有哪些画面 | `MenuBehaviorParam`（31 行） | `tutorialID` / `enableHelpMenu` |
| 涂装/贴花/自定义图案的编辑项 | `MenuPropertyLayoutParam` 的 `Pos/*`、`Size/*`、`Mask` 路径 + `MenuPropertySpecParam` 40000 段 + `MenuInputGestureParam` 250/251/252、1202–1205 | — |
| 3D 预览机位 | `MenuOffscrRendParam`（140 行）+ `MenuPartsModelRendParam`（14 行） | `camAtPos*` / `camDist` / `camFov` / `camDistMin·Max` / `GparamID` / `initModelDegX·Y` |
| 菜单后处理 | `MenuFilter`（28 行）+ `GraphicsParam` | `NoiseTexUpdateTime` / `Contrast` / `CenterThin` / `MenuBackBoke_FadeIn·Out` |
| 结算收支明细 | `MenuPropertyLayoutParam` 的 `in_*`/`out_*`/`totalBalance` 路径 | PropertyID 80001–80090 |
| 键位重映射 | `KeyAssignDisplayParam`（58）/ `KeyAssignMenuItemParam`（24）/ `KeyAssignParam` / `MenuInputGestureParam` | `enableUnassign` / `enablePadConfig` / `enableMouseConfig` / `enableDispConfigMenu` |
| 教程弹窗 | `TutorialParam`（201 行） | `MenuResourceType` / `ImageID` / `Keyguide0-3_ActJudgeParamID` / `UnlockEventFlagID` |
| 字幕样式 | `FeFreeDialogParam`（31 行）+ `FeTextEffectParam`（280 行） | `FontScale` / `FontColor_*` / `BaseRect_*` / `DisplayTime` |
| 世界空间动作按钮 | `ActionButtonParam`（144 行） | `regionType` / `iconID` / `priority` / `invalidFlag` / `grayoutFlag` / `raycastType` |
| 敌方开火预兆 | `AttackActionParam_PC` / `AttackActionParam_NPC`（**本机 `van/regulation-bin` 下存在**） | `shootIndicationType`(@76) / `shootIndicationDmypolyId`(@80) / `alertShowType`(@57) / `alertLevel`(@58) |

---

## 附：本维度最值得记住的 5 句话

1. **UI 的信息密度问题，本质是"优先级问题"而不是"数量问题"**——AC6 的解法是把优先级写成数据（`DisplayCondition`、`Simple` 前缀、`CompareType`），而不是写成代码分支。
2. **"实时数值对比"的 90% 工作量在取数层。** 一个 `(表, 偏移, 类型, 公式, 常数)` 的地址注册表，比一百个 `if (weapon.type == X)` 强。
3. **数据驱动 UI 把"数值正确性"的责任搬到了数据上，因此你必须造校验。** AC6 的 105 条取数配方在正确理解"尾偏移"后做到 105/105 位置与类型全中——**说明这套体系可以做到零漂移，但前提是有人把偏移语义契约化并持续校验**；我第一遍按"首偏移"读就得到了 14% 失效的假结论。
4. **可及性功能"没做"和"没开放"是两件事。** AC6 有完整的字幕样式配置表（`FeFreeDialogParam`）但没开放给玩家；有 HUD 位置/缩放/透明度编辑器（`MenuInputGestureParam` 9201–9206）却是最被低估的功能。
5. **TA 在这套体系里的价值不在"能不能画出一个界面"，而在"能不能让一个界面在上百个部件的上千个字段之上，永远显示正确的数字，并且改起来不用改代码"。**
