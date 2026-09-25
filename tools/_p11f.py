# -*- coding: utf-8 -*-
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi, paramdex_fields as pf
V = r'./ac6_merge/van/regulation-bin'
D = r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs/'
def rows(t, root=V):
    p = os.path.join(root, t + '.param'); b=open(p,'rb').read(); d=pi.parse(p)
    return [(rid, b[off:off+d['rowsize']], d['rowsize']) for rid, off in d['rows']], d
for t, dn in [('RuntimeSoundExpressionParam_Pc','RuntimeSoundExpressionParam'),('RuntimeSoundExpressionParam_Npc','RuntimeSoundExpressionParam')]:
    fl, tot = pf.fields_of(D+dn+'.xml')
    rs, d = rows(t)
    print('== %s rows=%d rowsize=%d struct=%d ==' % (t, len(rs), rs[0][2], tot))
    def col(nm, fmt):
        for o,ty,n,_ in fl:
            if n==nm: return [struct.unpack_from(fmt, r, o)[0] for _,r,_ in rs]
    for nm, fmt in [('Expression','<B'),('RTPC_OnOff','<B'),('Eval01_Condition','<i'),('ConditionID','<i')]:
        v=col(nm,fmt); c=collections.Counter(v)
        print('  %-18s 唯一=%d  top: %s' % (nm, len(c), c.most_common(8)))
    for nm in ['Eval01_MinValue','Eval01_MaxValue','RTPC_MinValue','RTPC_MaxValue']:
        v=col(nm,'<f'); print('  %-18s min=%.3f max=%.3f 非零=%d' % (nm, min(v), max(v), sum(1 for x in v if x)))
    # 行 ID 分布
    ids=[rid for rid,_,_ in rs]
    print('  行ID: 唯一=%d 前10=%s' % (len(set(ids)), ids[:10]))
    dm=[(o,n) for o,ty,n,_ in fl if 'Dmypoly' in n]
    for nm in [n for _,n in dm]:
        v=col(nm,'<i'); print('  %-18s 非 -1 行数=%d' % (nm, sum(1 for x in v if x!=-1)))
print()
print('== SoundIDSpatialSetting (6 行) ==')
fl2, tot2 = pf.fields_of(D+'SoundIDSpatialSetting.xml')
rs2, d2 = rows('SoundIDSpatialSetting')
for rid, r, _ in rs2:
    print('  [%-3s] SoundID_Type=%d SoundID_No=%d ReflectLv=%d' % (rid,
        struct.unpack_from('<i',r,0)[0], struct.unpack_from('<I',r,4)[0], struct.unpack_from('<b',r,8)[0]))
