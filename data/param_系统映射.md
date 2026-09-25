# AC6 param 表 → 游戏系统 → UE5 模块 映射（自动生成，2026-09-11）

数据源：本机 UXM 解包后的 regulation.bin（van），257 张表，55911 行，20.1 MB。

说明：行数/槽数为**实测**；列语义未知（本机 paramdef 为艾尔登法环系旧定义），故只按表名归类。


## A. 相机与视角

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `LockCamParam` | 98 | 94 |  |
| `CutsceneMapIdParam` | 74 | 13 |  |
| `CutsceneReplaceSfxParam` | 38 | 1 |  |
| `CutsceneTimezoneConvertParam` | 7 | 3 |  |
| `GarageCameraAnimParam` | 7 | 49 |  |
| `Zoomblur` | 7 | 8 |  |
| `DirectionCameraParam` | 6 | 5 |  |
| `CutsceneGparamTimeParam` | 4 | 3 |  |
| `SubWindowCamParam` | 2 | 22 |  |
| `CutsceneGparamWeatherParam` | 1 | 10 |  |

## B. 装配-部件

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `EquipParamWeapon_Npc` | 813 | 276 |  |
| `ReinforceParamWeapon` | 464 | 33 |  |
| `EquipmentLineupParam` | 318 | 8 |  |
| `EquipParamWeapon` | 284 | 389 |  |
| `EquipParamGoods` | 218 | 35 |  |
| `PartsDrawParam` | 152 | 36 |  |
| `PartsDrawParam_ps4` | 152 | 36 |  |
| `PartsDrawParam_ps5` | 152 | 36 |  |
| `PartsDrawParam_scarlett` | 152 | 36 |  |
| `PartsDrawParam_xb1` | 152 | 36 |  |
| `EquipParamProtector` | 121 | 225 |  |
| `EquipmentMenuManageCategoryParam` | 110 | 8 |  |
| `PartsTokenParam` | 95 | 5 |  |
| `TankWheelModelParam` | 85 | 7 |  |
| `EquipParamAccessory` | 43 | 25 |  |
| `TankWheelParam` | 35 | 9 |  |
| `EquipMtrlSetParam` | 28 | 13 |  |
| `EquipParamGenerator` | 24 | 85 |  |
| `EquipParamBooster` | 23 | 96 |  |
| `AutoAssembleEvaluate` | 20 | 4 |  |
| `EquipParamFcs` | 19 | 52 |  |
| `ReinforceParamProtector` | 17 | 17 |  |
| `TankArmourParam` | 11 | 13 |  |
| `PartsBreakLotteryParam` | 8 | 5 |  |
| `TankBaseParam` | 8 | 16 |  |
| `ShieldParam_Npc` | 5 | 24 |  |
| `ShieldParam_Pc` | 2 | 24 |  |
| `PartsBreakParam` | 1 | 26 |  |

## C. 战斗-攻击与弹丸

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `Bullet_Npc` | 2539 | 222 |  |
| `AtkParam_Npc` | 1748 | 260 |  |
| `AttackActionParam_NPC` | 1371 | 25 |  |
| `AtkParam_Pc` | 712 | 260 |  |
| `Bullet` | 568 | 222 |  |
| `AttackActionParam_PC` | 418 | 25 |  |
| `BladeHomingAngSpeedParam` | 177 | 16 |  |
| `ThrowParam` | 131 | 33 |  |
| `CylinderParam` | 95 | 16 |  |
| `AtkOperationPartsParam` | 94 | 12 |  |
| `BulletShotgunParam_NPC` | 91 | 111 |  |
| `BulletShotgunParam_PC` | 81 | 111 |  |
| `CartridgeBehaviorParam` | 78 | 18 |  |
| `ShootReboundParam` | 51 | 49 |  |
| `AtkNpcOperationPartsParam` | 45 | 8 |  |
| `CoolTimeParam` | 40 | 8 |  |
| `BladeHomingAutoCancelEnableParam` | 38 | 15 |  |
| `WepAbsorpPosParam` | 13 | 33 |  |
| `BladeHomingParam` | 10 | 16 |  |
| `WhiteSignCoolTimeParam` | 10 | 4 |  |
| `WwiseValueToStrParam_Switch_BulletGenerateType` | 3 | 8 |  |
| `BulletCreateLimitParam` | 2 | 8 |  |

