# -*- coding: utf-8 -*-
"""把 257 张 param 表按游戏系统归类，映射到 UE5 模块。这是 UE5 复刻文档的骨架。"""
import importlib.util, os, glob, io

spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)

names = sorted(os.path.basename(f)[:-6] for f in glob.glob(os.path.join(pi.ROOTS['van'], '*.param')))
size = {}
for n in names:
    p = pi.parse(os.path.join(pi.ROOTS['van'], n + '.param'))
    size[n] = (p['rowcount'], p['rowsize'] // 4)

# 规则：按前缀/关键词归类到游戏系统
RULES = [
 ('A. 相机与视角',      ['LockCam','DirectionCamera','SubWindowCam','GarageCamera','Zoomblur','CutsceneGparam','CutsceneMapId','CutsceneReplaceSfx','CutsceneTimezone']),
 ('B. 装配-部件',       ['EquipParamWeapon','EquipParamProtector','EquipParamBooster','EquipParamGenerator','EquipParamFcs','EquipParamAccessory','EquipParamGoods','EquipmentLineup','EquipmentMenu','EquipMtrlSet','AutoAssembleEvaluate','ReinforceParam','PartsToken','PartsBreak','PartsDraw','TankArmour','TankBase','TankWheel','ShieldParam']),
 ('C. 战斗-攻击与弹丸', ['AtkParam','AttackActionParam','Bullet','BulletShotgun','BulletCreateLimit','CylinderParam','ThrowParam','BladeHoming','CoolTime','CartridgeBehavior','ShootRebound','WepAbsorpPos','AtkNpcOperation','AtkOperation']),
 ('D. 战斗-伤害与防御', ['DamageLevelConv','DamageLevelConvThreshold','KnockBack','SpEffect','SpEffectVfx','CalcCorrectGraph','HitMtrl','HitEffectSfx','ChrHitMaterialCheck','SeMaterialConvert','ENAutoRecovery','MultiPlayCorrection','ENAutoRecoveryControl']),
 ('E. 动作与移动',      ['BehaviorParam','BehaviorChangeStateMatrix','ActionButton','MovementAcType','MovementEnemyType','MovementFlyEnemy','MovementRideObj','JumpSpecifyAlt','BoostParam','ThrustersParam','ThrustersLocomotion','ThrustersSfxId','Buoyancy','ChrActTurn','ChrProxyPhysics','RigidBody','Ragdoll','AnimMoveCorrection','ReTargetAnimSet','FootIK','FootIKSetup','HandIK','LookAt','Jiggler']),
 ('F. 角色与敌人',      ['NpcParam','NpcThink','NpcAiAction','NpcEquipParts','NpcParts','NpcMaterial','NpcTransform','NpcSystemMsg','NpcArenaGameEffect','RoleParam','EnemyCommon','CharaInit','ChrModel','PhantomParam','TentativePlayer']),
 ('G. 关卡与地图',      ['MapArea','MapParts','MapGimmick','MapDefaultInfo','GameArea','PlayRegion','MiniArea','PathFindCost','AssetEnvironmentGeometry','AssetMaterialSfx','AssetModelSfx','AssetTranscription','BonfireWarp','ObjAct','InteractiveSmoke','Skydome','GrassLod','GrassType','WetAspect','Depthline','WorldMapLegacyConv','LoadBalancer','LoadBalancerDrawDist','LoadBalancerNewDrawDist']),
 ('H. 任务与叙事',      ['MissionParam','MissionSystemMsg','TalkParam','MailParam','FeFreeDialog','FeTextEffect','TutorialParam','TutorialActJudge','KnowledgeLoadScreen','ArchiveParam']),
 ('I. UI 与菜单',       ['MenuBehavior','MenuColorTable','MenuErrorHandling','MenuFilter','MenuInputGesture','MenuOffscrRend','MenuParam','MenuPartsModelRend','MenuPropertyLayout','MenuPropertySpec','MenuValueTable','MessageBox','SubWindow','KeyAssign','DefaultKeyAssign','NamePlate','EmblemPiece','PresetEmblem','DecalParam','PlayerColoring','PlayerMaterialPreset','PlayerWeatheringTex','PlayerCamouflage','ActionButtonParam']),
 ('J. 音频',            ['SoundParam','SoundAutoReverb','SoundCutscene','SoundIDSpatial','SoundVoiceBankLoad','RuntimeSound','SeMaterialConvert','WwiseValueToStr','AiSoundParam','HitEffectSfx','FootSfx','ThrustersSfxId','PadRumble']),
 ('K. 系统与存档',      ['GameSystem','GamePresence','NetworkParam','NetworkMsg','WhiteSign','ShopLineup','ItemLot','ArenaParam','MercenaryRank','CompanyContribute','UnlockParam','BudgetParam','GraphicsParam','MaterialExParam','ArchiveParam','DecalParam']),
]
assigned = {}
for sysname, keys in RULES:
    for n in names:
        if n in assigned: continue
        if any(k.lower() in n.lower() for k in keys):
            assigned[n] = sysname
rest = [n for n in names if n not in assigned]

out = []
out.append('# AC6 param 表 → 游戏系统 → UE5 模块 映射（自动生成，2026-09-11）\n')
out.append('数据源：本机 UXM 解包后的 regulation.bin（van），257 张表，55911 行，20.1 MB。\n')
out.append('说明：行数/槽数为**实测**；列语义未知（本机 paramdef 为艾尔登法环系旧定义），故只按表名归类。\n')
for sysname, _ in RULES:
    rows = sorted([n for n, s in assigned.items() if s == sysname], key=lambda x: -size[x][0])
    if not rows: continue
    out.append('\n## %s\n' % sysname)
    out.append('| 表名 | 行数 | f32槽 |  说明 |')
    out.append('|---|---:|---:|---|')
    for n in rows:
        out.append('| `%s` | %d | %d |  |' % (n, size[n][0], size[n][1]))
if rest:
    out.append('\n## Z. 未归类（%d 张）\n' % len(rest))
    out.append('| 表名 | 行数 | f32槽 |')
    out.append('|---|---:|---:|')
    for n in sorted(rest, key=lambda x: -size[x][0]):
        out.append('| `%s` | %d | %d |' % (n, size[n][0], size[n][1]))

txt = '\n'.join(out)
path = r'./data/param_系统映射.md'
io.open(path, 'w', encoding='utf-8').write(txt)
print('已写出 %s（%d 字符）' % (path, len(txt)))
print()
cnt = {}
for n, s in assigned.items(): cnt[s] = cnt.get(s, 0) + 1
for sysname, _ in RULES:
    print('  %-22s %3d 张表' % (sysname, cnt.get(sysname, 0)))
print('  %-22s %3d 张表' % ('Z. 未归类', len(rest)))
