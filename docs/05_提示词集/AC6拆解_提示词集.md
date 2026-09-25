# 《装甲核心6：境界天火》拆解提示词集 v1

> 用途：把这份文件里的提示词**逐条复制**给任意一个外部 AI（ChatGPT / Claude / Gemini / 豆包 / DeepSeek / Kimi 等），让它完成对 AC6 的结构化拆解。
> 使用者画像：大四学生，目标岗位 **技术美术（TA）**，计划从**策划**入门 → 需要一份既懂设计、又能落到技术实现的拆解。
> 撰写日期：2026-09-10

---

## 0. 怎么用这份文件（先读这 90 秒）

### 三种用法

| 用法 | 用什么 | 适用场景 | 耗时 |
|---|---|---|---|
| **A. 一次性总纲** | `P0 母提示词` | 只想过一遍全貌、快速建立心智地图 | 1 次长回答 |
| **B. 分维精拆（推荐）** | `P1 ~ P16` 逐条发 | 每个维度单独开一个对话，产出深度可控、便于合并 | 16 次 |
| **C. 闭环验证** | `P17 → P18 → P19 → P20` | 深挖 → 打假 → 合成报告 → 转成个人能力与作品集 | 4 次 |

**推荐顺序**：先发 `P0` 拿到全局骨架 → 用 `P1~P16` 逐维精拆（每条都让 AI 按统一格式输出）→ 用 `P18` 对最满意的几份做对抗审查 → 用 `P19` 合并成一份《AC6 设计拆解报告》→ 用 `P20` 变成你自己的学习路线和 TA 作品集任务书。

> 说明：`P0` 里列出的维度顺序是**建议阅读顺序**；`P1~P16` 只是条目编号（你指定的 4 个维度在前，TA 重点维度紧随），两者内容一一对应，顺序不同不影响使用。文末附有 16 天排期表。

### 三条使用纪律

1. **一条提示词 = 一个新对话**。`P1~P16` 都是自包含的，不要塞进同一个对话，否则后半段质量会塌。
2. **必须要求它标证据等级**。AC6 的精确数值网络上流传的错漏极多（尤其是补丁后的版本差异），所以每条提示词都强制它标 `A/B/C/D`。看到 `D` 不要生气，那是它在诚实，反而可以用你手上的数据去补。
3. **你有别人没有的杀手锏**：你本地有解包后的游戏本体和 `regulation.bin`（257 张 param 表）。**附录 A** 给出了"问题 → 去哪张表验证"的索引。把 AI 的结论当成"假设"，拿表去证伪，这就是你能写进作品集、也能在面试里讲的东西。

---

## P0. 母提示词（一次性全量拆解）

````
你是一位复合身份的资深从业者：游戏系统策划（10 年）+ 技术美术（TA，10 年）+ 关卡设计师。你的任务是对《装甲核心6：境界天火》（ARMORED CORE VI: FIRES OF RUBICON，FromSoftware，2023）做一次**结构化的设计拆解**。

【我的背景，决定你的输出取向】
我是大四学生，职业目标是技术美术（TA），打算从策划岗入门。所以你的输出必须同时满足两件事：
① 讲清楚"这个设计为什么这么做"（策划视角）；
② 讲清楚"它在技术上是怎么实现的、需要什么技能"（TA 视角）。
不要写成游戏评测、不要写成剧情简介、不要写百科条目。

【你没有游戏文件】
你只能依靠你的知识。请严格区分：
A = 游戏内可直接观察到的事实 / 官方公开资料
B = 社区实测、Wiki、数据挖掘结论
C = 基于同类游戏的合理推断
D = 你不确定（必须写明"如何验证"）
每一条结论和每一个数值都必须带等级标记。绝对不要编造精确数值；如果你只记得量级，就写量级。

【统一输出规范（每个维度都遵守）】
1. 结论先行：每节开头先给 3~5 条要点，再展开。
2. 表格优先：机制清单、状态机、参数、反馈矩阵一律用 Markdown 表格。
3. 每条机制按四段式写：设计意图 → 实现手段（可观察到的） → 玩家体验/结果 → 可复用结论。
4. 禁止无机制支撑的形容词结论。不许出现"打击感很好""非常沉浸"这类话；要拆成具体通道（帧数、位移、音量、颜色、粒子、参数）。
5. 每个维度必须回答"分析三问"：
   ① 如果删掉这个机制，玩家体验会怎么变？
   ② 如果它的参数被放大/缩小 10 倍，会怎样？（用来定位设计空间的边界）
   ③ 它到底在解决什么问题？有没有更简单的替代方案？为什么没用？
6. 每个维度最后给出"验证路径"：若要证实/证伪本条，应查看哪张游戏数据表或做什么实测。

【拆解维度（按此顺序输出）】
1. 镜头与相机系统
2. 战斗框架与数值底层（含姿态/硬直、伤害类型、资源经济）
3. 装配与机体数值系统（AC 的灵魂）
4. 动作、动画与运动系统（TA 重点）
5. 手感与反馈设计 Game Feel（TA 重点）
6. 关卡与遭遇设计
7. 敌人 AI 与 Boss 设计
8. 美术方向与渲染表现（TA 重点）
9. UI/UX 与信息设计（TA 重点）
10. 音频设计
11. 剧情与叙事结构
12. 世界观与设定体系
13. 系统与元循环（经济 / 进度 / 多周目 / PvP）
14. 难度曲线与教学
15. 技术实现与数据管线（TA 重点）
16. 系列演化与商业定位

【最后必须给出】
- 一张"设计要素 → TA 技能"的映射总表（最少 20 行）：左边是游戏里的做法，右边是复刻它需要的引擎/工具/技能。
- 一份"如果我要在 UE5 里做一个 AC6 战斗最小原型，必须实现的功能清单"，按 优先级 P0/P1/P2 排序。

现在开始。用 Markdown 输出，不要用代码块包裹整篇回答。在开始前，先列出你打算怎么组织这次拆解（3~5 行即可），然后再正式输出。
````

---

## P1. 镜头与相机系统

````
你是动作游戏相机系统的资深设计者。请拆解《装甲核心6：境界天火》（AC6）的**第三人称相机系统**。
我大四，目标技术美术（TA），需要"设计意图 + 技术实现"双视角。

【分析对象】
AC6 是高速机甲动作游戏，玩家机体可以在三维空间高速机动，同时要用准星/锁定框射击。它的相机必须同时服务"看清自己"和"瞄准敌人"这两个互相拉扯的需求。

【必须回答】
1. 列出相机状态机：常规跟随、软锁（目标在视野内自动吸附）、硬锁（锁定后相机跟随目标）、手动瞄准/自由视角、突击推进（Assault Boost）高速态、快速推进（Quick Boost）瞬间位移、近战突进、被击中/姿态崩溃（Stagger）、Boss 战、死亡与结算镜头、机库（Garage）展示镜头。给出每个状态的出现条件与退出条件。
2. 每个状态的相机参数：跟随机体的距离、高度偏移、FOV、位置阻尼、旋转阻尼、前瞻（look-ahead）、偏移量。用表格。数值给量级并标证据等级。
3. 锁定系统是相机的核心，请拆开讲：
   - 软锁的触发条件（屏幕空间角度？距离？视线遮挡？）
   - 硬锁的切换规则（右摇杆推动方向 + 候选目标的评分方式？）
   - 丢失锁定的条件（距离、遮挡、目标死亡、玩家主动解除）
   - 锁定后，机体朝向与相机朝向如何解耦——是"机体转向相机目标"还是"相机绑死机体"？
   - 硬锁的代价是什么（设计上为什么要给代价）？
4. 速度感是怎么做出来的？请把"很快"拆成可实现的通道：FOV 变化曲线、相机位置滞后、推进器粒子拖尾、后处理（径向模糊/色差/速度线）、镜头抖动、音效。分别说明各自贡献了什么。
5. 镜头抖动（Camera Shake）系统：分类列出（开火后坐、被命中、爆炸、落地、QB、Boss 招式），给出每类的强度、时长、衰减方式（指数/线性）与叠加规则。多个抖动同时发生怎么处理？
6. 准星/锁定框与真实弹道的关系：FCS（火控系统）的落点偏差如何通过 UI 和相机表达？玩家看到的"准星"到底代表什么？
7. 过场与实机的衔接：任务开场、剧情演出、结算如何进出？是否可操作？镜头是否无缝？
8. 分析三问（见通用规范第 5 条）。
9. 验证路径：AC6 的数据表里有 LockCamParam、DirectionCameraParam、SubWindowCamParam、GarageCameraAnimParam、Zoomblur 等表。请说明每个表大概负责相机的哪一块，以及要验证你的哪条结论该看哪张表。

【TA 转化要求】
最后给我一节"复刻手册"：在 UE5 里做一套等价的机甲相机，需要哪些具体组件与做法（如 SpringArm 长度/滞后、相机滞后实现、FOV Kick 曲线、Shake 的叠加与衰减策略、Cinemachine/Sequencer 的用法、后处理体积如何被战斗状态驱动）。要具体到"用什么节点/什么思路"，不要只给名词。

【输出规范】
结论先行；表格优先；每条结论四段式（设计意图→实现手段→玩家体验→可复用结论）；数值必须标 A/B/C/D 等级；禁止无机制支撑的形容词；不确定就写不确定并给出验证方法。
````

---

## P2. 战斗框架与数值底层

````
你是动作游戏的战斗系统策划 + 数值策划。请拆解《装甲核心6：境界天火》（AC6）的**战斗框架与数值底层**。
我大四，目标技术美术（TA），需要理解"玩家的每一次开火背后有哪些系统在同时运转"。

【必须回答】
1. 画出战斗的核心循环（时间尺度从 0.2 秒到 10 秒）：索敌 → 接近/拉开 → 输出 → 资源见底 → 换弹/回能 → 姿态积累 → 硬直窗口 → 爆发 → 撤离。用文字流程图表示，标出每一步的典型耗时量级。
2. **姿态/硬直系统（ACS）**是 AC6 战斗的心脏，请重点拆：
   - 姿态值（Attitude Stability）与姿态回复（Attitude Recovery）分别怎么影响积累与衰减
   - 硬直（Stagger）触发的阈值逻辑、硬直持续时间
   - 硬直期间受到的"直接命中伤害加成"（Direct Hit Adjustment）机制
   - 为什么"把敌人打晃"比"直接堆伤害"更好玩？这个设计替代了什么传统做法？
