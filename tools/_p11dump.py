# -*- coding: utf-8 -*-
"""P11 音频维度：按 paramdex 字段定义 dump 指定表的行（支持 fixstr 字符串列）"""
import sys, os, struct, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi
import paramdex_fields as pf

ROOTS = {'van': r'./ac6_merge/van/regulation-bin',
         'mob': r'./ac6_merge/mob/regulation-bin',
         'reibis': r'./ac6_merge/reibis/regulation-bin'}

def raw(path):
    b = open(path,'rb').read()
    d = pi.parse(path)
    e = '>' if b[0x2C]==0xFF else '<'
    didx = [r[1] for r in d['rows']]
    base = min(didx)
    rows=[]
    for rid, off in d['rows']:
        rows.append((rid, off-base))
    return b, d, rows

def dump(table, ver='van', cols=None, limit=None, params=None):
    D = r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs/'
    xml = D + table + '.xml'
    if not os.path.exists(xml):
        for cand in [table.rsplit('_',1)[0], table.replace('_Pc','').replace('_Npc','').replace('_PC','').replace('_NPC','')]:
            if os.path.exists(D + cand + '.xml'): xml = D + cand + '.xml'; break
    fl, total = pf.fields_of(xml)
    p = os.path.join(ROOTS[ver], table + '.param')
    if not os.path.exists(p):
        print('MISSING', p); return
    b, d, rows = raw(p)
    base = min(r[1] for r in d['rows'])
    print('# %s/%s  行数=%d rowsize=%d  结构大小=%d' % (ver, table, d['rowcount'], d['rowsize'], total))
    for rid, off in rows:
        if limit is not None and rid not in limit: continue
        out=[]
        for f in fl:
            o, ty, nm, disp = f
            if cols and nm not in cols: continue
            if o + 4 > d['rowsize']: continue
            v=None
            if ty=='fixstr':
                ln = 16
                import re as _re
                _m=_re.search(r'\[(\d+)\]$', nm)
                if _m: ln=int(_m.group(1))
                elif ty=='fixstrW': ln=2
                v=b[base+off+o:base+off+o+ln].split(b'\x00')[0].decode('utf-8','replace')
            elif ty in ('f32',): v=struct.unpack_from('<f', b, base+off+o)[0]
            elif ty in ('s32','u32'): v=struct.unpack_from('<i' if ty=='s32' else '<I', b, base+off+o)[0]
            elif ty in ('s16','u16'): v=struct.unpack_from('<h' if ty=='s16' else '<H', b, base+off+o)[0]
            elif ty in ('s8','u8'): v=struct.unpack_from('<b' if ty=='s8' else '<B', b, base+off+o)[0]
            else: continue
            out.append('%s=%s' % (nm, v))
        print('  [%s] %s' % (rid, '  '.join(out)))

if __name__=='__main__':
    t=sys.argv[1]; ver=sys.argv[2] if len(sys.argv)>2 else 'van'
    cols=sys.argv[3].split(',') if len(sys.argv)>3 else None
    lim=None
    if len(sys.argv)>4 and sys.argv[4]!='-': lim=set(int(x) for x in sys.argv[4].split(','))
    dump(t, ver, cols, lim)
