# -*- coding: utf-8 -*-
import os, re, struct, importlib.util, sys
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
spec2 = importlib.util.spec_from_file_location('pf', r'./tools/paramdex_fields.py')
pf = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(pf)
PD = pf.PD
DN = os.path.join(PD, 'Developer Names')

def devnames(tbl):
    p = os.path.join(DN, tbl + '.txt')
    if not os.path.exists(p): return {}
    out = {}
    for ln in open(p, encoding='utf-8', errors='replace'):
        ln = ln.strip()
        m = re.match(r'^(\d+)\s+(.*)$', ln)
        if m: out[int(m.group(1))] = m.group(2)
    return out

def rows(tbl, paramfile=None, root='van'):
    pf_ = os.path.join(PD, 'Defs', tbl + '.xml')
    fl, total = pf.fields_of(pf_)
    p = pi.parse(os.path.join(pi.ROOTS[root], (paramfile or tbl) + '.param'))
    def get(ridx, name, fmt=None):
        for o, t, n, d in fl:
            if n.split(':')[0].split('[')[0] == name:
                o2 = p['datastart'] + ridx*p['rowsize'] + o
                if o2 + 4 > len(p['b']): return None
                return struct.unpack_from('<' + (fmt or pf.TYPE_FMT.get(t, 'i')), p['b'], o2)[0]
        return 'NOFIELD'
    def col(name):
        return [get(i, name) for i in range(p['rowcount'])]
    return p, fl, get, col

def show(tbl, ridx_list, fieldnames, paramfile=None, root='van'):
    p, fl, get, col = rows(tbl, paramfile, root)
    dn = devnames(paramfile or tbl)
    print('### %s  rows=%d rowsize=%d' % (tbl, p['rowcount'], p['rowsize']))
    for i in ridx_list:
        if i >= p['rowcount']: continue
        print('  row%-4d rid=%-8d %s' % (i, p['rows'][i][0], dn.get(p['rows'][i][0], '')))
        for fn in fieldnames:
            v = get(i, fn)
            if isinstance(v, float): print('      %-44s %.4f' % (fn, v))
            else: print('      %-44s %s' % (fn, v))
    return p, fl, get, col

def show_rid(tbl, rids, fieldnames, paramfile=None, root='van'):
    p, fl, get, col = rows(tbl, paramfile, root)
    dn = devnames(paramfile or tbl)
    idx = {p['rows'][i][0]: i for i in range(p['rowcount'])}
    print('### %s  rows=%d rowsize=%d' % (tbl, p['rowcount'], p['rowsize']))
    hdr = '  rid    %s' % (' | '.join(f[:26] for f in fieldnames))
    print(hdr)
    for r in rids:
        if r not in idx:
            print('  %-6d (MISSING)' % r); continue
        vals=[]
        for fn in fieldnames:
            v = get(idx[r], fn)
            vals.append(('%.3f'%v) if isinstance(v,float) else str(v))
        print('  %-6d %s   # %s' % (r, ' | '.join(vals), dn.get(r,'')))
    return p, fl, get, col, idx