3. 伤害类型与防御：Kinetic（动能）/ Energy（能量）/ Explosive（爆炸）三类攻击与三种抗性。请说明：
   - 是减法减伤还是乘法减伤？（不确定就说不确定，并给出判定方法）
   - 属性克制在装配层面的实际影响有多大
   - 为什么用三属性而不是常见的"物理/魔法"二分
4. 四武器槽（右手/左手/右肩/左肩）的职能分工，以及"肩部武器与手臂武器的开火冲突"是怎么被设计的（动作互斥表）。
5. 资源经济：把 EN（能量）、热量/过热、弹药、AP、姿态值视为五种互相牵制的资源。给出"资源流向图"：谁产出、谁消耗、谁回复、回复的延迟与曲线形状。
6. 命中判定：区分 hitscan 与实体弹丸；弹速、追踪（Blade Homing）、散射、AoE、跳弹（Ricochet）与跳弹角度。近战吸附的机制（角度/速度/取消条件）。
7. 防御性动作：Quick Boost 期间是否存在无敌帧？击退（Knockback）与受击硬直、倒地与起身的设计。请明确区分"你知道的"和"你推断的"。
8. 敌方战斗结构：从玩家视角看，敌人的"预警 → 出招 → 硬直/收招"三段结构如何塑造攻防节奏。
9. Boss 战的阶段化与"读招—惩罚"循环。
10. 分析三问：删掉 ACS 硬直系统会怎样？删掉三属性克制会怎样？把 TTK（击杀耗时）缩短 10 倍会怎样？
11. 验证路径：相关数据表包括 EquipParamWeapon、AtkParam_Pc、AttackActionParam_PC、BehaviorParam_PC、Bullet、DamageLevelConvParam、DamageLevelConvThresholdParam、KnockBackParam、ShootReboundParam、SpEffectParam、CoolTimeParam。请说明每条结论该去哪张表验证。

【TA 转化要求】
给我一份"最小战斗原型参数表"：在 UE5 里实现"姿态积累 → 硬直 → 直接命中加成"这套循环，需要哪些参数、放在哪里（数据资产/DataTable）、怎么让策划可调。要能直接照着做。

【输出规范】
结论先行；表格优先；每条结论四段式；数值必须标 A/B/C/D 等级；禁止编造精确数值；不确定就写不确定并给出验证方法。
````

---

## P3. 剧情与叙事结构

````
你是叙事设计师。请拆解《装甲核心6：境界天火》（AC6）的**剧情结构与叙事手法**。
我大四，目标技术美术（TA）、从策划入门，需要的是"叙事是怎么被工程化实现的"，不是剧情复述。

【硬性要求】
不要复述剧情梗概当分析。每一步都要回答"这个叙事效果是用什么载体、什么触发条件实现的"。

【必须回答】
1. 叙事载体清单：任务简报、战斗中实时通讯（comm）、过场动画、场景拾取物/文档、邮件系统、结局演出。分别说明各自的**信息密度、可控性、成本**，以及为什么 AC6 更依赖"战斗中通讯"。
2. 主角设计：玩家是沉默的、无脸的佣兵。请分析这个选择的后果——它让哪些东西变容易了（代入、定制、分支），又牺牲了什么（情感表达、角色弧光）。有没有代价补偿机制？
3. 结构：给出主要章节/任务节点的叙事骨架，标出**信息释放的节奏**（Coral 是什么、伊比斯之火发生了什么、强化人改造的代价、幕后势力是谁）。分期揭露的顺序为什么这么排？
4. 多结局结构：三个结局各是什么、触发条件是什么、分歧点出现在流程的哪个位置、共有几个关键决策点。请画成决策树（文字/mermaid 均可）。
5. 角色功能表：把主要角色按"叙事功能"归类（雇主/权威、他者/异质声音、镜像对手、失败者镜像、旧时代的遗民、体制的傲慢……），说明每个角色在结构上承担什么职责。角色名请标注你对该名字的把握程度。
6. 分支如何与玩法耦合：选择是否体现在"任务列表的增减"而不是过场动画？这样做的好处是什么？玩家怎么感知到自己的选择生效了？
7. 世界观信息的"碎片化"与"可达性"如何平衡？（魂系那种"不给答案"和 AC6 这种"有人一直在跟你说话"的差别）
8. 分析三问：如果主角开口说话会怎样？如果把通讯语音全部换成文字日志会怎样？如果只有一个结局会怎样？
9. 验证路径：数据表里有 TalkParam（台词）、MailParam（邮件）、MissionParam（任务）、MissionSystemMsgAnswerParam（任务中的选择/应答）、FeFreeDialogParam（自由对话）、Cutscene*Param（过场调度）。请说明每条叙事结论该去哪张表验证，并说明从这些表能读出什么（比如：台词总数、分支应答数量）。

【TA 转化要求】
给一节"叙事系统的技术实现"：对话/语音触发、任务状态机、分支存档标记、过场调度（时间/天气/地图切换）分别怎么实现，TA 在其中做什么（工具、状态机、Timeline、本地化管线）。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定并给验证方法；禁止把剧情概要当分析。
````

---

## P4. 世界观与设定体系

````
你是世界观架构师（worldbuilding designer）。请拆解《装甲核心6：境界天火》（AC6）的**世界观与设定体系**，重点是"设定如何被设计成可玩、可视、可扩展"。
我大四，目标技术美术（TA），需要设定与美术/关卡资产的对应关系。

【必须回答】
1. 设定骨架：把核心设定整理成一张表——行星 Rubicon 3、Coral（这种物质的设定双重性：能源 / 可能是生命）、伊比斯之火（Fires of Ibis）、企业势力（Arquebus、Balam、Schneider's、Furlong、Elcano 等）、行星封锁机构（PCA）、本地抵抗组织、RaD、Overseer、研究机构。每一项注明：设定内容 + 在游戏里**通过什么方式被玩家感知到**（任务/环境/台词/道具）。不确定的名称标注不确定。
2. Coral 这个核心设定承担了几重功能？（能源、政治争夺对象、准生命体、结局选择的标的、主题载体）为什么一个设定要同时背这么多功能？这是好设计还是有风险？
3. 强化人（Augmented Human）设定与"人性的代价"主题：设定如何为"玩家反复换身体/换零件"这个玩法提供叙事合法性？
4. 世界观的呈现方式：环境叙事（废墟、巨型结构、战场残骸）、关卡美术、UI 文本、通讯。请举 3~5 个"设定通过场景被讲出来"的具体例子（不确定的例子请标注）。
5. 术语与命名法：整理一份术语表（中英日对照，标注把握程度）。分析企业名、机体型号（如 AH12、AAP07、IA-01、IB-01 这类代号）的命名规律——这套命名法在传递什么感觉？
6. 与系列前作的关系：AC 系列长期的世界观母题（企业统治、佣兵经济、AI、资源战争）。Coral 与前作的对应物是否构成传承？（不确定就标注）
7. 主题层：资源掠夺/殖民主义、后人类、雇佣兵伦理、共同体与个体。这些主题是通过"说"还是通过"玩家的选择成本"表达的？
8. 可扩展性：这套世界观给续作/DLC/衍生留了哪些开口？
9. 分析三问：如果 Coral 只是普通化石能源会怎样？如果主角从一开始就知道全部真相会怎样？如果去掉"企业"这个层级只保留国家会怎样？
10. 验证路径：数据表里有 UnlockParam_Archive、UnlockParam_Archive_Logs/Terms/Tips（档案/术语/提示解锁）、TalkParam、MailParam、GameAreaParam。说明如何从数据层量化"世界观投放量"（比如术语条目数、档案条目数）。

【TA 转化要求】
给一节"设定 → 资产"的映射：巨型结构、废墟、企业标识/涂装系统、Coral 的能量表现，各自需要什么美术与技术支持（模块化建模、贴花系统、自发光材质、体积雾、LOD/性能预算）。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；禁止把设定罗列当分析；不确定的专有名词必须标注。
````

---

## P5. 装配与机体数值系统

````
你是数值策划 + 装备系统策划。请拆解《装甲核心6：境界天火》（AC6）的**机体装配（Assembly）与数值系统**——这是这个游戏真正的"职业/天赋树"。
我大四，目标技术美术（TA），需要理解"模块化"从设计到资产的完整链路。

【必须回答】
1. 槽位系统：头部、核心、手臂、腿部、推进器（Booster）、FCS、发电机（Generator）、扩展（Expansion）、右手武器、左手武器、右肩武器、左肩武器。给出完整槽位表，并说明**槽位之间的耦合关系**（谁决定谁的上限、谁给谁开门）。
2. 三大资源轴：重量、EN 负荷/输出、热量与 EN 消耗。说明它们如何构成"没有免费午餐"的结构。给一张"换任何一个部件，会连带影响哪些数值"的影响矩阵。
3. 关键派生数值清单：AP、三种抗性、姿态稳定/姿态回复、总重与载重比、EN 输出与负荷、推进力、QB（快速推进）推力/消耗/时长/冷却、AB（突击推进）推力、跳跃性能、近战推力、FCS 的三段距离辅助与导弹锁定修正。逐项说明：它影响什么玩法行为。
4. 数值的非线性：重量对性能的影响是线性的吗？有没有阈值/断点？收益曲线是递增还是递减？请明确区分"你知道的"和"你推断的"，并给出验证方法。（提示：魂系传统上使用曲线表来实现非线性收益）
5. 腿部类型与移动元型：轻/中/重二足、逆关节、四足、坦克。给一张元型表：机动性、载重、稳定性、代表玩法、典型战术、优点与死穴。
6. OS 强化（OS Tuning）：用"可分配点数"置换能力的系统。请列出强化类别（如武器/防御/机动/系统辅助），说明它的设计作用——为什么在装配之外还要给一层加点？
7. 自动配装：游戏里有自动装配功能。它是怎么评分的（评价函数可能考虑什么）？自动配装的存在对新手意味着什么？
8. 装配即难度：为什么 AC6 的核心难度调节器是"配装"而不是难度选项？这个设计把"卡关"的解法从操作转向了什么？
9. 分析三问：如果没有重量限制会怎样？如果部件不能互换（固定机体）会怎样？如果所有部件数值都是线性叠加会怎样？
10. 验证路径：EquipParamWeapon、EquipParamProtector、EquipParamBooster、EquipParamGenerator、EquipParamFcs、EquipmentLineupParam、AutoAssembleEvaluate、CalcCorrectGraph、OsReinforce、OsReinforcePoint、PartsTokenParam。请给出"每条结论 → 去哪张表 → 找什么字段"的对照表。

