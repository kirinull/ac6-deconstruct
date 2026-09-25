# -*- coding: utf-8 -*-
"""audit_table_usage.py —— 判定 257 张 AC6 param 表「到底是不是 AC6 在用的」。

为什么需要它
------------
本项目的「第 6 坑 = 遗留表陷阱」已经踩过三次（GameAreaParam 是魂1数据、
PlayRegionParam 是魂3、NpcAiActionParam 行名是 R1攻撃）。这些表**结构合法、
数据非空**，所以任何只看「有没有数据」的检查都会把它们当成 AC6 机制。

本项目也踩过更隐蔽的一次：**靠表名是否出现在文档里**来判断「这张表有没有被拆过」。
那个方法不成立——索引清单里罗列一次也算命中；加进不同语料，「未提及」数会在
37 / 31 / 0 之间跳（0 是循环论证，因为语料里包含了表清单本身）。

本脚本改用三条**可证伪**的判据：

  ① 结构自洽  行宽是否与 paramdex 期望一致（不一致 → def 匹配错了，结论不可用）
  ② 内容空壳  所有非 padding 字段的最大「非零非哨兵」率
  ③ 外键自洽  按 paramdex 日文显示名把字段映射到目标表，
              再统计该字段的取值在**目标表行 ID**里的命中率

判别逻辑：
  · 命中率 = 0% 且样本足够            → LEFTOVER  遗留嫌疑（最硬的信号）
  · 最大非零率 = 0                    → EMPTY     空壳表
  · 其余                              → IN_USE    在用

⚠️ 注意：全局 ID 空间（把所有表的行 ID 并起来）**不能**用作判据——
实测 36507 个 ID 让 1050/1090/1100 这类小值到处偶然命中，区分度为零。
必须按字段语义绑定到**特定目标表**。

用法：
    python tools/audit_table_usage.py                 # 控制台摘要
    python tools/audit_table_usage.py --csv out.csv   # 附导出
    python tools/audit_table_usage.py --table ThrowParam   # 单表详情
"""
import os
import io
import re
import sys
import glob
import struct
import importlib.util
import collections

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pi = _load('pi', os.path.join(_HERE, 'param_inspect.py'))
pf = _load('pf', os.path.join(_HERE, 'paramdex_fields.py'))

DEFS_DIR = os.path.join(pf.PD, 'Defs')

# ── 不参与内容统计的类型/名字 ────────────────────────────────
PAD_TYPES = {'dummy8', 'fixstr', 'fixstrW'}
PAD_PREFIX = ('pad', 'reserved', 'dummy', 'dmy', 'disableParam')

# ── 外键规则：paramdex 日文显示名关键词 -> 目标 ID 空间名 ─────
# 目标空间见 SPACE_BUILDERS。只保留「ID 空间本机可查」的规则。
FK_RULES = [
    (('キャラID', 'キャラＩＤ'), 'CHR'),
    (('武器ID',), 'WEAPON'),
    (('防具ID', 'パーツID'), 'PROTECTOR'),
    (('弾丸ID', '弾ID'), 'BULLET'),
    (('ジェネレータID',), 'GENERATOR'),
    (('ブースタID',), 'BOOSTER'),
    (('FCS ID', 'ＦＣＳ'), 'FCS'),
]

# ── 角色 ID 联合空间 ─────────────────────────────────────────
# 教训：把「キャラID」类字段只对 NpcParam 验，会得到大量**假阳性遗留**。
# 实测 NpcParam.RetargetReferenceChrId = 3000/3020/3400 三个值，
#   对 NpcParam 命中 0/117（0.0%），看似遗留；
#   对「角色联合空间」命中 117/117（100.0%）—— 完全合法。
# 原因：角色 ID 同时出现在多张「按角色索引」的表里（模型/转向/AI/材质/音效…），
#       NpcParam 只是其中之一。所以判据必须用**联合空间**，不能用单表。
CHR_INDEX_TABLES = [
    'ChrModelParam', 'ChrActTurnParam', 'ChrActTurnParam_Npc', 'NpcThinkParam',
    'NpcMaterialParam', 'AiSoundParam', 'RuntimeSoundParam_Npc',
    'AttackActionParam_NPC', 'EquipParamWeapon_Npc', 'BehaviorParam_NPC',
]

