# -*- coding: utf-8 -*-
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi
V = r'./ac6_merge/van/regulation-bin'
M = r'./ac6_merge/mob/regulation-bin'
def load(t, root=V):
    p = os.path.join(root, t + '.param')
    b = open(p, 'rb').read(); d = pi.parse(p)
    return b, d, min(r[1] for r in d['rows'])
# --- SoundVoiceBankLoad as UTF-16 ---
b, d, base = load('SoundVoiceBankLoad')
print('== SoundVoiceBankLoad rows=%d rowsize=%d ==' % (d['rowcount'], d['rowsize']))
for rid, off in d['rows']:
    s = b[off:off+d['rowsize']].decode('utf-16-le', 'replace').split('\x00')[0]
    print('  %-4s %s' % (rid, s))