【TA 转化要求】
给一节"模块化机甲的资产管线"：12 个槽位的部件如何做到任意组合而不穿模/不塌骨架？需要什么（共享骨架与重定向、挂点 socket 规范、材质实例与涂装遮罩、装配预览相机与打光、部件 LOD 与绘制预算、数据驱动的装配 UI）。这是 TA 的核心工作，请写具体。

【输出规范】
结论先行；表格优先；四段式；数值标 A/B/C/D 等级；禁止编造精确数值；不确定就写不确定 + 验证方法。
````

---

## P6. 动作、动画与运动系统（TA 重点）

````
你是动画技术总监（Animation TA）。请拆解《装甲核心6：境界天火》（AC6）的**动作、动画与运动系统**。
我是大四学生，目标技术美术（TA），这一节是我最需要吃透的部分。请把"机甲动起来"这件事拆到可实现的粒度。

【必须回答】
1. 动作集清单：移动（走/冲刺/悬浮/爬升/下降/跳跃）、Boost 系统（普通加速、Quick Boost 瞬时位移、Assault Boost 长距离突进）、近战突进、踢击、开火、换弹、被击、姿态崩溃、倒地/起身。给一张**动作优先级与互斥表**：哪些动作可以同时进行、哪些会打断、哪些有取消窗口。
2. 上下半身分离：腿部运动（移动动画）与上半身瞄准（武器朝向跟随锁定目标）如何协同？躯干扭转是否有角度上限？瞄准方向与移动方向不一致时怎么处理？
3. 位移系统：走的是"根运动（root motion）"还是"参数驱动速度 + 动画跟随"？空中悬浮的物理模型是什么（重力、升力、能量消耗的平衡）？请说明你的判断依据。
4. 地形适应：脚部 IK 如何处理不平地面与坡度？机甲这种"刚性大质量物体"的脚部接触是怎么做的？
5. 转身与惯性：机体朝向的角速度是多少量级？是否受载重影响？"重装机转不过来"是刻意设计还是物理结果？
6. 重量感是怎么来的？请拆成可实现的通道：预备动作（anticipation）、加速度曲线、伺服/液压延迟、二次运动（机械晃动/惯性摆动）、落地冲击、音效。特别说明"机甲零件之间的相对运动"是如何模拟的——这是区别于人类角色的关键。
7. 受击表现分级：轻击、重击、姿态崩溃（Stagger）分别是怎样的动作状态？击退位移如何与动画配合？是否有无敌帧？
8. 判定帧与动画的耦合：武器的"开火帧""近战判定帧""命中窗口"是怎么对齐到动画上的？谁说了算（动画通知/数据表/状态机）？
9. 分析三问：如果没有 Quick Boost 会怎样？如果把动画速度整体放慢 50% 会怎样（重量感会变强还是变糊）？如果所有动画都用根运动会怎样？
10. 验证路径：FootIKParam、FootIKSetupParam、HandIKParam、LookAtParam/LookAtHeadParam/LookAtSpineParam、ReTargetAnimSetParam（动画重定向！）、AnimMoveCorrectionParam、JigglerBaseParam/JigglerBehaviorParam/JigglerBehaviorSlideParam/JigglerBehaviorTargetBoneRateParam/JigglerBehaviorWorldFixParam（机械二次运动）、ChrProxyPhysicsParam、RigidBodyParam、RagdollParam、MovementAcTypeParam、ThrustersLocomotionParam_PC、BoostParam。请说明这几张表分别对应上面哪一条结论。

【TA 转化要求】
给一份"复刻清单（UE5）"：实现"机甲 QB 瞬移 + 机械晃动 + 脚部 IK"需要什么（Animation Blueprint 状态机与 Blend Space、Layered Blend 上下半身、IK Rig/Retargeter、Physics Asset 与约束、二次运动模块如 Jiggle/AnimDynamics、Motion Warping、动画通知与判定对齐）。请标明每项的难度和大致工作量（人日量级即可）。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；禁止无机制支撑的形容词（"很有重量感"不算结论）；不确定就说不确定 + 验证方法。
````

---

## P7. 手感与反馈设计 Game Feel（TA 重点）

````
你是"手感（game feel）"方向的资深设计师兼 TA。请拆解《装甲核心6：境界天火》（AC6）的**输入手感与反馈系统**。
我大四，目标技术美术（TA）。手感是 TA 最能做出差异化的战场，因为你既要懂设计意图，又要能把它参数化、工具化。

【必须回答】
1. 输入层：
   - 输入缓冲（input buffer）：按键提前多久有效？
   - 取消窗口（cancel window）：哪些动作可以被打断、在什么时间点？
   - 瞄准辅助：准星/锁定对被瞄准目标的磁吸与粘滞（aim assist / magnetism）如何设计？硬锁与软锁分别提供多少辅助？
   - 手柄曲线与死区、扳机键的半程输入（如果用了）
   - "按住 vs 点按"的区分设计
2. 输出层：这是重点。请建立一张**反馈矩阵**：
   行 = 事件（普通命中、姿态积累、姿态崩溃、击杀、被击中、被破防、近战命中、爆炸、部件破坏、QB、AB、落地、任务目标完成）
   列 = 反馈通道（顿帧 hitstop、镜头抖动、粒子/特效、音效、UI 数字跳字、敌人动作中断、材质火花、手柄震动、后处理冲击、时间缩放）
   格子 = 强度与持续时间。
3. 顿帧（hitstop）：AC6 里哪些事件会顿帧？顿帧是全局时间缩放还是只冻结双方？顿帧的时长量级？持续开火时顿帧如何避免"糊成一团"？
4. 反馈延迟预算：从玩家按下按键到看到/听到反馈，业界典型预算是多少毫秒？AC6 这类重型机甲会不会故意增加延迟来制造重量感？如何在"重量感"和"迟滞感"之间找平衡？
5. 视觉反馈的层级：如何让玩家在混乱的爆炸中仍然分辨"我打中了""我被打中了""我破防了"？颜色、形状、位置、音高各承担什么？
6. 正反馈与负反馈的对称性：玩家的攻击反馈和受击反馈在设计上如何保持一致的"语言"？
7. 分析三问：如果去掉顿帧会怎样？如果所有反馈通道的强度都拉满会怎样（审美疲劳）？如果给玩家 0 延迟的完美反馈会怎样？
8. 验证路径：HitMtrlParam、HitEffectSfxParam、HitEffectSfxConceptParam、ChrHitMaterialCheckParam、SeMaterialConvertParam、PadRumble、DamageLevelConvParam、SpEffectParam、HitEffectSfxConceptParam。说明"材质 → 特效/音效/震动"的映射是怎么被数据化的。

【TA 转化要求】
1. 给一份"手感调参工具"的设计：TA 应该给策划做一个什么样的实时调参面板（顿帧时长、抖动曲线、粒子强度、音效层级、后处理强度）？请描述这个工具的功能、数据接口与工作流。
2. 给一份"最小可玩手感 Demo"的实现清单（UE5）：命中顿帧、镜头抖动、命中特效分级、手柄震动，各自的关键节点与参数暴露方式。

【输出规范】
结论先行；矩阵/表格优先；四段式；证据等级 A/B/C/D；禁止"打击感很好"这类空话；不确定就说不确定 + 验证方法。
````

---

## P8. 关卡与遭遇设计

````
你是关卡设计师。请拆解《装甲核心6：境界天火》（AC6）的**关卡与遭遇（encounter）设计**。
我大四，目标技术美术（TA），需要理解"关卡如何为高速三维移动服务"以及"大规模场景的技术代价"。

【必须回答】
1. 关卡类型学：大型开放区块（多目标点）、线性突入、Boss 竞技场、防守/护送、潜行破坏、限时任务。给一张表：类型、典型时长、失败条件、评价条件、设计目的。
2. 空间尺度：因为玩家有 Quick Boost / Assault Boost / 飞行，关卡距离必须以"移动时间"而不是"米"来计量。请说明：
   - 一个"跳跃点"到下一个掩体的典型距离量级
   - 垂直空间如何被利用
   - 巨型结构（如巨型建筑/炮台/山脉）如何同时充当"地标"和"战斗舞台"
3. 引导系统：玩家在复杂三维场景里怎么知道去哪？请拆开：目标指示器、HUD 雷达/罗盘、任务语音提示、地标剪影、地形引导（峡谷/通道）、光照引导。分别说明强弱与失效场景（比如在室内或沙尘天气）。
4. 遭遇编排：敌人组合怎么配（近战/远程/重装/飞行/炮台）？增援如何触发（时间/位置/击杀数/剧情）？地形掩体与高低差如何参与？
5. 目标设计：主目标 + 可选目标 + 隐藏目标（如情报收集、特定敌人击杀）。评价系统的 S 条件大概考核什么（时间/伤害/消耗/击杀数）？请标注不确定。
6. 资源与检查点：任务中是否有补给点？弹药/修理费如何与关卡长度挂钩？失败重试的成本是什么（时间、金钱、进度）？
7. 请挑 3 个有代表性的关卡做逐个拆解（例如：水坝突袭类关卡、翻越巨型墙体类关卡、大型 Boss 竞技场关卡、地下探索关卡）。对每个给出：目标结构、空间结构、敌人编排、节奏曲线（紧张/喘息）、教学意图、以及"如果重做我会改什么"。不确定关卡名请描述清楚而不是硬报名字。
8. 分析三问：如果去掉飞行/悬浮能力，关卡会怎么变？如果关卡改成完全线性的一本道会怎样？如果取消任务内检查点会怎样？
9. 验证路径：MapAreaParam、MapPartsParam、MapGimmickParam、GameAreaParam、PlayRegionParam、MiniAreaParam、PathFindCostParam、AssetEnvironmentGeometryParam。说明这些表如何反映关卡的分区与机关结构。

【TA 转化要求】
给一节"大场景的技术美术预算"：视距与绘制距离分级（游戏甚至按平台分了多套绘制距离参数）、遮挡剔除、HLOD、LOD、粒子上限、流式加载。说明 TA 在关卡制作流程中介入的时机与产出物。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法；禁止"关卡设计很棒"这类空话。
````

---

## P9. 美术方向与渲染表现（TA 重点）

````
你是资深技术美术（TA）+ 美术总监。请拆解《装甲核心6：境界天火》（AC6）的**美术方向与渲染表现**。
我大四，目标技术美术（TA）。这一节请务必落到"用什么技术手段实现什么视觉效果"，我要能照着做。