# ── 子弹 ID 也是双轨的 ───────────────────────────────────────
# 教训（与 CHR 同型）：Bullet（玩家，568 行）与 Bullet_Npc（2537 行）是**两套独立
# ID 空间，交集只有 12 个**。把 NPC 侧表的外键只对 Bullet 验，会得到假阳性遗留：
#   Bullet_Npc.intervalCreateBulletId 对 Bullet 命中 0/111 = 0.0%（看似遗留）
#                                     对并集命中 111/111 = 100.0%（完全合法）
BULLET_TABLES = ['Bullet', 'Bullet_Npc']

# ── 字段级「废弃」标记 ───────────────────────────────────────
# paramdex 的 DisplayName/Description 里会写明字段已废弃（日文原文）。
# 这类字段**值不再维护**，所以拿它做外键检验会得到无意义的低命中率。实测：
#   LookAtParam.predictionBulletId 显示名 = "【廃止予定】ターゲット予測に用いる弾丸ID"
# → 该字段 77% 命中纯属偶然，不是「表遗留」。
# 关键区分：**字段级废弃 ≠ 表级遗留**。这是两个不同的结论，不能混。
DEPRECATED_MARKERS = ('廃止', '未使用', '使用しない')


def is_deprecated_field(disp, desc=''):
    t = (disp or '') + '|' + (desc or '')
    return any(m in t for m in DEPRECATED_MARKERS)


_DEP_CACHE = {}


def deprecated_fields_of(defname):
    """返回该参数定义里被标注为废弃/未使用的字段名集合。"""
    if defname in _DEP_CACHE:
        return _DEP_CACHE[defname]
    out = set()
    p = os.path.join(DEFS_DIR, defname + '.xml') if defname else ''
    if p and os.path.exists(p):
        s = io.open(p, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'<Field Def="([^"]+)">(.*?)</Field>', s, re.S):
            # ⚠️ Def 可能带默认值：`s32 predictionBulletId = -1`
            #    用 split()[-1] 取名字会拿到 '-1'（实测踩过），必须先按类型切、再按 '=' 切。
            mm = re.match(r'^([A-Za-z0-9_]+)\s+(.+)$', m.group(1).strip())
            if not mm:
                continue
            nm = mm.group(2).split('=')[0].strip()
            nm = nm.split(':')[0].split('[')[0].strip()
            if not nm or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', nm):
                continue
            body = m.group(2)
            dn = re.search(r'<DisplayName>([^<]*)</DisplayName>', body)
            de = re.search(r'<Description>([^<]*)</Description>', body)
            if is_deprecated_field(dn.group(1) if dn else '',
                                   de.group(1) if de else ''):
                out.add(nm)
    _DEP_CACHE[defname] = out
    return out

# 唯一值太少的字段不参与遗留判定：那是**系统性引用**（少数几个确定的 ID），
# 而不是「一堆指向陌生 ID 体系的散值」。实测 RetargetReferenceChrId 唯一值 = 3。
MIN_UNIQUE_FOR_LEFTOVER = 5

# 遗留判定阈值（**启发式，不是硬事实**）。报告必须同时给出原始命中率，
# 让读者能自己复核，而不是只接受一个标签。
LEFTOVER_RATE_THRESHOLD = 0.50

MAX_FIELDS = 48       # 每表最多检查的字段数（控时）
MAX_ROWS = 3000       # 每表最多检查的行数
MIN_FK_SAMPLE = 5     # 外键判定所需最少非零样本


# ══════════════════════════════════════════════════════════════
# def 索引：只解析 paramdex 一次，按「名字」与「结构大小」双路匹配
# ══════════════════════════════════════════════════════════════
_DEFS = None


def all_defs():
    global _DEFS
    if _DEFS is None:
        _DEFS = {}
        for p in sorted(glob.glob(os.path.join(DEFS_DIR, '*.xml'))):
            n = os.path.basename(p)[:-4]
            try:
                fl, sz = pf.fields_of(p)
            except Exception:
                continue
            _DEFS[n] = (fl, sz)
    return _DEFS


