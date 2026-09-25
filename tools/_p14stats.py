# -*- coding: utf-8 -*-
import os,sys,re,struct,importlib.util,collections
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
sys.path.insert(0, r'./tools')
import paramdex_fields as pf

def build(tbl):
    pdname=tbl
    for c in [tbl, tbl+'Param', tbl.replace('Param','')]:
        if os.path.exists(os.path.join(pf.PD,'Defs',c+'.xml')): pdname=c;break
    fl,total = pf.fields_of(os.path.join(pf.PD,'Defs',pdname+'.xml'))
    return fl,total

def readall(tbl, sub='van'):
    p=pi.parse(os.path.join(pi.ROOTS[sub],tbl+'.param'))
    fl,total=build(tbl); b=p['b']; ds=p['datastart']; rs=p['rowsize']
    fm={'u8':'B','s8':'b','u16':'H','s16':'h','u32':'I','s32':'i','f32':'f'}
    res=[]
    for i,(rid,idx) in enumerate(p['rows']):
        d=b[ds+i*rs: ds+i*rs+rs]; r={}
        for off,typ,name,disp in fl:
            if ':' in name or '[' in name or typ not in fm: continue
            sz=pf.TYPE_SIZE[typ]
            if off+sz>len(d): continue
            r[name]=struct.unpack_from('<'+fm[typ],d,off)[0]
        res.append((rid,r))
    return p,res

p,rows = readall('TutorialParam')
print('TutorialParam 行数=%d 行宽=%d' % (p['rowcount'], p['rowsize']))
c1=collections.Counter(r['MenuResourceType'] for _,r in rows)
print('MenuResourceType 分布:', dict(sorted(c1.items())))
c2=collections.Counter(r['RepeatType'] for _,r in rows)
print('RepeatType 分布:', dict(sorted(c2.items())))
print('UnlockEventFlagID 非零:', sum(1 for _,r in rows if r['UnlockEventFlagID']!=0), '/', len(rows))
print('enableMultiResponseKeyguide 分布:', dict(collections.Counter(r['enableMultiResponseKeyguide'] for _,r in rows)))
print('OpenSE 非零:', sum(1 for _,r in rows if r['OpenSE']!=0))
nkg=sum(1 for _,r in rows if any(r['Keyguide%d_ActJudgeParamID'%k] for k in range(4)))
print('含 >=1 个 Keyguide 槽的行数:', nkg, '/', len(rows))
cnt=collections.Counter()
for _,r in rows:
    n=sum(1 for k in range(4) if r['Keyguide%d_ActJudgeParamID'%k])
    cnt[n]+=1
print('Keyguide 槽位使用数分布 {槽数:行数}:', dict(sorted(cnt.items())))
ids=collections.Counter()
for _,r in rows:
    for k in range(4):
        v=r['Keyguide%d_ActJudgeParamID'%k]
        if v: ids[v]+=1
print('被 Keyguide 引用的 ActJudge ID (ID:次数):', dict(sorted(ids.items())))
print('ImageID 非零:', sum(1 for _,r in rows if r['ImageID']!=0))
print('ImageID 唯一值数:', len(set(r['ImageID'] for _,r in rows)))
# 前缀分组
c3=collections.Counter(str(rid)[:4] for rid,_ in rows)
print('行ID 前4位分组:', dict(sorted(c3.items())))
