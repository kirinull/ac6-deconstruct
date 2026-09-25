# -*- coding: utf-8 -*-
"""第 2 批（开火/命中/冲击）需要的两张**补充表**。

【为什么要补表，而不是改 M0 那套 CSV】
  M0 的 data/ue_datatables/*.csv 是文档 session 的 tools/export_ue_datatables.py 产出的
  精选用列集（每表 6~15 列）。它归文档 session 维护，我不改 —— 改了会被下次重导出覆盖掉。
  但第 2 批需要两个它没带的量：
    ① Bullet.AtkIdBullet / InitVellocity / HitRadius  —— 弹丸 → 攻击 的那一跳
    ② AtkParam_Pc 的行 id                              —— 上面那一跳的落点
  所以这里从 **raw .param** 直接另出两张小表，任何时候都能重跑重建。

【已验证的数据链】（脚本会自己再校验一次）
  Bullet.atkId_Bullet (u32@4)  --数值 id-->  AtkParam_Pc 的行
  · AtkParam_Pc 的 raw 行数 == CSV 行数（712），行序一一对应 → 由行序建立 id↔行名
  · Bullet 的 446 个不同 atkId 里 435 个能命中 AtkParam_Pc 的行 id（97.5%）
  · 自证：Bullet[Proto_Vertical_missile].atkId = 3100 → AtkParam_Pc[Proto_Vertical_missile]

产出：
  data/ue_datatables/BulletCombat.csv     Name, AtkIdBullet, InitVellocityMS, HitRadiusM, NumShoot, HomingAngleDPS
  data/ue_datatables/AttackIdMap.csv      Name(=<十进制 id>), RowName
  + 对应的 *.struct.txt（gen_data_rows.py 读它生成 C++ 结构体）

用法：python ue5ops/build_combat_tables.py
"""
import os, io, re, csv, struct, importlib.util, sys
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, 'data', 'ue_datatables')
spec = importlib.util.spec_from_file_location('pi', os.path.join(BASE, 'tools', 'param_inspect.py'))
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)


PD = r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs'
_TYPE_SIZE = {'u8':1,'s8':1,'u16':2,'s16':2,'u32':4,'s32':4,'f32':4,'angle32':4,
              'f64':8,'u64':8,'s64':8,'dummy8':1,'fixstr':1,'fixstrW':2,'f16':2}


def paramdex_fields(xml_name):
    """[(offset, name, jp_display, type)]，位域与数组都摊平成独立字段。

    ★ 为什么不硬编码偏移：本项目已经因为"猜列号/猜偏移"静默错过一次
      （2026-09-19：把 Bullet.initVellocity 猜成偏移 20，实际 20 是 life，44 才是初速）。
      偏移一律从 paramdex 定义里读，字段改名/改序时脚本会自己发现。"""
    root = ET.parse(os.path.join(PD, xml_name + '.xml')).getroot()
    out = []; off = 0; bu = 0; bb = 1
    for f in root.find('Fields').findall('Field'):
        d = (f.get('Def') or '').strip()
        m = re.match(r'^([A-Za-z0-9_]+)\s+(.+)$', d)
        if not m:
            continue
        typ, rest = m.group(1), m.group(2)
        nm = rest.split('=')[0].strip()
        disp = f.findtext('DisplayName') or ''
        mb = re.search(r':(\d+)$', nm)
        if mb:
            if bu == 0:
                bb = _TYPE_SIZE.get(typ, 1)
            out.append((off, nm.split(':')[0], disp, typ)); bu += int(mb.group(1))
            if bu >= bb * 8:
                off += bb; bu = 0
            continue
        if bu:
            off += bb; bu = 0
        arr = re.search(r'\[(\d+)\]$', nm)
        if arr:
            n = int(arr.group(1)); base = nm[:arr.start()]
            for k in range(n):
                out.append((off + k * _TYPE_SIZE.get(typ, 1), '%s[%d]' % (base, k), disp, typ))
            off += n * _TYPE_SIZE.get(typ, 1); continue
        out.append((off, nm, disp, typ)); off += _TYPE_SIZE.get(typ, 4)
    return out


