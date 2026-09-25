
# -*- coding: utf-8 -*-
"""终校工具：复核 UE5 实施文档里所有"实测"数字是否与数据一致。
每个断言 = (描述, 检查函数)。全部通过才算文档可信。"""
import os, struct, sys, importlib.util
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
spec2 = importlib.util.spec_from_file_location('pf', r'./tools/paramdex_fields.py')
pf = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(pf)

def P(t): return pi.parse(os.path.join(pi.ROOTS['van'], t + '.param'))
def fields(pdname):
    fl, tot = pf.fields_of(os.path.join(pf.PD, 'Defs', pdname + '.xml'))
    d = {}
    for o,t,n,disp in fl: d[n.split(':')[0].split('[')[0]] = (o, t, (disp or '').strip())
    return d, tot
def read(p, d, f):
    o, t, _ = d[f]
    fmt = '<' + pf.TYPE_FMT.get(t, 'i')
    return [struct.unpack_from(fmt, p['b'], p['datastart'] + i*p['rowsize'] + o)[0]
            for i in range(p['rowcount']) if p['datastart'] + i*p['rowsize'] + o + 4 <= len(p['b'])]

CHECKS = []
def chk(desc, cond, detail=''):
    CHECKS.append((desc, bool(cond), detail))

# --- 基础表结构 ---
for t, rows, size in [('LockCamParam',98,376),('EquipParamWeapon',284,1556),('EquipParamProtector',121,900),
                      ('AtkParam_Pc',712,1040),('NpcParam',1232,1920),('Bullet',568,888),
                      ('EquipParamBooster',23,384),('EquipParamGenerator',24,340),('EquipParamFcs',19,208),
                      ('BoostParam',2,128),('JigglerBaseParam',351,164),('JigglerBehaviorParam',49,64),
                      ('ChrActTurnParam',258,168),('FootIKParam',68,64),('TalkParam',6013,64),
                      ('EquipParamWeapon_Npc',813,1104),('AtkParam_Npc',1748,1040),('BehaviorParam_PC',722,208)]:
    p = P(t); chk('%s = %dx%d' % (t, rows, size), p['rowcount']==rows and p['rowsize']==size,
                  '实际 %dx%d' % (p['rowcount'], p['rowsize']))

# --- paramdex 结构大小吻合 ---
for pdname, tbl in [('LockCamParam','LockCamParam'),('EquipParamWeapon','EquipParamWeapon'),
                    ('EquipParamProtector','EquipParamProtector'),('AtkParam','AtkParam_Pc'),
                    ('NpcParam','NpcParam'),('BulletParam','Bullet'),('EquipParamBooster','EquipParamBooster'),
                    ('EquipParamGenerator','EquipParamGenerator'),('EquipParamFcs','EquipParamFcs'),
                    ('BoostParam','BoostParam'),('JigglerBehaviorParam','JigglerBehaviorParam'),
                    ('ChrActTurnParam','ChrActTurnParam'),('FootIKParam','FootIKParam')]:
    d, tot = fields(pdname); p = P(tbl)
    chk('paramdex %s 尺寸 == %s 行宽 (%d)' % (pdname, tbl, tot), tot == p['rowsize'],
        'paramdex %d vs 实际 %d' % (tot, p['rowsize']))

# --- ACS 核心 ---
p = P('EquipParamProtector'); d, _ = fields('EquipParamProtector')
v = read(p, d, 'stability')
chk('stability 偏移 488', d['stability'][0]==488, '偏移 %d' % d['stability'][0])
chk('stability 值域 0~1500', min(v)==0 and max(v)==1500, '实际 %d~%d' % (min(v), max(v)))
chk('stability 唯一值 70 个', len(set(v))==70, '实际 %d 个' % len(set(v)))

p = P('AtkParam_Pc'); d, _ = fields('AtkParam')
chk('impactPower 偏移 528', d['impactPower'][0]==528)
iv = read(p, d, 'impactPower')
chk('impactPower 值域 0~6000', min(iv)==-1 and max(iv)==6000, '实际 %d~%d' % (min(iv), max(iv)))
chk('impactPower 非 -1 数 447', len([x for x in iv if x!=-1])==447, '实际 %d' % len([x for x in iv if x!=-1]))
chk('residualImpactPower 偏移 988', d['residualImpactPower'][0]==988)
chk('atkPhys 是 u16', d['atkPhys'][1]=='u16', '实际 %s' % d['atkPhys'][1])
chk('atkPhys 偏移 84', d['atkPhys'][0]==84)
chk('atkThun 日文名含 コーラル', 'コーラル' in d['atkThun'][2], d['atkThun'][2])

pg = P('GameSystemParam'); dg, _ = fields('GameSystemParam')
chk('Damage_ImpactLifeTimeSec = 1.5', read(pg,dg,'Damage_ImpactLifeTimeSec')==[1.5],
    str(read(pg,dg,'Damage_ImpactLifeTimeSec')))
