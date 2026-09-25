# -*- coding: utf-8 -*-
"""AC6 loose .param inspector — 实现标准 Souls param 扩展行格式(LONGDATA)。
参考 ac6_merge/paramdiff.py 的 parse_param(项目内既有、已验证的解析器)。"""
import os, struct, sys, glob

ROOTS = {'van': r'./ac6_merge/van/regulation-bin',
         'mob': r'./ac6_merge/mob/regulation-bin',
         'reibis': r'./ac6_merge/reibis/regulation-bin'}

FLAG01, INTDATA, LONGDATA, OFFSETPT = 0x01, 0x02, 0x04, 0x08

def parse(path):
    b = open(path, 'rb').read()
    big = b[0x2C] == 0xFF
    e = '>' if big else '<'
    fmt2d, fmt2e = b[0x2D], b[0x2E]
    pos = 0
    strings_offset = struct.unpack_from(e + 'I', b, pos)[0]; pos = 4
    pos += 2
    pos += 2
    pos += 2                                    # paramdef_data_version
    rowcount = struct.unpack_from(e + 'H', b, pos)[0]; pos += 2
    paramtype = None; actual_strings = 0; pt_off = 0
    if fmt2d & OFFSETPT:
        pos += 4
        pt_off = struct.unpack_from(e + 'q', b, pos)[0]; pos += 8
        pos += 0x14
        actual_strings = pt_off
    else:
        paramtype = b[pos:pos+0x20].split(b'\x00')[0].decode('shift_jis', 'replace'); pos += 0x20
    pos += 4
    if (fmt2d & FLAG01 and fmt2d & INTDATA) or (fmt2d & LONGDATA):
        pos += 16
    rows = []
    for _ in range(rowcount):
        if fmt2d & LONGDATA:
            rid = struct.unpack_from(e+'i', b, pos)[0]; pos += 4
            pos += 4
            didx = struct.unpack_from(e+'Q', b, pos)[0]; pos += 8
            noff = struct.unpack_from(e+'q', b, pos)[0]; pos += 8
        else:
            rid = struct.unpack_from(e+'i', b, pos)[0]; pos += 4
            didx = struct.unpack_from(e+'I', b, pos)[0]; pos += 4
            noff = struct.unpack_from(e+'I', b, pos)[0]; pos += 4
        rows.append((rid, didx))
    if len(rows) > 1:   rowsize = rows[1][1] - rows[0][1]
    elif len(rows) == 1: rowsize = (actual_strings or strings_offset) - rows[0][1]
    else: rowsize = 0
    datastart = min((r[1] for r in rows), default=0)
    return {'rowcount': rowcount, 'rowsize': rowsize, 'rows': rows,
            'datastart': datastart, 'b': b, 'paramtype': paramtype, 'longdata': bool(fmt2d & LONGDATA)}

def col(p, i, c, fmt='<f'):
    off = p['datastart'] + i*p['rowsize'] + c*4
    if off+4 > len(p['b']): return None
    return struct.unpack_from(fmt, p['b'], off)[0]

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else '--selftest'
    if mode == '--selftest':
        tot = ok = 0; nonint = []
        for sub, root in ROOTS.items():
            for f in sorted(glob.glob(os.path.join(root, '*.param'))):
                p = parse(f); tot += 1
                if p['rowcount'] == 0 or p['rowsize'] <= 0 or p['rowsize'] % 4:
                    nonint.append(sub+'/'+os.path.basename(f)); continue
                if p['datastart'] + p['rowcount']*p['rowsize'] > len(p['b']): 
                    nonint.append('OVERFLOW '+sub+'/'+os.path.basename(f)); continue
                ok += 1
        print('总表 %d，结构自洽 %d，异常 %d' % (tot, ok, len(nonint)))
        if nonint: print('异常样例:', nonint[:10])
    else:
        tbl = mode; sub = sys.argv[2] if len(sys.argv) > 2 else 'van'
        p = parse(os.path.join(ROOTS[sub], tbl + '.param'))
        print('%s/%s  行数=%d  行数据宽=%d 字节(%d 个 f32)  data起点=%d  扩展行格式=%s'
              % (sub, tbl, p['rowcount'], p['rowsize'], p['rowsize']//4, p['datastart'], p['longdata']))
        print('行 ID 前 20:', [r[0] for r in p['rows']][:20])
        print()
        print('%-5s %12s %12s %12s %8s' % ('列','min','max','mean','非零行'))
        for c in range(min(20, p['rowsize']//4)):
            vs = [col(p,i,c) for i in range(p['rowcount'])]
            vs = [v for v in vs if v is not None]
            if not vs: break
            nz = sum(1 for v in vs if v != 0.0)
            print('%-5d %12.3f %12.3f %12.3f %8d' % (c, min(vs), max(vs), sum(vs)/len(vs), nz))
