# -*- coding: utf-8 -*-
"""
把本机解包的 regulation.bin 导出成 UE5 DataTable 可直接导入的 CSV。

用途：打通「有数据」→「UE5 能导入」这最后一步。
- 行名（CSV 第一列 Name）取自 paramdex 的 Names/Developer Names，没有则用 rowId
- 字段名转成 UE 友好的 PascalCase（不含 : . [ ] 空格）
- 类型映射到 UE：u8/s8→int32（UE CSV 惯用）、u16/s16/u32/s32→int32、f32→float
- 同时输出一个 .struct.txt，列出字段与类型，照着建 Struct / C++ USTRUCT

⚠️ 合规：这是**在你本机、对你自己的游戏数据**做的本地转换，产物仅供个人学习研究，
不要分发。UE 文档里也请不要把游戏原始数值当作自己的资产。

用法：
    python tools/export_ue_datatables.py                     # 导出默认的核心装备表
    python tools/export_ue_datatables.py EquipParamBooster   # 只导某张表
    python tools/export_ue_datatables.py --list              # 列出可导出的表
"""
import os, sys, csv, io, re, struct, importlib.util

# 剪枝开关（命令行可改）
PRUNE_ZERO = True     # 丢掉全零列（默认开：UE 里几百列的表没法用）
PRUNE_CONST = False   # 是否也丢掉"所有行同值"的常量列
STARTER_MODE = False  # --starter：只导出手工挑过的起步字段集

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

pi = _load('pi', os.path.join(HERE, 'param_inspect.py'))
pf = _load('pf', os.path.join(HERE, 'paramdex_fields.py'))

OUTDIR = os.path.join(ROOT, 'data', 'ue_datatables')

# paramdex 定义名 -> 实际 .param 表名
DEFAULT_TABLES = [
    ('EquipParamWeapon', 'EquipParamWeapon'),
    ('EquipParamProtector', 'EquipParamProtector'),
    ('EquipParamBooster', 'EquipParamBooster'),
    ('EquipParamGenerator', 'EquipParamGenerator'),
    ('EquipParamFcs', 'EquipParamFcs'),
    ('AtkParam', 'AtkParam_Pc'),
    ('BulletParam', 'Bullet'),
    ('NpcParam', 'NpcParam'),
]

# paramdex 名 -> 实际表名（模糊匹配用）
ALIAS = {a: b for a, b in DEFAULT_TABLES}
ALIAS.update({
    'BehaviorParam': 'BehaviorParam_PC', 'BulletParam_Npc': 'Bullet_Npc',
    'AtkParam_Npc': 'AtkParam_Npc', 'ChrActTurnParam': 'ChrActTurnParam',
    'LockCamParam': 'LockCamParam', 'CameraRumbleParam': 'PadRumble',
    'JigglerBehaviorParam': 'JigglerBehaviorParam', 'JigglerBaseParam': 'JigglerBaseParam',
    'BoostParam': 'BoostParam', 'TentativePlayerParam': 'TentativePlayerParam',
    'MovementAcTypeParam': 'MovementAcTypeParam', 'CalcCorrectGraph': 'CalcCorrectGraph',
    'MissionParam': 'MissionParam', 'DamageLevelConvThresholdParam': 'DamageLevelConvThresholdParam',
    'EnemyCommonParam': 'EnemyCommonParam', 'NpcThinkParam': 'NpcThinkParam',
    'PartsBreakLotteryParam': 'PartsBreakLotteryParam', 'MenuParam': 'MenuParam',
    'PlayerColoringPresetParam': 'PlayerColoringPresetParam', 'DecalParam': 'DecalParam',
    'SpEffect': 'SpEffectParam',
})


