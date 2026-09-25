# -*- coding: utf-8 -*-
"""P7 手感：按 paramdex 字段名从 .param 读值。用法: python tools/_p7dump.py <表> <字段1,字段2,...> [van] [--hist]"""
import os, re, sys, struct, importlib.util
from _f7 import fmtnum
import xml.etree.ElementTree as ET
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
sys.path.insert(0, r'./tools')
import paramdex_fields as pf

PD = pf.PD
def build(tbl):
    pdname = tbl
    for cand in [tbl, tbl.replace('_Pc','').replace('_PC','').replace('_Npc',''), tbl+'Param', tbl.replace('Param','')]:
        if os.path.exists(os.path.join(PD,'Defs',cand+'.xml')): pdname=cand; break
    p = os.path.join(PD,'Defs',pdname+'.xml')
    if not os.path.exists(p):
        import glob
        c=[f for f in glob.glob(os.path.join(PD,'Defs','*.xml')) if tbl.lower()[:8] in os.path.basename(f).lower()]
        if c: p=c[0]; pdname=os.path.basename(c[0])[:-4]
    fl,total = pf.fields_of(p)
    return pdname, fl, total

def readfield(par, off, typ, name):
    b = par['b']; ds = par['datastart']; rs = par['rowsize']
    n = par['rowcount']
    fmtmap={'u8':'B','s8':'b','u16':'H','s16':'h','u32':'I','s32':'i','f32':'f','angle32':'i'}
    out=[]
    arr = re.search(r'\[(\d+)\]$', name)
    cnt = int(arr.group(1)) if arr else 1
    base = typ
    if typ in ('dummy8',): return None
    if typ not in fmtmap: return None
    sz = pf.TYPE_SIZE[typ]
    for i in range(n):
        vals=[]
        ok=True
        for k in range(min(cnt,4)):
            o = ds + i*rs + off + k*sz
            if o+sz>len(b): ok=False; break
            vals.append(struct.unpack_from('<'+fmtmap[typ], b, o)[0])
        if ok: out.append(vals)
    return out

if __name__=='__main__':
    tbl=sys.argv[1]; names=[x for x in sys.argv[2].split(',') if x]
    sub='van'
    for a in sys.argv[3:]:
        if a in pi.ROOTS: sub=a
    pdname, fl, total = build(tbl)
    path=os.path.join(pi.ROOTS[sub], tbl+'.param')
    if not os.path.exists(path):
        import glob
        cands=[pdname, pdname+'Param', tbl+'_Pc', tbl+'_PC', tbl+'_Npc', tbl+'_NPC', tbl.replace('Param','')]
        for c in cands:
            q=os.path.join(pi.ROOTS[sub], c+'.param')
            if os.path.exists(q): path=q; break
        else:
            g=[f for f in glob.glob(os.path.join(pi.ROOTS[sub],'*.param')) if os.path.basename(f).lower().startswith(tbl.lower()[:6])]
            if g: path=g[0]
    par=pi.parse(path)
    print('# 表 %s  (paramdex %s.xml, 结构%dB)  文件 %s' % (tbl, pdname, total, os.path.basename(path)))
    print('# 行数=%d 行宽=%d  data起点=%d' % (par['rowcount'], par['rowsize'], par['datastart']))
    idx={n:o for o,t,n,d in [(f[0],f[1],f[2],f[3]) for f in fl]}
    typ={n:t for o,t,n,d in fl}
    for nm in names:
        cand=[k for k in idx if k==nm or k.startswith(nm)]
        if not cand: print('  !! 未找到字段 %s' % nm); continue
        for c in cand:
            v=readfield(par, idx[c], typ[c], c)
            if v is None: print('  -- %s : 无法读取(类型%s)'%(c,typ[c])); continue
            flat=[x[0] for x in v]
            nz=[x for x in flat if x!=0]
            hist={}
            for x in flat: hist[x]=hist.get(x,0)+1
            top=sorted(hist.items(), key=lambda kv:-kv[1])[:12]
            print('  %-44s @%-5d %-5s  min=%-10s max=%-10s 非零=%d/%d' % (c, idx[c], typ[c], fmtnum(min(flat)), fmtnum(max(flat)), len(nz), len(flat)))
            print('       top值: %s' % ', '.join('%s×%d'%(fmtnum(k),n) for k,n in top))
