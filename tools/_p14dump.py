# -*- coding: utf-8 -*-
"""P14: 逐字节解码 TutorialActJudgeParam / TutorialParam / KnowledgeLoadScreenItemParam / MissionParam"""
import os, re, sys, struct, importlib.util
import xml.etree.ElementTree as ET
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
sys.path.insert(0, r'./tools')
import paramdex_fields as pf

def build(tbl):
    pdname = tbl
    for cand in [tbl, tbl.replace('_Pc',''), tbl+'Param', tbl.replace('Param','')]:
        if os.path.exists(os.path.join(pf.PD,'Defs',cand+'.xml')): pdname=cand; break
    p = os.path.join(pf.PD,'Defs',pdname+'.xml')
    fl,total = pf.fields_of(p)
    return pdname, fl, total

def rows(tbl, sub='van'):
    p = pi.parse(os.path.join(pi.ROOTS[sub], tbl+'.param'))
    _, fl, total = build(tbl)
    b=p['b']; ds=p['datastart']; rs=p['rowsize']
    out=[]
    for i,(rid,idx) in enumerate(p['rows']):
        d = b[ds+i*rs: ds+i*rs+rs]
        out.append((rid, d))
    return p, fl, out

def rd(d, off, typ):
    fm={'u8':'B','s8':'b','u16':'H','s16':'h','u32':'I','s32':'i','f32':'f','u64':'Q','s64':'q'}
    if typ not in fm: return None
    sz=pf.TYPE_SIZE[typ]
    if off+sz>len(d): return None
    return struct.unpack_from('<'+fm[typ], d, off)[0]

def dump(tbl, sub='van'):
    p, fl, rws = rows(tbl, sub)
    print('== %s/%s  行数=%d 行宽=%d data起点=%d' % (sub, tbl, p['rowcount'], p['rowsize'], p['datastart']))
    hdr = ['%s' % n for _,_,n,_ in fl]
    for rid, d in rws:
        vals=[]
        for off,typ,name,disp in fl:
            if ':' in name: continue
            arr = re.search(r'\[(\d+)\]$', name)
            if arr: continue
            v = rd(d, off, typ)
            vals.append('%s=%s' % (name, v))
        print('rid=%-8d %s' % (rid, ' | '.join(vals)))
    print()

if __name__ == '__main__':
    dump(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else 'van')