def find_def(tbl, rowsize):
    """返回 (def_name, fields, size, how) —— how 说明是靠名字还是靠尺寸匹配上的。"""
    defs = all_defs()
    cands = [tbl]
    for suf in ('_Pc', '_PC', '_Npc', '_NPC', '_pc', '_npc'):
        if tbl.endswith(suf):
            cands.append(tbl[:-len(suf)])
    cands += [tbl + 'Param', tbl.replace('Param', '')]
    # 平台后缀（LoadBalancer*_xb1x 等）
    for plat in ('_xb1x', '_xsx', '_xb1', '_xss', '_ps4'):
        if tbl.endswith(plat):
            cands.append(tbl[:-len(plat)])
    for c in cands:
        if c in defs:
            fl, sz = defs[c]
            if sz == rowsize:
                return c, fl, sz, 'name+size'
    # 名字没中：按结构大小唯一反查
    hits = [(n, fl, sz) for n, (fl, sz) in defs.items() if sz == rowsize]
    if len(hits) == 1:
        return hits[0][0], hits[0][1], hits[0][2], 'size-only'
    for c in cands:                       # 退一步：名字中但尺寸不符
        if c in defs:
            fl, sz = defs[c]
            return c, fl, sz, 'name(size diff %+d)' % (sz - rowsize)
    return None, None, None, 'unmatched'


# ══════════════════════════════════════════════════════════════
# 内容画像
# ══════════════════════════════════════════════════════════════
def content_profile(param, fields):
    """返回 (最大非零率, 检查字段数, 检查行数)。非零 = 既不是 0 也不是 -1 哨兵。"""
    bf = pf.bitfield_map(fields)
    ds, rs, buf = param['datastart'], param['rowsize'], param['b']
    nrows = min(param['rowcount'], MAX_ROWS)
    if nrows <= 0 or rs <= 0:
        return 0.0, 0, 0
    best = 0.0
    checked = 0
    for off, typ, name, disp in fields:
        base = name.split(':')[0].split('[')[0]
        if typ in PAD_TYPES:
            continue
        if any(base.startswith(x) for x in PAD_PREFIX):
            continue
        if checked >= MAX_FIELDS:
            break
        checked += 1
        try:
            if base in bf:
                vs = pf.read_bitfield(param, bf[base])[:nrows]
            else:
                fmt = '<' + pf.TYPE_FMT.get(typ, 'i')
                sz = pf.TYPE_SIZE.get(typ, 4)
                vs = []
                for i in range(nrows):
                    o = ds + i * rs + off
                    if o + sz > len(buf):
                        break
                    vs.append(struct.unpack_from(fmt, buf, o)[0])
        except Exception:
            continue
        if not vs:
            continue
        nz = sum(1 for v in vs if v not in (0, -1))
        best = max(best, nz / float(len(vs)))
    return best, checked, nrows


def column_values(param, fields, target):
    """取某字段的全部值（支持位域）。"""
    bf = pf.bitfield_map(fields)
    for off, typ, name, disp in fields:
        base = name.split(':')[0].split('[')[0]
        if base != target:
            continue
        if base in bf:
            return pf.read_bitfield(param, bf[base])
        fmt = '<' + pf.TYPE_FMT.get(typ, 'i')
        sz = pf.TYPE_SIZE.get(typ, 4)
        out = []
        ds, rs, buf = param['datastart'], param['rowsize'], param['b']
        for i in range(param['rowcount']):
            o = ds + i * rs + off
            if o + sz > len(buf):
                break
            out.append(struct.unpack_from(fmt, buf, o)[0])
        return out
    return None


def fk_target_for(fields, dep=None):
    """找出本表的外键字段与目标空间。返回 [(field, space, disp, is_deprecated), ...]

    `dep` = 该表被标注为废弃的字段名集合。废弃字段值不再维护，
    **不参与遗留判定**（否则会把「字段废弃」误判成「整表遗留」）。
    """
    dep = dep or set()
    out = []
    for off, typ, name, disp in fields:
        base = name.split(':')[0].split('[')[0]
        if typ in PAD_TYPES or any(base.startswith(x) for x in PAD_PREFIX):
            continue
        for kws, space in FK_RULES:
            if any(k in disp for k in kws):
                out.append((base, space, disp, base in dep))
                break
    return out