## D. 战斗-伤害与防御

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `SpEffectParam` | 4120 | 239 |  |
| `SpEffectVfxParam` | 791 | 49 |  |
| `CalcCorrectGraph` | 169 | 20 |  |
| `DamageLevelConvParam` | 132 | 64 |  |
| `SeMaterialConvertParam` | 83 | 8 |  |
| `HitEffectSfxParam` | 71 | 60 |  |
| `HitEffectSfxConceptParam` | 64 | 32 |  |
| `DamageLevelConvThresholdParam` | 57 | 52 |  |
| `HitMtrlParam` | 45 | 24 |  |
| `KnockBackParam` | 4 | 20 |  |
| `ChrHitMaterialCheckParam` | 2 | 64 |  |
| `ENAutoRecoveryControlParam` | 2 | 40 |  |
| `MultiPlayCorrectionParam` | 2 | 8 |  |

## E. 动作与移动

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `BehaviorParam` | 3069 | 52 |  |
| `ChrActTurnParam_Npc` | 2124 | 42 |  |
| `LookAtParam_Npc` | 993 | 31 |  |
| `BehaviorParam_PC` | 722 | 52 |  |
| `ThrustersParam_NPC` | 501 | 97 |  |
| `LookAtParam` | 469 | 31 |  |
| `JigglerBaseParam` | 351 | 41 |  |
| `ChrActTurnParam` | 258 | 42 |  |
| `BehaviorChangeStateMatrixParam` | 227 | 8 |  |
| `MovementEnemyTypeParam` | 216 | 172 |  |
| `ActionButtonParam` | 144 | 28 |  |
| `LookAtSpineParam` | 138 | 64 |  |
| `ThrustersParam_PC` | 103 | 175 |  |
| `FootIKSetupParam` | 86 | 33 |  |
| `ThrustersLocomotionParam_PC` | 74 | 68 |  |
| `FootIKParam` | 68 | 16 |  |
| `JigglerBehaviorParam` | 49 | 16 |  |
| `HandIKParam` | 47 | 16 |  |
| `JigglerBehaviorTargetBoneRateParam` | 42 | 16 |  |
| `JumpSpecifyAltParam` | 35 | 11 |  |
| `ReTargetAnimSetParam` | 35 | 16 |  |
| `JigglerBehaviorSlideParam` | 33 | 20 |  |
| `MenuBehaviorParam` | 31 | 8 |  |
| `RagdollParam` | 24 | 12 |  |
| `AnimMoveCorrectionParam` | 22 | 16 |  |
| `ThrustersSfxIdParam_PC` | 22 | 8 |  |
| `MovementAcTypeParam` | 19 | 241 |  |
| `RigidBodyParam` | 17 | 22 |  |
| `MovementFlyEnemyParam` | 10 | 28 |  |
| `ThrustersSfxIdParam_NPC` | 6 | 8 |  |
| `BuoyancyParam` | 4 | 10 |  |
| `JigglerBehaviorWorldFixParam` | 4 | 8 |  |
| `LookAtHeadParam` | 4 | 8 |  |
| `MovementRideObjParam` | 3 | 17 |  |
| `BoostParam` | 2 | 32 |  |
| `ChrProxyPhysicsParam` | 1 | 18 |  |

## F. 角色与敌人

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `NpcParam` | 1232 | 480 |  |
| `NpcThinkParam` | 1178 | 104 |  |
| `CharaInitParam` | 802 | 101 |  |
| `NpcMaterialParam` | 417 | 7 |  |
| `NpcEquipPartsParam` | 137 | 153 |  |
| `NpcAiActionParam` | 126 | 5 |  |
| `NpcPartsParam` | 110 | 15 |  |
| `PhantomParam` | 66 | 14 |  |
| `ChrModelParam` | 62 | 3 |  |
| `RoleParam` | 33 | 32 |  |
| `NpcTransformParam` | 12 | 9 |  |
| `NpcSystemMsgParam` | 3 | 8 |  |
| `TentativePlayerParam` | 2 | 528 |  |
| `EnemyCommonParam` | 1 | 66 |  |
| `NpcArenaGameEffectParam` | 1 | 16 |  |

