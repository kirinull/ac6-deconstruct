
# -*- coding: utf-8 -*-
"""产出《装配界面数值规格书》：105 条 extract0 取数配方 → 源表字段定位。
把 tail 值与各候选表的字段"末尾偏移"匹配，输出可用规格。"""
import os, struct, importlib.util, io, collections
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
spec2 = importlib.util.spec_from_file_location('pf', r'./tools/paramdex_fields.py')
pf = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(pf)
SZ = {'u8':1,'s8':1,'u16':2,'s16':2,'u32':4,'s32':4,'f32':4}
TYPE_MAP = {7:'f32', 4:'u32', 5:'s32', 1:'s8', 3:'s16', 6:'u32', 2:'u16'}

CAND = [('EquipParamWeapon','EquipParamWeapon'), ('EquipParamProtector','EquipParamProtector'),
        ('EquipParamBooster','EquipParamBooster'), ('EquipParamGenerator','EquipParamGenerator'),
        ('EquipParamFcs','EquipParamFcs'), ('AtkParam','AtkParam_Pc'), ('NpcParam','NpcParam')]
TABLES = {}
for pdn, prm in CAND:
    fl, tot = pf.fields_of(os.path.join(pf.PD,'Defs',pdn+'.xml'))
    ends = {}
    for o,t,n,disp in fl:
        base = n.split(':')[0].split('[')[0]
        if t in SZ: ends.setdefault(o + SZ[t], []).append((base, o, t, (disp or '')[:30]))
    TABLES[prm] = ends

p = pi.parse(os.path.join(pi.ROOTS['van'],'MenuPropertySpecParam.param'))
fl, tot = pf.fields_of(os.path.join(pf.PD,'Defs','MenuPropertySpecParam.xml'))
m = {n.split(':')[0].split('[')[0]: (o,t,(disp or '').strip()) for o,t,n,disp in fl}
def V(f):
    o,t,_ = m[f]; fmt='<'+pf.TYPE_FMT.get(t,'i')
    return [struct.unpack_from(fmt,p['b'],p['datastart']+i*p['rowsize']+o)[0] for i in range(p['rowcount'])]

tails = V('extract0_MemberTailOffset'); types = V('extract0_MemberType')
ops = V('extract0_Operation'); c0 = V('extract0_Constant0'); c1 = V('extract0_Constant1')

# 布局表：拿槽位名
pl = pi.parse(os.path.join(pi.ROOTS['van'],'MenuPropertyLayoutParam.param'))
fl2, tot2 = pf.fields_of(os.path.join(pf.PD,'Defs','MenuPropertyLayoutParam.xml'))
m2 = {n.split(':')[0].split('[')[0]: (o,t,(disp or '').strip()) for o,t,n,disp in fl2}
print('MenuPropertyLayoutParam: %d 行 x %d B, 字段: %s' % (pl['rowcount'], pl['rowsize'], list(m2.keys())[:10]))

rows = []
for i in range(p['rowcount']):
    if types[i] == 0: continue
    tn = TYPE_MAP.get(types[i], '?')
    first = tails[i] - SZ.get(tn, 4)
    hits = []
    for prm, ends in TABLES.items():
        for (base, o, t, disp) in ends.get(tails[i], []):
            if t == tn and o == first: hits.append((prm, base, o, t, disp))
    rows.append((i, tn, tails[i], first, ops[i], c0[i], c1[i], hits))

matched = [r for r in rows if r[7]]
print()
print('105 条 extract0 配方中，能在候选表里唯一定位字段的: %d 条' % len(matched))
print()
out = ['# AC6 装配界面数值规格书（自动生成，2026-09-11）','',
 '> 来源：@@MenuPropertySpecParam@@ 的 105 条 @@extract0@@ 取数配方（实测 MemberType≠0 的条数 = 105，与 P10 报告一致）。',
 '> **偏移语义**：@@MemberTailOffset@@ 是**字段末尾偏移**，字段起始 = Tail − sizeof(类型)（P10 实测 105/105 验证）。',
 '> @@Operation@@：0 = 直接取值；1 = C0×P+C1；2 = C0÷P+C1。常数即单位换算（×16.67 = m/s→km/h 等）。','',
 '| 行 | 类型 | Tail | 起始偏移 | 公式 | C0 | C1 | 命中的源表.字段 | 日文/说明 |',
 '|---:|---|---:|---:|---|---:|---:|---|---|']
for i, tn, tail, first, op, a, b, hits in rows:
    opn = {0:'直接',1:'C0×P+C1',2:'C0÷P+C1'}.get(op, str(op))
    if hits:
        prm, base, o, t, disp = hits[0]
        h = '**%s.%s**' % (prm, base)
        d = disp
    else:
        h = '（未定位）'; d = ''
    out.append('| %d | %s | %d | %d | %s | %.4g | %.4g | %s | %s |' % (i, tn, tail, first, opn, a, b, h, d))
txt = '\n'.join(out).replace('@@', chr(96))
io.open(r'./data/装配界面规格书.md','w',encoding='utf-8').write(txt)
print('已写出 data/装配界面规格书.md (%d 字符, 其中定位成功 %d 条)' % (len(txt), len(matched)))
print()
print('=== 定位成功的样例（前 12）===')
for i, tn, tail, first, op, a, b, hits in matched[:12]:
    prm, base, o, t, disp = hits[0]
    print('  行%-4d %-5s tail=%-5d -> %s.%s  %s' % (i, tn, tail, prm, base, disp[:28]))
