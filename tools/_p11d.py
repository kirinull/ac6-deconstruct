# -*- coding: utf-8 -*-
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi, paramdex_fields as pf
V = r'./ac6_merge/van/regulation-bin'
M = r'./ac6_merge/mob/regulation-bin'
def rows(t, root=V):
    p = os.path.join(root, t + '.param'); b=open(p,'rb').read(); d=pi.parse(p)
    return [(rid, b[off:off+d['rowsize']], d['rowsize']) for rid, off in d['rows']], d
fl, tot = pf.fields_of(r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs/HitEffectSfxParam.xml')
rs, d = rows('HitEffectSfxParam')
names = [f[2] for f in fl if f[0] < 100]
print('== HitEffectSfxParam 非空行明细 (SfxId 槽) ==')
for rid, r, _ in rs:
    vals = [(names[i], struct.unpack_from('<i', r, i*4)[0]) for i in range(25)]
    nz = [(n,v) for n,v in vals if v>0]
    if nz:
        bf = pf.bitfield_map(fl)
        nb = sum(1 for k,(bo,bs,bw) in bf.items() if k.startswith('bFollow_') and (r[bo]>>bs)&1)
        print('  [%-4s] %-70s  bFollow=%d' % (rid, ' '.join('%s=%d'%x for x in nz), nb))
print()
print('== HitEffectSfxConceptParam 64 行 ==')
fl2, tot2 = pf.fields_of(r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs/HitEffectSfxConceptParam.xml')
print(' 字段数 %d, 结构 %d 字节' % (len(fl2), tot2))
rs2, d2 = rows('HitEffectSfxConceptParam')
used = 0
for rid, r, _ in rs2:
    vals = [(f[2], struct.unpack_from('<h', r, f[0])[0]) for f in fl2]
    s = ' '.join('%s=%d'%(n,v) for n,v in vals if v>0)
    if s: used += 1
    print('  [%-4s] %s' % (rid, s if s else '(全 0)'))
print(' 非空行数 = %d / %d' % (used, len(rs2)))
