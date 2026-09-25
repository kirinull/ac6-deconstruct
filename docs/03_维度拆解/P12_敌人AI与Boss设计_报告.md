# P12 ·《装甲核心 6：境界天火》敌人 AI 与 Boss 设计拆解

> 读者设定：大四、目标技术美术（TA）、从策划岗入门。
> 证据分级：**A** = 游戏内可直接观察 / 官方；**B** = 社区实测、Wiki、数据挖掘（本报告凡标 B 的均附本机实测命令与原始输出）；**C** = 基于同类游戏的合理推断；**D** = 不确定，附验证方法。
> 本报告所有"实测"均来自本机解包的 `van/regulation-bin/*.param` + AC6 专用 paramdex，命令与原始输出见第 1 节。

---

## 0. 结论先行

1. **AC6 的敌人系统是"同 ID 多表"结构**：同一只敌人（如 `30000000` 警備MT）在 `NpcParam` / `NpcThinkParam` / `NpcEquipPartsParam` / `MovementEnemyTypeParam` / `ChrActTurnParam_Npc` / `DamageLevelConvThresholdParam` 里用的是**同一个行 ID**。做一只新敌人 = 在 8 张表里各加一行同 ID 的行，**不改代码**。（B，实测见 1.2）
2. **感知有四套视野 + 嗅觉 + 雷达**，但实战里只有第一套 `eye_*` 在用：`searchEye_dist` 1178 行中仅 7 行非零、`searchEye2_dist` 全 0、`battleEye_dist` 仅 3 行非零。这是**继承魂系感知框架后没有删干净的残留**。（B）
3. **听觉实际上被关掉了**：`ear_dist` 在 1047/1178 行填 `0.1` 米（等价于无）。所以 AC6 的"被声音吸引"主要靠脚本而不是这套感知参数。（B）
4. **敌人攻击的"预兆"不在敌人表里**：`AttackActionParam_NPC`（1371 行）里 `shootIndicationType` **全为 0**，而 `AttackActionParam_PC`（418 行）里有 33 行 = 1（`強射撃予兆`）。→ 射撃予兆这套 UI/FX 预告是挂在 **PC（玩家一系/AC 类机体）攻击动作**上的。**P7 报告把它标成"敌方攻击预警"需要修正**。（B，实测见 1.4）
5. **敌人的 `alertLevel` 确实存在且存在稀缺**：`AttackActionParam_NPC.alertLevel = 1` 仅 47/1371 行；`alertShowType = 2（出さない）` 102 行。也就是说**绝大多数杂兵攻击没有专属预警通道**，读招靠的是"动作预备 + 弹药飞行时间 + 音效"。（B）
6. **"双血条"是被数据明确分开的两套系统**：AP 走 `NpcParam` 的 HP；姿态/冲击走 `EnemyCommonParam`（本体体干 100 / 动作体干 20 / 回复延迟 5s / 20 点每秒回复）+ `NpcParam.stabilityVal` + `EquipParamProtector.stability`。**姿态条是可回复的、AP 不可回复**。（B/C）
7. **每个敌人的"受击反应词汇表"是单独的一张阶梯**：`DamageLevelConvThresholdParam` 57 行、48 种唯一步梯；自机是 `[150,1600,1600,2000,7500,9000,13000]`，警備MT 只有 `[10,40,121,221, 然后 999999999×3, -1×4]` —— **小 MT 根本不会被"吹飞"（DL5 不存在）**；四脚MT 则是 `[1800,2100,2200,2300,…]`（硬得多）。（B）
8. **受击等级 → 手柄震动是一条真实链路**：`CameraRumbleParam`（文件 `PadRumble.param`）的行名直接写着 `9280 段階加算被弾 / 9290 100%加算被弾 / 9300 小よろけ / 9310 大よろけ（スタッガー）/ 9320 吹っ飛び開始`。**DL→震动的映射是表驱动的，不是代码硬编码**。（B，复核了 P7）
9. **部位破坏是"部位 HP 表 + 抽选表"两段式**：`NpcPartsParam`（110 行）给每个部位 `partsHp` / `partsDmgCorrect` / `addImpactRate` / `hitFEType`；`PartsBreakLotteryParam`（8 行）用 `pairN_Value / pairN_Weight` 做**加权抽选**（例：rid=11 是 `(0,20),(20,80)`，rid=9999 是 `(0,100),(10,100),(20,100)`）。（B）
10. **AI 架构 = 「脚本层（logicId） + 目标评分层（索敌度/交戦度） + 通知层（BehaviorChangeStateMatrix） + EzState 动画状态机」四层**，不是纯行为树。`BehaviorChangeStateMatrixParam` 227 行里，每行 = 「一条动画/事件 → 在哪些运动状态下有效（20 位掩码）→ 通知 AI 的迁移类型（30 行非零）→ AI 通知 ID（22 行非零：1000/1100/1200/1210/1500）」。（B/C）
11. **`NpcAiActionParam`（126 行）是魂系遗留物**：行名全是"R1攻撃 / ローリング / はしご / ジェスチャID"，且 `key3` 全 0、40 行是手势。AC6 的敌人动作不走"模拟手柄输入"这条路。（B）
12. **难度旋钮的真实排序（从廉价到昂贵）**：受击反应阶梯 → 转向速度 → 视距/索敌阈值 → 开火节奏 → 距离带与站位 → 招式组合与预警长度。**血量几乎不在设计者的手里**，因为它同时破坏战斗时长、姿态节奏、弹药经济三条线。
13. **敌方 AC 分两档**：`汎用…AC`（32xxxxxx）走完整 NPC 表族（有自己的预设/移动/转向/受击阶梯）；**命名佣兵 AC（10xxxxxx–21xxxxxx）把 `equipWeaponPresetId / npcPartsParamId / movementTypeParamId / chrActTurnParamIdOffset` 全部留 0 或 −1**，落回"AC 默认行"——而 `ChrActTurnParam rid=0` 在 PC 表与 NPC 表里**逐字段完全相同**（`baseTurnSpeedDPS=360`、`turnAccelDPSS=9999999`）。装配由任务数据注入。（B）

---

## 1. 实测证据（命令 + 原始输出）

> 工具：`python tools/paramdex_fields.py <表名>`、`python tools/param_inspect.py <表名>`，
> 以及本报告自写的 `_scratch/p12_ai.py`（按 paramdex 偏移直读，位域另走 `pf.read_bitfield`）。
> 数据源：`<WORKSPACE>/ac6_merge/van/regulation-bin/*.param` + `<WORKSPACE>/tools/WitchyBND/Assets/Paramdex/AC6/`。

### 1.1 表结构与行宽（全部 SIZE MATCH）

```
$ python tools/paramdex_fields.py ChrActTurnParam_Npc
# ChrActTurnParam_Npc  <-  paramdex: ChrActTurnParam.xml
# 字段数 40, 计算结构大小 168 字节
# 实际: 2124 行 x 168 字节  -> SIZE MATCH
```

| 表 | 实测行数 × 行宽 | 与 paramdex 尺寸校验 |
|---|---:|---|
| NpcThinkParam | 1178 × 416 | MATCH |
| NpcAiActionParam | 126 × 20 | MATCH |
| BehaviorChangeStateMatrixParam | 227 × 32 | MATCH |
| RoleParam | 33 × 128 | MATCH |
| EnemyCommonParam | 1 × 264 | **DIFF −8（单行表，行宽不可信，只认字段名）** |
| NpcParam | 1232 × 1920 | MATCH |
| NpcEquipPartsParam | 137 × 612 | MATCH |
| NpcPartsParam | 110 × 60 | MATCH |
| NpcTransformParam | 12 × 36 | MATCH |
| MovementEnemyTypeParam | 216 × 688 | MATCH |
| MovementAcTypeParam | 19 × 964 | MATCH |
| MovementFlyEnemyParam | 10 × 112 | MATCH |
| MovementRideObjParam | 3 × 68 | MATCH |
| AttackActionParam_NPC | 1371 × 100 | MATCH |
| AttackActionParam_PC | 418 × 100 | MATCH |
| LookAtParam_Npc | 993 × 124 | MATCH |
| **ChrActTurnParam_Npc** | **2124 × 168** | MATCH |
| ChrActTurnParam（PC / 玩家，对照用） | 258 × 168 | MATCH |
| TentativePlayerParam（玩家自身，对照用） | 2 × 2112 | MATCH |
| DamageLevelConvThresholdParam | 57 × 208 | MATCH |
| DamageLevelConvParam | 132 × 256 | MATCH |
| PartsBreakLotteryParam | 8 × 20 | MATCH |
| PartsBreakParam | 1 × 104 | **DIFF −24（单行表）** |
| PadRumble（= CameraRumbleParam） | 174 × 84 | MATCH |

### 1.2 「同 ID 多表」——本报告最重要的一条实测

```
$ python -c "...打印 NpcParam.rid 与 NpcEquipPartsParam/NpcPartsParam/Movement.. 的 rid 交集..."
  34000000   in NpcEquipPartsParam=True  in NpcPartsParam=False
  30200200   in NpcEquipPartsParam=True  in NpcPartsParam=False
  30000000   in NpcEquipPartsParam=True  in NpcPartsParam=False
NpcEquipPartsParam rows=137 rowsize=612  rid范围=0..85300000
NpcPartsParam rid样例: [0, 9999, 31500000, 31500010, 36000010, 36000020, 40000010, ...] ...共 110
```

行名对照（`Developer Names/`，全量开发注释）：

```
MovementEnemyTypeParam:  0 default -- デフォルト | 9300 reverse joint -- 逆関節
NpcEquipPartsParam:      30000000 c3000 security MT (rifle) -- c3000 警備MT（ライフル）
ChrActTurnParam_Npc:     30000000 c3000 security MT (rifle) normal time -- c3000 警備MT（ライフル）　通常時
                         32500000 c3250 Regular Army AC (Normal) Normal time -- c3250 正規軍AC（ノーマル）　通常時
DamageLevelConvThresholdParam: 30000000 [10,40,121,221,...] | 32500000 [1550,1650,1750,1850,...]
NpcParam:                30000000 General purpose security MT real rifle -- 汎用　警備MT　実ライフル
```

→ 同一 ID `30000000` 在 5 张表里都是"警備MT（実ライフル）"。**这就是 AC6 的敌人装配线。**

### 1.3 感知四通道实测（`NpcThinkParam`，n=1178）

```
  eye_dist             nz=1100  top=[(450,264),(500,178),(250,112),(0,78),(600,55)]
  searchEye_dist       nz=7     top=[(0,1171),(250,6),(450,1)]
  searchEye2_dist      nz=0     top=[(0,1178)]
  battleEye_dist       nz=3     top=[(0,1175),(450,2),(1200,1)]
  ear_dist             nz=1085  top=[(0.1,1047),(0.0,93),(3000.0,25),(2500.0,7)]
  nose_dist            nz=227   top=[(0,951),(9999,85),(100,37),(3000,31)]
  radar_dist           nz=311   top=[(0,867),(9999,67),(10,45),(100,25),(300,21)]
  eye_angX             nz=1053  top=[(30,351),(40,284),(0,125),(120,110),(180,83)]
  eye_angY             nz=1125  top=[(50,278),(40,267),(180,199),(60,104),(30,62)]
  eye_BackOffsetDist   nz=1082  top=[(10,978),(0,96),(15,64)]
  eye_BeginDist        nz=1094  top=[(10,974),(0,84),(20,50)]
  isSearchEnableReycast nz=1174 top=[(1,1174),(0,4)]
```

### 1.4 攻击预警字段实测（决定性）

```
$ python "...直读 AttackActionParam_NPC / _PC 的 alertLevel / alertShowType / shootIndicationType..."
=== AttackActionParam_NPC (xml=AttackActionParam) rows=1371 rowsize=100
  alertShowType            nonzero=102  top=[(0,1269),(2,102)]
  alertLevel               nonzero=47   top=[(0,1324),(1,47)]
  shootIndicationType      nonzero=0    top=[(0,1371)]
  isTaeShootTimingOnly     nonzero=37   top=[(0,1334),(1,37)]
  lockRange                nonzero=1371 top=[(99999.0,1357),(300.0,6),(450.0,6)]
  shootIndicationDmypolyId nonzero=1371 top=[(-1,1371)]
=== AttackActionParam_PC (xml=AttackActionParam) rows=418 rowsize=100
  alertShowType            nonzero=0    top=[(0,418)]
  alertLevel               nonzero=34   top=[(0,384),(1,34)]
  shootIndicationType      nonzero=33   top=[(0,385),(1,33)]
  shootIndicationDmypolyId nonzero=418  top=[(-1,418)]
```