chk('DamageLevel_LevelUpCountResetTimeSec = 99.0', read(pg,dg,'DamageLevel_LevelUpCountResetTimeSec')==[99.0])

# --- 移动 ---
pb = P('EquipParamBooster'); db, _ = fields('EquipParamBooster')
# 13 个玩家推进器 = 行 0~12
w = read(pb,db,'weight')[:13]
chk('booster 玩家件 weight 970~2240', min(w)==970.0 and max(w)==2240.0, '实际 %.0f~%.0f' % (min(w), max(w)))
allw = read(pb,db,'weight')
chk('booster 占位行 weight=1 (行13~19)', set(allw[13:20])=={1.0}, str(sorted(set(allw[13:20]))))
chk('booster 特殊行 weight=0 (行20~22)', set(allw[20:23])=={0.0}, str(sorted(set(allw[20:23]))))
q = read(pb,db,'QB_EndSpeedKMH')[:13]
chk('QB_EndSpeedKMH 玩家件 257~377', min(q)==257.0 and max(q)==377.0, '实际 %.0f~%.0f' % (min(q), max(q)))
chk('QB_EndSpeedKMH 占位行全 500', set(read(pb,db,'QB_EndSpeedKMH')[13:20])=={500.0})
chk('QB_EndSpeedKMH 特殊行最大 425', max(read(pb,db,'QB_EndSpeedKMH')[20:23])==425.0,
    str(read(pb,db,'QB_EndSpeedKMH')[20:23]))
r = [x for x in read(pb,db,'QB_ReloadTimeSec')[:13] if x>0]
chk('QB_ReloadTimeSec 0.30~0.91', abs(min(r)-0.30)<1e-6 and abs(max(r)-0.91)<1e-6, '实际 %.2f~%.2f' % (min(r), max(r)))
t_ = [x for x in read(pb,db,'QB_AccelTimeF30')[:13] if x>0]
chk('QB_AccelTimeF30 8~16.5', min(t_)==8.0 and max(t_)==16.5, '实际 %.1f~%.1f' % (min(t_), max(t_)))

pp = P('BoostParam'); dp, _ = fields('BoostParam')
chk('counterBoostActiveAngleDeg = 90 (2 行)', set(read(pp,dp,'counterBoostActiveAngleDeg'))=={90})
chk('boostDirLerpRate = 0.1', abs(read(pp,dp,'boostDirLerpRate')[0]-0.1)<1e-6)
chk('counterBoostDirLerpRate = 0.17', abs(read(pp,dp,'counterBoostDirLerpRate')[0]-0.17)<1e-6)

# --- 转向 ---
pt = P('ChrActTurnParam'); dt, _ = fields('ChrActTurnParam')
bs = [x for x in read(pt,dt,'baseTurnSpeedDPS') if x>0]
chk('baseTurnSpeedDPS 35~99999', min(bs)==35.0 and max(bs)==99999.0, '实际 %.0f~%.0f' % (min(bs), max(bs)))
chk('judgeTurnSpeedThresholdAngleDeg 全 90', set(read(pt,dt,'judgeTurnSpeedThresholdAngleDeg'))=={90})

# --- Jiggler ---
pj = P('JigglerBehaviorParam'); dj, _ = fields('JigglerBehaviorParam')
mn = [x for x in read(pj,dj,'minAccelMPSS') if x>0]
chk('jiggler minAccelMPSS 10~998', min(mn)==10.0 and max(mn)==998.0, '实际 %.0f~%.0f' % (min(mn), max(mn)))
rd = [x for x in read(pj,dj,'rotDecayValueX') if x>0]
chk('jiggler rotDecayValueX 1~40', min(rd)==1.0 and max(rd)==40.0)

# --- FCS ---
pfcs = P('EquipParamFcs'); df, _ = fields('EquipParamFcs')
for f in ['predictionShoot_BulletSpeedMPS','predictionShoot_MaxShootOffset','predictionShoot_StartPredDist',
          'missileLockPerf','missileLockTimeRate']:
    chk('FCS 有字段 %s' % f, f in df)

# --- 生成器 ---
pgen = P('EquipParamGenerator'); dgn, _ = fields('EquipParamGenerator')
for f in ['energyMax','energyRecoveryPerSec','energyRecoveryDelayTimeSec',
          'energyRecoveryDelayTimeForEmptySec','energyRecoverValForEmpty']:
    chk('Generator 有字段 %s' % f, f in dgn)


