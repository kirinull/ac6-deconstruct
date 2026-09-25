
# -*- coding: utf-8 -*-
"""严格口径审计：只接受精确名或明确的 _PC/_Pc/_NPC/_Npc 后缀映射。"""
import os, glob, importlib.util, io
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
spec2 = importlib.util.spec_from_file_location('pf', r'./tools/paramdex_fields.py')
pf = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(pf)

actual = {os.path.basename(f)[:-6] for f in glob.glob(os.path.join(pi.ROOTS['van'],'*.param'))}
# 显式别名表（paramdex 名 -> 实际表名），只在确定时给
ALIAS = {
 'AtkParam':'AtkParam_Pc', 'AtkParam_Npc':'AtkParam_Npc',
 'BehaviorParam':'BehaviorParam_PC', 'BehaviorParam_NPC':'BehaviorParam',
 'BulletParam':'Bullet', 'BulletParam_Npc':'Bullet_Npc',
 'BulletShotgunParam':'BulletShotgunParam_PC',
 'AttackActionParam':'AttackActionParam_PC', 'AttackActionParam_NPC':'AttackActionParam_NPC',
 'CharaInitParam':'CharaInitParam',
 'ThrustersParam_PC':'ThrustersParam_PC', 'ThrustersParam_NPC':'ThrustersParam_NPC',
 'ThrustersLocomotionParam_PC':'ThrustersLocomotionParam_PC',
 'SpEffect':'SpEffectParam', 'SpEffectVfx':'SpEffectVfxParam',
 'EquipParamWeapon':'EquipParamWeapon', 'EquipParamWeapon_NPC':'EquipParamWeapon_Npc',
 'EquipParamProtector':'EquipParamProtector', 'EquipParamBooster':'EquipParamBooster',
 'EquipParamGenerator':'EquipParamGenerator', 'EquipParamFcs':'EquipParamFcs',
 'EquipParamAccessory':'EquipParamAccessory', 'EquipParamGoods':'EquipParamGoods',
 'NpcParam':'NpcParam', 'NpcThinkParam':'NpcThinkParam',
 'LockCamParam':'LockCamParam', 'PadRumble':'PadRumble', 'BoostParam':'BoostParam',
 'JigglerBaseParam':'JigglerBaseParam', 'JigglerBehaviorParam':'JigglerBehaviorParam',
 'JigglerBehaviorSlideParam':'JigglerBehaviorSlideParam',
 'JigglerBehaviorTargetBoneRateParam':'JigglerBehaviorTargetBoneRateParam',
 'JigglerBehaviorWorldFixParam':'JigglerBehaviorWorldFixParam',
 'FootIKParam':'FootIKParam', 'FootIKSetupParam':'FootIKSetupParam',
 'AnimMoveCorrectionParam':'AnimMoveCorrectionParam',
 'ChrActTurnParam':'ChrActTurnParam', 'ChrActTurnParam_Npc':'ChrActTurnParam_Npc',
 'MovementAcTypeParam':'MovementAcTypeParam', 'TentativePlayerParam':'TentativePlayerParam',
 'ActionButtonParam':'ActionButtonParam', 'CoolTimeParam':'CoolTimeParam',
 'KnockBackParam':'KnockBackParam', 'DamageLevelConvParam':'DamageLevelConvParam',
 'CalcCorrectGraph':'CalcCorrectGraph', 'DecalParam':'DecalParam',
 'MaterialExParam':'MaterialExParam', 'GraphicsParam':'GraphicsParam',
 'LoadBalancerParam':'LoadBalancerParam', 'ChrModelParam':'ChrModelParam',
 'EnemyCommonParam':'EnemyCommonParam', 'PartsBreakParam':'PartsBreakParam',
 'TutorialActJudgeParam':'TutorialActJudgeParam', 'TutorialParam':'TutorialParam',
 'MissionParam':'MissionParam', 'TalkParam':'TalkParam', 'MailParam':'MailParam',
 'ArchiveParam':'ArchiveParam', 'ArenaParam':'ArenaParam', 'ShopLineupParam':'ShopLineupParam',
 'ItemLotParam':'ItemLotParam', 'GameSystemParam':'GameSystemParam', 'NetworkParam':'NetworkParam',
 'SoundParam':'SoundParam', 'MenuParam':'MenuParam', 'ChrProxyPhysicsParam':'ChrProxyPhysicsParam',
 'MapAreaParam':'MapAreaParam', 'MapPartsParam':'MapPartsParam', 'GameAreaParam':'GameAreaParam',
}
rows=[]
for x in sorted(glob.glob(os.path.join(pf.PD,'Defs','*.xml'))):
    name = os.path.basename(x)[:-4]
    tbl = ALIAS.get(name) or (name if name in actual else None)
    if tbl is None or tbl not in actual: continue
    fl, tot = pf.fields_of(x)
    p = pi.parse(os.path.join(pi.ROOTS['van'], tbl + '.param'))
    rows.append((name, tbl, tot, p['rowsize'], tot-p['rowsize'], p['rowcount']))

match = [r for r in rows if r[4]==0]; bad = [r for r in rows if r[4]!=0]
print('严格口径：可映射 paramdex 表 %d 个' % len(rows))
print('  SIZE MATCH  : %d' % len(match))
print('  SIZE DIFF   : %d' % len(bad))
print('  精确率      : %.1f%%' % (100*len(match)/len(rows)))
print()
print('=== 不一致清单（含行数，用于判断哪些不可信）===')
print('%-32s %-32s %7s %7s %6s %6s' % ('paramdex','实际表','parmdex','实际','差','行数'))
for n,t,tot,rs,d,rc in sorted(bad, key=lambda r:-abs(r[4])):
    print('%-32s %-32s %7d %7d %+6d %6d' % (n[:32], t[:32], tot, rs, d, rc))
print()
single = [r for r in bad if r[5] <= 1]
print('其中「单行表」%d 个（行宽由字符串表偏移推出，不可信）: %s' % (len(single), ', '.join(r[1] for r in single)))