def build_spaces(per):
    """构造各目标 ID 空间。CHR 与 BULLET 都是**多表联合**（见上方注释的实测依据）。"""
    def union(names):
        s = set()
        for t in names:
            s |= per.get(t, set())
        return s

    spaces = {
        'NpcParam': per.get('NpcParam', set()),
        'WEAPON': union(['EquipParamWeapon', 'EquipParamWeapon_Npc']),
        'PROTECTOR': per.get('EquipParamProtector', set()),
        'BULLET': union(BULLET_TABLES),
        'GENERATOR': per.get('EquipParamGenerator', set()),
        'BOOSTER': per.get('EquipParamBooster', set()),
        'FCS': per.get('EquipParamFcs', set()),
    }
    spaces['CHR'] = union(CHR_INDEX_TABLES)
    spaces['_CHR_TABLES'] = [t for t in CHR_INDEX_TABLES if t in per]
    spaces['_BULLET_TABLES'] = [t for t in BULLET_TABLES if t in per]
    return spaces


# ══════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════
def id_sets():
    """每张表的行 ID 集合（判外键用）。"""
    out = {}
    for f in sorted(glob.glob(os.path.join(pi.ROOTS['van'], '*.param'))):
        name = os.path.basename(f)[:-6]
        try:
            p = pi.parse(f)
        except Exception:
            continue
        out[name] = set(r[0] for r in p['rows'])
    return out


def raw_nonzero_rate(param, max_rows=300):
    """不需要参数定义：整行原始字节里非零字节的占比（用于 NO_DEF 表的粗判）。"""
    ds, rs, buf = param['datastart'], param['rowsize'], param['b']
    if rs <= 0:
        return 0.0
    tot = nz = 0
    for i in range(min(param['rowcount'], max_rows)):
        o = ds + i * rs
        if o + rs > len(buf):
            break
        chunk = buf[o:o + rs]
        tot += len(chunk)
        nz += sum(1 for b in chunk if b != 0)
    return (nz / float(tot)) if tot else 0.0


def audit():
    per = id_sets()
    spaces = build_spaces(per)
    rows = []
    for f in sorted(glob.glob(os.path.join(pi.ROOTS['van'], '*.param'))):
        tbl = os.path.basename(f)[:-6]
        rec = dict(table=tbl, rows=0, rowsize=0, defname='', match='', maxnz=0.0,
                   fk_field='', fk_space='', fk_rate=None, fk_hit=0, fk_n=0,
                   fk_narrow=None, fk_unique=0, note='', verdict='',
                   dep_count=0, fk_skipped_deprecated='')
        try:
            p = pi.parse(f)
        except Exception as e:
            rec.update(verdict='PARSE_FAIL', note=str(e)[:60])
            rows.append(rec)
            continue
        rec['rows'], rec['rowsize'] = p['rowcount'], p['rowsize']

        defname, fields, defsize, how = find_def(tbl, p['rowsize'])
        rec['defname'], rec['match'] = defname or '', how

        if fields is None:
            # 无参数定义：外键无法验证，但可粗判内容是否为空
            rec['maxnz'] = raw_nonzero_rate(p)
            rec['verdict'] = 'EMPTY' if rec['maxnz'] == 0.0 else 'NO_DEF'
            rec['note'] = '字节非零率 %.1f%%（无 def，外键不可验）' % (rec['maxnz'] * 100)
            rows.append(rec)
            continue

        rec['maxnz'], nchk, nrow = content_profile(p, fields)
        rec['note'] = '%d 字段/%d 行' % (nchk, nrow)

        # 逐个外键字段核验；取「命中率最低」的一个作为本表代表（最可疑）。
        # 被标注废弃的字段直接跳过：它值不再维护，低命中率没有诊断意义。
        dep = deprecated_fields_of(defname) if defname else set()
        rec['dep_count'] = len(dep)
        cands = []
        skipped_dep = []
        for base, space, disp, isdep in fk_target_for(fields, dep):
            if isdep:
                skipped_dep.append(base)
                continue
            target_ids = spaces.get(space)
            if not target_ids:
                continue
            vs = column_values(p, fields, base)
            if not vs:
                continue
            nz = [v for v in vs if v not in (0, -1)]
            if len(nz) < MIN_FK_SAMPLE:
                continue
            hit = sum(1 for v in nz if v in target_ids)
            cands.append((hit / float(len(nz)), len(nz), base, space, hit,
                          len(set(nz)), disp))
        rec['fk_skipped_deprecated'] = ','.join(skipped_dep)
        if cands:
            cands.sort(key=lambda x: (x[0], -x[1]))
            rate, n, base, space, hit, uniq, disp = cands[0]
            rec.update(fk_field=base, fk_space=space, fk_rate=rate,
                       fk_hit=hit, fk_n=n, fk_unique=uniq)
            # 若是角色类字段，额外记录「只对 NpcParam 单表」的命中率，
            # 用来暴露「目标空间选错」这一类假阳性
            if space == 'CHR':
                npc = spaces.get('NpcParam') or set()
                rec['fk_narrow'] = sum(1 for v in
                                       [x for x in column_values(p, fields, base)
                                        if x not in (0, -1)] if v in npc) / float(n)
            rec['note'] += '  FK %s->%s %d/%d=%.0f%% (唯一值%d)' % (
                base, space, hit, n, rate * 100, uniq)

        # ── 判决 ──
        # 阈值是**启发式**，报告里必须同时给出原始命中率供复核，不能只给标签。
        if rec['maxnz'] == 0.0:
            rec['verdict'] = 'EMPTY'
        elif (rec['fk_rate'] is not None
              and rec['fk_rate'] < LEFTOVER_RATE_THRESHOLD
              and rec['fk_n'] >= MIN_FK_SAMPLE
              and rec['fk_unique'] >= MIN_UNIQUE_FOR_LEFTOVER):
            rec['verdict'] = 'LEFTOVER'
        else:
            rec['verdict'] = 'IN_USE'
        rows.append(rec)
    return rows, spaces