TDF 枚举原文（`Tdfs/`，cp932 解码）：

```
AtkActParam_AlertShowType.tdf   : "トリガー","0" | "出さない","2"
AtkActParam_ShootIndicationType.tdf: "なし","0" | "強射撃予兆","1"
AtkActParam_TriggerAlertLevel.tdf  : "小","0" | "大","1" | "レベル数","2"
BulletAlertShowType.tdf            : "出さない","0" | "追尾中","1" | "生存中","2"
```

### 1.5 受击反应阶梯（`DamageLevelConvThresholdParam`，57 行 / 48 种唯一步梯）

```
  x1  rid例=0        [150, 1600, 1600, 2000, 7500, 9000, 13000, -1, -1, -1, -1]   <- 自机
  x2  rid例=30000000 [10, 40, 121, 221, 999999999, 999999999, 999999999, -1, -1, -1, -1]
  x2  rid例=30500000 [40, 176, 310, 410, 999999999, 999999999, 999999999, -1, ...]
  x2  rid例=34000000 [1800, 2100, 2200, 2300, 999999999, 999999999, 999999999, -1, ...]
  x3  rid例=32500000 [1550, 1650, 1750, 1850, 999999999, 999999999, 999999999, -1, ...]
  x1  rid例=99900010 [300, 1500, 3000, 3500, 7500, 9000, 13000, -1, ...]
DamageLevelConvParam 唯一步梯数: 10
  x51 [1,2,3,4,5,5,5,5,5,5,5,5] | x51 [1,2,3,4,4,4,4,...] | x19 [1,2,3,3,3,...]
```

`999999999` = 永不突破；`-1` = 该级不存在。**敌人的"能被打出多少种受击反应"是逐类型（甚至逐个体）配置的设计资产。**

### 1.6 受击等级 → 震动链路复核（P7 结论）

```
$ python tools/paramdex_fields.py CameraRumbleParam
# CameraRumbleParam  <-  paramdex: CameraRumbleParam.xml
# 字段数 22, 计算结构大小 84 字节
$ PadRumble rows=174 rowsize=84
 rid=9280   Stage addition hit -- 段階加算被弾
 rid=9290   100% additional hit -- 100％加算被弾
 rid=9300   Small stagger -- 小よろけ
 rid=9310   Great stagger (stagger) -- 大よろけ（スタッガー）
 rid=9320   Start blowing away -- 吹っ飛び開始
```

### 1.7 部位表与破坏抽选

```
=== NpcPartsParam rows=110 rowsize=60 ===
  hitFEType       min=-1 max=2 nz=58  top=[(0,52),(1,37),(2,20),(-1,1)]
  addImpactRate   min=0.0 max=1.0 nz=75 top=[(1.0,65),(0.0,35),(0.25,6)]
  partsHp         top=[(999999,42),(9999999,19),(1000,15),(6000,6),(12000,5)]
  ownerDmgCorrect top=[(1.0,53),(0.1,28),(0.01,14),(0.0,6),(0.25,4),(3.0,3)]
=== PartsBreakLotteryParam 8 行全量 ===
 rid=10    v0=20 w0=100
 rid=11    v0=0 w0=20  v1=20 w1=80
 rid=12    v0=10 w0=20 v1=20 w1=80
 rid=9999  v0=0 w0=100 v1=10 w1=100 v2=20 w2=100
```

（P7 的 `hitFEType` 0×52 / 1×37 / 2×20 / −1×1 与 `addImpactRate=0` 35 行**完全复现**。）

### 1.8 「动画驱动开火」与 AI 通知

```
AttackActionParam_NPC.isTaeShootTimingOnly = 1  ->  37 / 1371 行
  （日文名：TAEからの射撃リクエストでのみ実際に射撃する = 只在动画事件请求时才真正击发）
BehaviorChangeStateMatrixParam 227 行：
  NoticeStateID 非零 22 行，唯一值 {1000, 1100, 1200, 1210, 1500}
  TransitionActionAiType 非零 30 行，取值 {10,11,12,20,21,23,30,31,32,33,40,41,50,51,60,61,62,63,70}
  行名样例： rid=91010200  2脚クイックブースト          notice=1100  aiType=12
            rid=990001000 敵ベース 共通 攻撃          notice=1500
            rid=90001013  自機ベース 共通 地上ガードブレイク aiType=33
```

### 1.9 `NpcAiActionParam` 是魂系遗留（126 行全量抽样）

```
rid=0     mv=0 k1=8  k2=0  hold=0000  R1 attack, R1 attack combo -- R1攻撃、R1攻撃コンボ
rid=18    mv=1 k1=0  k2=0  hold=1000  Move ↑ -- 移動　↑
rid=36    mv=1 k1=17 k2=0  hold=1000  Rolling ↑ -- ローリング　↑
rid=90    mv=0 k1=20 k2=0  hold=0000  ladder, up -- はしご、上り
rid=100   mv=0 k1=22 k2=0  hold=0000  Gesture ID00 -- ジェスチャID00
  key3  n=126 nonzero=0  top=[(0,126)]
```

### 1.10 `NpcParam` 关键字段实测（1232 行）

```
  hitHeight/chrHitHeight   min=0 max=120   敌 AC=15.0（与玩家同）| 50200000 重ガードメカ=70 | 61000000 ウミグモ=35
  hitRadius/chrHitRadius   min=0 max=110   敌 AC=3.0  | 50200000=75 | 61000000=55 | 34000000 四脚MT=14
  teamType                 top=[(5,1104),(3,54),(12,18),(9,16),(0,15),(7,13)]
  hitStopType              top=[(2,1171),(0,61)]
  receiveDmgHitStopType    top=[(1,1232)]           <- 全 1232 行 = 1（复核 P7）
  weakPartsDamageRate      top=[(1.0,1232)]         <- 全 1.0
  partsDamageRate1         top=[(1.0,1222),(0.1,9),(0.0,1)]
  partsDamageRate2         top=[(1.0,1207),(0.0,25)]
  partsBreakVariationId    top=[(0,1232)]           <- 全 0，本作未使用
  isVisibleEnemySearchStateFE top=[(1,1169),(0,63)]
  isVisibleApBar           top=[(1,1180),(0,52)]
  equipWeaponPresetId      唯一=135 非零=935       -> 指向 NpcEquipPartsParam 同 ID 行
  npcPartsParamIdBegin/End 非 -1 的 97 行，唯一区间 14 个 -> NpcPartsParam 的区间指针
  movementTypeParamId      非零 1112 行            -> MovementEnemyTypeParam 同 ID 行
  chrActTurnParamIdOffset  -> ChrActTurnParam_Npc
$ enableImpactGaugeFE  off=1419 整字节读 top=[(1,933),(0,299)]   <- 复核 P7 的 933/1232
```

**`NpcParam.atkActParamId_00..31`（32 个武器槽）指向哪张攻击表？**

```
全部 NpcParam.atkActParamId 非-1 条目数: 8766
  命中 AttackActionParam_PC : 199   (2.3%)
  命中 AttackActionParam_NPC: 8614  (98.3%)
  都不在                     : 145   (1.7%)
敌 AC 行（10000000 / 10700000 / 12000000 / 12500000 / 12700000）：32 槽全为 -1
```

### 1.11 敌我对称性：存在**两类**敌方 AC（这是本条最重要的发现）

```
rid        名称                                  preset       parts               move        turnOff     hitH/hitR
32000000   汎用 アバランチ エース                32000000     -1..-1              32000000    32000000    15/4
32500000   汎用 正規軍AC ノーマル                 32500000     -1..-1              32500000    32500000    18/4
33000000   汎用 ゴーストMT 近接オービット         33000000     -1..-1              33000000    33000000    14/5
30000000   汎用 警備MT 実ライフル                 30000000     -1..-1              30000000    30000000    10/3
34000000   汎用 四脚MT 三連バズ                   34000000     -1..-1              34000000    34000000    20/14
50200000   汎用 重ガードメカ                      50200000     50200010..50200080  50200000    50200000    70/75
------ 以下：命名佣兵 AC（剧情角色）------
10000000   10000000_決戦のエースA                  0            -1..-1              0           0           15/3
11100000   11100009_炉心の無人AC                   0            -1..-1              0           0           15/3
12500000   12500000_エア                          0            -1..-1              0           0           15/3
12700000   12700000_オンボーディングNPAC           0            -1..-1              0           0           15/3

ChrActTurnParam_Npc rid=0 = "AC - 通常時"；MovementEnemyTypeParam rid=0 = "default"；rid=9300 = "reverse joint"
玩家自身（TentativePlayerParam, rows=2 rowsize=2112）：
  rid=0  playerChrHitHeight=10.0  playerChrHitRadius=3.8  playerMapHitHeight=12.0 playerMapHitRadius=4.5 addImpactDisableTimeSec=1.5
  rid=1  playerChrHitHeight=10.0  playerChrHitRadius=3.8  playerMapHitHeight=12.0 playerMapHitRadius=4.5 addImpactDisableTimeSec=2.5
```

⚠️ **必须修正的读法**：命名佣兵 AC 的 `hitHeight=15 / hitRadius=3` **并不等于玩家自身的 `10.0 / 3.8`**。
- `汎用…AC`（32000000/32500000）走**完整 NPC 表族**（自己的装配预设、移动、转向、受击阶梯）。
- **命名佣兵 AC**（10000000–21400000）的 `preset/parts/move/turnOff` **全部为 0 或 −1**，即**不引用任何 NPC 专有表，落回"AC 默认行"**（`ChrActTurnParam_Npc rid=0 = AC - 通常時`、`MovementEnemyTypeParam rid=0 = default`）。它们的武器槽（`weaponId0..31`）同样全为 −1 → **装配由任务/剧情数据注入，不在 regulation 里**。（B/C）

### 1.12 「敌我转向参数逐位相同」——对称性的决定性证据

```
$ python "...对比 ChrActTurnParam(PC,258行) 与 ChrActTurnParam_Npc(2124行) 的 rid=0..."
字段                                        玩家 ChrActTurnParam[0]    NPC ChrActTurnParam_Npc[0]
baseTurnSpeedDPS                          360.0                    360.0
turnAccelDPSS                             9999999.0                9999999.0
lookTargetModeTurnSpeedDPS                999.0                    999.0
lookTargetModeTurnSpeedDPSAtLowDeltaAngle 360.0                    360.0
lookTargetMode_LookAheadSecond            0.0                      0.0
timeTurnRate_MaxTimeSec                   0.0                      0.0
reverseTurnBrakeDPSS                      -1.0                     -1.0

玩家 ChrActTurnParam baseTurnSpeedDPS 唯一=28  top=[(0.0,57),(1080,42),(360,21),(600,21),(60,15),(1200,12)]
NPC  ChrActTurnParam_Npc baseTurnSpeedDPS  top=[(90.0,1065),(0.0,403),(150,157),(180,83),(60,82),(120,71)]
```

→ **AC 基准 360 deg/s，量产 MT 众数 90 deg/s（1/4）**。这是"难度旋钮"最干净的一个证据。
→ `turnAccelDPSS = 9999999` 在 PC 与 NPC 两张表的 rid=0 都是"瞬时角加速度" → AC 的转向没有加速过程，**所以"绕圈"对 AC 无效，只能靠 QB 位移**（C，但与游戏体验一致）。

---

## 2. 敌人类型学

### 2.1 一条比类型学更重要的事实：敌人是"同 ID 表族"

开发者行名（`Developer Names/NpcThinkParam.txt`，全量 1177 行）本身就是一份**敌人分类学手稿**。它的编号段直接暴露了设计者的分类：

