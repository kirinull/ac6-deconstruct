# -*- coding: utf-8 -*-
r"""为导入准备 CSV：修正「行名去重用了大小写敏感键」的缺陷

背景（可复现）：
  tools/export_ue_datatables.py:186 的 `if nm in used:` 用大小写敏感字典去重，
  但 UE 的 FName 行名大小写不敏感 —— 于是仅大小写不同的两个行名双双通过去重，
  到 UE 导入时才撞车，后者被静默丢弃（日志报 Duplicate row name）。
  实测丢失 14 行（AtkParam_Pc 13 + Bullet 1），其中 3 行是真正不同的数据：
    Bullet      hand_gun(Life=1)             vs Hand_gun(Life=2.25)
    AtkParam_Pc PA_Breaker_Weak_Attack_1     vs PA_Breaker_Weak_attack_1
    AtkParam_Pc Beam_naginata_strong_attack  vs Beam_Naginata_Strong_attack

本脚本在本地等效修正：按「小写键」去重，保留原大小写，后续出现者加 _N 后缀
（与修正后的导出器行为一致：第 2 次出现 -> _1，第 3 次 -> _2）。

产出：<project>/data/ue_datatables/*.csv  + rename_report.csv
"""
import io, os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'.\data\ue_datatables'
DST = r'<UE_PROJECTS>\AC6Proto\data\ue_datatables'

def dedup_names(names):
    '''大小写不敏感去重（与修正后的导出器等效）

    关键：先把**所有原始名**（小写）放进 reserved，改名时不得撞 reserved ——
    否则 "X" 的第 2 次出现会被改成 "X_1"，而文件里可能本来就有一行叫 "X_1"。
    '''
    reserved = {n.lower() for n in names}   # 全部原始名，禁止被改名结果占用
    used = set()
    out = []
    for nm in names:
        key = nm.lower()
        if key not in used:
            used.add(key); out.append(nm)   # 该名首次出现 -> 原样保留
        else:
            i = 1
            while True:
                cand = '%s_%d' % (nm, i)
                ck = cand.lower()
                if ck not in used and ck not in reserved:
                    used.add(ck); out.append(cand); break
                i += 1
    return out

os.makedirs(DST, exist_ok=True)
report, total_fixed = [], 0
for f in sorted(os.listdir(SRC)):
    if not f.endswith('.csv'): continue
    rows = list(csv.reader(io.open(os.path.join(SRC, f), encoding='utf-8-sig', newline='')))
    if not rows: continue
    hdr, data = rows[0], rows[1:]
    orig = [r[0] for r in data]
    new  = dedup_names(orig)
    fixed = [(a, b, r) for a, b, r in zip(orig, new, data) if a != b]
    total_fixed += len(fixed)
    with io.open(os.path.join(DST, f), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, lineterminator=chr(13) + chr(10))
        w.writerow(hdr)
        for r, nn in zip(data, new):
            rr = list(r); rr[0] = nn
            w.writerow(rr)
    flag = 'OK ' if not fixed else 'FIX'
    print('%s %-22s 行 %4d  改名 %d' % (flag, f[:-4], len(data), len(fixed)))
    for a, b, r in fixed:
        report.append([f[:-4], a, b, ','.join(r[1:])])
        print('      %-42s -> %s' % (a, b))

if report:
    rp = os.path.join(DST, 'rename_report.csv')
    with io.open(rp, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, lineterminator=chr(13) + chr(10))
        w.writerow(['Table', 'OriginalName', 'RenamedTo', 'RowValues'])
        w.writerows(report)
    print()
    print('改名报告 -> %s (%d 条)' % (rp, len(report)))
print()
print('合计改名 %d 行' % total_fixed)