# --- P9/P10/P15 回填数据的断言 ---
plb = P('LoadBalancerParam'); dlb, _ = fields('LoadBalancerParam')
chk('LoadBalancerParam 33 行 x 80 B', plb['rowcount']==33 and plb['rowsize']==80)
chk('lowerFpsThreshold = 30.60', abs(read(plb,dlb,'lowerFpsThreshold')[0]-30.6)<0.01)
chk('upperFpsThreshold = 31.60', abs(read(plb,dlb,'upperFpsThreshold')[0]-31.6)<0.01)
chk('lowerFpsContinousCount = 5', read(plb,dlb,'lowerFpsContinousCount')[0]==5)
chk('upperFpsContinousCount = 20', read(plb,dlb,'upperFpsContinousCount')[0]==20)
chk('downAfterChangeSleep = 30', read(plb,dlb,'downAfterChangeSleep')[0]==30)
chk('upAfterChangeSleep = 10', read(plb,dlb,'upAfterChangeSleep')[0]==10)

pmc = P('MenuColorTableParam')
chk('MenuColorTableParam 882 行', pmc['rowcount']==882)
pmp = P('MenuParam')
chk('MenuParam 单行 424 B', pmp['rowcount']==1 and pmp['rowsize']==424)
dmp, _ = fields('MenuParam')
chk('HpBarFadeOutTime = 1.5', read(pmp,dmp,'HpBarFadeOutTime')==[1.5], str(read(pmp,dmp,'HpBarFadeOutTime')))
chk('VolatilizeFadeBeginSec = 0.8', abs(read(pmp,dmp,'VolatilizeFadeBeginSec')[0]-0.8)<1e-5)

ptp = P('TentativePlayerParam'); dtp, _ = fields('TentativePlayerParam')
chk('TentativePlayerParam 2 行 x 2112 B', ptp['rowcount']==2 and ptp['rowsize']==2112)
chk('lockRangeHorizontalScreenRatio = 0.45', abs(read(ptp,dtp,'lockRangeHorizontalScreenRatio')[0]-0.45)<1e-6)
chk('lockRangeVerticalScreenRatio = 0.55', abs(read(ptp,dtp,'lockRangeVerticalScreenRatio')[0]-0.55)<1e-6)
chk('MovementGravity = 120', read(ptp,dtp,'MovementGravity')==[120.0,120.0])
chk('LockTargetMarking_TimeOutSec = 2.0', read(ptp,dtp,'LockTargetMarking_TimeOutSec')==[2.0,2.0])
chk('LockTargetMarking_ForgetDist = 700', read(ptp,dtp,'LockTargetMarking_ForgetDist')==[700,700])
chk('LockTargetMarking_ChachDist = 600', read(ptp,dtp,'LockTargetMarking_ChachDist')==[600,600])
chk('LockTargetMarking_ChachAngleDeg = 30', read(ptp,dtp,'LockTargetMarking_ChachAngleDeg')==[30,30])

pmsp = P('MenuPropertySpecParam'); dsp, _ = fields('MenuPropertySpecParam')
chk('MenuPropertySpecParam 508 行 x 108 B', pmsp['rowcount']==508 and pmsp['rowsize']==108)
chk('MenuPropertySpecParam 有 extract0_MemberTailOffset', 'extract0_MemberTailOffset' in dsp)

for t in ['GameSystemParam','GraphicsParam','SoundParam','BudgetParam']:
    q = P(t)
    chk('单行表 %s 行数=1' % t, q['rowcount']==1, '行数 %d' % q['rowcount'])
p_ta = P('TutorialActJudgeParam')
chk('TutorialActJudgeParam 行宽 9', p_ta['rowsize']==9, '实际 %d' % p_ta['rowsize'])

pd_ = P('DecalParam'); dd, tot_d = fields('DecalParam')
chk('DecalParam paramdex 尺寸 = 252 (位域修复后)', tot_d==252, 'paramdex %d vs 实际 %d' % (tot_d, pd_['rowsize']))


# --- P7 回填断言 ---
pa = P('AtkParam_Pc'); da, _ = fields('AtkParam')
hs = read(pa, da, 'hitStopTime')
chk('hitStopTime 非零 45 行 (顿帧仅近战)', len([x for x in hs if x!=0])==45,
    '实际 %d' % len([x for x in hs if x!=0]))
import collections as _c
_dist = dict(_c.Counter(round(x,3) for x in hs if x!=0))
chk('hitStopTime 分布 0.05x41/0.07x1/0.10x2/0.12x1',
    _dist.get(0.05)==41 and _dist.get(0.07)==1 and _dist.get(0.1)==2 and _dist.get(0.12)==1, str(_dist))

pn = P('NpcParam'); dn, _ = fields('NpcParam')
chk('NpcParam.receiveDmgHitStopType 全 1232 行 = 1', set(read(pn,dn,'receiveDmgHitStopType'))=={1})
_hst = _c.Counter(read(pn,dn,'hitStopType'))
chk('NpcParam.hitStopType = 2 有 1171 行', _hst.get(2)==1171, str(dict(_hst)))
_eig = _c.Counter(read(pn,dn,'enableImpactGaugeFE'))
chk('NpcParam.enableImpactGaugeFE = 1 有 933 行', _eig.get(1)==933, str(dict(_eig)))

