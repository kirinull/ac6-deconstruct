# -*- coding: utf-8 -*-
import io, os, re
D = r'.\data\ue_datatables'
pairs = []
for f in sorted(os.listdir(D)):
    if f.endswith('.csv'):
        base = f[:-4]
        st = os.path.join(D, base + '.struct.txt')
        if os.path.exists(st): pairs.append((base, os.path.join(D, f), st))
print('配对成功 %d 组\n' % len(pairs))
allok = True
for base, csvp, stp in pairs:
    hdr = io.open(csvp, encoding='utf-8-sig').readline().strip().split(',')
    cols = [c.strip() for c in hdr]
    assert cols[0] == 'Name', base + ' 首列不是 Name: ' + cols[0]
    cols = cols[1:]
    txt = io.open(stp, encoding='utf-8').read()
    fields = re.findall(r'UPROPERTY\([^)]*\)\s+(?:float|int32|int64|uint8|bool|FString)\s+([A-Za-z_][A-Za-z0-9_]*)', txt)
    only_csv = [c for c in cols if c not in fields]
    only_st  = [f for f in fields if f not in cols]
    status = 'OK ' if (not only_csv and not only_st) else 'XX '
    if only_csv or only_st: allok = False
    print('%s %-22s CSV %2d 列 / struct %2d 字段' % (status, base, len(cols), len(fields)))
    if only_csv: print('      只在 CSV 有 : ' + ', '.join(only_csv))
    if only_st:  print('      只在 struct: ' + ', '.join(only_st))
print()
print('全部一致' if allok else '★ 存在不一致，必须以 CSV 列名为准（UE 按列名匹配结构体字段）')
