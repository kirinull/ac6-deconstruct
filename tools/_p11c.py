# -*- coding: utf-8 -*-
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import param_inspect as pi
V = r'./ac6_merge/van/regulation-bin'
M = r'./ac6_merge/mob/regulation-bin'
R = r'./ac6_merge/reibis/regulation-bin'
def rows(t, root=V):
    p = os.path.join(root, t + '.param')
    b = open(p, 'rb').read(); d = pi.parse(p)
    return [(rid, b[off:off+d['rowsize']], d['rowsize']) for rid, off in d['rows']]

print('#### 1. RuntimeSoundParam_Pc / Npc 统计')
for t in ['RuntimeSoundParam_Pc','RuntimeSoundParam_Npc']:
    rs = rows(t)
    rw = rs[0][2]
    def f(o,ty='i'): return [struct.unpack_from('<'+ty, r, o)[0] for _,r,_ in rs]
    cond = f(4); sp = f(8,'H'); slot = f(10,'h'); seid = f(12)
    rtpc = [r[20:36].split(b'\x00')[0].decode('utf8','replace') for _,r,_ in rs]
    rtpcv= f(36,'B'); appl= f(37,'B'); stype = f(39,'B')
    dur  = f(40); inter= f(44); other= f(48)
    print(' %s rows=%d rowsize=%d' % (t, len(rs), rw))
    print('   ConditionID: n=%d min=%d max=%d' % (len(set(cond)), min(cond), max(cond)))
    print('   SoundPlayer(再生タイプ) 分布:', dict(sorted(collections.Counter(sp).items())))
    print('   SlotNo(再生スロット番号) 分布:', dict(sorted(collections.Counter(slot).items())))
    print('   soundType 分布:', dict(sorted(collections.Counter(stype).items())))
    print('   RTPC01_ID 非空:', collections.Counter([x for x in rtpc if x]))
    print('   RTPC01_Value 非零行:', sum(1 for v in rtpcv if v), ' 值集合:', sorted(set(rtpcv)))
    print('   RTPC01_ValueChangeDuration(ms) 分布:', dict(sorted(collections.Counter(dur).items())))
    print('   PlayInterval(ms) 非零行=%d 值=%s' % (sum(1 for v in inter if v), sorted(set(inter))))
    print('   IsApplyEnemyFriendPlayer=1 行数:', sum(1 for v in appl if v))
    print('   SeID_OtherPlayer 非零行数:', sum(1 for v in other if v))
    print('   SeID 唯一数=%d' % len(set(seid)))

print()
print('#### 2. HitEffectSfxParam (71x240)')
import importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paramdex_fields as pf
fl, tot = pf.fields_of(r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs/HitEffectSfxParam.xml')
rs = rows('HitEffectSfxParam')
print(' rows=%d rowsize=%d' % (len(rs), rs[0][2]))
# SfxId 槽位非零统计
slot_names = [f[2] for f in fl if f[0] < 100]
print(' SfxId 槽位数=%d' % len(slot_names))
cnt = collections.Counter()
for _, r, _ in rs:
    for i, nm in enumerate(slot_names):
        v = struct.unpack_from('<i', r, i*4)[0]
        if v > 0: cnt[nm] += 1
print(' 所有槽位均有效的行数: %d / %d' % (sum(1 for _,r,_ in rs if all(struct.unpack_from('<i',r,i*4)[0]>0 for i in range(len(slot_names)))), len(rs)))
# bFollow 位
bf = pf.bitfield_map(fl)
follow_true = collections.Counter()
for _, r, _ in rs:
    for k,(bo,bs,bw) in bf.items():
        if k.startswith('bFollow_'):
            if (r[bo] >> bs) & 1: follow_true[k]+=1
print(' bFollow_* 置位统计(前12):', dict(sorted(follow_true.items())[:12]), '... 共%d个位' % len(follow_true))
allset = [k for k in follow_true if follow_true[k]==len(rs)]
none   = [k for k in bf if k.startswith('bFollow_') and follow_true.get(k,0)==0]
print(' 恒置位(71/71)的位: %s' % allset)
print(' 恒清零的位: %s' % none)