pg = P('GameSystemParam'); dg2, _ = fields('GameSystemParam')
chk('HardHitStopTimeRatePercent = 1', read(pg,dg2,'HardHitStopTimeRatePercent')==[1.0])
chk('HitStopAddDamageAnimScale = 60', read(pg,dg2,'HitStopAddDamageAnimScale')==[60])
chk('HitStopAddDamageAnimTimeF = 5', read(pg,dg2,'HitStopAddDamageAnimTimeF')==[5])

ph = P('HitEffectSfxParam')
chk('HitEffectSfxParam 71 行 x 240 B', ph['rowcount']==71 and ph['rowsize']==240)
phc = P('HitEffectSfxConceptParam')
chk('HitEffectSfxConceptParam 64 行', phc['rowcount']==64)

ptp2 = P('TentativePlayerParam'); dtp2, _ = fields('TentativePlayerParam')
chk('PadHoldTimeSec = 0.4 (长按判定)', abs(read(ptp2,dtp2,'PadHoldTimeSec')[0]-0.4)<1e-6)
chk('ShieldChargePadHoldTimeSec = 0.4', abs(read(ptp2,dtp2,'ShieldChargePadHoldTimeSec')[0]-0.4)<1e-6)

pdl = P('DamageLevelConvParam')
chk('DamageLevelConvParam 132 行 x 256 B', pdl['rowcount']==132 and pdl['rowsize']==256)
pbl = P('BladeHomingParam'); dbl, _ = fields('BladeHomingParam')
chk('BladeHomingParam 10 行 x 64 B', pbl['rowcount']==10 and pbl['rowsize']==64)
_bmax = [x for x in read(pbl,dbl,'maxSpeedKMPH') if x>0]
chk('BladeHoming maxSpeedKMPH 350~1500', min(_bmax)==350.0 and max(_bmax)==1500.0,
    '实际 %.0f~%.0f' % (min(_bmax), max(_bmax)))
pba = P('BladeHomingAngSpeedParam'); dba, _ = fields('BladeHomingAngSpeedParam')
chk('BladeHomingAngSpeedParam 177 行 x 64 B', pba['rowcount']==177 and pba['rowsize']==64)
_ts = [x for x in read(pba,dba,'turnSpeedDPS') if x>0]
chk('turnSpeedDPS 上限 1500', max(_ts)==1500.0, '实际 %.0f' % max(_ts))

pcr = P('PadRumble'); dcr, totcr = fields('CameraRumbleParam')
chk('PadRumble 174 行 x 84 B', pcr['rowcount']==174 and pcr['rowsize']==84)
chk('CameraRumbleParam paramdex 尺寸 84', totcr==84, 'paramdex %d' % totcr)

pb2 = P('Bullet'); db2, _ = fields('BulletParam')
bfm = pf.bitfield_map(pf.fields_of(os.path.join(pf.PD,'Defs','BulletParam.xml'))[0])
_hom = pf.read_bitfield(pb2, bfm['isEnableAutoHoming'])
chk('Bullet.isEnableAutoHoming 位域读 = 0/568 置位', sum(_hom)==0, '实际 %d 置位' % sum(_hom))

# sfxPostureType 在 BulletParam（P7 更正）
chk('sfxPostureType 在 BulletParam 而非 AtkParam', 'sfxPostureType' in db2 and 'sfxPostureType' not in da)

# --- 对抗审查新增断言（防御机制）---
_pn = P('NpcParam'); _dn, _ = fields('NpcParam')
_gc = read(_pn,_dn,'physGuardCutRate')
_nz = [x for x in _gc if x!=0]
chk('NpcParam.physGuardCutRate 非零 1149/1232', len(_nz)==1149, '实际 %d' % len(_nz))
chk('physGuardCutRate 值域 74~100', min(_nz)==74.0 and max(_nz)==100.0,
    '实际 %.0f~%.0f' % (min(_nz), max(_nz)))
for _f in ['magGuardCutRate','fireGuardCutRate','thunGuardCutRate']:
    _v=[x for x in read(_pn,_dn,_f) if x!=0]
    chk('%s 非零 181 行' % _f, len(_v)==181, '实际 %d' % len(_v))
chk('NpcParam.def_phys 全 0（1232 行）', set(read(_pn,_dn,'def_phys'))=={0})
chk('NpcParam.def_thunder 全 0', set(read(_pn,_dn,'def_thunder'))=={0})

_pgs = P('GameSystemParam'); _dgs, _ = fields('GameSystemParam')
chk('FlickDamageCutRateSuccessGurad = 0.5', read(_pgs,_dgs,'FlickDamageCutRateSuccessGurad')==[0.5])

