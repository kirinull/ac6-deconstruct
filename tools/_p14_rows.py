# -*- coding: utf-8 -*-
import os,sys,re,struct,importlib.util
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)
sys.path.insert(0, r'./tools')
import paramdex_fields as pf
def build(tbl):
    pdname=tbl
    for c in [tbl, tbl+'Param']:
        if os.path.exists(os.path.join(pf.PD,'Defs',c+'.xml')): pdname=c;break
    return pf.fields_of(os.path.join(pf.PD,'Defs',pdname+'.xml'))[0]
def readall(tbl, sub='van'):
    p=pi.parse(os.path.join(pi.ROOTS[sub],tbl+'.param')); fl=build(tbl)
    b=p['b']; ds=p['datastart']; rs=p['rowsize']; fm={'u8':'B','s8':'b','u16':'H','s16':'h','u32':'I','s32':'i','f32':'f'}
    res=[]
    for i,(rid,idx) in enumerate(p['rows']):
        d=b[ds+i*rs: ds+i*rs+rs]; r={}
        for off,typ,name,disp in fl:
            if ':' in name or '[' in name or typ not in fm: continue
            if off+pf.TYPE_SIZE[typ]>len(d): continue
            r[name]=struct.unpack_from('<'+fm[typ],d,off)[0]
        res.append((rid,r))
    return p,res
def dumptbl(tbl, cols, sub='van', idfilter=None):
    p,rows=readall(tbl,sub)
    print('== %s/%s 行数=%d 行宽=%d' % (sub,tbl,p['rowcount'],p['rowsize']))
    print('| rid | '+ ' | '.join(cols) +' |')
    for rid,r in rows:
        if idfilter and not idfilter(rid): continue
        print('| %d | '%rid + ' | '.join(str(r.get(c)) for c in cols)+' |')
if __name__=='__main__':
    tbl=sys.argv[1]; cols=sys.argv[2].split(',')
    filt=None
    if len(sys.argv)>3:
        pat=sys.argv[3]
        filt=lambda rid: re.match(pat,str(rid))
    dumptbl(tbl,cols,'van',filt)