【必须回答】
1. 视觉定位：用一句话定义它的视觉语言（工业硬科幻？去饱和冷色调？高对比能量光？巨型尺度对比？）。然后拆成可执行的要素：色调范围、对比度策略、材质倾向、形态语言、尺度关系（人 / 建筑 / 机甲 / 巨型结构）。
2. 材质体系：
   - 金属 PBR 的做法（粗糙度范围、金属度、法线细节、划痕/磨损/旧化如何叠加）
   - 涂装（paint）与贴花（decal）系统：玩家自定涂装是如何在不重做贴图的前提下实现的（遮罩 + 材质参数 + 贴花投影？）
   - 能量发光（Coral / 推进器 / 武器充能）的自发光与 Bloom 配合
   - 玻璃、涂层、破损、弹痕
3. 机甲资产管线：模块化部件、共享骨架、材质实例化、LOD 策略。一个可换装 12 个槽位的机甲，美术怎么保证风格统一又互不穿模？
4. VFX 清单：推进器尾焰、QB 残影/拖尾、AB 长尾迹、枪口火焰、弹道轨迹、导弹尾烟、近战刀光、命中火花、爆炸、Coral 粒子、Boss 招式预警特效。给一张"特效 → 技术实现（粒子系统类型/材质/后处理/是否屏幕空间）"的映射表。
5. 后处理栈：Bloom、色差（chromatic aberration）、胶片颗粒、径向模糊/Zoom Blur、速度线、色调映射（tone mapping）、抗锯齿策略。分别说明：它们各自贡献什么感觉、开启/关闭的代价、如何在"高速战斗"时动态调节。
6. 光照与天空：Rubicon 的灰黄沙尘、夜间战斗、室内工厂、地下空间。分析其光照模型与大气效果（体积雾、God Ray、天空盒）。说明这些如何服务于"看不清但又不难受"的可读性平衡。
7. 可读性（readability）：在高速战斗 + 大量粒子 + 复杂背景下，玩家如何分辨敌我、弹道、预警？请给出对比度、轮廓光、颜色编码、特效层级的策略。
8. 性能策略：面向主机 60fps 的取舍（粒子预算、屏幕空间效果成本、绘制距离分级、按平台分档的参数）。请说明哪些效果是"贵"的、TA 会怎么砍。
9. 分析三问：如果把饱和度整体拉高 30% 会怎样？如果去掉所有后处理会怎样（干净但失去什么）？如果不用自发光只用反光会怎样？
10. 验证路径：GraphicsParam、MaterialExParam、DecalParam、PlayerColoringPresetParam、PlayerMaterialPresetParam、PlayerWeatheringTexPresetParam、PlayerCamouflagePattern、EmblemPieceSpec、PartsDrawParam_*（按平台分档）、LoadBalancerDrawDistScaleParam_*、GrassLodRangeParam、SkydomeAssetParam、WetAspectParam、Zoomblur。说明每条视觉结论该去哪张表验证。

【TA 转化要求】
选 2 个效果做"复刻方案书"（每个不超过 300 字 + 一张节点/步骤清单）：
① 推进器尾焰 + QB 残影；② 命中火花与爆炸的分级反馈。
要求写清：用什么系统（Niagara/Cascade、材质域、后处理）、关键参数、性能注意点、可复用性。

【输出规范】
结论先行；映射表优先；四段式；证据等级 A/B/C/D；禁止"画质很好"这类空话；不确定就说不确定 + 验证方法。
````

---

## P10. UI / UX 与信息设计（TA 重点）

````
你是 UI/UX 设计师 + 技术 UI 方向的 TA。请拆解《装甲核心6：境界天火》（AC6）的**界面与信息设计**。
我大四，目标技术美术（TA）。机甲游戏的 UI 信息密度极高，是"技术 UI"最好的学习样本。

【必须回答】
1. HUD 元素清单与信息层级：AP 条、姿态/ACS 条、四武器槽与弹药、锁定框与锁定进度、雷达/罗盘、EN 条、任务目标、伤害数字、警告提示。给一张表：元素、位置、更新频率、紧急度、可关闭性。
2. 信息密度管理：屏幕同时有几十个数字时如何不崩？请拆开：状态驱动的显隐（何时出现/何时淡出）、颜色编码、尺寸与对比层级、动效节奏、边缘化（不重要的信息放屏幕边缘）。
3. 锁定反馈：软锁与硬锁在 UI 上如何区分？锁定进度/导弹锁定提示如何表达？这是"信息即玩法"的典型案例，请重点分析。
4. 装配界面（Garage）的信息设计：
   - 数值对比（换件前后的差值如何呈现）
   - 重量/EN/热量等约束的可视化
   - 试算与预览、保存配装（AC Data）
   - 涂装/贴花/徽章的编辑界面
   请特别说明：这种"高维数值 + 高自由度编辑"的界面，技术上是如何做到实时响应的？
5. 任务流程界面：简报 → 出击 → 战斗中 → 结算（含弹药/修理费扣除）→ 商店/机库。画出流程图并标注每一步玩家做的决策。
6. 可及性（accessibility）：HUD 开关、字幕、色盲支持、按键重映射、文本大小。同时说明"没有难度选项"这一决定的得与失。
7. 反馈一致性：UI 动画时长、音效与 UI 的同步、警告音的优先级。
8. 分析三问：如果只显示 AP 和锁定框、隐藏其他所有信息会怎样？如果装配界面不给数值只给雷达图会怎样？如果没有伤害数字会怎样？
9. 验证路径：Menu*Param 系列（MenuParam、MenuPropertySpecParam、MenuPropertyLayoutParam、MenuValueTableParam、MenuBehaviorParam、MenuColorTableParam、MenuFilter、MenuInputGestureParam）、MenuPartsModelRendParam、MenuOffscrRendParam、KeyAssignDisplayParam、ActionButtonParam。说明"UI 由数据表驱动"这件事的证据与含义。

【TA 转化要求】
给一节"技术 UI 的实现"：
- 数据驱动 UI 的架构（数据表 → 绑定 → 视图；如何避免 UI 与逻辑耦合）
- UI 性能（合批、Draw Call、材质数量、动效开销、UI 与 3D 场景的混合渲染）
- 一个"实时数值对比"组件的实现思路（策划改表 → UI 自动更新）
说明 TA 在这套体系里的职责边界。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法。
````

---

## P11. 音频设计

````
你是音频总监 + 音频技术方向（technical audio）。请拆解《装甲核心6：境界天火》（AC6）的**音频设计**。
我大四，目标技术美术（TA）。音频常被 TA 忽略，但它是"信息通道"，也是中间件与工具链的重镇。

【必须回答】
1. 层次结构：BGM（菜单/战斗/Boss/结局）、环境音、机械音（伺服、液压、脚步、推进器）、武器音（按动能/能量/爆炸区分）、UI 音、通讯语音。给一张表：层次、触发条件、优先级、可屏蔽性。
2. **信息性音频**（最重要的一节）：AC6 里有很多"用声音传递战术信息"的设计。请列出：锁定提示音、导弹来袭警报、姿态崩溃警告、EN 耗尽提示、敌人充能预警音。分析：为什么这些信息要用声音而不是视觉？声音的信息带宽优势在哪里？如果玩家静音玩会损失什么？
3. 机甲音效的设计方法论：如何做出"几吨重的机器"的声音？请拆开：低频冲击、金属共振、伺服电机、液压、延迟与层次叠加、录音素材的变形处理。
4. 混音（mixing）：战斗中通讯语音必须清晰可懂，同时爆炸要够猛。优先级与侧链（ducking）如何设计？
5. 动态音乐：BGM 是否随战斗状态切换（探索/交战/Boss 阶段/濒死）？如何做到无缝？
6. 空间音频：三维高速移动中，声音定位如何不糊？距离衰减、多普勒、混响区域（室内/室外/地下）如何切换？
7. 分析三问：如果去掉所有锁定提示音会怎样？如果 BGM 全程播放不切换会怎样？如果通讯语音改成纯字幕会怎样？
8. 验证路径：这张游戏的数据表里存在大量 `WwiseValueToStrParam_Switch_*` 表（Switch_Weapon_Type、Switch_WeaponMaterial、Switch_AttackPowerType、Switch_BulletGenerateType、Switch_GeneratorType、Switch_ShootSeCategory、Switch_DestroyedSeType、Switch_Material、Switch_BGMStatus）以及 SoundParam、RuntimeSoundParam_Pc/Npc、SoundAutoReverbEvaluationDistParam、SoundAutoReverbSelectParam、SeMaterialConvertParam、HitEffectSfxParam、ThrustersSfxIdParam_PC、SoundVoiceBankLoad、WwiseValueToStrParam_Reflect*。请据此说明：
   - 这款游戏的音频中间件是哪一套（请说明你的判断依据）
   - "游戏参数驱动音频切换"的机制是怎么运作的（材质、武器类型、发电机类型、攻击属性各自会切换什么）
   - 动态混响是怎么被自动选择的

【TA 转化要求】
给一节"音频技术美术"的工作内容：中间件集成、参数（RTPC/Switch）绑定、音频资源命名与打包、声音预算与内存、音频事件与动画/状态的同步、音频调试工具。说明如果要复刻这套体系需要学什么（Wwise 优先）。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法。
````

---

## P12. 敌人 AI 与 Boss 设计

````
你是 AI 行为设计师 + Boss 设计者。请拆解《装甲核心6：境界天火》（AC6）的**敌人与 Boss 设计**。
我大四，目标技术美术（TA），需要理解"行为如何被数据驱动"。

