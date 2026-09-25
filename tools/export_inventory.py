# -*- coding: utf-8 -*-
"""导出 257 张 param 表的真实结构清单（行数 × 行数据宽 × f32槽数），作为 UE5 复刻文档的数据底座。"""
import importlib.util, os, glob, csv, io, json

spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)

OUT = r'./data'
os.makedirs(OUT, exist_ok=True)

rowsout = []
for sub in ['van', 'mob', 'reibis']:
    root = pi.ROOTS[sub]
    for f in sorted(glob.glob(os.path.join(root, '*.param'))):
        n = os.path.basename(f)[:-6]
        try:
            p = pi.parse(f)
            rc, rs = p['rowcount'], p['rowsize']
            rowsout.append({'table': n, 'source': sub, 'rows': rc, 'row_bytes': rs,
                            'f32_slots': rs // 4 if rs % 4 == 0 else '',
                            'file_bytes': os.path.getsize(f),
                            'datastart': p['datastart'], 'longdata': p['longdata']})
        except Exception as ex:
            rowsout.append({'table': n, 'source': sub, 'rows': '', 'row_bytes': '',
                            'f32_slots': '', 'file_bytes': os.path.getsize(f),
                            'datastart': '', 'longdata': '', 'error': str(ex)[:60]})

# van 主表清单
van = [r for r in rowsout if r['source'] == 'van']
with io.open(os.path.join(OUT, 'param_tables_van.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['table','rows','row_bytes','f32_slots','file_bytes','datastart','longdata'])
    w.writeheader()
    for r in sorted(van, key=lambda x: -(x['row_bytes'] if isinstance(x['row_bytes'], int) else 0)):
        w.writerow({k: r.get(k, '') for k in w.fieldnames})

# 三目录对照
with io.open(os.path.join(OUT, 'param_tables_all.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=['table','source','rows','row_bytes','f32_slots','file_bytes','datastart','longdata','error'])
    w.writeheader()
    for r in rowsout: w.writerow(r)

ok = [r for r in van if isinstance(r['rows'], int) and r['rows'] > 0]
print('van 表数: %d，可解析: %d' % (len(van), len(ok)))
print('总行数（数据规模感）: %d 行' % sum(r['rows'] for r in ok))
print('总文件字节: %.1f MB' % (sum(r['file_bytes'] for r in van) / 1048576))
print()
print('=== 行数最多的 22 张表（内容规模 TOP）===')
for r in sorted(ok, key=lambda x: -x['rows'])[:22]:
    print('  %-40s %7d 行  %5s B/行  %4s 槽' % (r['table'], r['rows'], r['row_bytes'], r['f32_slots']))
print()
print('=== 行宽最大的 12 张表（单条记录最复杂）===')
for r in sorted(ok, key=lambda x: -(x['row_bytes'] if isinstance(x['row_bytes'], int) else 0))[:12]:
    print('  %-40s %5s 行  %6s B  %4s 槽' % (r['table'], r['rows'], r['row_bytes'], r['f32_slots']))
