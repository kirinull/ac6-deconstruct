# 执行须知（本文件是被派发的独立任务）

- 你是一个**独立 session**，只负责下面这一个维度。你不需要写代码，只需要产出高质量的拆解报告。
- 请先读同目录的 _shared.md，严格遵守其中的身份设定、证据分级与硬性纪律。
- 报告写成一份完整的中文 Markdown，**建议 3500~6000 字**（宁深勿泛；表格不计入字数）。
- 必须包含：结论先行要点 → 分节展开（表格优先）→ 分析三问 → TA 转化要求 → 验证路径（去查哪张数据表）。
- **必须包含「实测证据」小节**：凡声称"实测/查表得知"的，把实际执行的命令与原始输出片段贴进去；没真跑过就删掉"实测"字样、改成推断或待验证。
- 用 write 工具把报告写入：<repo>/docs/03_维度拆解/P15_技术实现与数据管线_报告.md
- 完成后只回复 6 行以内摘要：实际字数、覆盖的主要小节、你标为 D 级（不确定）的结论条数、最值得用本地数据验证的 1 条。

---

下面是本维度的具体任务：

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