【必须回答】
1. 敌人类型学：给一张表——杂兵（MT 类）、轻型快速、重型/四足、飞行、炮台/固定、狙击、护盾型、无人机群、精英 AC（敌方佣兵）。每类：战斗职能、行为特征、玩家应对手段、教学目的。
2. 敌方 AC（佣兵）与玩家的对称性：敌方 AC 使用和玩家相同的部件系统吗？这种对称性带来什么（读招可预测、装配有意义）与什么代价（数值膨胀风险）？
3. AI 行为结构：感知（视觉/听觉/雷达/被击中后的仇恨）、索敌、站位与距离保持、开火节奏、冷却与换弹、撤退与求援、增援触发。请用状态机描述一个典型敌人的完整行为循环。
4. **读招设计**（最重要的部分）：敌人的每一招如何做到"可读"？请拆开：预警信号（音效/动作预备/特效颜色/UI 提示）、可反应窗口时长、惩罚窗口、玩家可用应对手段（闪避/防御/走位）。给一张"招式 → 预警 → 窗口 → 惩罚"的表。
5. Boss 设计模板：阶段划分、招式表与冷却、部位破坏、场地机制、演出与音乐切换、血量与姿态值的双重血条。请说明"双血条（AP + 姿态）"如何改变 Boss 战的节奏。
6. 请挑 3~4 个有代表性的 Boss 做逐个拆解，说明各自承担的教学职责（例如：第一场大型 Boss 教你什么、中期的巨型 Boss 教你什么、终盘的人形 Boss 教你什么）。名称不确定时请描述战斗特征而非硬报名字。
7. 难度调优手段：敌人 AI 的哪些参数是难度旋钮（反应时间、命中率、开火频率、追击欲望）？为什么调这些比调血量更高级？
8. 分析三问：如果敌人永远不会主动接近会怎样？如果去掉所有预警信号会怎样？如果敌人的 AI 完全随机（不做距离管理）会怎样？
9. 验证路径：NpcThinkParam（思考）、NpcAiActionParam（行动）、BehaviorParam / BehaviorChangeStateMatrixParam（行为与状态迁移矩阵）、RoleParam（角色分工）、EnemyCommonParam、NpcParam、NpcEquipPartsParam、MovementEnemyTypeParam / MovementFlyEnemyParam / MovementRideObjParam、CharaInitParam、PartsBreakParam。请说明每条结论该去哪张表验证，以及"状态迁移矩阵"这种结构意味着什么样的 AI 架构。

【TA 转化要求】
给一节"数据驱动的敌人管线"：行为树/状态机与数据表的配合、策划如何在不改代码的情况下做新敌人、动画通知与判定的对齐、AI 调试可视化工具（行为状态显示、感知范围可视化、参数热重载）。说明 TA 能做哪些工具来加速这一流程。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法。
````

---

## P13. 系统与元循环（经济 / 进度 / 多周目 / PvP）

````
你是系统策划（meta systems designer）。请拆解《装甲核心6：境界天火》（AC6）的**元循环（meta loop）与经济系统**。
我大四，目标技术美术（TA），需要理解"系统如何形成长期驱动"以及"存档/数据如何承载它"。

【必须回答】
1. 主循环：任务 → 报酬 → 弹药/修理费扣除 → 商店购买/解锁 → 装配 → 更难的任务。请画出完整闭环，标注每一环的"爽点"与"摩擦点"。
2. 经济系统：
   - 货币（任务报酬）的产出与消耗结构
   - 弹药费与修理费的设计意图——为什么打赢了还要扣钱？它对玩家行为有什么影响？
   - 零件价格梯度与解锁节奏
3. 进度系统：
   - 零件通过哪些途径解锁（商店购买、任务奖励、战斗记录/隐藏收集、竞技场奖励、周目奖励）
   - 是否存在"错过就没了"的内容？
   - 佣兵等级/排名系统的作用
4. 竞技场（Arena）：作为"无风险练习场"的设计作用。为什么一个高风险游戏需要一个零风险的试炼场？它如何与主线解耦？
5. 多周目（New Game+ / ++）：新增任务、新增零件、第三个结局。请分析这种"重复游玩如何提供新内容"的设计——是加难度还是加视角？
6. PvP（对战模式）：规则结构、平衡手段、与 PvE 数值的冲突。平衡补丁（Regulation 更新）在其中的作用。
7. 存档与分享：配装数据（AC Data）、涂装、徽章的保存与分享/导入导出。这类"社交资产"的设计价值。
8. 评价系统：任务 S 评价大概考核什么？评价系统如何引导玩家提升水平？
9. 分析三问：如果取消弹药费会怎样？如果没有竞技场会怎样？如果多周目只是把敌人血量翻倍会怎样？
10. 验证路径：MissionParam、ArenaParam、NpcArenaGameEffectParam、MercenaryRankTable、CompanyContributePointParam、ShopLineupParam、ItemLotParam、EquipParamGoods、UnlockParam_* 系列（Equipment/OsPoint/NpAcArena/Trophy/Archive/DecalImage/EmblemPiece/NamePlate）、MultiPlayCorrectionParam、NetworkParam、WhiteSignCoolTimeParam、PlayerMaterialPresetParam、PresetEmblemSpec。请说明每条结论该去哪张表验证。

【TA 转化要求】
给一节"系统数据的技术承载"：装备数据库与解锁标志位、存档结构与版本兼容、分享码/配装序列化的设计考虑（防篡改、跨版本、体积）、在线数据与本地数据的一致性。说明 TA/工具程序员在这里做什么。

【输出规范】
结论先行；表格/流程图优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法。
````

---

## P14. 难度曲线与教学

````
你是关卡/系统向的难度与新手引导设计者。请拆解《装甲核心6：境界天火》（AC6）的**难度曲线与教学（onboarding）设计**。
我大四，目标技术美术（TA），需要理解"教学如何被工程化"。

【必须回答】
1. 前 30 分钟：玩家经历了什么？请按分钟给出流程（开场演出 → 教学任务 → 装配引导 → 第一次竞技场/训练 → 第一次真正的任务）。每一步教什么、怎么教（教 vs 让玩家自己发现）。
2. 难度来源分解：AC6 的难度来自 ①操作精度 ②认知负荷（读招/信息处理）③装配决策 ④资源管理。请估计四者的大致占比，并说明哪一个是"主要矛盾"。
3. 教学系统：AC6 有大量教学条目（tutorial）。请分析：
   - 教学是如何分发的（主动教程 / 被动触发 / 档案查阅）
   - 一个关键设计：教学系统能判定"玩家是否真的做出了某个动作"（行为判定）。请说明这种"行为判定式教学"的价值，以及它比"读弹窗"强在哪里。
   - 教学与实战的衔接（学完立刻用得上吗）
4. 卡关的官方解法路径：当玩家打不过时，游戏希望他做什么？（换装 → 换武器 → 换策略 → 提高操作）请分析这个顺序的设计意图——为什么把"换装"放在第一位。
5. 考试型 Boss（教学墙）：请找 1~2 个"你必须学会某个机制才能通过"的关卡/Boss，说明它考的是什么、失败时游戏给了什么提示。
6. 失败成本：重试的时间成本、金钱成本（弹药/修理费）、进度损失。低失败成本 + 高惩罚强度，这个组合好不好？
7. 没有难度选项的得与失：请客观分析（玩家自主调节难度的方式是什么？哪些玩家被排斥了？可及性批评是否成立？）
8. 曲线形状：请描述整体难度曲线的形状（是线性上升、阶梯式，还是有明显的"墙"和"喘息"）。标注"喘息点"的位置与作用。
9. 分析三问：如果加入四档难度选项会怎样？如果把教学全部改成强制弹窗会怎样？如果取消竞技场会怎样？
10. 验证路径：TutorialParam、TutorialActJudgeParam（教学行为判定！）、KnowledgeLoadScreenItemParam（读盘时投放知识）、MissionParam、EnemyCommonParam。说明如何从数据层量化"教学投放量"。

【TA 转化要求】
给一节"教学系统的实现"：触发器与条件判定、进度标记与存档、上下文提示 UI（不打断心流的提示）、读盘期内容投放、本地化。说明 TA 在其中做什么（工具、状态机、条件编辑器）。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法。
````

---

## P15. 技术实现与数据管线（TA 重点，且可本地验证）

````
你是资深技术美术 + 工具链工程师。请拆解《装甲核心6：境界天火》（AC6）的**技术实现与数据管线**。
我大四，目标技术美术（TA）。这一节我要的是"能动手验证"的知识，不是泛泛而谈。

【背景，请认真读】
我本地已经用 UXM 解包了游戏本体，并且拿到了 `regulation.bin`（参数表集合）与 `paramdef`（参数定义）。我用脚本统计出：`regulation.bin` 里有 **257 张 param 表**。下面这些表名是**从我本地文件里实际读出来的**，是真实存在的（仅列出与你分析相关的部分）：
LockCamParam / DirectionCameraParam / SubWindowCamParam / GarageCameraAnimParam / Zoomblur / BoostParam / ThrustersParam_PC / ThrustersLocomotionParam_PC / ENAutoRecoveryControlParam / EquipParamWeapon / EquipParamProtector / EquipParamBooster / EquipParamGenerator / EquipParamFcs / EquipmentLineupParam / AutoAssembleEvaluate / CalcCorrectGraph / OsReinforce / OsReinforcePoint / AtkParam_Pc / AttackActionParam_PC / BehaviorParam_PC / BehaviorChangeStateMatrixParam / ActionButtonParam / CoolTimeParam / CartridgeBehaviorParam / Bullet / BulletShotgunParam_PC / CylinderParam / ThrowParam / BladeHomingParam / BladeHomingAngSpeedParam / BladeHomingAutoCancelEnableParam / DamageLevelConvParam / DamageLevelConvThresholdParam / KnockBackParam / ShootReboundParam / SpEffectParam / HitMtrlParam / HitEffectSfxParam / HitEffectSfxConceptParam / ChrHitMaterialCheckParam / SeMaterialConvertParam / PadRumble / PartsBreakParam / PartsBreakLotteryParam / FootIKParam / FootIKSetupParam / HandIKParam / LookAtParam / LookAtHeadParam / LookAtSpineParam / ReTargetAnimSetParam / AnimMoveCorrectionParam / JigglerBaseParam / JigglerBehaviorParam / JigglerBehaviorSlideParam / JigglerBehaviorTargetBoneRateParam / JigglerBehaviorWorldFixParam / ChrProxyPhysicsParam / RigidBodyParam / RagdollParam / BuoyancyParam / MovementAcTypeParam / MovementEnemyTypeParam / MovementFlyEnemyParam / MovementRideObjParam / TankArmourParam / TankBaseParam / TankWheelParam / TankWheelModelParam / NpcThinkParam / NpcAiActionParam / RoleParam / EnemyCommonParam / NpcParam / NpcEquipPartsParam / CharaInitParam / NpcMaterialParam / NpcPartsParam / MapAreaParam / MapPartsParam / MapGimmickParam / GameAreaParam / PlayRegionParam / MiniAreaParam / PathFindCostParam / AssetEnvironmentGeometryParam / MissionParam / MissionSystemMsgAnswerParam / TalkParam / MailParam / FeFreeDialogParam / CutsceneGparamTimeParam / CutsceneGparamWeatherParam / CutsceneMapIdParam / CutsceneReplaceSfxParam / GarageCutsceneParam / TutorialParam / TutorialActJudgeParam / KnowledgeLoadScreenItemParam / ArenaParam / NpcArenaGameEffectParam / MercenaryRankTable / CompanyContributePointParam / ShopLineupParam / ItemLotParam / EquipParamGoods / EquipMtrlSetParam / DecalParam / PlayerColoringPresetParam / PlayerMaterialPresetParam / PlayerWeatheringTexPresetParam / PlayerCamouflagePattern / EmblemPieceSpec / PresetEmblemSpec / NamePlateParam / GraphicsParam / MaterialExParam / WetAspectParam / SkydomeAssetParam / GrassLodRangeParam / GrassTypeParam / LoadBalancerParam / LoadBalancerDrawDistScaleParam_ps4 / _ps5 / _xb1 / _xb1x / _xss / _xsx / _win64 / PartsDrawParam_ps4 / _ps5 / _scarlett / LoadBalancerNewDrawDistScaleParam_* / SoundParam / RuntimeSoundParam_Pc / RuntimeSoundParam_Npc / SoundAutoReverbEvaluationDistParam / SoundAutoReverbSelectParam / SoundVoiceBankLoad / WwiseValueToStrParam_Switch_Weapon_Type / _Switch_WeaponMaterial / _Switch_AttackPowerType / _Switch_BulletGenerateType / _Switch_GeneratorType / _Switch_ShootSeCategory / _Switch_DestroyedSeType / _Switch_Material / _Switch_BGMStatus / WwiseValueToStrParam_ReflectAuxBusType / _ReflectTextureType / UnlockParam_Archive / _Archive_Logs / _Archive_Terms / _Archive_Tips / UnlockParam_Equipment / _OsPoint / _NpAcArena / _Trophy / _DecalImage / _EmblemPiece / _MenuCommand / _NamePlate_Solo / _NamePlate_Team / UnlockParam_DLC / MultiPlayCorrectionParam / NetworkParam / PhantomParam / WhiteSignCoolTimeParam / GamePresenceParam / GameSystemParam / BudgetParam / ChrModelParam / ChrActTurnParam / PartsTokenParam / ReinforceParamWeapon / ReinforceParamProtector / ShieldParam_Pc / TankArmourParam / DamageLevelConvParam / RuntimeSoundExpressionParam_Pc / MenuParam / MenuPropertySpecParam / MenuPropertyLayoutParam / MenuValueTableParam / MenuBehaviorParam / MenuColorTableParam / MenuFilter / MenuInputGestureParam / MenuPartsModelRendParam / MenuOffscrRendParam / KeyAssignDisplayParam