def main():
    argv = sys.argv[1:]
    per = id_sets()
    spaces = build_spaces(per)

    if '--table' in argv:
        tbl = argv[argv.index('--table') + 1]
        p = pi.parse(os.path.join(pi.ROOTS['van'], tbl + '.param'))
        dn, fields, dsz, how = find_def(tbl, p['rowsize'])
        print('表 %s : %d 行 x %d 字节' % (tbl, p['rowcount'], p['rowsize']))
        print('def 匹配: %s  (%s)  期望 %s' % (dn, how, dsz))
        if fields is None:
            print('无 def，无法继续（字节非零率 %.1f%%）' % (raw_nonzero_rate(p) * 100))
            return
        nz, nchk, nrow = content_profile(p, fields)
        print('内容画像: 最大非零率 %.1f%%  (检查 %d 字段 / %d 行)' % (nz * 100, nchk, nrow))
        dep = deprecated_fields_of(dn) if dn else set()
        if dep:
            print('★ 本表有 %d 个字段被 paramdex 标注为废弃/未使用: %s'
                  % (len(dep), ', '.join(sorted(dep)[:10])))
        print()
        print('  外键字段核验 —— 同时给出「联合空间」与「只对 NpcParam 单表」两个口径，')
        print('  用来暴露「目标空间选错」造成的假阳性：')
        for base, space, disp, isdep in fk_target_for(fields, dep):
            vs = column_values(p, fields, base)
            if not vs:
                continue
            good = [v for v in vs if v not in (0, -1)]
            if not good:
                continue
            tids = spaces.get(space) or set()
            hit = sum(1 for v in good if v in tids)
            tag = '  [已标注废弃 → 不参与遗留判定]' if isdep else ''
            print('   %-22s -> %-9s %4d/%4d = %6.1f%%  唯一值%3d  (%s)%s'
                  % (base, space, hit, len(good), 100.0 * hit / len(good),
                     len(set(good)), disp, tag))
            if space == 'CHR' and not isdep:
                npc = spaces.get('NpcParam') or set()
                h2 = sum(1 for v in good if v in npc)
                print('   %-22s    只对 NpcParam 单表  %4d/%4d = %6.1f%%   <-- 若此处为 0%%'
                      ' 而上一行很高，说明目标空间必须用联合空间'
                      % ('', h2, len(good), 100.0 * h2 / len(good)))
        return

    rows, spaces = audit()
    tally = collections.Counter(r['verdict'] for r in rows)
    print('=== AC6 param 表使用状态审计 ===')
    print('表总数 %d   （ID 空间：CHR 联合 %d 张表 = %d 个 ID；NpcParam 单表 %d 个）'
          % (len(rows), len(spaces.get('_CHR_TABLES', [])),
             len(spaces.get('CHR') or []), len(spaces.get('NpcParam') or [])))
    for k in ('IN_USE', 'LEFTOVER', 'EMPTY', 'NO_DEF', 'PARSE_FAIL'):
        if tally[k]:
            print('  %-11s %3d' % (k, tally[k]))
    print()

    lo = [r for r in rows if r['verdict'] == 'LEFTOVER']
    print('--- LEFTOVER（遗留嫌疑：外键命中率 < %.0f%% 且唯一值 >= %d）---'
          % (LEFTOVER_RATE_THRESHOLD * 100, MIN_UNIQUE_FOR_LEFTOVER))
    if not lo:
        print('  （无）')
    for r in sorted(lo, key=lambda x: -x['rows']):
        extra = ''
        if r['fk_narrow'] is not None:
            extra = '   [只对 NpcParam 单表: %.1f%%]' % (r['fk_narrow'] * 100)
        print('  %-34s %5d 行  %-22s -> %-6s %5.1f%% (%d/%d, 唯一值 %d)%s'
              % (r['table'], r['rows'], r['fk_field'], r['fk_space'],
                 100.0 * (r['fk_rate'] or 0), r['fk_hit'], r['fk_n'],
                 r['fk_unique'], extra))
    print()

    print('--- EMPTY（空壳：所有检查字段全 0 或全 -1）---')
    em = [r for r in rows if r['verdict'] == 'EMPTY']
    if not em:
        print('  （无）')
    for r in sorted(em, key=lambda x: -x['rows']):
        print('  %-40s %5d 行  %s' % (r['table'], r['rows'], r['note']))
    print()

    nd = [r for r in rows if r['verdict'] == 'NO_DEF']
    print('--- NO_DEF（无参数定义：外键不可验证，但内容非空）--- 共 %d 张' % len(nd))
    for r in sorted(nd, key=lambda x: -x['rows'])[:12]:
        print('  %-42s %5d 行 x %4d B' % (r['table'], r['rows'], r['rowsize']))
    if len(nd) > 12:
        print('  ... 还有 %d 张（完整清单见 --csv 输出）' % (len(nd) - 12))
    print()

    pf_ = [r for r in rows if r['verdict'] == 'PARSE_FAIL']
    if pf_:
        print('--- PARSE_FAIL ---')
        for r in pf_:
            print('  %-40s %s' % (r['table'], r['note']))
        print()

    # ── 字段级废弃清单（与「表级遗留」是两个不同的结论，必须分开报）──
    dep_tables = [(r['table'], r['defname'], r['dep_count'])
                  for r in rows if r['dep_count']]
    dep_tables.sort(key=lambda x: -x[2])
    n_dep = sum(c for _, _, c in dep_tables)
    print('--- 字段级「废弃/未使用」标注（paramdex 原文，全库共 %d 个字段 / %d 张表）---'
          % (n_dep, len(dep_tables)))
    print('    注意：这是**字段级**结论，不等于「整表遗留」。取值前必须排除这些字段。')
    for t, d, c in dep_tables:
        print('  %-34s def=%-28s %2d 个' % (t, d, c))
    print()

    if '--csv' in argv:
        out = argv[argv.index('--csv') + 1]
        import csv
        with open(out, 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.writer(fh)
            w.writerow(['table', 'verdict', 'rows', 'rowsize', 'def', 'def_match',
                        'max_nonzero_rate', 'fk_field', 'fk_space', 'fk_hit',
                        'fk_samples', 'fk_rate', 'fk_unique', 'fk_narrow_rate',
                        'deprecated_field_count', 'fk_skipped_deprecated'])
            for r in rows:
                w.writerow([r['table'], r['verdict'], r['rows'], r['rowsize'],
                            r['defname'], r['match'], '%.4f' % r['maxnz'],
                            r['fk_field'], r['fk_space'], r['fk_hit'], r['fk_n'],
                            '' if r['fk_rate'] is None else '%.4f' % r['fk_rate'],
                            r['fk_unique'],
                            '' if r['fk_narrow'] is None else '%.4f' % r['fk_narrow'],
                            r['dep_count'], r['fk_skipped_deprecated']])
        print('CSV 已写出: %s' % out)


if __name__ == '__main__':
    main()