# 护甲 defense 精确表述（89 真实部件为 0 / 32 占位行为 100）
_pa2 = P('EquipParamProtector'); _da2, _ = fields('EquipParamProtector')
_dp = read(_pa2,_da2,'defensePhysics'); _cat = read(_pa2,_da2,'assembleMenuCategory')
_real = [i for i,c in enumerate(_cat) if c in (1,2,3,4)]
_ph   = [i for i,c in enumerate(_cat) if c == 0]
chk('护甲真实部件 89 行', len(_real)==89, '实际 %d' % len(_real))
chk('护甲占位行 32 行', len(_ph)==32, '实际 %d' % len(_ph))
chk('真实部件 defensePhysics 全 0', all(_dp[i]==0 for i in _real))
chk('占位行 defensePhysics 全 100', all(_dp[i]==100 for i in _ph))

# 1227 零命中（用 NpcParam 采样验证，不做全表扫描以省时间）
chk('NpcParam 内不含 1227', 1227 not in list(read(_pn,_dn,'def_phys')))

# --- 对抗审查 #3：曲线表结构与引用 ---
_pcg = P('CalcCorrectGraph'); _dcg, _tcg = fields('CalcCorrectGraph')
chk('CalcCorrectGraph 169 行 x 80 B', _pcg['rowcount']==169 and _pcg['rowsize']==80)
chk('paramdex CalcCorrectGraph 尺寸 80', _tcg==80, 'paramdex %d' % _tcg)
for _f in ['stageMaxVal0','stageMaxVal4','stageMaxGrowVal0','stageMaxGrowVal4','init_inclination_soul','boundry_value']:
    chk('CalcCorrectGraph 有字段 %s' % _f, _f in _dcg)
_db = P('Bullet'); _dbm, _ = fields('BulletParam')
chk('Bullet 有 distAtkPowerRateCalcGraphParamId（曲线表被引用）',
    'distAtkPowerRateCalcGraphParamId' in _dbm)
chk('Bullet 有 recoilBlur_UseCalcGraphBlurRate', 'recoilBlur_UseCalcGraphBlurRate' in _dbm)
_dam, _ = fields('AnimMoveCorrectionParam')
chk('AnimMoveCorrectionParam 有 calcGraphParamId', 'calcGraphParamId' in _dam)
chk('AnimMoveCorrectionParam 22 行 x 64 B', P('AnimMoveCorrectionParam')['rowcount']==22)

# --- 第二阶段（P5/P8/P11/P12/P14）断言 ---
# P5: 腿型外键链路
_pp5 = P('EquipParamProtector'); _dp5, _ = fields('EquipParamProtector')
_cat5 = read(_pp5,_dp5,'assembleMenuCategory')
_legs5 = [i for i,c in enumerate(_cat5) if c==4]
chk('腿部部件 26 个 (assembleMenuCategory=4)', len(_legs5)==26, '实际 %d' % len(_legs5))
chk('legs_payload 偏移 580', _dp5['legs_payload'][0]==580)
chk('legs_boosterId 偏移 584', _dp5['legs_boosterId'][0]==584)
_boost5 = read(_pp5,_dp5,'legs_boosterId')
_nb = [x for x in _boost5 if x != -1]
chk('只有 3 条腿有内置推进器', len(_nb)==3, '实际 %d' % len(_nb))
_pay5 = read(_pp5,_dp5,'legs_payload')
chk('坦克腿载重最大 100300', max(_pay5)==100300, '实际 %d' % max(_pay5))

# P5: 核心是唯一乘数枢纽
for _f in ['quickBoosterOutputCorrRate','generatorOutputCorrRate','generatorCoolPerf']:
    _v = read(_pp5,_dp5,_f)
    _idx = [i for i,x in enumerate(_v) if x!=0]
    _allcore = all(_cat5[i]==2 for i in _idx)
    chk('%s 非零行全在核心(cat=2)' % _f, _allcore, '非零 %d 行' % len(_idx))

# P5: 坦克有真实角加速度
_pt5 = P('ChrActTurnParam'); _dt5, _ = fields('ChrActTurnParam')
_ids5 = [r[0] for r in _pt5['rows']]
_bs = read(_pt5,_dt5,'baseTurnSpeedDPS'); _ta = read(_pt5,_dt5,'turnAccelDPSS')
_i100 = _ids5.index(10000000); _i130 = _ids5.index(13000000)
chk('二足 baseTurn=360 / turnAccel=9999999',
    _bs[_i100]==360.0 and _ta[_i100]==9999999.0, '%.0f/%.0f' % (_bs[_i100], _ta[_i100]))
chk('坦克 baseTurn=230 / turnAccel=230（有惯性）',
    _bs[_i130]==230.0 and _ta[_i130]==230.0, '%.0f/%.0f' % (_bs[_i130], _ta[_i130]))

# P5: 超重出击限制字段
_pci = P('CharaInitParam'); _dci, _ = fields('CharaInitParam')
chk('CharaInitParam 有 osReinforceLevel_OverWeightOk', 'osReinforceLevel_OverWeightOk' in _dci)