【你的任务】
1. **从这个表名清单反推架构**：请分析这份表名清单能证明/暗示什么。例如：`LoadBalancerDrawDistScaleParam_ps5` 与 `PartsDrawParam_ps5` 这样的命名说明了什么？`Jiggler*` 系列五张表的存在说明了什么？`ReTargetAnimSetParam` 说明了什么？`WwiseValueToStrParam_Switch_*` 说明音频架构是什么？`TutorialActJudgeParam` 说明教学系统具备什么能力？`AutoAssembleEvaluate` 说明什么？请逐条给出"表名 → 推断 → 置信度"。
2. **数据驱动架构总览**：以"一个武器从策划填表到玩家手上开火"为线索，串起涉及的表（EquipParamWeapon → EquipmentLineupParam / ShopLineupParam → AtkParam_Pc → AttackActionParam_PC → BehaviorParam_PC → Bullet → HitMtrlParam / HitEffectSfxParam → DamageLevelConvParam → SpEffectParam）。请把这个链路讲成一条可理解的故事，并指出每一环由谁负责（策划/程序/TA/美术/音频）。
3. **参数表与 paramdef 的关系**：解释 param 表、paramdef（表结构定义）、row/field 的关系。说明"为什么改了 paramdef 就能改表结构"，以及社区工具链一般怎么工作。
4. **从数据反推设计的通用方法**：给一套方法论——当我想验证一个设计假设（比如"姿态阈值是固定值还是百分比"）时，应该怎么查表、怎么做对照实验、怎么排除干扰。请给出 5 个可执行的验证案例。
5. **从数据反推视觉/音频资产**：`PartsDrawParam`、`MaterialExParam`、`DecalParam`、`SeMaterialConvertParam`、`NpcMaterialParam` 这类表说明美术资产是被数据索引的。请说明这对 TA 的意义（资产命名规范、材质与数据的绑定、变体管理）。
6. **性能分级**：`LoadBalancer*` 与 `PartsDrawParam_*` 按平台分档说明了什么？TA 在做跨平台项目时应该怎么设计"分档参数"体系？
7. **工程化与合规**：分析这类数据驱动架构的优点与代价（改一个数就上线 vs 难以追踪依赖）。同时给出合规提醒：本地学习研究可以做什么、不可以做什么（不分发版权资产、不破坏在线服务）。
8. **分析三问**：如果所有数值都硬编码在代码里会怎样？如果参数表没有版本管理会怎样（补丁如何影响 mod 与存档）？如果表结构频繁变动会怎样？

【TA 转化要求】
给我一份"用数据表学 TA 的 4 周实操计划"：每周目标、要看的表、要产出的东西（一张表、一个脚本、一份可视化报告）。要求能在本地解包环境里完成。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；不确定就说不确定 + 验证方法；禁止编造参数含义（你只能基于表名和公开知识推断，并明确标注推断）。
````

---

## P16. 系列演化与商业定位

````
你是产品/市场方向的游戏策划。请分析《装甲核心6：境界天火》（AC6）的**系列演化与商业定位**。
我大四，目标技术美术（TA），这一节帮我看清"我在做的是什么类型的产品"，避免只懂技术不懂市场。

【必须回答】
1. 系列脉络：从 1997 年初代 Armored Core 到 AC6 的演化（含中间的低谷期作品）。请用表格列出关键世代：作品名、年代、平台、核心变化、口碑/表现（不确定的标注不确定）。
2. AC6 的定位转折：沉默了十年后重启，它保留了哪些系列基因、砍掉了哪些、加入了哪些现代设计？请明确区分"系列传统"与"本作新增"。
3. 与开发商其他作品的关系：FromSoftware 在魂系上的积累（关卡、Boss、难度哲学、碎片化叙事）如何被移植进机甲题材？哪些移植是成功的、哪些是别扭的？
4. 竞争环境：机甲动作这个品类在当代的市场位置。为什么"没有竞品"既是机会也是风险？
5. 目标用户：核心老玩家 vs 新玩家的需求冲突。AC6 是如何同时讨好两边（或得罪了谁）的？
6. 内容体量与商业模型：主线时长、多周目、PvP、是否有 DLC/更新（不确定就标注）。它是一次性买断还是长线运营？平衡补丁（Regulation）在其中扮演什么角色？
7. 长尾生态：Mod 社区、PvP 社区、速通/挑战玩法。玩家自创内容（配装分享、涂装、徽章）如何延长生命周期？
8. 对从业者的启示：从产品定位角度，AC6 给"垂直细分品类怎么做"提供了什么经验？
9. 分析三问：如果 AC6 做成开放世界会怎样？如果做成纯 PvP 竞技游戏会怎样？如果降低操作门槛以扩大用户群会怎样？
10. 验证路径：MissionParam（任务数量反映内容体量）、ArenaParam（竞技场条目）、UnlockParam_DLC（是否存在 DLC 内容入口）、MultiPlayCorrectionParam / NetworkParam（联机设计）、MercenaryRankTable（长期成长设计）。请说明可以从数据层量化哪些"内容体量"指标。

【TA 转化要求】
用 3~5 句话说明：了解产品定位后，一个 TA 应该在技术上优先投入什么（例如资产规模决定管线策略、跨平台决定性能预算、长线运营决定工具与热更新能力）。

【输出规范】
结论先行；表格优先；证据等级 A/B/C/D；不确定就说不确定 + 验证方法；禁止把营销话术当分析。
````

---

## P17. 深挖追问（对任何一条结论下钻三层）

````
上一轮你给出了关于《装甲核心6：境界天火》的分析。现在我要对其中最关键的结论做下钻。

【选择下钻对象】
从你的输出里挑出 **3 条最"空"或最像常识的结论**（即：说了等于没说、或者任何动作游戏都成立的那种），然后对每一条连做三层下钻：
- 第一层：这条结论具体指哪个系统、哪个参数、哪个时间点？
- 第二层：它是怎么实现的？（机制、数据结构、状态机、资源流向）
- 第三层：如果把它拆到"一个策划能填、一个程序能实现、一个 TA 能调试"的粒度，需要哪些字段和数值？

【硬性要求】
1. 三层下钻必须逐层给出可验证的细节，不允许在第二层就退回抽象描述。
2. 每一层结尾必须回答："我怎么知道你说的是对的？"（给出验证方法：看哪张数据表 / 做什么实测 / 用什么对照实验）
3. 如果某一条你其实并不知道答案，请直接说"这条我无法下钻到第三层，原因是……"，然后给出"获取答案的路径"。**宁可承认不知道，也不要编。**
4. 最后补一句：这三条结论里，哪一条对"技术美术"的技能提升最有价值？为什么？

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D。
````

---

## P18. 对抗审查（让 AI 打假自己）

````
你现在切换角色：你是这篇《装甲核心6：境界天火》拆解报告的**审稿人 / 红队**。你的任务是**找出报告里的错误、幻觉和"正确的废话"**。

【审查清单（逐条检查，不能跳过）】
1. **数值幻觉**：报告里出现的所有精确数值（秒、米、度、百分比、帧数）——哪些是真实可信的？哪些是编造的？请逐条列出并标注"可信 / 存疑 / 很可能是编的"。特别注意：不同补丁版本（Regulation 更新）会改变数值，报告是否忽略了版本差异？
2. **系列混淆**：报告是否把 AC 系列其他作品（AC4/AC4A、AC5/VD、甚至其他机甲游戏）的设计错记成了 AC6 的设计？
3. **魂系套用**：报告是否把 FromSoftware 魂系游戏的惯例（例如翻滚无敌帧、篝火、韧性系统）想当然地套到了 AC6 上？请逐条指出。
4. **正确的废话**：哪些结论其实是任何动作游戏都成立的？把它们删掉，报告会损失什么？（如果不损失什么，就说明这些是凑字数的。）
5. **幸存者偏差**：报告是否只分析了"成功的部分"？AC6 有哪些**被广泛批评**的设计（例如某些关卡、某些 Boss、平衡性问题、可及性批评）？请补上，并且给出这些批评的合理性评估。
6. **缺失的维度**：报告漏掉了哪些对理解这个游戏至关重要的系统？
7. **不可验证的断言**：哪些结论根本无法证伪？把它们单独列出来，并说明为什么它们没有分析价值。
8. **最重要的追问**：如果这份报告是一个求职者写给面试官的，面试官最可能在哪一点上把他问倒？请给出 5 个"犀利追问"及其回答要点。

