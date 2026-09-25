# -*- coding: utf-8 -*-
"""任意表的任意字段统计（现场演示工具，配套 docs/04_元分析/P20 第 5 节与附录 C）。

用法: python tools/check_field.py <表名> <paramdef名> <字段名>
例:   python tools/check_field.py AtkParam_Pc AtkParam hitStopTime

设计要点：**同时打印「全体」与「非零」两种中位口径** —— 这是本项目的第 7 类坑
（统计口径陷阱）的现场防御手段。任何引用都必须带上口径。
"""
import importlib.util as I, os, struct, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
pi = I.module_from_spec(s := I.spec_from_file_location('pi', os.path.join(HERE, 'param_inspect.py')))
s.loader.exec_module(pi)
pf = I.module_from_spec(s2 := I.spec_from_file_location('pf', os.path.join(HERE, 'paramdex_fields.py')))
s2.loader.exec_module(pf)

if len(sys.argv) < 4:
    print(__doc__)
    sys.exit(1)

tbl, pdname, field = sys.argv[1], sys.argv[2], sys.argv[3]
p = pi.parse(os.path.join(pi.ROOTS['van'], tbl + '.param'))
FL, _ = pf.fields_of(os.path.join(pf.PD, 'Defs', pdname + '.xml'))
f = {n.split(':')[0].split('[')[0]: (o, t) for o, t, n, d in FL}
if field not in f:
    print('字段 %s 不在 %s.xml 中；可用字段：' % (field, pdname))
    print(', '.join(sorted(f)[:60]))
    sys.exit(2)

o, t = f[field]
v = [struct.unpack_from('<' + pf.TYPE_FMT[t], p['b'], p['datastart'] + i * p['rowsize'] + o)[0]
     for i in range(p['rowcount'])]
nz = [x for x in v if x]
print('%s.%s  %d 行 / 行宽 %d B / 偏移 %d / 类型 %s'
      % (tbl, field, p['rowcount'], p['rowsize'], o, t))
print('  非零 %d 行 | min=%.3f max=%.3f 中位(全体)=%.3f 中位(非零)=%.3f'
      % (len(nz), min(v), max(v), st.median(v), st.median(nz) if nz else 0))
if len(set(v)) <= 12:
    print('  唯一值: %s' % sorted(set(v)))
if nz and len(nz) <= 80:
    print('  非零行号: %s' % [i for i, x in enumerate(v) if x])