def field_offsets(xml_name):
    return {n: (o, t) for o, n, d, t in paramdex_fields(xml_name)}


def val(p, i, off, fmt='<f'):
    o = p['datastart'] + i * p['rowsize'] + off
    if o + 4 > len(p['b']):
        return None
    try:
        return struct.unpack_from(fmt, p['b'], o)[0]
    except Exception:
        return None


def rows_of(csv_base):
    r = list(csv.reader(io.open(os.path.join(D, csv_base + '.csv'), encoding='utf-8-sig')))
    return r[0], r[1:]


def write_struct(fname, struct_name, note, fields, nrows):
    L = ['// DataTable row struct for %s  (%s)' % (fname, note),
         '// 生成：ue5ops/build_combat_tables.py',
         '// 行数 %d；字段 %d 个' % (nrows, len(fields)),
         '//', '// USTRUCT(BlueprintType)',
         '// struct %s : public FTableRowBase' % struct_name,
         '// {', '//     GENERATED_BODY()', '//']
    for doc, ctype, nm, dflt in fields:
        L.append('//     /** %s */' % doc)
        L.append('//     UPROPERTY(EditAnywhere, BlueprintReadWrite) %s %s = %s;' % (ctype, nm, dflt))
        L.append('//')
    L += ['// };', '']
    io.open(os.path.join(D, fname + '.struct.txt'), 'w', encoding='utf-8', newline='').write(chr(10).join(L))


def write_csv(fname, header, lines):
    io.open(os.path.join(D, fname + '.csv'), 'w', encoding='utf-8-sig', newline='').write(
        '\r\n'.join([','.join(header)] + lines) + '\r\n')


# ── ① AttackIdMap ─────────────────────────────────────────────────────────
ap = pi.parse(os.path.join(pi.ROOTS['van'], 'AtkParam_Pc.param'))
ap_ids = [r[0] for r in ap['rows']]
_, ap_rows = rows_of('AtkParam_Pc')
ap_names = [r[0] for r in ap_rows]
if len(ap_ids) != len(ap_names):
    sys.exit('AtkParam_Pc 行数不一致 raw=%d csv=%d —— 行序对应不成立' % (len(ap_ids), len(ap_names)))
if len(set(ap_ids)) != len(ap_ids):
    sys.exit('AtkParam_Pc 行 id 有重复，映射不唯一')

write_csv('AttackIdMap', ['Name', 'RowName'],
          ['%d,%s' % (ap_ids[i], ap_names[i]) for i in range(len(ap_names))])
write_struct('AttackIdMap', 'FAttackIdMapRow', 'AC6 无此表，本项目自建；用途见 build_combat_tables.py',
             [('对应的 AtkParam_Pc 行名', 'FName', 'RowName', 'NAME_None')], len(ap_names))
print('AttackIdMap     %d 行  id 范围 %d ~ %d' % (len(ap_names), min(ap_ids), max(ap_ids)))

# ── ② BulletCombat ────────────────────────────────────────────────────────
bu = pi.parse(os.path.join(pi.ROOTS['van'], 'Bullet.param'))
_, bu_rows = rows_of('Bullet')
bu_names = [r[0] for r in bu_rows]
if bu['rowcount'] != len(bu_names):
    sys.exit('Bullet 行数不一致 raw=%d csv=%d' % (bu['rowcount'], len(bu_names)))