【输出格式】
用表格输出每一条问题：`原文结论 | 问题类型 | 严重程度(高/中/低) | 为什么有问题 | 修正后的说法`。
最后给一段总体评价：这份报告的可信度百分比，以及"最该被扔掉的 3 条结论"。

【纪律】
不要为了显得严格而编造批评。如果某条结论其实是正确的，就明确说"这条没问题"。
````

---

## P19. 汇总合成（把多轮结果合并成一份报告）

````
我手里有多轮关于《装甲核心6：境界天火》（AC6）的拆解结果（来自不同对话/不同维度）。请你把它们**合并、去重、去冲突**，产出一份结构统一的《AC6 设计拆解报告》。

【我会粘贴给你的材料】
（在此粘贴 P1~P16 的输出，可分批粘贴）

【合并规则】
1. **冲突优先处理**：如果两份材料对同一机制给出不同说法，不要和稀泥。请用表格列出冲突项，分别给出"说法 A / 说法 B / 你倾向哪一个 / 理由 / 如何验证"。
2. **去重**：同一结论在多处出现的，只保留一次，并合并各自的补充细节。
3. **保留证据等级**：合并后每个数值仍要带 A/B/C/D 等级。如果两处等级不一致，取更保守的那个并说明。
4. **补齐短板**：指出材料整体最薄弱的 3 个维度，并说明需要补什么。

【最终报告结构】
1. 一句话总结（这个游戏最核心的设计主张是什么）
2. 系统总览图（用文字/表格画出各系统之间的依赖关系：装配 → 战斗数值 → 反馈 → 关卡 → 元循环）
3. 分维度详述（每维：结论先行 3~5 条 + 表格 + 四段式要点）
4. **设计要素 → TA 技能映射表**（不少于 25 行）：游戏做法 | 需要的技术能力 | 学习优先级 | 可验证的练习项目
5. 10 条"如果我要复刻，必须先解决的技术难题"（按难度排序）
6. 一份"待验证清单"：所有 D 级结论 + 验证方法（查哪张表、做什么实测）
7. 参考与不确定声明：明确列出哪些内容是不确定的、哪些依赖版本

【输出格式】
Markdown。大量使用表格。开头放一个目录。不要用代码块包裹整篇回答。
````

---

## P20. 能力转化（把拆解变成你的 TA 作品集与学习路线）

````
你是"游戏行业求职教练 + 技术美术负责人"。我是一名大四学生，职业目标是**技术美术（TA）**，计划从**策划岗**入门。我已经完成了对《装甲核心6：境界天火》（AC6）的系统拆解。

【粘贴材料】
（在此粘贴 P19 的汇总报告，或 P1~P16 的结论要点）

【我的现状（请按此校准难度）】
- 学历/年级：大四
- 目标岗位：技术美术（TA），进入路径：策划岗入门
- 已具备的技能：（在此填写：如 UE5 基础 / Maya 或 Blender / Python / 着色器基础 / 是否有作品）
- 可用时间：每天 X 小时，距离毕业还有 Y 个月

【你要产出的东西】
1. **能力缺口表**：把 AC6 拆解里出现的每一项技术能力，对照我"已具备/部分具备/完全不会"，给出学习优先级（P0/P1/P2）。用表格，不少于 20 行。
2. **学习路线图**：按"月 → 周"给出 3 个月计划。每周：学什么、产出什么可展示的东西、如何验收。要求每个月的产出都能进作品集。
3. **作品集项目设计**：基于 AC6 拆解，给我 3 个可落地的 TA 作品集项目，每个包含：
   - 项目名与一句话卖点
   - 复刻的是 AC6 的哪个系统
   - 技术要点（引擎/工具/关键技术）
   - 工作量估计（人日）
   - 验收标准（能演示出什么效果）
   - 面试时怎么讲（3 句话）
   要求难度递进：一个"能做完"，一个"有亮点"，一个"能吹"。
4. **最小原型任务书**：一份 UE5 的"AC6 式机甲战斗最小原型"任务书，按 P0/P1/P2 排序，P0 部分必须能在 2 周内做完。要具体到：需要哪些系统、哪些数据资产、哪些蓝图/材质/Niagara、验收标准是什么。
5. **五个可讲的拆解故事**：从拆解结果里挑 5 个点，写成"面试可讲"的 60 秒小故事（现象 → 我的分析 → 我验证的方法 → 我学到的能力）。要求每个故事都体现"我不仅看懂了，我还动手验证过"。
6. **诚实的风险提示**：以我（大四、从策划入门、想做 TA）的处境，最可能的三个卡点是什么？分别给出应对方案。不要安慰我，直接说难点。

【纪律】
- 不要给我"多练习、多学习"这类废话，每一周都要有具体产出物。
- 如果我填写的现状信息不足，先列出你需要我补充的信息，再基于假设给出方案并标明假设。
- 输出 Markdown，表格优先。
````

---

# 附录 A. 真实 param 表索引（你的杀手锏）

> 来源：你本地解包后的 `regulation.bin`，共 **257 张** param 表（用 `paramdiff_tables.csv` 统计得到）。
> 用法：AI 给了结论 → 查这张表 → 证实或证伪 → 把过程写进你的拆解报告/作品集。
> 注意：**表名可靠**；表内**字段含义需要 `paramdef` 才能确定**（你本地已有 `paramdef.paramdefbnd.dcx`）。

| 你想验证的问题 | 去看哪张表 | 能证明什么 |
|---|---|---|
| 相机状态与锁定行为 | `LockCamParam`、`DirectionCameraParam`、`SubWindowCamParam`、`GarageCameraAnimParam` | 锁定相机参数、方向相机（自由视角）、子窗口（瞄准/画中画）、机库展示镜头 |
| 速度感与冲刺变焦 | `Zoomblur`、`GraphicsParam` | 冲刺时的变焦/径向模糊确实被数据化，不是纯后处理常量 |
| 推进器 / AB / QB 性能 | `BoostParam`、`ThrustersParam_PC`、`ThrustersLocomotionParam_PC` | 推力、消耗、时长、移动学参数 —— QB/AB 手感的数值来源 |
| EN 经济 | `EquipParamGenerator`、`ENAutoRecoveryControlParam` | 发电机输出/容量 + **自动回复曲线**（回复延迟与速率） |
| 武器面板与三属性 | `EquipParamWeapon`、`AtkParam_Pc`、`AttackActionParam_PC` | 面板数值、攻击参数（三属性/姿态伤害）、动作参数 |
| 弹丸与弹道 | `Bullet`、`BulletShotgunParam_PC`、`CylinderParam`、`ThrowParam` | 弹速、散射、追踪、投掷物 |
| 近战吸附（刀光追踪） | `BladeHomingParam`、`BladeHomingAngSpeedParam`、`BladeHomingAutoCancelEnableParam` | 近战吸附的角度/角速度/取消条件 —— "近战为什么这么黏" |
| 硬直与击退 | `DamageLevelConvParam`、`DamageLevelConvThresholdParam`、`KnockBackParam`、`ShootReboundParam` | 伤害等级转换、**阈值表**（姿态系统核心）、击退、跳弹 |
| 命中反馈 | `HitMtrlParam`、`HitEffectSfxParam`、`HitEffectSfxConceptParam`、`ChrHitMaterialCheckParam`、`PadRumble` | "材质 → 特效/音效/震动"的映射是数据化的 |
| 部件破坏 | `PartsBreakParam`、`PartsBreakLotteryParam` | 部位破坏规则 + 随机抽选（RNG 参与） |
| 装配与自动配装 | `EquipParamProtector/Booster/Generator/Fcs`、`EquipmentLineupParam`、`AutoAssembleEvaluate` | 全部部件表 + **AI 自动配装的评价函数** |
| 数值曲线（边际收益） | `CalcCorrectGraph` | 魂系同款"曲线表"，用于实现非线性收益 —— 重量/收益是否线性直接查它 |
| OS 强化 | `OsReinforce`、`OsReinforcePoint`、`UnlockParam_OsPoint` | 强化项、点数成本、解锁点 |
| 动作与状态机 | `BehaviorParam_PC`、`BehaviorChangeStateMatrixParam`、`ActionButtonParam`、`CoolTimeParam`、`CartridgeBehaviorParam` | 行为表、**状态迁移矩阵**（AI/动作架构证据）、按键、冷却、弹匣行为 |
| 机甲惯性与二次运动 | `JigglerBaseParam`、`JigglerBehaviorParam`、`JigglerBehaviorSlideParam`、`JigglerBehaviorTargetBoneRateParam`、`JigglerBehaviorWorldFixParam`、`ChrProxyPhysicsParam`、`RigidBodyParam` | 机械晃动/惯性摆动是**专门一套系统**（5 张表！）、代理物理、刚体 |
| 动画与 IK | `FootIKParam`、`FootIKSetupParam`、`HandIKParam`、`LookAtParam`、`LookAtHeadParam`、`LookAtSpineParam`、`ReTargetAnimSetParam`、`AnimMoveCorrectionParam` | 脚部 IK 地形适应、注视（头/脊柱分层）、**动画重定向**（共享骨架证据）、位移修正 |
| 移动元型 | `MovementAcTypeParam`、`MovementEnemyTypeParam`、`MovementFlyEnemyParam`、`MovementRideObjParam`、`TankArmourParam`、`TankBaseParam`、`TankWheel*`、`BuoyancyParam` | 机体移动类型、飞行敌人、载具、坦克专用表、浮力 |
| 敌人 AI | `NpcThinkParam`、`NpcAiActionParam`、`RoleParam`、`EnemyCommonParam`、`NpcParam`、`NpcEquipPartsParam` | AI 思考、行动、角色分工、通用参数、NPC 装备 |
| 关卡与地图 | `MapAreaParam`、`MapPartsParam`、`MapGimmickParam`、`GameAreaParam`、`PlayRegionParam`、`MiniAreaParam`、`PathFindCostParam` | 区域划分、地图部件、机关、寻路代价 |
| 任务与分支 | `MissionParam`、`MissionSystemMsgAnswerParam`、`TalkParam`、`MailParam`、`FeFreeDialogParam` | 任务表、**任务中的选择/应答（分支证据）**、台词、**邮件（叙事载体）**、自由对话 |
| 过场演出 | `CutsceneGparamTimeParam`、`CutsceneGparamWeatherParam`、`CutsceneMapIdParam`、`CutsceneReplaceSfxParam`、`GarageCutsceneParam` | 过场的时间/天气/地图/音效替换 —— 过场是**参数化调度**的 |
| 教学系统 | `TutorialParam`、`TutorialActJudgeParam`、`KnowledgeLoadScreenItemParam` | 教学项 + **行为判定**（能验证玩家是否真的做了动作）+ 读盘期投放知识 |
| 竞技场与排名 | `ArenaParam`、`NpcArenaGameEffectParam`、`MercenaryRankTable`、`CompanyContributePointParam` | 竞技场条目、效果、佣兵等级、企业贡献 |
| 涂装 / 徽章 / 贴花 | `DecalParam`、`PlayerColoringPresetParam`、`PlayerMaterialPresetParam`、`PlayerWeatheringTexPresetParam`、`PlayerCamouflagePattern`、`EmblemPieceSpec`、`PresetEmblemSpec`、`NamePlateParam` | 涂装预设、**旧化贴图预设**、迷彩、徽章构件 —— 玩家定制是靠"预设+遮罩"实现的 |
| 渲染与性能分档 | `GraphicsParam`、`LoadBalancerParam`、`LoadBalancer*DrawDistScaleParam_ps5/xsx/win64…`、`PartsDrawParam_ps5/scarlett…`、`GrassLodRangeParam`、`SkydomeAssetParam`、`WetAspectParam`、`MaterialExParam` | **按平台分档的绘制距离与部件绘制预算**（跨平台优化的实证）、天空/湿润/材质扩展 |
| 音频（中间件） | `SoundParam`、`WwiseValueToStrParam_Switch_*`（9 张）、`SoundAutoReverb*`、`RuntimeSoundParam_Pc/Npc`、`ThrustersSfxIdParam_PC`、`SeMaterialConvertParam`、`SoundVoiceBankLoad` | 中间件是 **Wwise**；音频由武器类型/材质/发电机/攻击属性等**游戏参数驱动切换**；动态混响自动选择 |
| 经济与解锁 | `ShopLineupParam`、`ItemLotParam`、`EquipParamGoods`、`EquipMtrlSetParam`、`UnlockParam_*`（14 张） | 商店、掉落、素材、各类解锁标志位 |
| 联机 | `MultiPlayCorrectionParam`、`NetworkParam`、`WhiteSignCoolTimeParam`、`GamePresenceParam`、`PhantomParam` | 联机数值修正、在线状态、幻影（其他玩家） |
| 平台差异 | `PartsDrawParam_ps4/ps5/scarlett`、`LoadBalancerDrawDistScaleParam_*` | 同一套内容按平台给出不同绘制预算 —— TA 跨平台分档设计的现成案例 |