| ID 段 | 开发命名族 | 说明 |
|---|---|---|
| 30000000 / 30000100 / 30000200 | 警備MT 実ライフル / ENライフル / ミサイル | PCA 治安部队 |
| 30200000–30201830 | 旧共産圏MT（投ライ・カバー／ダブマシ／ロケマシ／ミサライ／キャノン／盾系） | RLF 杂兵，**同一底盘 × 11 种武器组合** |
| 30500000–30500400 | 正規軍MT ノーマル / 支援 / 近接 / 火炎放射 / 爆撃 | Balam 正规军 |
| 34000000–34000300 | 四脚MT 三連バズ / 九連バズ / スナイパー / グレネード | 四足重装 |
| 36000000–36001303 | 建機クモ 近接 / 支援 / 狙撃 / 装甲 | 工程蛛（多足） |
| 37000000–37001303 | デリーター 通常 / 格闘 / 狙撃 / エース | 重型 MT |
| 41500000–41500200 | 特攻MT ノーマル / PA / 大型ミサイル | 自爆型 |
| 42000000 | 次世代プロトAC | 精英 |
| 50000000–50200000 | ガードメカ(空中) / バグ / 重ガードメカ | 无人机 / 护盾机 |
| 51000000–51500000 | 大型輸送ヘリ / 軍事用USドローン / 戦闘ヘリ | 航空 |
| 52000000 / 52500000 / 53000000 | 戦闘車両 / サンフラワー / 自爆衛星 | 车辆 / 炮座 / 自杀卫星 |
| 60500000 / 61000000 / 62500000 / 64000000 | ファラオン / ウミグモ / サンドワーム / 資源発掘艦 | 大型生物・舰船 |
| 7xxxxxxx | 地上勢力砲台（グレネード/バズーカ/ガトリング/連装ミサイル/垂直/水平/スナイパー/レーザー） | 固定炮台，**每类都有 `イベント発射` 版本** |
| 10000000–21400000 | 決戦のエースA/B、ナンバー1〜7、ワイルド・ギースA–F、灰の民A–E、独立傭兵、刺客、ドランカー、エア | 人形 AC |

### 2.2 类型学表（战斗职能 / 行为特征 / 玩家应对 / 教学目的）

> 「行为特征」列的数值取自第 1 节实测（`eye`=视觉距离 m，`battle`=战斗开始距离 m，`radar`=雷达 m）。

| 类型 | 代表 ID | 战斗职能 | 行为特征（实测参数） | 玩家应对 | 教学目的 |
|---|---|---|---|---|---|
| **杂兵 MT（MT 类）** | 30000000 警備MT | 数量压制、消耗弹药 | eye 450 / battle 450 / radar 0 / 听觉 0.1；`TeamAttackEffectivity=30`，`thinkAttr_doAdmirer=1`（会"围"） | 单发重武器一发一只；不要被 6~10 只同时锁 | **教"弹药经济"与"目标优先级"** |
| **轻量快攻 MT** | 30200000 旧共産圏MT | 贴身骚扰 | `isUseBoostRiseMove=1`、`thinkAttr_doAdmirer=1`、`TeamAttackEffectivity=70`；`eye 450` | 用 QB 脱离包围、用高冲击武器打散 | **教"被围时的位移方向"** |
| **重型 / 四足** | 34000000 四脚MT | 区域封锁、正面硬抗 | eye 500；姿态阶梯 `[1800,2100,2200,2300]`（自机是 150/1600）；hitRadius 14 | **不能正面拼姿态**，需绕后 / 用高冲击 | **教"姿态值有类型差异，要换武器"** |
| **护盾 / 装甲型** | 30200300 ショット盾、30200600 ライ盾、50200000 重ガードメカ | 强迫换位 | `NpcPartsParam.isShieldGuardEnable / isPaGuardEnable / isPhysGuardEnable` 位域；重ガードメカ `hitH 70 / hitR 75`（巨型判定）、`battle 500`、`radar 65535`（无雷达） | 绕过盾面打背面；或用 EN/実弾 对相性 | **教"伤害类型 × 装甲"** |
| **飞行** | 51500000 戦闘ヘリ、51200010 USドローン | 立体压制 | 戦闘ヘリ eye 450 / radar **15**（几乎无雷达）| 用垂直导弹/对空 FCS | **教"锁定高度与 FCS 选择"** |
| **炮台 / 固定** | 72300000 / 72500000 / 72700000 / 72800000 / 73100000 | 领地化、逼你走位 | eye **1500~5000**、battle 600~3000、`thinkAttr_doAdmirer=0`、`TeamAttackEffectivity=0`；很多填了 `イベント発射`（脚本触发） | 别在开阔地停；用掩体分段接近 | **教"地图 = 敌人"** |
| **狙击** | 36000200 建機クモ狙撃、72700000 スナイパー(大)、73900000 アネモネ | 远距离惩罚站桩 | 狙撃版行名固定带 `戦闘距離・視界長め`；アネモネ eye 9999 / battle 9999 | 用高速冲刺走位，不要原地输出 | **教"移动也是防御"** |
| **无人机群** | 50100000 バグ、51200010 ドローン、53000000 自爆衛星 | 逼迫换弹/换目标 | バグ `eye 450`、`TeamAttackEffectivity=0`、`radar 0`；自爆衛星 `eye 500 / battle 350`（主动接近） | 用 AoE / 引信武器清群 | **教"范围清场武器存在"** |
| **精英 AC（敌方佣兵）** | 10000000 決戦のエースA、10700000 ナンバー2、12500000 エア | 检查装配与操作 | **radar 10**、`MemoryTargetForgetTime=9999`、`keepTargetRaycastDist=500`、`TeamAttackEffectivity=0`、`hitH 15 / hitR 3`（AC 类判定盒；玩家自身是 `TentativePlayerParam 10 / 3.8`，敌 AC 反而更大） | 与打玩家自己同构：抢姿态、读 QB | **教"最终考核：用你学的全部"** |
| **Boss 级大型** | 61000000 ウミグモ（eye 900 / radar 700 / nose 300）、50200000 重ガードメカ、42000000 次世代プロトAC | 分段考试 | 见第 6、7 节 | 见第 6、7 节 | 见第 7 节 |

**四段式（类型学整体）**
- **设计意图**：让玩家在 30 秒内通过"轮廓 + 移动方式 + 枪口"判断威胁等级，而不需要 UI 说明。
- **实现手段**：轮廓尺寸（`hitHeight 10→70`）、判定半径（`hitRadius 3→75`）、雷达/视距组合（`radar 0` vs `radar 700`）、`TeamAttackEffectivity`（0 / 30 / 70 三档决定"是否被围"）、`thinkAttr_doAdmirer`（472/1178 行为 1）。
- **玩家体验**：看到"胖"的就知道要绕后；看到细长带雷达的就知道会先发现你；看到 bat 群就知道要换 AoE。
- **可复用结论**：**类型差异应当写在"感知参数 + 判定体积 + 团队系数"三处，而不是写在血量上。** 血量差异玩家不可见，感知/体积差异一秒可见。

---

## 3. 敌方 AC 与玩家的对称性

### 3.1 数据证据

| 问题 | 实测答案 | 证据 |
|---|---|---|
| 敌 AC 用玩家部件系统吗？ | **分成两档**：`汎用…AC`（32xxx）用完整 NPC 专有表；**命名佣兵 AC**（10xxx–214xxx）全部回落到 AC 默认行 | ① `NpcParam` 里命名佣兵 AC 的 32 个 `weaponIdN` **全为 −1**、`equipWeaponPresetId=0`、`npcPartsParamId=-1`、`movementTypeParamId=0`、`chrActTurnParamIdOffset=0`；② `ChrActTurnParam_Npc rid=0 = "AC - 通常時"`、`MovementEnemyTypeParam rid=0 = "default"` |
| 敌方 AC 的判定盒 | 命名佣兵 AC 统一 `15.0 / 3.0`；`汎用…AC` 为 `15/4`、`18/4`、`14/5`；**玩家自身为 `10.0 / 3.8`**（`TentativePlayerParam.playerChrHitHeight/Radius`） | 1.11 实测。→ 敌 AC 的受击体积**比玩家更大**，是有意的"可被击中"补偿（C） |
| 敌 AC 的攻击表 | 敌 AC 的 `atkActParamId_00..31` **全为 −1**，不指向 `AttackActionParam_NPC`（普通敌人 98.3% 指向它） | 1.10 实测 |
| 姿态阶梯 | 命名佣兵 AC 类**未在 `DamageLevelConvThresholdParam` 里单独建行**（只有 `32500000 正規軍AC` 等有 `[1550,1650,1750,1850]`） | 1.5 实测 → 命名佣兵 AC 大概走自机/AC 默认阶梯 `[150,1600,1600,2000,7500,9000,13000]`（D，待验证） |

→ **C 级结论**：AC6 有两条"敌人 AC"路线：**量产 NPC AC 走数据表**（可批量调参），**剧情佣兵 AC 走装配注入 + 共享 AC 默认行**（更接近玩家，但也意味着它们的差异完全靠装配和脚本）。

### 3.2 对称性带来什么

**收益**
1. **读招可预测**：玩家看到敌 AC 抬左手，那是他熟悉的左臂武器预备动作。**同一个动画资产同时服务敌我**，学习成本被复用到两次。
2. **装配有意义**：因为敌 AC 的部件有和玩家一样的抗性/重量/姿态，玩家能建立"打哪个部位、用什么弹种"的心理模型。
3. **转向参数逐位相同 —— 这是"对称性"最硬的实测证据**：
   `ChrActTurnParam`（PC，258 行）rid=0 与 `ChrActTurnParam_Npc`（2124 行）rid=0 **逐字段完全一致**：
   `baseTurnSpeedDPS=360.0 / turnAccelDPSS=9999999.0（瞬时）/ lookTargetModeTurnSpeedDPS=999.0 / lookTargetModeTurnSpeedDPSAtLowDeltaAngle=360.0 / lookTargetMode_LookAheadSecond=0.0 / reverseTurnBrakeDPSS=-1.0`
   → 敌方 AC 的转向能力**就是玩家 AC 的转向能力**，不存在"AI 转身更快"的作弊。（B）
   对照：量产 MT 的 `baseTurnSpeedDPS` 众数是 **90 deg/s**（1065/2124 行）——**只有 AC 基准的 1/4**。
4. **AI 行为可迁移**：开发者行名里 `12600000 ACテスト先生`（AC 测试老师）与 `21400000 シミュレーター無人AC` 直接说明他们用同一套 AC 参数做训练/测试。

**代价**
1. **数值膨胀风险**：敌 AC 不能靠"提高 AI 精度"变强，只能靠**更好的装配**。而装配是离散的、可被玩家抄的 → 长线必然走向"给 Boss 加专属规则"。
2. **它不能被打成"杂兵"**：因为姿态阶梯 1550/1650/1750/1850 远高于自机，敌 AC 的姿态条几乎只能被高冲击武器推动 → 逼玩家换装，而不是"打得更准"。
3. **AI 无法作弊**：共用判定盒意味着 AI 不能有"更小的受击判定"或"无视硬直"。所以 AC6 的敌 AC 难度必须靠**行为节奏**（QB 频率、脱离距离、开火窗口）来表达——这正是第 8 节难度旋钮的来源。
4. **制作成本**：加一只新敌 AC = 一次装配 + 一套招式脚本，**不是加一张表**。所以数量受限（开发者行名里整套人形 AC 只有 30 个左右 ID 段）。

---

## 4. AI 行为结构

### 4.1 四层架构（C 级，由数据结构反推）

```
┌─ 第 1 层：脚本层 ── NpcThinkParam.logicId（唯一 220 个，众数 30200000×213）
│    决定"这只敌人的行为模板"。GoalActionID 指定状态图（100 是绝对众数，1124/1178）
├─ 第 2 层：目标评分层 ── EnemyCommonParam + NpcThinkParam.searchThreshold_*
│    索敵度（awareness）与交戦度（combat point）两套 meter 打分选目标
├─ 第 3 层：通知层 ── BehaviorChangeStateMatrixParam（227 行）
│    动画/物理事件 → 状态掩码 → TransitionActionAiType + NoticeStateID → 唤醒 AI
└─ 第 4 层：动作层 ── EzState 动画状态机 + NpcParam.atkActParamId → AttackActionParam
     NpcThinkParam.idAttackCannotMove 字段日文名就是「動けなくなったときに行うEzState番号」
```

### 4.2 感知（实测）

