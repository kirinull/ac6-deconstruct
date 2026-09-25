# -*- coding: utf-8 -*-
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi
V = r'./ac6_merge/van/regulation-bin'
M = r'./ac6_merge/mob/regulation-bin'
ZERO = chr(0)
tabs = [f for f in sorted(os.listdir(V)) if f.startswith('WwiseValueToStrParam')]
def dec(s):
    t = None
    try:
        t = s.decode('utf-8')
        if all(ord(c) >= 32 or c == ZERO for c in t):
            return t.split(ZERO)[0]
    except Exception:
        pass
    try:
        return s.decode('utf-16-le').split(ZERO)[0]
    except Exception:
        return repr(s)
for t in tabs:
    for tag, root in (('van', V), ('mob', M)):
        p = os.path.join(root, t)
        if not os.path.exists(p): continue
        b = open(p, 'rb').read()
        d = pi.parse(p)
        base = min(r[1] for r in d['rows'])
        rw = d['rowsize']
        if tag == 'mob':
            print('### %s [mob] rows=%d rowsize=%d' % (t, d['rowcount'], rw)); continue
        print('### %s [van] rows=%d rowsize=%d' % (t, d['rowcount'], rw))
        for rid, off in d['rows']:
            s = b[off:off+rw]
            print('  %-6s |%s|' % (rid, dec(s)))
        print()