---

# 附录 B. 已知锚点清单（给 AI 兜底，但**要求它复核**）

把这些作为"起点"塞给 AI，可以显著减少它答偏；但**必须**同时要求它复核，否则它会顺手把错的当对的。

| 锚点 | 说明 | 我方把握 |
|---|---|---|
| 游戏全名 | ARMORED CORE VI: FIRES OF RUBICON，FromSoftware，2023 | 高 |
| 主角设定 | 沉默、无脸的强化人佣兵，玩家可自定义 | 高 |
| 核心身份 | 佣兵（Mercenary），靠接任务赚钱，装备可完全自定义 | 高 |
| 舞台 | 行星 Rubicon 3（Rubicon III），争夺物质 Coral | 高 |
| 三大伤害类型 | Kinetic（动能）/ Energy（能量）/ Explosive（爆炸），对应三种抗性 | 高 |
| 姿态系统 | 姿态稳定/回复 → 打满触发硬直（Stagger / ACS overload），硬直期间受创加成 | 高 |
| 部件槽位 | 头/核心/手臂/腿/推进器/FCS/发电机/扩展 + 四武器槽（右手/左手/右肩/左肩） | 高 |
| 移动技 | Boost、Quick Boost（QB）、Assault Boost（AB）、近战突进、踢击 | 高 |
| 三结局 | **The Fires of Raven**（Cinder Carla / Handler Walter 线）、**Liberator of Rubicon**（Ayre 线）、**Alea Iacta Est**（ALLMIND，真结局） | 高（2026-09-11 已联网核实） |
| 结局与周目 | 第三个结局 Alea Iacta Est 需要先完成前两个结局；但"Liberator of Rubicon 是否需要 NG+"存在相互矛盾的说法，请 AI 自行核实 | 中 |
| 强化人世代 | Augmented Human 的世代设定（第 1~10 世代）与其代价 | 中 |
| 主要势力 | Arquebus、Balam、Schneider's、Furlong、Elcano、PCA（行星封锁机构）、RLF（本地抵抗组织）、RaD、Overseer、Rubicon 研究机构 | 中（拼写待核） |
| 标志性 Boss | **AH12: HC Helicopter**、**HA-T-102 Juggernaut**、**AAP07: BALTEUS**、**IA-13: SEA SPIDER**、**IB-01: CEL 240**、**IB-07: SOL 644**（Ayre）、EB-0309 STRIDER、ENTANGLE / Sulla、IA-24: KITE、IA-27: GHOST | 高（2026-09-11 已联网核实，编号可用） |
| 竞技场 | Arena（单人对战 NPC），与主线分离 | 高 |
| 元循环 | 任务报酬 − 弹药费 − 修理费 → 商店买件 → 装配 → 更难任务 | 高 |
| 货币名 | **COAM**（游戏内货币，靠完成任务赚取） | 高（2026-09-11 已联网核实） |
| 敌方机体代号体系 | 存在正式的编号体系：`AH12`（直升机）、`HA-T-102`、`AAP07`、`EB-0309`、`IA-xx`（C-Weapon 系列）、`IB-xx`、`AM02` 等 | 高 |
| 平衡补丁 | 通过 Regulation 更新调整数值（影响 mod 与攻略） | 中-高 |

**给 AI 的强制指令（每次都附上）**：
> 上表是"未经你核实的锚点"。请逐条判断：确认 / 不确定 / 有误。有误的请给出正确说法并说明依据。**不要因为我给了就默认它对。**

---

# 附录 C. 常见翻车点（AI 会怎么骗你）

| 翻车点 | 表现 | 对策（已写进提示词的哪一条） |
|---|---|---|
| **数值幻觉** | 给出"0.35 秒无敌帧""QB 有 12 帧无敌"这种精确到离谱的数字 | 强制 A/B/C/D 证据分级 + 禁止编造精确数值 |
| **魂系套用** | 把翻滚无敌帧、篝火、韧性系统当成 AC6 的机制 | P18 对抗审查第 3 条 |
| **系列混淆** | 把 AC4/AC5 的机制（如 AC5 的"UNAC"）说成 AC6 的 | P18 第 2 条 |
| **正确的废话** | "打击感很强""沉浸感优秀""难度设计合理" | 统一规范第 4 条（禁止无机制支撑的形容词）+ P17 深挖 |
| **只讲优点** | 不提可及性批评、平衡性争议、争议关卡 | P18 第 5 条（幸存者偏差） |
| **版本失忆** | 忽略补丁导致数值变化，把 1.0 的平衡当现状 | P18 第 1 条 |
| **把百科当分析** | 大段剧情复述、设定罗列 | 各维度的"硬性要求"节 |
| **不敢说不知道** | 用模糊措辞糊过去 | 规范里明确写"宁可承认不知道" |
| **忽略你的数据优势** | 它不知道你有解包数据 | P15 把真实表名清单喂给它 + 附录 A |

---

# 附录 D. 短版提示词（上下文预算不足时用）

如果某个 AI 有长度限制、或你想要一个快速版，用这条：

````
你是资深游戏系统策划 + 技术美术。请对《装甲核心6：境界天火》（FromSoftware, 2023）做拆解，读者是一名想入行技术美术（TA）的大四学生。

要求：
1. 按这 16 个维度分别输出：相机 / 战斗数值与姿态硬直 / 装配系统 / 动作与动画 / 手感与反馈 / 关卡遭遇 / 敌人与 Boss AI / 美术与渲染 / UI / 音频 / 剧情叙事 / 世界观 / 元循环经济 / 难度与教学 / 技术实现与数据管线 / 系列与商业定位。
2. 每个维度：先给 3 条结论，再用表格列关键机制，每条机制按"设计意图 → 实现手段 → 玩家体验 → 可复用结论"写。
3. 每个数值必须标证据等级：A 游戏内可观察/官方，B 社区实测/数据挖掘，C 合理推断，D 不确定（并写如何验证）。不确定就直接说不确定，不要编。
4. 禁止"打击感很好"这类没有机制支撑的评价；禁止复述剧情梗概当分析。
5. 每个维度结尾回答三个问题：删掉它会怎样？参数放大/缩小 10 倍会怎样？它解决什么问题、有没有更简单的替代？
6. 最后给两张表：①"设计要素 → TA 技能"映射（≥20 行）；②"待验证清单"（所有不确定项 + 验证方法）。

补充：我本地有解包后的游戏数据（regulation.bin，257 张 param 表，含 LockCamParam / BoostParam / EquipParamWeapon / AtkParam_Pc / BehaviorParam_PC / JigglerBaseParam / FootIKParam / ReTargetAnimSetParam / TutorialActJudgeParam / WwiseValueToStrParam_Switch_* 等）。请在你认为需要验证的结论后标注"应查哪张表"。
````

---

## 附：建议的对话排期（一天一维，16 天走完）

| 天 | 内容 | 产出 |
|---|---|---|
| D1 | P0 母提示词 | 全局骨架 + 疑问清单 |
| D2–D3 | P5 装配 + P2 战斗 | 数值体系理解（这是游戏的核心） |
| D4–D5 | P6 动作动画 + P7 手感反馈 | **TA 重点**，直接产出复刻清单 |
| D6–D7 | P9 美术渲染 + P10 UI | **TA 重点** |
| D8 | P1 相机 | 独立系统，注意与 P6 交叉 |
| D9 | P8 关卡 + P12 敌人 Boss | 空间与行为 |
| D10 | P15 技术管线 | 结合本地解包实操 |
| D11 | P3 剧情 + P4 世界观 | 叙事与设定 |
| D12 | P11 音频 + P13 元循环 | 常被忽略的两块 |
| D13 | P14 难度教学 + P16 商业 | 收尾 |
| D14 | P17 深挖 | 把最虚的结论打实 |
| D15 | P18 对抗审查 | 打假，得到可信版本 |
| D16 | P19 + P20 | 合成报告 + 个人能力路线 |

> 提示：`P6 / P7 / P9 / P10 / P15` 是你作为未来 TA 的**主战场**，值得各花两天并把产出直接做成小 Demo。