# ★ 起步集（--starter）：只导出文档里已验证有意义的字段。
# 依据：docs/02_实施/UE5复刻_实施文档.md 第 5 章各节 + data/字段参考.md。
# 这是给 M0 用的最小可用集——几百列的表在 UE 里没法用。
STARTER_COLS = {
    'EquipParamWeapon': [
        'weight', 'attackBasePhysics', 'attackBaseMagic', 'attackBaseFire', 'attackBaseThunder',
        'attackBaseStamina', 'saWeaponDamage', 'weaponWeightRate',
    ],
    'EquipParamProtector': [
        'weight', 'ap', 'stability', 'legs_payload', 'armMaxWeight',
        'partsDamageRate', 'corectSARecover', 'assembleMenuCategory',
        'legs_MovementParamId', 'legs_TurnParamId', 'legs_boosterId',
        'isHeavyWeightAddAnim',
    ],
    'EquipParamBooster': [
        'weight', 'consumeEN', 'consumeEN_BoostUp', 'consumeFixedEN_QB',
        'QB_EndSpeedKMH', 'QB_StartAddSpeedKMH', 'QB_AccelTimeF30', 'QB_ReloadTimeSec',
        'dashBoost_EndSpeedKMH', 'flyBoost_EndSpeedKMH',
        'flyBoostUpperMaxSpeedKMH', 'flyBoostUpperAccelMPSS',
        'upperBoostMaxSpeedKMPH', 'upperBoostStartAccelMPSS', 'flyBoostDownMaxSpeedKMH',
    ],
    'EquipParamGenerator': [
        'weight', 'energyMax', 'energyRecoveryPerSec', 'consumeEN',
        'energyRecoveryDelayTimeSec', 'energyRecoveryDelayTimeForEmptySec',
        'energyRecoverValForEmpty',
    ],
    'EquipParamFcs': [
        'weight', 'predictionShoot_BulletSpeedMPS', 'predictionShoot_MaxShootOffset',
        'predictionShoot_StartPredDist', 'missileLockPerf',
        'missileLockTimeRate', 'missileMultiLockTimeRate',
    ],
    'AtkParam': [
        'atkPhys', 'atkMag', 'atkFire', 'atkThun', 'atkStam',
        'impactPower', 'residualImpactPower', 'hitStopTime',
        'staggerCriticalRate_Phys', 'staggerCriticalRate_Mag',
        'staggerCriticalRate_Fire', 'staggerCriticalRate_Thun',
    ],
    'BulletParam': [
        'life', 'shootCameraRumbleParamId', 'distAtkPowerRateCalcGraphParamId',
        'recoilBlur_MinAngDegH', 'recoilBlur_MaxAngDegH',
        'recoilBlur_MinAngDegV', 'recoilBlur_MaxAngDegV',
    ],
    'NpcParam': [
        'def_phys', 'def_mag', 'def_fire', 'def_thunder',
        'physGuardCutRate', 'magGuardCutRate', 'fireGuardCutRate', 'thunGuardCutRate',
        'stabilityVal', 'hitStopType', 'receiveDmgHitStopType', 'enableImpactGaugeFE',
    ],
}

def filter_starter(pd_name, cols):
    """只保留起步集里点名的字段（原样返回 (ue_name, off, type, disp) 子集）"""
    want = STARTER_COLS.get(pd_name)
    if want is None:
        return cols, 0
    want_l = {w.lower() for w in want}
    out = []
    for c in cols:
        un, off, t, disp = c
        # 用 UE 名反推原始名匹配（ue_name 会去掉下划线并驼峰化）
        if un.lower() in want_l or any(un.lower() == ue_name(w).lower() for w in want):
            out.append(c)
    return out, len(cols) - len(out)


def ue_type(t):
    """paramdex 类型 -> UE 结构体类型（CSV 里我们只写数值，类型给 .struct.txt 用）"""
    if t == 'f32': return 'float'
    if t in ('u8', 's8', 'u16', 's16', 'u32', 's32'): return 'int32'
    if t in ('u64', 's64'): return 'int64'
    if t == 'f64': return 'double'
    if t == 'fixstr' or t.startswith('fixstr'): return 'FString'
    return None

def ue_name(raw):
    """字段名 -> UE 友好名（PascalCase，去非法字符）"""
    base = raw.split(':')[0].split('[')[0]
    # 去掉常见前缀噪声但保留可读性
    parts = re.split(r'[_\s]+', base)
    out = ''.join(p[:1].upper() + p[1:] for p in parts if p)
    out = re.sub(r'[^0-9A-Za-z]', '', out)
    if not out: return None
    if out[0].isdigit(): out = 'F' + out
    return out