## G. 关卡与地图

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `AssetEnvironmentGeometryParam` | 5116 | 86 |  |
| `AssetModelSfxParam` | 364 | 32 |  |
| `AssetTranscriptionParam` | 288 | 6 |  |
| `WorldMapLegacyConvParam` | 106 | 12 |  |
| `GameAreaParam` | 69 | 8 | **⚠️ 魂1 遗留数据（bonusSoul/humanityDropPoint），非 AC6 关卡表** |
| `ObjActParam` | 55 | 12 |  |
| `GrassTypeParam` | 51 | 66 |  |
| `LoadBalancerDrawDistScaleParam_ps4` | 48 | 32 |  |
| `SkydomeAssetParam` | 47 | 10 |  |
| `LoadBalancerDrawDistScaleParam_xb1` | 46 | 32 |  |
| `AssetMaterialSfxParam` | 44 | 32 |  |
| `LoadBalancerParam` | 33 | 20 |  |
| `MapAreaParam` | 25 | 10 |  |
| `LoadBalancerDrawDistScaleParam` | 22 | 32 |  |
| `LoadBalancerDrawDistScaleParam_ps5` | 22 | 32 |  |
| `LoadBalancerDrawDistScaleParam_xb1x` | 22 | 32 |  |
| `LoadBalancerDrawDistScaleParam_xss` | 22 | 32 |  |
| `LoadBalancerDrawDistScaleParam_xsx` | 22 | 32 |  |
| `WetAspectParam` | 20 | 8 |  |
| `BonfireWarpParam` | 15 | 8 |  |
| `GrassLodRangeParam` | 15 | 6 |  |
| `LoadBalancerNewDrawDistScaleParam_ps4` | 14 | 12 |  |
| `LoadBalancerNewDrawDistScaleParam_win64` | 14 | 12 |  |
| `MapGimmickParam` | 10 | 4 |  |
| `LoadBalancerNewDrawDistScaleParam_xb1` | 9 | 12 |  |
| `LoadBalancerNewDrawDistScaleParam_xb1x` | 9 | 12 |  |
| `PlayRegionParam` | 6 | 24 |  |
| `Depthline` | 4 | 16 |  |
| `PathFindCostParam` | 3 | 8 |  |
| `InteractiveSmokeParam` | 2 | 16 |  |
| `MiniAreaParam` | 2 | 4 |  |
| `LoadBalancerNewDrawDistScaleParam_ps5` | 1 | 14 |  |
| `LoadBalancerNewDrawDistScaleParam_xss` | 1 | 14 |  |
| `LoadBalancerNewDrawDistScaleParam_xsx` | 1 | 14 |  |
| `MapDefaultInfoParam` | 1 | 6 |  |
| `MapPartsParam` | 1 | 10 |  |

## H. 任务与叙事

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `TalkParam` | 6013 | 16 |  |
| `FeTextEffectParam` | 280 | 8 |  |
| `TutorialParam` | 201 | 12 |  |
| `MissionParam` | 111 | 88 |  |
| `ArchiveParam` | 57 | 32 |  |
| `MailParam` | 46 | 32 |  |
| `MissionSystemMsgAnswerParam` | 41 | 4 |  |
| `FeFreeDialogParam` | 31 | 16 |  |
| `TutorialActJudgeParam` | 31 | 2 |  |
| `MissionSystemMsgCommonParam` | 21 | 16 |  |
| `KnowledgeLoadScreenItemParam` | 5 | 7 |  |

## I. UI 与菜单

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `MenuPropertyLayoutParam` | 2512 | 8 |  |
| `EmblemPieceSpec` | 997 | 4 |  |
| `MenuColorTableParam` | 882 | 1 |  |
| `MenuPropertySpecParam` | 508 | 27 |  |
| `MenuValueTableParam` | 270 | 3 |  |
| `DecalParam` | 248 | 63 |  |
| `MenuInputGestureParam` | 175 | 4 |  |
| `PresetEmblemSpec` | 147 | 4 |  |
| `MessageBoxParam` | 141 | 6 |  |
| `MenuOffscrRendParam` | 140 | 20 |  |
| `NamePlateParam` | 122 | 4 |  |
| `DefaultKeyAssignParam` | 84 | 8 |  |
| `DefaultKeyAssignParam01` | 84 | 8 |  |
| `DefaultKeyAssignParam02` | 84 | 8 |  |
| `KeyAssignDisplayParam` | 58 | 8 |  |
| `PlayerMaterialPresetParam` | 46 | 16 |  |
| `PlayerCamouflagePattern` | 30 | 4 |  |
| `MenuErrorHandlingParam` | 28 | 8 |  |
| `MenuFilter` | 28 | 13 |  |
| `KeyAssignMenuItemParam` | 24 | 4 |  |
| `PlayerWeatheringTexPresetParam` | 24 | 9 |  |
| `UnlockParam_NamePlate_Solo` | 21 | 4 |  |
| `UnlockParam_NamePlate_Team` | 21 | 4 |  |
| `MenuPartsModelRendParam` | 14 | 1 |  |
| `PlayerColoringPresetParam` | 6 | 98 |  |
| `MenuParam` | 1 | 106 |  |
| `UnlockParam_EmblemPiece` | 1 | 6 |  |

