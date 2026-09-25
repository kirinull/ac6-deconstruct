# -*- coding: utf-8 -*-
# 数值级验证：从 DataTable 逐格读值，与源 CSV 比对
import unreal, io, os, csv, sys

DT_DIR = '/Game/AC6/Data/Tables'
CSV_DIR = r'<UE_PROJECTS>\AC6Proto\data\ue_datatables'

CHECKS = [
    ('DT_Booster',   'EquipParamBooster',   ['QBReloadTimeSec', 'QBEndSpeedKMH', 'ConsumeFixedENQB', 'Weight']),
    ('DT_Protector', 'EquipParamProtector', ['Stability', 'Ap', 'ArmMaxWeight']),
    ('DT_Attack',    'AtkParam_Pc',         ['ImpactPower', 'AtkPhys', 'HitStopTime']),
    ('DT_Weapon',    'EquipParamWeapon',    ['Weight', 'AttackBasePhysics']),
    ('DT_Npc',       'NpcParam',            ['StabilityVal', 'DefMag']),
    ('DT_GameSettings', 'GameSettings',     ['GravityMPSS', 'ImpactLifeTimeSec', 'BaseTurnSpeedDPS']),
    # ── 第 1 批新增 6 张表 ──
    ('DT_LockCam',     'LockCamParam',       ['CamDistTarget', 'CamFovY', 'ChrOrgOffsetY',
                                              'ChrTransChaseRateForNormalX', 'ChrTransChaseRateForQBX',
                                              'ChrTransChaseRateForBoostX', 'RotSpeedMinX', 'RotSpeedMaxX',
                                              'RotHiSpeedMaxX', 'RotRangeMinX', 'RotRangeMaxX']),
    ('DT_MovementAc',  'MovementAcTypeParam',['QuickBoostMaxSpeedKMPH', 'QuickBoostAccelMPSS',
                                              'QuickBoostAccelTimeSec', 'RoundDashMaxSpeedKMPH',
                                              'MinStiffTimeSec', 'MaxStiffTimeSec', 'JumpUpperMaxSpeedKMPH']),
    ('DT_Turn',        'ChrActTurnParam',    ['BaseTurnSpeedDPS', 'LookTargetModeTurnSpeedDPS', 'TurnAccelDPSS']),
    ('DT_PlayerParam', 'TentativePlayerParam',['MovementGravity', 'HighSpeedBrakeStartSpeedKMH',
                                              'BrakeStartSpeedKMH', 'LockRangeHorizontalScreenRatio']),
    ('DT_Rumble',      'PadRumble',          ['FovApplyType', 'LifeTimeSec', 'Priority', 'BeginDist']),
    ('DT_BoostParam',  'BoostParam',         ['BoostDirLerpRate', 'CounterBoostActiveAngleDeg']),
    # ── 第 2 批：攻击 ID 映射（本项目自建表；RowName 是 FName，不参与数值比对，
    #    只校验行数 —— 行数对上就等于 id↔行名 的对应关系被完整带进 UE）──
    ('DT_AttackIdMap', 'AttackIdMap',        []),
    ('DT_BulletCombat','BulletCombat',       ['AtkIdBullet', 'InitVellocityMS', 'HitRadiusM', 'NumShoot']),
]

def out(s): unreal.log('[VERIFY] ' + str(s))

def num(x):
    try: return float(x)
    except Exception: return None

total_cells = mism = 0
for dt_name, csv_base, cols in CHECKS:
    dt = unreal.load_object(None, '%s/%s' % (DT_DIR, dt_name))
    if dt is None:
        out('MISS dt ' + dt_name); continue
    rows = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
    csvp = os.path.join(CSV_DIR, csv_base + '.csv')
    if not os.path.exists(csvp): out('MISS csv ' + csvp); continue
    recs = list(csv.reader(io.open(csvp, encoding='utf-8', newline='')))
    hdr, data = recs[0], recs[1:]
    by_name = {r[0]: r for r in data}
    out('--- %s  (%d 行资产 / %d 行 CSV)' % (dt_name, len(rows), len(data)))
    for col in cols:
        if col not in hdr:
            out('    [无此列] ' + col); continue
        ci = hdr.index(col)
        # 签名是 (table, column)，返回整列字符串数组，顺序同 get_data_table_row_names
        colvals = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, col)
        bad = 0; checked = 0; vals = []
        for rn, got in zip(rows, colvals):
            src = by_name.get(str(rn))
            if src is None: continue
            a, b = num(got), num(src[ci])
            if a is None or b is None: continue
            checked += 1
            if abs(a - b) > 1e-4:
                bad += 1
                if bad <= 2: out('    [差异] %s.%s  UE=%s  CSV=%s' % (rn, col, got, src[ci]))
            vals.append(a)
        total_cells += checked; mism += bad
        if vals:
            out('    %-22s 比对 %4d 格  不一致 %d  min=%.4g max=%.4g' % (col, checked, bad, min(vals), max(vals)))
out('=' * 60)
out('总计比对 %d 格，不一致 %d 格' % (total_cells, mism))
out('VERIFY_DONE')