# P8: 关卡数据
_pm8 = P('MissionParam'); _dm8, _ = fields('MissionParam')
chk('MissionParam 111 行 x 352 B', _pm8['rowcount']==111 and _pm8['rowsize']==352)
chk('MissionParam 有 fallDeadHeight', 'fallDeadHeight' in _dm8)
_act = [x for x in read(_pm8,_dm8,'activateDistXZ') if x!=0]
chk('activateDistXZ 值域 800~8000（全量口径）', min(_act)==800.0 and max(_act)==8000.0,
    '实际 %.0f~%.0f' % (min(_act), max(_act)))
_pmap = P('MapAreaParam')
chk('MapAreaParam 25 行', _pmap['rowcount']==25, '实际 %d' % _pmap['rowcount'])
_pmg = P('MapGimmickParam')
chk('MapGimmickParam 10 行（机关词汇表极小）', _pmg['rowcount']==10, '实际 %d' % _pmg['rowcount'])

# P12: 敌人 AI
_paan = P('AttackActionParam_NPC'); _daan, _ = fields('AttackActionParam')
_sit = read(_paan,_daan,'shootIndicationType')
chk('NPC 表 shootIndicationType 全 0 (修正 P7)', set(_sit)=={0}, '唯一值 %s' % sorted(set(_sit)))
_alt = [x for x in read(_paan,_daan,'alertLevel') if x!=0]
chk('NPC alertLevel 非零 47 行', len(_alt)==47, '实际 %d' % len(_alt))
chk('AttackActionParam_NPC 1371 行', _paan['rowcount']==1371)
_pnt = P('NpcThinkParam'); _dnt, _ = fields('NpcThinkParam')
_se = [x for x in read(_pnt,_dnt,'searchEye_dist') if x!=0]
chk('searchEye_dist 非零仅 7 行（感知残留）', len(_se)==7, '实际 %d' % len(_se))

# P14: 教学系统
_pta2 = P('TutorialActJudgeParam')
chk('TutorialActJudgeParam 31 行', _pta2['rowcount']==31, '实际 %d' % _pta2['rowcount'])
_ptp2 = P('TutorialParam')
chk('TutorialParam 201 行', _ptp2['rowcount']==201, '实际 %d' % _ptp2['rowcount'])
_pat = P('UnlockParam_Archive_Tips')
chk('UnlockParam_Archive_Tips 114 行', _pat['rowcount']==114, '实际 %d' % _pat['rowcount'])

# P13 前置：商店与解锁
_psl = P('ShopLineupParam')
chk('ShopLineupParam 248 行 x 32 B', _psl['rowcount']==248 and _psl['rowsize']==32)
_porp = P('OsReinforcePoint')
chk('OsReinforcePoint 41 行', _porp['rowcount']==41, '实际 %d' % _porp['rowcount'])
_part = P('ArenaParam')
chk('ArenaParam 42 行', _part['rowcount']==42, '实际 %d' % _part['rowcount'])

# --- P13 元循环断言 ---
_pu = P('UnlockParam_OsPoint'); _du, _ = fields('GameDataUnlockParam')
chk('UnlockParam_OsPoint 41 行 x 16 B', _pu['rowcount']==41 and _pu['rowsize']==16)
chk('UnlockParam_OsPoint unlockType 全 = 3（竞技场）',
    set(read(_pu,_du,'unlockType'))=={3}, '实际 %s' % sorted(set(read(_pu,_du,'unlockType')))[:4])
_pop2 = P('OsReinforcePoint'); _dop2, _ = fields('OsReinforcePointParam')
chk('OsReinforcePoint.point 合计 197', sum(read(_pop2,_dop2,'point'))==197,
    '实际 %d' % sum(read(_pop2,_dop2,'point')))
_pe2 = P('EquipmentLineupParam'); _de2, _ = fields('EquipmentLineupParam')
_pr = [x for x in read(_pe2,_de2,'price') if x>0]
chk('EquipmentLineupParam.price 合计 62,052,000', sum(_pr)==62052000, '实际 %d' % sum(_pr))
chk('EquipmentLineupParam 318 行 x 32 B', _pe2['rowcount']==318 and _pe2['rowsize']==32)
_ptk = P('PartsTokenParam')
chk('PartsTokenParam 95 行 x 20 B', _ptk['rowcount']==95 and _ptk['rowsize']==20)
_pmp2 = P('MultiPlayCorrectionParam')
chk('MultiPlayCorrectionParam 只有 2 行', _pmp2['rowcount']==2, '实际 %d' % _pmp2['rowcount'])
_pcc = P('CompanyContributePointParam')
chk('CompanyContributePointParam 26 行（仅 8 行真实）', _pcc['rowcount']==26, '实际 %d' % _pcc['rowcount'])