| 通道 | 字段 | 实测 | 判断 |
|---|---|---|---|
| 视觉 | `eye_dist` / `eye_angX`（高さ角）/ `eye_angY`（幅角）/ `eye_VerticalMax/Min` | `eye_dist` 众数 450；`eye_angX` 众数 30°/40°；`eye_angY` 众数 50°/40°；`eye_VerticalMax/Min` 1083/1085 行为 0（**语义待定：0 = 不限 or 0 m**，D 级） | **主通道**，1100/1178 行非零 |
| 遮蔽 | `isSearchEnableReycast` | **1174/1178 = 1** | 视觉可见性做了射线遮挡 → 掩体有效 |
| 听觉 | `ear_dist` | **1047 行 = 0.1 m** | **实际关闭** |
| 嗅觉 | `nose_dist` | 951 行 = 0；227 行非零（100/3000/9999） | 少数敌人专用（航空、沙虫） |
| 雷达 | `radar_dist` / `radar_power` | 867 行 = 0；非零者多为 10/100/300/9999 | 精英/大型专用 |
| 被弹 | `initialHitResponseType`、`searchTargetDamageForgetTime` | 4.0（528 行）/ 8.0（472 行） | 被打后立即转敌，且**记忆 4~8 秒** |

**四套视野中只有第一套在用**（`searchEye_dist` 非零 7 行、`searchEye2_dist` 全 0、`battleEye_dist` 非零 3 行）。这是"引擎提供四套、策划只用一套"的典型遗留。（B）

### 4.3 索敌度 / 交戦度（这是 AC6 AI 最像"系统策划"的部分）

`EnemyCommonParam`（单行表，只认字段名，实测值）：

| 字段 | 实测值 | 含义 |
|---|---:|---|
| `AwarePointMax` | 100.0 | 索敵度上限 |
| `searchThreshold_Lv0toLv1`（NpcThinkParam） | 30（1167/1178 行） | 未察觉 → 可疑 |
| `searchThreshold_Lv1toLv2` | 90（1142/1178 行） | 可疑 → 已发现 |
| `AwarePointDescreasePerSec` | 20.0 | 索敵度每秒衰减（100→0 约 5 s） |
| `SearchToDiscoveryStatePoint` / `SearchToNomalStatePoint` | **−1.0 / 0.0** | 全局钩子未启用，下放到逐敌人阈值 |
| `CombatPointDecreaseTime` | 3.0 s | 交戦度停止累积多久后开始衰减 |
| `CombatPointDecreasePoint` | 20.0 | 每次衰减量 |
| `CombatPointDecreasePerSec_Sense` | 20.0 | 视听/被弹来源的衰减速率 |
| `CombatPointDecreasePerSec_Radar` | 30.0 | 雷达来源衰减更快 |
| `ShareTargetTime` | 0.20 s | 目标共享的"确认"时间 |
| `ShareTargetRecognitionLagError` | 0.0 | 共享延迟误差 |
| `ExcessSubAwarePointIntervalTime` | 0.0 | 索敵度上限后衰减立即开始 |

→ **实现手段**：把"发现玩家"从二值变成**可累积、可衰减、可共享的连续量**，并且**按感知通道给不同的衰减率**（雷达给你的情报比目击更易过期）。这是让"潜入/被发现"有中间态的机制基础。

**设计意图 → 玩家体验**：玩家有"躲进掩体后敌人还在找我"的窗口（约 5 秒衰减 + `SightTargetForgetTime` 10 秒 / 15 秒），以及"我打了 A，B 立刻知道"的压迫感（`doUseSharedTarget=1` 有 1061/1178 行，`shareTargetType=3` 有 1080 行，`shareTargetRecognitionLag=1.0` 有 933 行 —— 即**共享有 1 秒延迟**，这 1 秒就是玩家的"打一枪换位"窗口）。

### 4.4 目标共享与角色分工

| 机制 | 字段（实测） | 值 |
|---|---|---|
| 是否接受共享 | `NpcThinkParam.doUseSharedTarget` | 1：1061 / 0：117 |
| 共享类型 | `shareTargetType` | 3：1080（绝大多数） |
| 共享延迟 | `shareTargetRecognitionLag` | 1.0 s（933 行） |
| 索敌度共享距离 | `shareSearchPointTargetDist` | 200 m（1018 行） |
| 交戦度共享距离 | `shareCombatPointTargetDist` | 100 m（1007 行） |
| 共享比例 | `shareSearchPointRate` / `shareCombatPointRate` | 均 1.0（1105 / 1104 行） |
| 索敌目标共享距离 | `shareSearchTargetDist` | 200 m（716 行） |
| 攻击目标共享距离 | `shareAttackTargetDist` | 100 m（739 行） |
| 死亡后共享维持 | `keepSharingTargetAfterDiedTime` | — |
| 团队攻击意愿 | `TeamAttackEffectivity` | 70：552 / 0：562 / 30：44 |
| **围角色判定** | `thinkAttr_doAdmirer` | **1：472 / 0：706** |
| **角色评估频率** | `EnemyCommonParam.assignRoleEvaluateInterval` | **2.5 s** |
| **攻击角色战斗距离上限** | `EnemyCommonParam.assignAttackRoleBattleRange` | **250 m** |

→ **"围"（取り巻き）是一条独立的 AI 角色**：`thinkAttr_doAdmirer` 有 472 行开启，`assignRoleEvaluateInterval=2.5s` 表示每 2.5 秒重新评估谁当"攻击者"、谁当"围观者"。开发者行名里还专门有 `取り巻き検証用`（围角色验证用）一批测试行（93500000–93500020）。（B）
**设计意图**：避免"所有敌人挤成一团同时开火"的死亡陷阱，让场面有节奏。**玩家体验**：总有一两个在边上绕，所以不能只盯一个方向。

### 4.5 站位、距离带与撤退

| 机制 | 字段（实测） | 典型值 |
|---|---|---|
| 战斗开始距离 | `BattleStartDist` | 450（288 行）/ 500（188 行）/ 9999（77 行，只挨打不主动） |
| 保持目标射线距离 | `keepTargetRaycastDist` | 500 m（731 行） |
| 掩体解除距离 | `coverActionReleaseDist` | −1（875）/ 200（216）/ 100（55） |
| 掩体攻击距离 | `coverActionAttackDist` | −1（875）/ 500（247） |
| 归巢（边打边回） | `backhomeDist` / `backhomeBattleDist` / `maxBackhomeDist` | 500 / 300 / 9999（718 行） |
| 壁接触后归巢时长 | `BackHomeLife_OnHitEneWal` | 5.0 s（1102 行） |
| 非战斗徘徊时长 | `nonBattleActLife` | 1（1171 行） |
| **求援** | `callHelp_CallValidRange` / `callHelp_CallValidMinDistTarget` | **仅 14 / 1178 行非零**（15 / 5） |

→ **求援系统在正式数据里几乎是空的**，`platoonReplyTime` / `callHelp_MinWaitTime` / `callHelp_MaxWaitTime` / `callHelp_ReplyBehaviorType` **全部 1178 行为 0**。也就是说：**追兵与增援是靠任务脚本（增援用行名：`脱獄…増援用`、`領域離脱援護…最終増援用`、`浮上する新B層…増援用`）生成的，不是靠 AI 自发呼救。**（B，结论强）

### 4.6 一个典型敌人的完整行为循环（以 30200000 旧共産圏MT 为例，C 级还原）

```
[非战斗] nonBattleActLife=1s 一段徘徊
   │  eye_dist 450m 内 && isSearchEnableReycast 视线未遮 && eye_angX/angY 锥内
   ▼
[索敵度累积] AwarePoint += ...；>=30 → Lv1（可疑）
   │  goalAction_ToSearchLv1=1 → 转身/搜索动作
   │  听到动静（ear 0.1m 基本无效）
   ▼
[索敵度 >=90] → Lv2（已发现）goalAction_ToSearchLv2=1 → 进入战斗
   │  BattleStartDist 450m → 走位到开火距离带
   ▼
[交戦] TeamAttackEffectivity=70，doUseSharedTarget=1 → 每 1s 收到共享目标
   │  assignRoleEvaluateInterval 2.5s 重新分角色（攻击者 / 取り巻き）
   │  开火判定 → AttackActionParam_NPC 行 → isTaeShootTimingOnly 决定"动画事件击发"还是"计时击发"
   ▼
[被弹] initialHitResponseType → 立即转仇；searchTargetDamageForgetTime=4~8s
   │  受击等级 → DamageLevelConvThresholdParam 阶梯 → DamageLevelConvParam 映射
   │  → CameraRumbleParam 9280/9290/9300/9310/9320 + EzState 反应动画 + BehaviorChangeStateMatrix notice
   ▼
[脱战] MemoryTargetForgetTime=15s（记忆目标保留 15 秒）
   │  SightTargetForgetTime=10s / searchTargetLv2ForgetTime=1.0s
   ▼
[归巢] backhomeDist 500m → 边打边回；maxBackhomeDist 9999m 内不放弃
```

### 4.7 「状态迁移矩阵」意味着什么架构

`BehaviorChangeStateMatrixParam` 的 227 行，每行是：

| 列 | 语义 | 实测 |
|---|---|---|
| `state00..state19` | **20 个运动状态的 0/1 掩码**（地上/ダッシュ/しゃがみ/カバー/落下/空中ダッシュ/QB/斜面滑り/乗車中/浮遊/カバー乗り出し/タンク地上/タンク落下/VOB/地上死亡/空中死亡/…） | 每列非零 25~78 行 |
| `TransitionActionAiType` | 通知给 AI 的**迁移动作类型** | 非零 30 行；值 {10,11,12,20,21,23,30,31,32,33,40,41,50,51,60,61,62,63,70} |
| `NoticeStateID` | **AI 通知 ID** | 非零 22 行；唯一值 {1000, 1100, 1200, 1210, 1500} |

行名（开发注释）直接暴露了语义：
```
rid=90011910 aiType=20 "アサルトブースト開始"     -- Assault boost start
rid=90020000 aiType=40 "ガード開始"              -- guard start
rid=90021000 aiType=50 "格闘初段開始"            -- 近战第一段
rid=90022000 aiType=60 "射撃構え始め"            -- 举枪开始（＝预警帧！）
rid=990001000 notice=1500 "敵ベース　共通　攻撃"  -- 敌人攻击事件
rid=91010200 notice=1100  "2脚　クイックブースト"-- QB 事件
rid=990010103 notice=1200 "2脚　地上　ジャンプ踏切"-- 起跳
rid=990010005 notice=1000 "2脚　地上　ターン"    -- 转身
rid=990010110 notice=1210 "2脚　地上　ジャンプエッジジャンプ"
```

**架构结论（C，但证据强）**：
- 这不是行为树，而是 **「动画事件 → AI 通知」的广播总线 + 上方一个脚本状态机**。
- `state00..19` 掩码的作用是**过滤误报**：同一条"射撃構え始め"事件在 `カバー` 和 `VOB` 状态下的含义不同，掩码决定"这个状态里这条通知有效吗"。
- `notice=1500` 只有 1 行（敌人攻击），说明 **AI 只被告知"我攻击了"，而不知道"我攻击得手没有"** → 后续判断依赖交戦度与被弹反应，这解释了为什么 AC6 的敌人有时会"对着空气继续压制"。
- `aiType=60/61/62/63`（射撃構え始め / 射撃下ろし始め / 足止め射撃 1 段目・2 段目構え始め）**就是"读招"的技术底座**：预备动作本身是 AI 通知的一种类型。

---

## 5. 读招设计（本维度最重要）

### 5.1 AC6 的"预警通道"清单（区分它到底挂了什么）

| 通道 | 载体 | 数据证据 | 覆盖范围 |
|---|---|---|---|
| ① 动作预备（anticipation pose） | 动画资产 + `TransitionActionAiType=60/61/62/63` | BehaviorChangeStateMatrix 行名「射撃構え始め」等 | **全体敌人，主通道** |
| ② 弹药可见飞行 | `Bullet.life` / `homingBeginDist` / `homingAngle` | `Bullet` 568 行 | 导弹/慢弹 |
| ③ UI 预警（射撃予兆） | `AttackActionParam.shootIndicationType` + `shootIndicationDmypolyId` | **PC 表 33 行 =1（強射撃予兆）；NPC 表 0 行** | **仅 PC 系（AC 类）攻击动作** |
| ④ 告警等级 | `AttackActionParam.alertLevel` / `alertShowType` | NPC：`alertLevel=1` 47 行、`alertShowType=2（出さない）`102 行；PC：`alertLevel=1` 34 行 | 稀缺，非通用 |
| ⑤ 音效 | `NpcThinkParam.soundBehaviorId01..08`（8 个槽） | 1178 行表内固定 8 槽 | 全体（按行为绑定） |
| ⑥ 特效/颜色 | 武器 SFX + `Bullet` SFX 字段 | `Bullet.bulletSfxDeleteType_byLifeDead` 等 | 全体 |
| ⑦ 被击反馈（反向"读招"） | `DamageLevelConv*` → `CameraRumbleParam 9280–9320` | 1.6 | 全体 |