BF = field_offsets('BulletParam')
# 偏移**一律查表**，不写字面量（见 paramdex_fields 的说明）
COLS = [
    ('AtkIdBullet',    'atkId_Bullet',    '<i', 'int32', '指向 AtkParam_Pc 的行 id  (paramdex: atkId_Bullet 攻撃ID)'),
    ('InitVellocityMS','initVellocity',   '<f', 'float', '初速[m/s]  (paramdex: initVellocity)'),
    ('MaxVellocityMS', 'maxVellocity',    '<f', 'float', '最高速度[m/s]  (paramdex: maxVellocity)'),
    ('LifeSec',        'life',            '<f', 'float', '寿命[s]  (paramdex: life)'),
    ('DistM',          'dist',            '<f', 'float', '有效射程[m]  (paramdex: dist)'),
    ('GravityInMS2',   'gravityInRange',  '<f', 'float', '射程内重力[m/s^2]  (paramdex: gravityInRange)'),
    ('GravityOutMS2',  'gravityOutRange', '<f', 'float', '射程外重力[m/s^2]  (paramdex: gravityOutRange)'),
    ('HitRadiusM',     'hitRadius',       '<f', 'float', '弹药半径[m]  (paramdex: hitRadius 初期弾半径)'),
    ('NumShoot',       'numShoot',        '<H', 'int32', '同时发射数  (paramdex: numShoot u16)'),
    ('HomingAngleDPS', 'homingAngle',     '<h', 'float', '诱导性能[deg/s]  (paramdex: homingAngle s16)'),
    # ★ AC6 的"开火补正角锥"（P7 §2.3）：子弹允许被折向锁定目标的最大角度。
    #   实测众数：水平 15°（228/568）、垂直 25°（104/568）；346/568 与 348/568 非零。
    #   这条字段是"看起来瞄得很准却打不中"与"轻武器比重武器更粘"两个现象的直接来源。
    ('LockShootLimitAngH',  'lockShootLimitAng',   '<B', 'int32', '开火补正角度 水平[deg]  (paramdex: lockShootLimitAng u8)'),
    ('LockShootLimitAngV',  'lockShootLimitAng_V', '<B', 'int32', '开火补正角度 垂直[deg]  (paramdex: lockShootLimitAng_V u8)'),
]
missing = [c[1] for c in COLS if c[1] not in BF]
if missing:
    sys.exit('paramdex 里找不到这些 Bullet 字段，拒绝生成: %s' % missing)

ap_id_set = set(ap_ids)
hit = 0
lines = []
for i, n in enumerate(bu_names):
    cells = []
    for out_name, pd_name, fmt, _ct, _doc in COLS:
        o = BF[pd_name][0]
        v = val(bu, i, o, fmt)
        if out_name == 'AtkIdBullet':
            v = int(v or 0)
            if v in ap_id_set:
                hit += 1
        elif _ct == 'int32':
            v = int(v or 0)
        else:
            v = float(v or 0.0)
        cells.append(v)
    lines.append(n + ',' + ','.join(('%d' % c) if isinstance(c, int) else ('%.4f' % c) for c in cells))

write_csv('BulletCombat', ['Name'] + [c[0] for c in COLS], lines)
write_struct('BulletCombat', 'FBulletCombatRow',
             'AC6 有此表；本项目从 raw .param 抽出第 2 批需要的列，偏移取自 paramdex',
             [(c[4], c[3], c[0], '0') for c in COLS], len(bu_names))
print('BulletCombat    %d 行  atkId 命中 AtkParam_Pc 行 id 的 = %d (%.1f%%)'
      % (len(bu_names), hit, 100.0 * hit / max(1, len(bu_names))))
print('   列偏移（取自 paramdex）: ' + ', '.join('%s@%d' % (c[1], BF[c[1]][0]) for c in COLS))

# ── 自证 ──────────────────────────────────────────────────────────────────
id2name = {ap_ids[i]: ap_names[i] for i in range(len(ap_names))}
for probe in ('Proto_Vertical_missile', 'machine_gun', 'assault_rifle', 'bazooka', 'grenade_rifle', 'shotgun'):
    if probe in bu_names:
        i = bu_names.index(probe)
        aid = int(val(bu, i, 4, '<i') or 0)
        print('  自证 %-24s atkId=%-9d -> %s' % (probe, aid, id2name.get(aid, '未命中')))