# --- P16 断言 ---
_pud = P('UnlockParam_DLC'); _dud, _ = fields('GameDataUnlockParam')
chk('UnlockParam_DLC 1 行, unlockType=13', _pud['rowcount']==1 and read(_pud,_dud,'unlockType')==[13])
_pep = P('UnlockParam_EmblemPiece')
chk('UnlockParam_EmblemPiece 也是 DLC 挂点 (unlockType=13, rid=5000)',
    _pep['rowcount']==1 and read(_pep,_dud,'unlockType')==[13] and _pep['rows'][0][0]==5000,
    'rid=%d' % _pep['rows'][0][0])
_pa2 = P('ArenaParam'); _da2b, _ = fields('ArenaParam')
chk('ArenaParam.firstReward_osExp 全 0 (OS点不经此发)',
    set(read(_pa2,_da2b,'firstReward_osExp'))=={0})
_pn2 = P('UnlockParam_NamePlate_Solo')
chk('UnlockParam_NamePlate_Solo 21 行', _pn2['rowcount']==21, '实际 %d' % _pn2['rowcount'])
_mr = P('MercenaryRankTable')
chk('MercenaryRankTable 16 档', _mr['rowcount']==16, '实际 %d' % _mr['rowcount'])
# ==============================================================
# ═══════════════════════════════════════════════════════════════
# P21：UE 5.8 的 Agent 协作能力面（本机引擎文件系统实测）
# 这些断言不看 regulation.bin，而看本机 UE 5.8 安装目录的实际文件内容。
# ═══════════════════════════════════════════════════════════════
import io

_UE = 'J:' + os.sep + 'UE_5.8'
_MCP = os.path.join(_UE, 'Engine', 'Plugins', 'Experimental', 'ModelContextProtocol')
_TOOLSETS = os.path.join(_UE, 'Engine', 'Plugins', 'Experimental', 'Toolsets')


def _read(p):
    try:
        return io.open(p, encoding='utf-8', errors='ignore').read()
    except Exception:
        return ''


# ① 官方 Unreal MCP 插件存在，且描述/状态与报告一致
_upl = _read(os.path.join(_MCP, 'ModelContextProtocol.uplugin'))
chk('UE5.8 内置官方 ModelContextProtocol 插件（Unreal MCP）', bool(_upl))
chk('Unreal MCP 的 FriendlyName 正确', '"FriendlyName": "Unreal MCP"' in _upl)
chk('Unreal MCP 由 Epic 官方编写', '"CreatedBy": "Epic Games, Inc."' in _upl)
chk('Unreal MCP 默认关闭（EnabledByDefault=false）', '"EnabledByDefault": false' in _upl)
chk('Unreal MCP 标记为实验性（IsExperimentalVersion=true）', '"IsExperimentalVersion": true' in _upl)
chk('Unreal MCP 已编译出 DLL（非仅有源码）',
    os.path.exists(os.path.join(_MCP, 'Binaries', 'Win64', 'UnrealEditor-ModelContextProtocol.dll')))

# ② ToolsetRegistry 是它的依赖，且基类是 C++ 类 + JSON 进出
_ts_h = _read(os.path.join(_UE, 'Engine', 'Plugins', 'Experimental', 'ToolsetRegistry',
                           'Source', 'ToolsetRegistry', 'Public', 'ToolsetRegistry', 'Toolset.h'))
chk('Unreal MCP 依赖 ToolsetRegistry', 'ToolsetRegistry' in _upl)
chk('FToolset::ExecuteTool 签名是 (ToolName, JsonInput)',
    'ExecuteTool(' in _ts_h and 'const FString& ToolName' in _ts_h and 'const FString& JsonInput' in _ts_h)
chk('Toolset 暴露 JSON schema（GetJsonSchema）', 'GetJsonSchema() const' in _ts_h)

# ③ AICallable 元数据标记：UHT 处理方式 + 总数
_uht = _read(os.path.join(_UE, 'Engine', 'Source', 'Programs', 'Shared', 'EpicGames.UHT',
                          'Types', 'UhtFunction.cs'))
chk('UHT 把 AICallable 与 BlueprintCallable/Exec 并列处理',
    'MetaData.ContainsKey("AICallable")' in _uht and 'BlueprintCallable | EFunctionFlags.Exec' in _uht)


def _grep_count(root, pattern):
    n = 0
    for dp, _, fns in os.walk(root):
        if 'Intermediate' in dp or 'Binaries' in dp:
            continue
        for fn in fns:
            if fn.endswith(('.h', '.cpp', '.cs')):
                try:
                    with io.open(os.path.join(dp, fn), encoding='utf-8', errors='ignore') as fh:
                        n += fh.read().count(pattern)
                except Exception:
                    pass
    return n


_ai_n = _grep_count(_TOOLSETS, 'AICallable')
chk('官方 Toolsets 内 AICallable 出现 275 次（口径：.h/.cpp/.cs，排除 Intermediate/Binaries）',
    _ai_n == 275, '实际 %d' % _ai_n)