**关键判断**：**AC6 的读招是"动作优先"的**。数据里 UI 预警通道（③④）非常稀缺（NPC 表 `shootIndicationType` 全 0），说明设计者选择了"你看敌人的身体，而不是看 UI 提示"。这与魂系一脉相承，也解释了为什么 AC6 的"预警"在高速战斗中依然可读：**它把预警做进了机体的可读部位（枪口方向、肩部导弹盖、推进器喷焰颜色）。**

### 5.2 「招式 → 预警 → 窗口 → 惩罚」表

> 表中"窗口"是**可反应窗口**（看到预警到判定发生的时间），"惩罚窗口"是**敌人招式后的硬直**。
> ⚠️ 具体帧数我**没有实测到**（本机只有参数表，没有动画资产时长），因此帧数量级标 **C/D**，只有参数列是 B。验证方法见第 11 节。

| 招式类别 | 预警信号（数据支撑） | 可反应窗口 | 惩罚窗口 | 玩家应对 | 证据 |
|---|---|---|---|---|---|
| **MT 步枪点射** | 举枪动作（`aiType=60 射撃構え始め`）；无 UI 预警（NPC 表 `shootIndicationType=0`） | 短（C：约 0.2~0.4 s） | 极短，靠"打腿/打枪"制造 | 横向 QB；或直接秒杀 | B（表）/ D（秒数） |
| **肩部/背部导弹齐射** | 弹仓盖开 + 导弹可见飞行（`Bullet.life` 长、`homingBeginTime`）；`lockRange=99999` 行多为导弹类 | 长（导弹飞行 0.5~1.5 s，C） | 中：齐射后有换弹 | 侧向冲刺 + 高位脱离；或用护盾 | B（表）/ D（秒数） |
| **近战突进/刀** | 推进器爆发 + `aiType=50 格闘初段開始` / `51 格闘コンボ開始` | 中（冲刺接近时间 = 玩家的窗口） | 大：近战挥空后硬直最长 | QB 侧闪后反打背部 | B |
| **足止め射撃（站定连射）** | `aiType=62 / 63` 行名「足止め射撃 1 段目/2 段目構え始め」 | 中 | **大**：站定期间敌人不位移 | 绕侧后方；这是主要输出窗口 | B |
| **格挡/盾** | `NpcPartsParam.isShieldGuardEnable / isPaGuardEnable / isPhysGuardEnable` 位域；`aiType=40/41 ガード開始/終了` | — | 绕盾 | 换 EN / 实弹相性，或绕背 | B |
| **伏击型（建機クモ屋內待ち伏せ）** | 行名「屋内待ち伏せ用 視界短め 音なし 動かず」——**预置在场景里、不发声、不动** | 无预警（这是故意的） | 首击后 | 侦查/听脚步/先手 AoE | B |
| **固定炮台** | 多为 `イベント発射`（脚本击发）；`alertShowType=2 出さない` | 地图层面：炮口朝向 + 射线 | 无法惩罚（不可破坏的要看目标） | 掩体推进 | B |
| **自杀卫星/特攻 MT** | `eye 500 / battle 350`，主动接近；`BulletAlertShowType: 追尾中/生存中` | 中 | 无 | 提前击杀 / 冲刺脱离爆风 | B |
| **Boss 阶段技** | 阶段演出 + 全身动作 + 场地变化 | 长（Boss 招式普遍给 0.5~1.5 s 预警，C） | 大 | 见第 7 节 | C |

### 5.3 `alertLevel` / `shootIndicationType` 的正确读法（含对 P7 的修正）

**实测事实**：
- `AttackActionParam_PC`（418 行）：`alertLevel=1` **34 行**、`shootIndicationType=1（強射撃予兆）` **33 行**、`alertShowType` **全 0**。
- `AttackActionParam_NPC`（1371 行）：`alertLevel=1` **47 行**、`shootIndicationType` **全 0**、`alertShowType=2（出さない）` **102 行**、`isTaeShootTimingOnly=1` **37 行**。

**解读（C 级，但方向明确）**：
1. **`shootIndicationType`（強射撃予兆）是一套挂在"PC 一系攻击动作"上的预告显示**。考虑到 AC6 里玩家与敌 AC 共用 PC 攻击动作路径（第 3 节），这套预告更可能是**"玩家能看到敌人 AC 的强射撃予兆"**的实现（敌 AC 走 PC 路径），而不是"玩家自己攻击时给自己显示预告"。**但这一点我无法从本机参数表直接证伪**，标 D。
2. **普通敌人的预警走的是"动作 + 音效 + 弹药"，不是这套 UI 通道**。所以不能把 `alertLevel` 说成"敌方攻击预警等级"（P7 的表述过于宽泛）；准确说法是：**它是攻击动作的告警分级字段，NPC 表里只有 47/1371 行用到，是一份"精选名单"而不是通用机制。**
3. **`shootIndicationDmypolyId` 在两张表里全为 −1**，意味着预告位置默认落在武器自身的枪口 dummy poly 上，而不是独立挂点。**推论**：预告特效是**武器模型级的**（换武器就换预告），这解释了为什么 AC6 里不同武器的"预告"视觉差异那么大。（C）

**这告诉我们什么**：一套"预警系统"如果能被数据描述成 `{显示类型, 挂点, 等级}` 三个字段，策划就能在不改代码的前提下给某几个招式开专属预警——**这正是"读招设计"应当被工程化的形态**。

### 5.4 玩家侧的"读"：DL 阶梯与震动

**实测链路**（第 1.5 / 1.6 节）：
```
冲击值累积 → DamageLevelConvThresholdParam（逐敌人阶梯）→ 突破阈值
   → DamageLevelConvParam（132 行 / 10 种映射）→ 映射到 damageLevel 2..5
   → dmgLv_M=DL2（被弾ストップ=顿帧）/ dmgLv_L=DL3（小よろけ）
     dmgLv_BlowM=DL4（大よろけ・スタッガー）/ dmgLv_Push=DL5（吹っ飛び）
   → CameraRumbleParam 9280 / 9290 / 9300 / 9310 / 9320（手柄震动变体）
   → EzState 反应动画 + BehaviorChangeStateMatrix 通知 AI
```

**为什么这条链路对"读招"重要**：它给了玩家一个**反馈闭环**——玩家不只"读敌人的招"，也在"读自己的输出是否有效"。`CameraRumbleParam` 的分级（段階加算 / 100%加算 / 小よろけ / 大よろけ / 吹っ飛び）让玩家在**不看血条和姿态条**的情况下，仅凭手柄就知道自己的冲击有没有推过阈值。这是 TA 最值得偷的一个设计：**把"数值进度"编码成"触觉事件"**。

---

## 6. Boss 设计模板

### 6.1 阶段划分

本机数据里**没有**一张"Boss 阶段表"（`AIAttackParam.param` 不存在于 regulation，只有 paramdex 定义）。所以：

**B 级事实**：`AIAttackParam`（47 字段：`minOptimalDistance` / `maxOptimalDistance` / `intervalForExec` / `selectionTendency` / `shortRange|middle|far|outRangeTendency` / `deriveAttackId1..16` / `goalLifeMin|Max` / `comboExecDistance` …）**在 paramdex 里有定义，但 `van/regulation-bin/` 里没有对应的 `.param` 文件**（257 张表中无 `AIAttackParam`）。

```
$ ls <WORKSPACE>/ac6_merge/van/regulation-bin/*.param | wc -l
257
$ ls .../regulation-bin/ | grep -iE "aiattack|attack"
AttackActionParam_NPC.param
AttackActionParam_PC.param
WwiseValueToStrParam_Switch_AttackPowerType.param
```

→ **C 级结论（重要）**：AC6 的"招式选择与冷却"**不在数据表里**，而在 `NpcThinkParam.logicId` 指向的 **AI 逻辑脚本**里（唯一 220 个 logicId，众数 `30200000×213`）。`AIAttackParam` 是引擎侧保留的旧方案（"行動パラ移行予定"= 计划迁移到行动参数，多个字段的日文备注都写着这句话），本作**未采用**。

**这对拆解的意义**：Boss 的"阶段"是**脚本 + 动画 + SpEffect** 的组合，而不是表驱动的。可验证的痕迹在：
- `NpcPartsParam.brakSpEffectId`（破坏时特殊效果 ID）：110 行中 22 行非 −1（如 `74001000`、`36004011`、`64007010`），**这就是"部位破坏→阶段切换"的钩子**（B）。
- `RoleParam.spEffectID0..9`（常駐特殊効果 0..9）：33 行，**魂系遗留**（该表还有 `phantomParamId`、`summonStartAnimId`、`itemlotParamId`、`voiceChatGroup`、`roleNameColor` —— 全部是艾尔登法环的字段，AC6 未使用）。

### 6.2 双血条（AP + 姿态）如何改变节奏

| 机制 | 数据 | 效果 |
|---|---|---|
| AP（HP） | `NpcParam` HP 字段 + `isVisibleApBar`（1180/1232 = 1 显示） | **不可回复** → 决定战斗总时长 |
| 姿态/体干 | `EnemyCommonParam.bodyTrunk_BodyGaugePoint=100`（本体体干）、`bodyTrunk_ActionGaugePoint=20`（动作体干）、`bodyTrunk_PointHealWaitTimeSec=5.0`（回复等待）、`bodyTrunk_PointHealPerSec=20`（每秒回复） | **可回复**：停手 5 秒后每秒回 20 → 100 点约 5 秒回满 |
| 无伤连击保护 | `addImpactDisableTimeSec=2.0`（冲击无敌时间）+ `endPermanentStunStateValue=1000`（"ハメ抜け"= 连段逃脱阈值） | 防止无限锁死 |
| 逐敌人阈值 | `DamageLevelConvThresholdParam`（57 行 / 48 种阶梯） | 不同敌人对冲击的反应完全不同 |
| 冲击的"寿命" | `GameSystemParam.Damage_ImpactLifeTimeSec = 1.5`（P2/P7 已实测） | 冲击值 1.5 秒不用就衰减 |

**节奏后果（这是回答"双血条如何改变节奏"的核心）**：
1. **单血条**：一次交火是"累计伤害 → 归零"。玩家只需要"打得久"。
2. **双血条**：一次交火变成**两个并行时钟**——AP 是单调递减的长时钟；姿态是"充能-释放"的短时钟，且**会回退**。
3. 于是玩家被迫做**节奏决策**：是"稳扎稳打慢慢磨 AP"（但姿态会回落到 0，永远打不出 stagger），还是"用高冲击武器在 1.5 秒冲击寿命内一口气推过阈值"（但高冲击武器通常弹量少、DPS 低）。
4. `bodyTrunk_PointHealWaitTimeSec=5.0` 这个数就是**设计者给玩家的"连击窗口"预算**：你必须让敌人的姿态条在 5 秒内持续受到冲击。
5. `addImpactDisableTimeSec=2.0` + `endPermanentStunStateValue=1000` 是**防无限连**的安全阀，保证"打得好"和"打成木桩"之间有一条线。

**可复用结论**：双血条的价值不在"两条"本身，而在于**一条单调、一条可回复**。只要有一个会回退的资源，战斗节奏就会从"消耗战"变成"窗口战"。

### 6.3 部位破坏（PartsBreak）

**两段式结构（B，实测）**：

**第一段：`NpcPartsParam`（110 行 × 60 B）—— 定义"部位是什么"**
| 字段 | 作用 | 实测 |
|---|---|---|
| `hitFEType` | 命中特效类型 | 0 通常 ×52 / 1 弱点 ×37 / 2 装甲 ×20 / −1 不显示 ×1 |
| `partsHp` | 部位独立 HP | 999999 ×42（≈不可破）/ 9999999 ×19（绝对不可破）/ 1000 ×15 |
| `partsDmgCorrect` / `partsBulletDmgCorrect` | 部位受伤倍率 | 1.0 ×98 / 0.01 ×8（免疫） |
| `ownerDmgCorrect` | **打到这个部位时"本体"吃多少伤害** | 1.0 ×53 / 0.1 ×28 / 0.01 ×14 / 0.0 ×6 / **3.0 ×3** |
| `addImpactRate` | **本体冲击值修正** | 1.0 ×65 / **0.0 ×35** / 0.25 ×6 |
| `brakSpEffectId` | 破坏时施加的 SpEffect | 非 −1 有 22 行（阶段切换钩子） |
| `hitSpEffectId` | 被弹时施加的 SpEffect | 非 −1 有 42 行 |
| `isDmgIgnore` / `isBreakDisableLockonDmypoly` / `isShieldGuardEnable` / `isPaGuardEnable` / `isPhysGuardEnable` | 位域 | 见 5.2 |
| `lockonDmypoly` / `hpGaugeDmypoly` | 锁定点 / **HP 条挂点** | 决定"打这个部位时 UI 显示哪条血" |

