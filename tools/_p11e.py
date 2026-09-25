# -*- coding: utf-8 -*-
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi, paramdex_fields as pf
V = r'./ac6_merge/van/regulation-bin'
M = r'./ac6_merge/mob/regulation-bin'
D = r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs/'
def rows(t, root=V):
    p = os.path.join(root, t + '.param'); b=open(p,'rb').read(); d=pi.parse(p)
    return [(rid, b[off:off+d['rowsize']], d['rowsize']) for rid, off in d['rows']], d

fl, tot = pf.fields_of(D+'AiSoundParam.xml')
rs, d = rows('AiSoundParam')
print('== AiSoundParam rows=%d rowsize=%d struct=%d ==' % (len(rs), rs[0][2], tot))
bf = pf.bitfield_map(fl)
for rid, r, _ in rs[:12]:
    parts=[]
    for f in fl:
        o,ty,nm,disp = f
        if ty=='f32': v=struct.unpack_from('<f', r, o)[0]
        elif ty=='s32': v=struct.unpack_from('<i', r, o)[0]
        elif ty=='u8': v=r[o]
        else: continue
        parts.append('%s=%s' % (nm, round(v,2) if isinstance(v,float) else v))
    print('  [%-4s] %s' % (rid, ' '.join(parts)))
for k,(bo,bs,bw) in bf.items():
    c=sum(1 for _,r,_ in rs if (r[bo]>>bs)&1)
    print('   bit %-20s 置位 %d/%d' % (k, c, len(rs)))
print()
print('== PadRumble (CAMERA_RUMBLE_PARAM_ST) 174x84 ==')
fl2, tot2 = pf.fields_of(D+'CameraRumbleParam.xml')
rs2, d2 = rows('PadRumble')
print(' struct=%d rowsize=%d' % (tot2, rs2[0][2]))
def col(nm):
    for o,ty,n,_ in fl2:
        if n==nm:
            fmt={'f32':'<f','s16':'<h','u8':'<B'}[ty]
            return [struct.unpack_from(fmt, r, o)[0] for _,r,_ in rs2]
    return None
for nm in ['rumbleId','hdPadRumbleId','priority','targetType','lifeTimeSec','fovApplyType']:
    v=col(nm); print('  %-16s min=%s max=%s 非零=%d 唯一=%d' % (nm, min(v), max(v), sum(1 for x in v if x), len(set(v))))
for nm in ['beginDist','endDist','stopBeginDist','stopEndDist','stopRate','airRateSelf','landRateSelf','airRateAnother','landRateAnother','timeChangeRate','changeTime']:
    v=col(nm); print('  %-16s min=%.2f max=%.2f mean=%.2f 唯一=%d' % (nm, min(v), max(v), sum(v)/len(v), len(set(v))))
bf2 = pf.bitfield_map(fl2)
for k,(bo,bs,bw) in bf2.items():
    c=sum(1 for _,r,_ in rs2 if (r[bo]>>bs)&1)
    print('   bit %-20s 置位 %d/%d' % (k, c, len(rs2)))
print()
print('== 其它音效表 ==')
for t, dn in [('AssetMaterialSfxParam','AssetMaterialSfxParam'),('AssetModelSfxParam','AssetModelSfxParam'),
              ('GeneratorTypeSfxIdRplace_PC',None),('CutsceneReplaceSfxParam','CutsceneReplaceSfxParam'),
              ('SfxModelParam','SfxModelParam')]:
    rs3, d3 = rows(t)
    allv = collections.Counter()
    for _,r,_ in rs3:
        for i in range(0, min(len(r), 128), 4):
            v=struct.unpack_from('<i', r, i)[0]
            if v>0: allv[v]+=1
    print('  %-28s rows=%d rowsize=%d 非零槽位数=%d 唯一SfxId=%d' % (t, len(rs3), rs3[0][2], sum(allv.values()), len(allv)))