## J. 音频

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `RuntimeSoundExpressionParam_Pc` | 677 | 12 |  |
| `RuntimeSoundExpressionParam_Npc` | 459 | 12 |  |
| `RuntimeSoundParam_Npc` | 260 | 16 |  |
| `PadRumble` | 174 | 21 |  |
| `RuntimeSoundParam_Pc` | 165 | 16 |  |
| `WwiseValueToStrParam_Switch_Material` | 115 | 8 |  |
| `SoundCutsceneParam` | 105 | 10 |  |
| `WwiseValueToStrParam_RuntimeReflectTextureType` | 100 | 8 |  |
| `SoundVoiceBankLoad` | 66 | 16 |  |
| `WwiseValueToStrParam_Switch_ShootSeCategory` | 38 | 8 |  |
| `WwiseValueToStrParam_Switch_DestroyedSeType` | 37 | 8 |  |
| `AiSoundParam` | 34 | 8 |  |
| `FootSfxParam` | 26 | 211 |  |
| `WwiseValueToStrParam_ReverbAuxBusType` | 17 | 8 |  |
| `WwiseValueToStrParam_Switch_WeaponMaterial` | 17 | 8 |  |
| `RuntimeSoundGlobalParam` | 15 | 8 |  |
| `WwiseValueToStrParam_Switch_Weapon_Type` | 14 | 8 |  |
| `WwiseValueToStrParam_Switch_BGMStatus` | 8 | 8 |  |
| `SoundAutoReverbEvaluationDistParam` | 6 | 5 |  |
| `SoundIDSpatialSetting` | 6 | 8 |  |
| `WwiseValueToStrParam_ReflectTextureType` | 6 | 8 |  |
| `WwiseValueToStrParam_Switch_WeaponAtkAttribute` | 6 | 8 |  |
| `SoundAutoReverbSelectParam` | 5 | 8 |  |
| `WwiseValueToStrParam_ReflectAuxBusType` | 4 | 8 |  |
| `WwiseValueToStrParam_Switch_AttackPowerType` | 3 | 8 |  |
| `WwiseValueToStrParam_Switch_GeneratorType` | 3 | 8 |  |
| `SoundParam` | 1 | 18 |  |

## K. 系统与存档

| 表名 | 行数 | f32槽 |  说明 |
|---|---:|---:|---|
| `ItemLotParam` | 291 | 39 |  |
| `ShopLineupParam` | 248 | 8 |  |
| `MaterialExParam` | 212 | 24 |  |
| `UnlockParam_Archive_Tips` | 114 | 4 |  |
| `NetworkMsgParam` | 55 | 36 |  |
| `UnlockParam_Archive_Logs` | 50 | 4 |  |
| `ArenaParam` | 42 | 24 |  |
| `UnlockParam_NpAcArena` | 41 | 4 |  |
| `UnlockParam_OsPoint` | 41 | 4 |  |
| `UnlockParam_DecalImage` | 36 | 4 |  |
| `UnlockParam_Trophy` | 29 | 4 |  |
| `CompanyContributePointParam` | 26 | 8 |  |
| `UnlockParam_Equipment` | 24 | 4 |  |
| `UnlockParam_MenuCommand` | 22 | 4 |  |
| `MercenaryRankTable` | 16 | 4 |  |
| `GamePresenceParam` | 12 | 8 |  |
| `UnlockParam_Archive` | 4 | 4 |  |
| `UnlockParam_Archive_Terms` | 2 | 4 |  |
| `BudgetParam` | 1 | 34 |  |
| `GameSystemParam` | 1 | 178 |  |
| `GraphicsParam` | 1 | 50 |  |
| `NetworkParam` | 1 | 98 |  |
| `UnlockParam_DLC` | 1 | 6 |  |

## Z. 未归类（9 张）

| 表名 | 行数 | f32槽 |
|---|---:|---:|
| `AccountParam` | 181 | 4 |
| `Magic` | 151 | 20 |
| `OsReinforcePoint` | 41 | 2 |
| `GeneratorTypeSfxIdRplace_PC` | 30 | 8 |
| `AttachObj_Npc` | 29 | 136 |
| `OsReinforce` | 20 | 43 |
| `AttachObj_Pc` | 4 | 136 |
| `SfxModelParam` | 4 | 8 |
| `GarageCutsceneParam` | 3 | 20 |

> **⚠️ 遗留表说明（2026-09-11）**：经 P8 维度发现并复核，以下表装的是**其它游戏的遗留数据**，不要当作 AC6 的有效内容：
> `GameAreaParam`（魂1：bonusSoul/humanityDropPoint + 魂1 Boss 行名）、`PlayRegionParam`（魂3 遗留）、`MiniAreaParam`（两行全为 −1，未启用）、`PathFindCostParam`（3 行，疑似测试数据）、`BonfireWarpParam`（篣火，魂系概念）。
> 判据：字段名含魂系专有概念 + 开发者行名出现其它游戏的地名/Boss 名。