**第二段：`PartsBreakLotteryParam`（8 行 × 20 B）—— 定义"破坏后掉什么"**
`pair0_Value / pair0_Weight` … `pair4_Value / pair4_Weight`（5 组判定值 + 权重）。实测全量：

```
 rid=0     v0=-1 w0=0                                    （空）
 rid=10    v0=20 w0=100
 rid=11    v0=0  w0=20   v1=20 w1=80
 rid=12    v0=10 w0=20   v1=20 w1=80
 rid=20    v0=10 w0=100
 rid=30    v0=0  w0=100
 rid=40    v0=0  w0=100  v1=10 w1=100
 rid=9999  v0=0  w0=100  v1=10 w1=100  v2=20 w2=100
```

→ **设计意图**：部位破坏不是"掉一个固定零件"，而是**按权重抽一个"破损坏状态档位"**（0/10/20 三档），同一只 Boss 每次打断可能掉不同数量的部件。**这直接制造"重复挑战的差异感"**。
→ **可复用结论**：**随机性应当放在"表现层"（掉几个零件、从哪爆），不放在"判定层"（伤害、判定框）**。表里只抽 `Value ∈ {0,10,20}`，不抽难度。

### 6.4 场地机制与演出

- **场地 = 敌人**：固定炮台（7xxxxxxx 段，60+ 个 ID）在数据里就是敌人，`eye` 高达 1500~9999。`73900000 c7390 D層巨大砲台 アネモネ` 是其中一个把"场地"变成"Boss"的例子。
- **演出用敌人**：开发者行名里明确有一批「イベント制御用」「ボスエリア演出用」「中ボス演出用」「やられ役」（被秒杀役）的专用行 —— 例如 `30201523 組織との出会い 旧共産圏MT キャノン ボスエリア演出用`、`41501008/41501009 ストレート市街進行 特攻MT 中ボス演出用（吹き飛び用）`。**演出敌人是从普通敌人表里分支出来的，不是独立系统。**（B）
- **音乐/演出切换**：本机无相关表（音乐走 Wwise）。可验证痕迹：`NpcArenaGameEffectParam`、`ArenaParam.ranker_thinkParamID`（竞技场对手→thinkParam 的映射）。（D：音乐切换的触发点需实测）

---

## 7. 四个代表性 Boss 逐个拆解

> **命名纪律**：以下 4 个 Boss 的**战斗特征与数据**来自本机表；**官方编号**来自社区 Wiki（标 B，附 URL：<https://www.theloadout.com/armored-core-6/bosses>）。
> 数据侧我引用的是**开发者行名**（`Developer Names/`，全量注释），这是比社区命名更硬的证据。

### 7.1 第一场大型 Boss —— 「AH12：HC 直升机」（任务 1 关底）

| 项 | 内容 |
|---|---|
| 数据线索 | `51000000 汎用　大型輸送ヘリ` / `51500000 汎用　戦闘ヘリ 機関銃` / `51001004 初AC戦　置物　大型輸送ヘリ`（**"初AC战 置物"= 第一次 AC 战用的不会动的直升机**） |
| 实测参数 | 大型輸送ヘリ：`eye_dist=0`、`nose_dist=1000`（**靠"嗅觉"发现你！**）、`BattleStartDist=150`、`MemoryTargetForgetTime=15`、`radar=0`；戦闘ヘリ：`eye 450 / radar 15` |
| 教学职责 | ① **教"锁定与高度"**：直升机在空中，玩家第一次被迫处理垂直方向的锁定；② **教"移动中射击"**：因为 `BattleStartDist=150` 很近，玩家无法站桩；③ **教"目标不是人形"**：判定盒与 MT 不同 |
| 阶段 | 用 `51000000` vs `51010000 大型輸送ヘリ機銃` 两个 thinkParam 分离"载具本体"与"机炮"→ **本体与武器是两只敌人**（这是 AC6 的通用技巧，见 `74xxx 強襲揚陸艦 主砲/副砲/ミサイル砲` 与 `61000000 ウミグモ / 61010000 ウミグモ副砲`） |
| 玩家应对 | 用垂直导弹 / 高位冲刺绕到侧后方；不要在地面停 |
| 惩罚窗口 | 直升机悬停扫射的"定悬"期 |

### 7.2 第一道"装配墙" —— 「AAP07：BALTEUS」（观察点关底）

| 项 | 内容 |
|---|---|
| 战斗特征（社区 B） | 悬浮人形机 + 大量导弹齐射 + 火焰喷射 + 护盾（PA）。**是 AC6 最著名的"不换装配就打不过"的 Boss** |
| 数据线索 | `41500000 汎用　特攻MT　ノーマル` / `41500100 特攻MT　PA`（PA = Pulse Armor 护盾）—— 开发者专门给了"带 PA 的特攻 MT"一行。另有 `41500200 特攻MT　大型ミサイル` |
| 实测参数 | 特攻MT：`eye 450 / battle 450 / radar 0`、`isUseBoostRiseMove=1`（会上升） |
| 教学职责 | ① **教"护盾有血条"**：`NpcPartsParam.isPaGuardEnable` 位域与 `paTurnOnSfxId/paTurnOffSfxId`（NpcParam @1076/1092）说明 PA 是**有开关的、有音效的、有持续时间的**部件；玩家必须学会"等 PA 掉"；② **教"换装配"**：导弹齐射逼你换高机动腿 / 换对导弹的 FCS；③ **教"姿态即输出窗口"**：它是第一个姿态条长得能看清的 Boss |
| 双血条节奏 | 因为 PA 存在，实际是**三条时间轴**：PA（护盾）→ AP → 姿态。PA 期间伤害被吃掉 → 玩家必须"先破盾再进姿态循环"，节奏被切成"两段式" |
| 玩家应对 | 高冲击武器堆姿态 + 侧向 QB 躲导弹群；近距离时注意火焰 |

### 7.3 中期巨型 —— 「EC-0804：SMART CLEANER」/「IA-13：SEA SPIDER」类

| 项 | 内容 |
|---|---|
| 数据线索 | `50200000 汎用　重ガードメカ`（重护卫机，`hitH 70 / hitR 75`、`battle 500`、`radar 65535` 即无雷达、`parts=50200010..50200080` 共 7 个部位）；`61000000 汎用　ウミグモ`（海蛛，`eye 900 / radar 700 / nose 300`、`hitH 35 / hitR 55`） |
| 实测参数 | 重ガードメカ的 `npcPartsParamIdBegin/End = 50200010..50200080` → **一次性挂了 7 个可破坏部位**（B）；ウミグモ的行名带 `副砲` 分支（`61010000`）→ **本体 + 副炮多目标** |
| 教学职责 | ① **教"部位破坏"**：7 个部位意味着玩家必须"拆解"而不是"削血"；② **教"巨型敌人要绕"**：`hitRadius 75` 意味着正面判定面积极大，必须走侧后；③ **教"雷达无效"**：`radar 65535` = 关闭，只能靠视觉 |
| 部位破坏实测 | `NpcPartsParam` 里 `partsHp = 999999 / 9999999` 占 61/110 行——**大部分部位是"打不破的装饰件"**，真正可破的是少数。玩家需要学会从 `hitFEType`（1=弱点 / 2=装甲 / −1=不显示）的**视觉反馈**上分辨。 |
| 玩家应对 | 用高冲击推姿态 → 破坏窗口内集中打弱点部位；不要站在正面扇形 |

### 7.4 终盘人形 Boss —— 「IB-01：CEL 240」/ 敌 AC 类（含 12500000 エア）

| 项 | 内容 |
|---|---|
| 数据线索 | `12500000 12500000_エア`（行名：Ayre）、`10310000 ユーリヤ（オールマインド）決戦C`、`10000000 決戦のエースA`、`10700000 ナンバー2` |
| 实测参数 | `radar 10`、`eye 500 / battle 500`、`nose 9999`、`MemoryTargetForgetTime=9999`、`keepTargetRaycastDist=500`、`TeamAttackEffectivity=0`（不组队）、`isUseBoostRiseMove=1`、`hitH 15 / hitR 3`（与玩家共用"AC 类"转向/移动默认行 —— `ChrActTurnParam rid=0` 双方逐位相同；但受击盒比玩家的 `10 / 3.8` 更大） |
| 教学职责 | ① **总考核**：把前面所有单点教学合成一张考卷——读招（AC 的 QB 和抬枪）、装配（打它的姿态需要特定武器）、姿态管理（你自己的姿态条也是敌人）；② **教"对称性"**：它是"另一个你"，玩家的所有直觉都可迁移；③ **教"节奏极限"**：`MemoryTargetForgetTime=9999` 意味着**它永远不会忘记你**——没有脱战喘息 |
| 玩家应对 | 与打自己同构：抢姿态、破 QB、用近战在 stagger 窗口爆发 |

---

## 8. 难度旋钮排序

> 排序原则：**"越靠前，改动越便宜、玩家越察觉不到被改、越不破坏其他系统"**。这是本报告最实用的一张表。

| 序 | 旋钮 | 数据落点 | 实测值域 | 为什么比"调血量"高级 |
|---:|---|---|---|---|
| 1 | **受击反应阶梯** | `DamageLevelConvThresholdParam`（57 行 / 48 种）、`DamageLevelConvParam`（132 行 / 10 种） | 警備MT `[10,40,121,221,∞,∞,∞]` vs 四脚MT `[1800,2100,2200,2300,…]` vs 自机 `[150,1600,1600,2000,7500,9000,13000]` | 改变的是**"能不能被打出反应"**，不是"要打多久"。玩家感觉到的是"这只硬"，而不是"这只血厚" |
| 2 | **转向速度 / 角加速度** | `ChrActTurnParam_Npc`（2124 行 × 168 B）`baseTurnSpeedDPS` / `turnAccelDPSS` / `lookTargetMode_*`；对照 `ChrActTurnParam`（PC，258 行） | 玩家/AC 基准 **360 deg/s**（`ChrActTurnParam rid=0`）；量产 MT **90 deg/s**（1065 行）；150 ×157；180 ×83；60 ×82。`turnAccelDPSS=9999999` 有 1556 行（**瞬时转向**） | 直接决定"AI 跟不跟得上你的绕圈"。**AC：MT = 4 : 1** 就是这条旋钮的设计空间；0 成本、无副作用、玩家完全察觉不到被改 |
| 3 | **瞄准/预测** | `LookAtParam_Npc`（993 行 × 124 B）`maxRotSpeedDegPerSecX/Y`、`turnAccelDPSS_X/Y`、`predictionMaxTime`、`deflectType` | 上/下/左/右限界角、X/Y 轴最高旋回速度 | "AI 的准度"拆成了**转向速率 + 预测时间**两个连续旋钮，可以做成"打偏"而不是"不开枪" |
| 4 | **感知参数** | `NpcThinkParam.eye_dist / eye_angX / eye_angY / radar_dist / nose_dist` + `EnemyCommonParam.AwarePoint*` | eye 众数 450（264 行）；radar 多为 0；`AwarePointMax=100`、`DescreasePerSec=20` | 改变**"战斗什么时候开始"**。行名里有大量 `視界短め / 視界狭い / 視界0 / レーダー0` 的变体 → 这是开发者最常用的旋钮 |
| 5 | **索敌遗忘时间** | `searchTargetLv1ForgetTime`（1.0 s ×815）、`Lv2ForgetTime`（1.0 ×815）、`SightTargetForgetTime`（10 ×620 / 15 ×237）、`searchTargetDamageForgetTime`（4 ×528 / 8 ×472）、`MemoryTargetForgetTime`（15 ×792） |  | 改变**"能不能脱战"**。终盘 Boss 就是把它调到 9999 |
| 6 | **开火节奏 / 目标共享延迟** | `shareTargetRecognitionLag`（1.0 s ×933）、`TeamAttackEffectivity`（70/30/0）、`EnemyCommonParam.ShareTargetTime=0.20` |  | 改变**"被围的密度"**。1 秒的共享延迟 = 玩家的 1 秒换位窗口 |
| 7 | **距离带与站位** | `BattleStartDist`（450/500/9999）、`keepTargetRaycastDist`（500 ×731）、`coverActionAttackDist`（−1/500）、`backhomeDist`、`assignAttackRoleBattleRange=250` |  | 改变**"战场形状"**。9999 = 它不主动接近（很多炮台/狙击行如此） |
| 8 | **援军/角色** | `thinkAttr_doAdmirer`（1 ×472）、`assignRoleEvaluateInterval=2.5`、`callHelp_*`（仅 14 行非零） |  | 只能靠脚本。**引擎留了呼救系统但数据里是空的** |
| 9 | **招式组合与预警长度** | ⚠️ **不在 param 表里**（`AIAttackParam` 未随 regulation 发布）→ 在 `NpcThinkParam.logicId` 脚本 + 动画资产里 | logicId 唯一 220 个 | 最贵的旋钮，也是 Boss 差异化的唯一来源 |
| 10 | **血量** | `NpcParam` HP 字段 | — | **排在最后**：它同时影响战斗时长、姿态节奏、弹药经济三条线；且完全不可见（玩家看不到"这只血是 1.2 倍"），是最"懒"的旋钮 |