def row_names(pd_name, param_name, rows):
    """优先用 paramdex 的 Names / Developer Names 作行名，否则 rowId"""
    names = {}
    for sub in ('Names', 'Developer Names'):
        fp = os.path.join(pf.PD, sub, pd_name + '.txt')
        if not os.path.exists(fp):
            # 有些表的行名文件用实际表名
            fp = os.path.join(pf.PD, sub, param_name + '.txt')
        if os.path.exists(fp):
            try:
                txt = io.open(fp, encoding='cp932', errors='replace').read()
            except Exception:
                txt = io.open(fp, encoding='utf-8', errors='replace').read()
            for line in txt.split('\n'):
                if not line.strip(): continue
                m = re.match(r'^(\d+)\s+(.*)$', line.strip())
                if m:
                    rid = int(m.group(1))
                    label = m.group(2).split(' -- ')[0].strip()
                    if rid not in names and label:
                        names[rid] = label
    out = []
    used = {}
    for r in rows:
        rid = r[0]
        label = names.get(rid)
        if label:
            nm = re.sub(r'[^0-9A-Za-z]+', '_', label).strip('_')
        else:
            nm = ''
        if not nm:
            nm = 'Row_%d' % rid
        # 去重
        if nm in used:
            used[nm] += 1
            nm = '%s_%d' % (nm, used[nm])
        else:
            used[nm] = 0
        out.append(nm)
    return out

def export(pd_name, param_name, verbose=True):
    x = os.path.join(pf.PD, 'Defs', pd_name + '.xml')
    f = os.path.join(pi.ROOTS['van'], param_name + '.param')
    if not os.path.exists(x):
        if verbose: print('  跳过 %-28s (paramdex 无定义 %s.xml)' % (param_name, pd_name))
        return None
    if not os.path.exists(f):
        if verbose: print('  跳过 %-28s (regulation 无此表)' % param_name)
        return None

    p = pi.parse(f)
    fl, total = pf.fields_of(x)
    size_ok = (total == p['rowsize'])

    # 收集可导出的数值字段
    cols = []           # (ue_name, offset, pd_type, jp_disp)
    seen = set()
    for off, t, raw, disp in fl:
        if t not in pf.TYPE_FMT:          # 跳过 dummy8/fixstr 等
            continue
        base = raw.split(':')[0].split('[')[0]
        if base.lower().startswith(('pad', 'dummy', 'reserved')):
            continue
        un = ue_name(raw)
        if not un or un in seen:
            continue
        seen.add(un)
        cols.append((un, off, t, (disp or '').strip()))

    if not cols:
        if verbose: print('  跳过 %-28s (无可用数值字段)' % param_name)
        return None

    # ★ 起步集过滤（--starter 时启用）
    if STARTER_MODE:
        cols, _ncut = filter_starter(pd_name, cols)
        if not cols:
            if verbose: print('  跳过 %-28s (起步集里未列该表)' % param_name)
            return None

    # ★ 剪枝：默认丢掉"全零列"（UE 里 573 列的表没法用）
    #   文档 4.1 节实测：武器表 389 个 f32 槽里只有约 15 个是真连续量、133 个全零
    raw_rows = []
    for i in range(p['rowcount']):
        base = p['datastart'] + i * p['rowsize']
        row = []
        for un, off, t, disp in cols:
            o = base + off
            if o + 4 > len(p['b']):
                row.append(0); continue
            row.append(struct.unpack_from('<' + pf.TYPE_FMT[t], p['b'], o)[0])
        raw_rows.append(row)

    dropped_zero = dropped_const = 0
    keep_idx = []
    for c in range(len(cols)):
        colvals = [r[c] for r in raw_rows]
        if PRUNE_ZERO and all(v == 0 for v in colvals):
            dropped_zero += 1; continue
        if PRUNE_CONST and len(set(colvals)) <= 1:
            dropped_const += 1; continue
        keep_idx.append(c)

    cols = [cols[c] for c in keep_idx]
    raw_rows = [[r[c] for c in keep_idx] for r in raw_rows]
    if not cols:
        if verbose: print('  跳过 %-28s (剪枝后无字段)' % param_name)
        return None

    names = row_names(pd_name, param_name, p['rows'])

    os.makedirs(OUTDIR, exist_ok=True)
    csv_path = os.path.join(OUTDIR, param_name + '.csv')
    st_path  = os.path.join(OUTDIR, param_name + '.struct.txt')

    def fmt_cell(v, t):
        # 浮点去噪：f32 常有 0.5600000023841858 这类尾数，UE 里难看且无意义
        if t == 'f32':
            r = round(float(v), 6)
            return int(r) if r == int(r) else r
        return v

    with io.open(csv_path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['Name'] + [c[0] for c in cols])
        for i, row in enumerate(raw_rows):
            w.writerow([names[i]] + [fmt_cell(v, cols[c][2]) for c, v in enumerate(row)])

    with io.open(st_path, 'w', encoding='utf-8') as fh:
        fh.write('// DataTable row struct for %s  (paramdex: %s)\n' % (param_name, pd_name))
        fh.write('// paramdex 结构 %d 字节 vs 实际 %d 字节 -> %s\n' % (
            total, p['rowsize'], 'MATCH' if size_ok else 'DIFF %+d（字段偏移可能不可靠，谨慎使用！）' % (total - p['rowsize'])))
        fh.write('// 行数 %d；字段 %d 个\n//\n' % (p['rowcount'], len(cols)))
        fh.write('// USTRUCT(BlueprintType)\n// struct F%sRow : public FTableRowBase\n// {\n//     GENERATED_BODY()\n//\n' % param_name)
        for un, off, t, disp in cols:
            fh.write('//     /** %s  (offset %d) */\n' % (disp[:60] or '-', off))
            fh.write('//     UPROPERTY(EditAnywhere, BlueprintReadWrite) %s %s = 0;\n\n' % (ue_type(t), un))
        fh.write('// };\n')

    if verbose:
        flag = '' if size_ok else '  ⚠️ 尺寸不符(%+d)' % (total - p['rowsize'])
        print('  ✓ %-26s %5d 行 × %3d 字段 (剪掉全零%d/常量%d) -> %s.csv%s' % (
            param_name, p['rowcount'], len(cols), dropped_zero, dropped_const, param_name, flag))
    return {'table': param_name, 'rows': p['rowcount'], 'cols': len(cols), 'size_ok': size_ok}