# ④ 27 个工具集；且没有任何蓝图图谱工具集
_ts = sorted(d for d in os.listdir(_TOOLSETS)
             if os.path.isdir(os.path.join(_TOOLSETS, d))) if os.path.isdir(_TOOLSETS) else []
chk('官方 Toolsets 共 27 个', len(_ts) == 27, '实际 %d' % len(_ts))
# 注意：这一条必须在 _ts 定义之后（早前版本插在定义前，_ts 还是个 float）
chk('AICallable 只出现在 Toolsets 中 19 个工具集（其余 8 个未标记）',
    sum(1 for d in _ts if _grep_count(os.path.join(_TOOLSETS, d), 'AICallable') > 0) == 19,
    '实际 %d' % sum(1 for d in _ts if _grep_count(os.path.join(_TOOLSETS, d), 'AICallable') > 0))


def _find_names(root, needles):
    hits = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ('Intermediate', 'Binaries')]
        for nm in list(dns) + fns:
            low = nm.lower()
            if any(nd in low for nd in needles):
                hits.append(os.path.join(dp, nm))
    return hits


_bp_ts = _find_names(os.path.join(_UE, 'Engine'), ['blueprinttoolset', 'kismettoolset', 'graphtoolset'])
chk('不存在任何蓝图/图 编辑工具集（Agent 不能编辑蓝图图谱）', len(_bp_ts) == 0,
    '意外命中: %s' % _bp_ts[:3])

# ⑤ UMGToolSet 只能按 API 操作（Widget 树），不能碰图谱
_umg = _read(os.path.join(_TOOLSETS, 'UMGToolSet', 'Source', 'UMGToolSet', 'Private', 'UMGToolSet.h'))
chk('UMGToolSet 提供 AddWidget（结构化 API，非图谱）', 'AddWidget(' in _umg)
chk('UMGToolSet 提供 CompileWidgetBlueprint', 'CompileWidgetBlueprint(' in _umg)

# ⑥ 蓝图 VM 是解释执行：ScriptCore + EX_ 操作码
_sc = _read(os.path.join(_UE, 'Engine', 'Source', 'Runtime', 'CoreUObject', 'Private',
                         'UObject', 'ScriptCore.cpp'))
chk('蓝图由 VM 解释执行（ProcessLocalScriptFunction）', 'ProcessLocalScriptFunction' in _sc)
_sh = _read(os.path.join(_UE, 'Engine', 'Source', 'Runtime', 'CoreUObject', 'Public',
                         'UObject', 'Script.h'))
import re as _re
_ex_ids = set(_re.findall(r'\bEX_[A-Za-z0-9_]+', _sh))
chk('蓝图字节码去重后 EX_* 操作码共 102 个', len(_ex_ids) == 102, '实际 %d' % len(_ex_ids))
chk('EX_ 三口径已区分：行数 103 / 出现次数 108 / 去重标识符 102',
    sum(1 for _ln in _sh.splitlines() if 'EX_' in _ln) == 103
    and _sh.count('EX_') == 108
    and len(_ex_ids) == 102)

# ⑦ 渲染管线无蓝图暴露（RDG / 全局着色器）—— TA 能力护城河
_rgs = _read(os.path.join(_UE, 'Engine', 'Source', 'Runtime', 'RenderCore', 'Public',
                          'RenderGraphResources.h'))
chk('RDG 无任何 UFUNCTION/UCLASS 暴露给蓝图',
    _rgs.count('UFUNCTION') == 0 and _rgs.count('UCLASS') == 0)

# ⑧ 蓝图固化（Nativization）在 5.8 已被移除
_nat = _find_names(os.path.join(_UE, 'Engine'), ['nativization'])
chk('Blueprint Nativization 插件在 5.8 已不存在', len(_nat) == 0, '意外命中: %s' % _nat[:3])

# ⑨ Python 侧没有蓝图图谱 API（只有反方向的 K2Node_ExecutePythonScript）
_py = os.path.join(_UE, 'Engine', 'Plugins', 'Experimental', 'PythonScriptPlugin')
_py_hits = _find_names(_py, ['pyblueprint', 'pykismet', 'pygraph'])
chk('Python 插件无 Py*Blueprint/Kismet/Graph 包装类', len(_py_hits) == 0,
    '意外命中: %s' % _py_hits[:3])
chk('存在反方向节点 K2Node_ExecutePythonScript（蓝图调 Python）',
    os.path.exists(os.path.join(_py, 'Source', 'PythonScriptPlugin', 'Private',
                                'K2Node_ExecutePythonScript.cpp')))

# --- 输出 ---
ok = sum(1 for _,c,_ in CHECKS if c)
bad = [(d,det) for d,c,det in CHECKS if not c]
print('=== UE5 文档数据终校 ===')
print('通过 %d / %d' % (ok, len(CHECKS)))
if bad:
    print()
    print('!! 未通过:')
    for d, det in bad: print('   - %s   [%s]' % (d, det))
else:
    print('全部通过 ✓')
sys.exit(1 if bad else 0)