**关键洞察**：AC6 的开发者在数据里**留下了一份"难度调参词表"**——`Developer Names/NpcThinkParam.txt` 里出现频率最高的后缀是：
`ウロウロしない`（不徘徊）、`防衛用`（防御用）、`視界短め`（视距短）、`視界狭い`、`視界0`、`レーダー0`、`共有しない`（不共享）、`共有短め`、`タゲ共有遅延 Ns`、`戦闘距離最大`、`離れる距離 225/275/300`、`帰巣距離長め`、`すぐ忘れる`（很快忘记）、`音にも反応しない`、`目潰し`、`やられ役`（被秒杀役）。
→ **这就是一份现成的难度旋钮清单**，而且它证明：**同一个底盘可以通过 5~8 个后缀参数产生 10+ 种行为变体**（例如 30200000 段有 300+ 行，几乎全是"同一底盘 × 参数后缀"）。

---

## 9. 分析三问

### 问 1：如果敌人永远不会主动接近，会怎样？

**实测支撑**：`BattleStartDist=9999` 的行在 1178 行里只有 77 行（且集中在炮台/舰船/沙虫），`backhomeBattleDist` 众数是 300（516 行），`keepTargetRaycastDist` 众数 500（731 行）。**说明现版本绝大多数敌人是"会接近"的。**

**如果全部改成不接近**：
- 战斗会退化成**两列炮台对轰**。因为 AC6 的玩家武器里，中远距离 DPS 最高的是导弹/步枪，而敌人不会进近战距离 → 近战武器（刀）整套报废 → 装配系统的一半失效。
- **姿态机制失效**：`DamageLevelConvThresholdParam` 的阈值是为"能打到"设计的，敌人不接近意味着玩家要主动接近，节奏从"攻防"变成"追击"；`bodyTrunk_PointHealWaitTimeSec=5.0` 的窗口会因为你追不上而永远拿不到。
- **教学链断掉**：第 2 节的类型学里，"护盾型""无人机群""飞行"三类全靠"接近/被接近"的博弈。

**反过来说，为什么现版本保留了一小撮"不接近"的敌人（炮台/狙击）**：它们提供**地图层面的压力**，让玩家不能站桩，是"读招"在空间尺度上的延伸。

### 问 2：如果去掉所有预警信号，会怎样？

**实测支撑**：预警主要由三部分构成：① 动作预备（`aiType=60/61/62/63` 的"構え始め"通知）、② 弹药可见飞行（`Bullet.life` / `homingBeginTime`）、③ 稀缺的 UI 通道（NPC 表 `shootIndicationType` 全 0、`alertLevel=1` 仅 47/1371）。

**如果全部去掉**（动画直接命中、弹药瞬时到达、无音效）：
- **AC6 会从"动作游戏"变成"反应游戏"**。因为 `ChrActTurnParam_Npc.baseTurnSpeedDPS` 众数 90 deg/s、`turnAccelDPSS=9999999`（瞬时）的 AI 在无预警下等于"必定命中"。
- **玩家唯一解是"堆防御/堆血"** → 直接杀死装配系统的多样性（因为装配的意义在于"用机动换防御"）。
- **双血条会崩掉**：姿态条的价值建立在"玩家能预判并避开冲击"上；无预警时姿态条变成纯粹的"随机惩罚"。
- **`addImpactDisableTimeSec=2.0` 和 `endPermanentStunStateValue=1000` 这两个防连值会变得毫无意义**（因为玩家根本打不出连段，只会被连）。

**关键点**：所以预警不是"礼貌"，它是**让高速机动 AI 与人类反应时间（约 250 ms）兼容的唯一手段**。AC6 的选择是"把预警做进机体动画"，代价是**必须为每种武器做一套可读的预备姿态**（成本落在动画师和 TA 身上）。

### 问 3：如果敌人的 AI 完全随机（不做距离管理），会怎样？

**实测支撑**：距离管理在数据里非常密集：`keepTargetRaycastDist`（1016/1178 非零，众数 500）、`coverActionAttackDist`（−1/500）、`coverActionReleaseDist`、`BattleStartDist`、`assignAttackRoleBattleRange=250`、`MovementEnemyTypeParam` 的 `roundDashMaxSpeedKMPH` / `landingHorizontalBrake*`（让敌人"绕圈"而不是"撞脸"）。

**如果去掉**：
- **`thinkAttr_doAdmirer`（围角色，472 行开启）和 `assignRoleEvaluateInterval=2.5s` 立刻失去意义**——因为"围"的前提是"不同角色站不同距离"。
- **`TeamAttackEffectivity` 的三档（0/30/70）失效**——它本质上就是"多少人可以同时进入攻击距离"的控制。
- **玩家的核心操作（QB 绕后）失效**：随机站位的敌人不会给你"背后"。
- 结果：**战斗从"空间博弈"退化为"数值交换"**，AC6 引以为豪的"装配 = 战术选择"链条断裂。

**有没有更简单的替代方案？** 有：**行为树里的随机权重**（魂系的老做法）。AC6 没用它的原因是——**它训练过玩家"绕着敌人转"这一核心操作**（QB 是游戏最大的操作卖点）。如果敌人随机站位，QB 的战术价值就只剩"躲伤害"，而不是"抢位置"。**距离管理是 QB 这套操作的存在前提。**

---

## 10. TA 转化：数据驱动的敌人管线

### 10.1 管线全貌（从"同 ID 多表"反推）

```
任务脚本（决定放谁、放几只、在哪）
      │ 传 thinkParamId / npcParamId
      ▼
┌───────────────────────── 同 ID 表族 ─────────────────────────┐
│ NpcParam(1920B)       ── 基础：HP/判定盒/部位指针/武器槽      │
│ NpcThinkParam(416B)   ── 感知/索敌阈值/共享/归巢/logicId      │
│ NpcEquipPartsParam    ── 装配预设（武器模型/挂点/关节）        │
│ NpcPartsParam         ── 部位 HP/倍率/冲击修正/破坏 SpEffect  │
│ MovementEnemyTypeParam── 移动速度/加速度/刹车/硬直时间        │
│ ChrActTurnParam_Npc   ── 逐运动状态的转向速度/角加速度        │
│ LookAtParam_Npc       ── 瞄准轴限界/预测时间                  │
│ DamageLevelConvThresholdParam ── 受击反应阶梯                 │
└──────────────────────────────────────────────────────────────┘
      │ 运行时
      ▼
AI 逻辑脚本（logicId） ←── BehaviorChangeStateMatrixParam（动画事件 → AI 通知）
      │                            ▲
      │                            │ TAE（动画事件）
      ▼                            │
AttackActionParam_NPC ──► Bullet_Npc ──► AtkParam_Npc ──► SpEffect
      │
      └─► isTaeShootTimingOnly：是否只在动画事件时真正击发（37/1371）
```

**TA 关键认识**：**动画（TAE）是 AI 的输入源之一**。`BehaviorChangeStateMatrixParam` 的 227 行里，`notice=1000/1100/1200/1210/1500` 这些 AI 通知全都是**从动画事件广播出去的**。也就是说，TA 做的动画事件（"射撃構え始め"、"ジャンプ踏切"）直接决定了 AI 能不能工作。

### 10.2 策划如何在不改代码的情况下做新敌人（实测可行，因为 ID 空间统一）

**新敌人 = 8 张表 × 1 行同 ID + 1 段脚本**。工作流：

1. 复制一个相似的 `NpcParam` 行（例：抄 `30200000`）→ 改 ID（例 `30202000`）、HP、`hitHeight/hitRadius`。
2. 复制 `NpcThinkParam` 同 ID 行 → 调 `eye_dist / eye_angY / BattleStartDist / share* / backhome*`；把 `logicId` 指到一个已有脚本。
3. 复制 `NpcEquipPartsParam` 同 ID 行 → 换 `weaponId0..31` + `weaponDmyId*`（32 个挂点）。
4. 复制 `ChrActTurnParam_Npc` 的 **11 行一组**（通常时/冲刺/高速冲刺/ブースト/刹车/空中/QB/180 度…）→ 调 `baseTurnSpeedDPS`。
5. `MovementEnemyTypeParam` / `LookAtParam_Npc` / `DamageLevelConvThresholdParam` 各 1 行。
6. `NpcParam.atkActParamId_00..31` 指向 `AttackActionParam_NPC` 的 32 个槽。

**TA 能做的加速工具**：
- **ID 生成器 + 一致性检查器**：输入一个新 ID，自动在 8 张表里插入同 ID 的空行并回填外键（`npcPartsParamIdBegin/End`、`equipWeaponPresetId`、`movementTypeParamId`、`chrActTurnParamIdOffset`），检查是否有悬空引用。→ 本报告的第 1.2 节脚本就是雏形。
- **差异对比器**：`paramdiff_report.md` 已存在于本项目，可扩展为"选两只敌人 → 列出所有差异字段"，这等于**自动生成策划的调参说明**。
- **参数可视化曲线**：把 `DamageLevelConvThresholdParam` 的阶梯画成折线叠在一起（自机 / MT / 四脚 / AC），策划一眼看出"这只敌人的反应曲线是不是和别的重了"。

### 10.3 动画通知与判定的对齐（最容易出事的地方）

**本机的实测证据链**：
- `AttackActionParam.isTaeShootTimingOnly = 1`（NPC 表 37 行）→ **子弹在动画事件触发的那一刻生成，而不是"看到枪口就生成"**。
- `BehaviorChangeStateMatrixParam.state00..19` 的**状态掩码** → 同一条动画事件在不同运动状态下会被**过滤**，避免"在 QB 中播了射击姿态就发子弹"。
- `NpcPartsParam.hitSpEffectId / brakSpEffectId` → 判定命中后由 SpEffect 承担后续逻辑（而不是写死在代码里）。

**这意味着**：
- **动画事件的命名与状态掩码必须成对设计。** 一个 `shoot` 事件若没有对应的状态掩码，会在敌人处于 `VOB`/`浮遊`/`死亡` 状态时也误触发。
- **判定帧 ≠ 动画帧**：因为 `isTaeShootTimingOnly` 只控制"击发时刻"，判定框（`NpcParam.hitHeight/hitRadius`、`AtkParam` 的 hit box）是独立的。**这就是"看起来打到了但没伤害"这类 bug 的温床**，也是 TA 最应该做工具的地方。

**TA 工具建议**：
1. **TAE 事件 ↔ BehaviorChangeStateMatrix ↔ AI 通知 三方对照表生成器**：给出"这个动画事件在哪些状态下有效、会触发哪个 AI 通知"。
2. **判定框可视化**：把 `NpcParam.hitHeight/hitRadius`、`chrHitHeight/chrHitRadius`、`NpcPartsParam` 的部位范围叠加在模型上渲染（AC6 的参数里 `hitHeight` 实测 min=0.0 / max=120.0，跨度极大；且敌 AC 的 15/3 与玩家的 `TentativePlayerParam 10/3.8` **不一致**，靠眼睛绝对看不出来）。

### 10.4 AI 调试可视化工具（TA 的差异化价值）