if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    if '--keep-all' in args:
        PRUNE_ZERO = False; PRUNE_CONST = False; args.remove('--keep-all')
    if '--starter' in args:
        STARTER_MODE = True; args.remove('--starter')
    if '--prune-const' in args:
        PRUNE_CONST = True; args.remove('--prune-const')
    if '--list' in args:
        print('可导出的 paramdex 定义（%d 个）：' % len(ALIAS))
        for k in sorted(ALIAS): print('   %-34s -> %s' % (k, ALIAS[k]))
        sys.exit(0)

    print('导出 UE5 DataTable CSV')
    print('来源: %s' % pi.ROOTS['van'])
    print('输出: %s' % OUTDIR)
    print()
    targets = []
    if args:
        for a in args:
            # 允许直接给实际表名或 paramdex 名
            if a in ALIAS: targets.append((a, ALIAS[a]))
            else:
                cand = [k for k, v in ALIAS.items() if v == a]
                targets.append((cand[0] if cand else a, a))
    else:
        targets = DEFAULT_TABLES

    ok = []
    for pd_name, param_name in targets:
        r = export(pd_name, param_name)
        if r: ok.append(r)

    print()
    print('成功导出 %d 张表。' % len(ok))
    print()
    print('下一步（UE5 里导入）：')
    print('  1. 按同名 .struct.txt 建 USTRUCT（或蓝图 Struct），字段名照抄')
    print('  2. 内容浏览器右键 -> 导入 -> 选 .csv，行类型选刚建的 Struct')
    print('  3. 导入时确认第一列被识别为 Row Name（UE 默认读第一列做行名）')
    print()
    print('⚠️ 尺寸不符的表在 .struct.txt 顶部有警告，其字段偏移可能不可靠，务必先跑 tools/paramdex_audit.py 核对。')
    print()
    print('导出后建议跑一次格式校验（确认 UE 能正确导入）：')
    print('  python tools/validate_ue_csv.py')