| 工具 | 用到的数据 | 实现要点 |
|---|---|---|
| **感知范围可视化** | `NpcThinkParam.eye_dist / eye_angX / eye_angY / eye_VerticalMax/Min`、`radar_dist`、`nose_dist` | 画锥体（水平半角 `eye_angX`、垂直半角 `eye_angY`、上下限 `eye_VerticalMax/Min`）；**必须区分四套视野**（`eye_*` / `searchEye_*` / `searchEye2_*` / `battleEye_*`）并用不同颜色，否则策划会以为自己在调的东西在生效 |
| **索敌度 / 交戦度 meter** | `EnemyCommonParam.AwarePointMax=100`、`searchThreshold_Lv0toLv1=30`、`Lv1toLv2=90`、`AwarePointDescreasePerSec=20`、`CombatPointDecrease*` | 逐敌人画两条进度条 + 阈值刻度线；这两个数**决定 AI 什么时候转身**，是调 AI 时最需要看的东西 |
| **状态迁移矩阵可视化** | `BehaviorChangeStateMatrixParam` 227 行 × 20 位掩码 | 做成 227×20 的热力矩阵，行是事件、列是运动状态，格子是"有效/无效"。**这个图能一次性暴露"哪些动画事件在哪些状态下不会通知 AI"** |
| **AI 通知日志** | `NoticeStateID ∈ {1000,1100,1200,1210,1500}` + `TransitionActionAiType ∈ {10..70}` | 运行时打印带时间戳的通知流，叠在行为状态条上。因为通知只有 5 个 ID，极容易可视化 |
| **击发时刻校验** | `AttackActionParam.isTaeShootTimingOnly` | 在时间轴上同时标出「动画事件帧」与「子弹生成帧」，两者不一致时高亮——**直接抓"打空/早发"bug** |
| **受击反应阶梯编辑器** | `DamageLevelConvThresholdParam`（11 个阈值）+ `DamageLevelConvParam`（12 个等级） | 画成阶梯折线，横轴是冲击值、纵轴是 DL；叠加 `PadRumble 9280–9320` 的震动预览（**边调边震**） |
| **部位与判定盒视图** | `NpcPartsParam.partsHp/partsDmgCorrect/addImpactRate/hitFEType` + `NpcParam.hitHeight/hitRadius` | 3D 叠加；用 `hitFEType` 的值（−1/0/1/2）上色；`addImpactRate=0` 的部位（35 行）标红——**"打这里不涨姿态"是最容易被策划忘掉的坑** |
| **参数热重载** | 全部 `.param` | 因为 AC6 的参数是内存映射的松散表，理论上可以做"改表→立刻生效"；至少可以做"导出 → 重载 → 对比"。本项目的 `paramdiff.py` 已具备解析能力 |

**一句话总结 TA 的机会**：AC6 的 AI 是"数据驱动 + 脚本驱动"混合体，**脚本部分不可见，数据部分可见**。TA 能做的最有价值的事，就是把**不可见的部分（AI 通知流、索敌度、击发时刻）变成可见的**，把**可见但反直觉的部分（20 位状态掩码、四套视野、逐敌人 DL 阶梯）变成可比较的**。

---

## 11. 验证路径（每条结论该查哪张表）

| 结论 | 验证表 / 方法 | 本机已完成 |
|---|---|---|
| 敌人感知参数 | `NpcThinkParam`（1178×416）：`eye_*` / `ear_*` / `nose_*` / `radar_*` / `searchEye*` / `battleEye*` |
| 索敌度与交戦度 | `EnemyCommonParam`（单行，只认字段名）+ `NpcThinkParam.searchThreshold_Lv0toLv1/Lv1toLv2` |
| 目标共享 | `NpcThinkParam.doUseSharedTarget / shareTargetType / share*Dist / shareTargetRecognitionLag` + `EnemyCommonParam.ShareTargetTime` |
| 围角色 / 分工 | `NpcThinkParam.thinkAttr_doAdmirer`（1 ×472）+ `EnemyCommonParam.assignRoleEvaluateInterval=2.5 / assignAttackRoleBattleRange=250` | ✔ |
| 增援 / 求援 | `NpcThinkParam.callHelp_*`（全部 0）+ 任务脚本（行名含「増援用」） | ✔（结论：引擎留空，靠脚本） |
| **状态迁移矩阵的架构含义** | `BehaviorChangeStateMatrixParam`（227×32）：`state00..19` 掩码 + `TransitionActionAiType` + `NoticeStateID` | ✔ |
| 敌人行为模板 | `NpcThinkParam.logicId`（唯一 220）+ `GoalActionID`（众数 100）+ `Developer Names/NpcThinkParam.txt`（1177 行开发注释） | ✔ |
| 受击反应 / 姿态阶梯 | `DamageLevelConvThresholdParam`（57×208）+ `DamageLevelConvParam`（132×256） | ✔ |
| 姿态回复与防连 | `EnemyCommonParam.bodyTrunk_*` / `addImpactDisableTimeSec` / `endPermanentStunStateValue` | ✔ |
| **读招 · UI 通道** | `AttackActionParam_NPC`（`alertLevel` 47 / `alertShowType` 102 / `shootIndicationType` 0）+ `AttackActionParam_PC`（33 / 0 / 34）+ `Tdfs/AtkActParam_*.tdf` | ✔ |
| 读招 · 动画通道 | `BehaviorChangeStateMatrixParam` 行名「射撃構え始め」「格闘初段開始」「ガード開始」 | ✔ |
| 读招 · 击发时刻 | `AttackActionParam.isTaeShootTimingOnly`（37/1371） | ✔ |
| 部位破坏 | `NpcPartsParam`（110×60）+ `PartsBreakLotteryParam`（8×20，加权抽选）+ `PartsBreakParam`（单行）+ `NpcParam.npcPartsParamIdBegin/End` | ✔ |
| 护盾 / PA / 实盾 | `NpcPartsParam.isShieldGuardEnable / isPaGuardEnable / isPhysGuardEnable`（位域）+ `NpcParam.paTurnOnSfxId / paTurnOffSfxId` | ✔（位域需用 `read_bitfield`） |
| 敌我对称性 | `NpcParam`（敌 AC：`hitH 15/hitR 3`、`weaponIdN=−1`、`equipWeaponPresetId=0`、`movementTypeParamId=0`）+ `ChrActTurnParam_Npc rid=0 = "AC - 通常時"` | ✔ |
| 敌方攻击表归属 | `NpcParam.atkActParamId_00..31` 与 `AttackActionParam_PC/_NPC` 的 rid 求交（实测 98.3% 指向 NPC 表） | ✔ |
| 转向 / 瞄准（难度旋钮） | `ChrActTurnParam_Npc`（2124×168）+ **对照 `ChrActTurnParam`（PC，258×168）** + `LookAtParam_Npc`（993×124） | ✔ |
| 玩家自身判定盒 / 姿态基准 | `TentativePlayerParam`（2×2112）：`playerChrHitHeight/Radius`、`playerMapHit*`、`stabilityBaseVal`、`addImpactDisableTimeSec` | ✔ |
| 移动性能 | `MovementEnemyTypeParam`（216×688）/ `MovementFlyEnemyParam`（10×112）/ `MovementRideObjParam`（3×68）/ `MovementAcTypeParam`（19×964） | ✔（行宽） |
| 震动链路 | `PadRumble.param`（内部类型 `CAMERA_RUMBLE_PARAM_ST`，174×84）= `CameraRumbleParam` 9280/9290/9300/9310/9320 | ✔ |
| **尚未验证（D）** | ① Boss 阶段切换的具体触发（推测在 `NpcPartsParam.brakSpEffectId` + 脚本）；② 音乐切换点；③ 具体招式的帧数/秒数；④ `AIAttackParam` 未发布但引擎是否在别处读取 | 见下节 |

---

## 12. D 级（不确定）清单与验证方法

| # | 不确定项 | 为什么不确定 | 怎么验证 |
|---|---|---|---|
| 1 | `AttackActionParam_PC.shootIndicationType=1` 到底是"敌方 AC 的预告"还是"玩家自己的预告" | 只能看到字段在 PC 表上；无法从参数表判断运行时给谁显示 | 进游戏锁一只敌 AC，观察其强射击前是否出现预告图标/特效；或改表把 33 行清 0 看变化 |
| 2 | 各招式的**可反应窗口秒数** | 本机只有参数表，没有动画（TAE/HKX）资产时长 | 解包 `*.hkx` / `*.tae`（WitchyBND 可解），量出预备帧→判定帧；或 60fps 录像逐帧 |
| 3 | Boss "阶段"的触发条件 | regulation 里无阶段表 | 抓 `NpcPartsParam.brakSpEffectId` 非 −1 的 22 行（如 `74001000`）→ 追 SpEffectParam 的效果，看是否切换 thinkParam/装配 |
| 4 | 音乐/演出切换点 | 音乐走 Wwise，不在 param | 查 Wwise 事件表 / 听感实测 |
| 5 | 敌 AC 的装配来源 | `weaponIdN` 全 −1 说明不在 `NpcParam` 里，但也没找到"敌 AC 装配表" | 全 regulation 搜"包含 32 个武器槽且引用 EquipParamWeapon"的表；或查任务/Assembly 数据 |
| 6 | `AIAttackParam`（47 字段）是否在运行时被读取 | `.param` 文件不存在于 regulation | 检查内存/其他 BND；若确无，则"招式选择在脚本"的结论加强 |
| 7 | `NpcParam.partsBreakVariationId` 全 0 是"未使用"还是"默认档" | 只能看到值全 0 | 找到该字段的消费方（`partsBreakVariationId` 指向哪张表）；若指向的表不存在则为未使用 |
| 8 | `Ear_dist=0.1` 是否真的等价于"听不见" | 需要知道引擎有没有最小值判定 | 改一只敌人 `ear_dist` 到 3000 做 A/B；或用行名对照「音効かない」的变体行 |
| 9 | `NpcAiActionParam` 是否完全未使用 | 行名是魂系遗留，但没有反引用证据（paramdex 里无表引用它） | 查 exe/脚本对 `NpcAiActionParam` 的字符串引用 |
| 10 | `RoleParam`（33 行）在 AC6 是否被使用 | 字段全是艾尔登法环的（`phantomParamId`/`itemlotParamId`/`voiceChatGroup`） | 同上，查运行时引用 |
| 11 | 命名佣兵 AC 的姿态阶梯 | 它们在 `DamageLevelConvThresholdParam` 里没有独立行 | 抓一只敌 AC 用同一武器打，记录打出 DL2/DL3/DL4 的冲击值，与自机 `[150,1600,1600,2000,…]` 对比 |
| 12 | 玩家 `playerChrHitHeight=10 / Radius=3.8` 是否随装配变化 | 该表叫 "Tentative"（暂定），只有 2 行 | 换四条腿型再测受击体积（需内存读取或 mod）；或查 `ChrModelParam` / 腿部 `NpcPartsParam` 是否有对应倍率 |
| 13 | `eye_VerticalMax/Min` 的 0 是"不限"还是"0 米" | 1083/1085 行为 0，无法从值判断 | 找一只填了非零值的敌人（如 `eye_VerticalMax=300`）与填 0 的对比，测玩家飞到高空是否仍被发现 |

---

## 13. 一句话总结

**AC6 的敌人与 Boss 设计，本质上是一套"同 ID 多表 + 动画事件通知 + 双时钟资源（AP / 姿态）"的工程体系：**
- **敌人类型差异**写在感知参数、判定体积、团队系数上（一秒可见），不写在血量上（永远不可见）；
- **读招**写在动画预备与弹药飞行上（`aiType=60/61/62/63`、`isTaeShootTimingOnly`），UI 预警（`shootIndicationType`）只给极少数攻击；
- **Boss 差异化**被挤到脚本层（`logicId` 220 个 + `AIAttackParam` 未发布），代价是"数据驱动"的边界到这里为止；
- **教学职责**是通过 boss 的"第一次"来分配的：第一次高度（直升机）、第一次护盾与装配（BALTEUS）、第一次部位破坏与巨型（重护卫机/海蛛）、第一次"打你自己"（终盘 AC）。

对 TA 来说，这套体系里最值得做的工具是：**把不可见的 AI 状态（通知流、索敌度、击发时刻）可视化**，以及**把可见但反直觉的数据（20 位状态掩码、四套视野、逐敌人受击阶梯、`addImpactRate=0` 的部位）变成可比较的**。
