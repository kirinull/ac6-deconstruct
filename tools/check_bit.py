# -*- coding: utf-8 -*-
"""位域字段专用统计（现场演示工具 —— 附录 C 故事 ③ 的现场证据）。

用法: python tools/check_bit.py <表名> <paramdef名> <字段名>
例:   python tools/check_bit.py Bullet BulletParam isEnableAutoHoming

背景：`u8 isEnableAutoHoming:1` 在偏移 172 的 **bit4**。
按整字节读得到 568/568「全部置位」（结论完全相反）；按 bit4 读才是 0/568。
凡字段名带 `:N` 的，必须按位读取。
"""
import importlib.util as I, os, struct, sys

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
bf = pf.bitfield_map(FL)
whole = {n.split(':')[0].split('[')[0]: (o, t) for o, t, n, d in FL}
if field not in bf:
    print('%s 不是位域字段（bitfield_map 未收录）。位域字段有：' % field)
    print(', '.join(sorted(bf)))
    sys.exit(2)

o, t = whole[field]
bytes_ = [struct.unpack_from('<' + pf.TYPE_FMT[t], p['b'], p['datastart'] + i * p['rowsize'] + o)[0]
          for i in range(p['rowcount'])]
bits = pf.read_bitfield(p, bf[field])
print('%s.%s  位域=%s  类型=%s 偏移=%d' % (tbl, field, bf[field], t, o))
print('  按整字节非零: %d/%d' % (sum(1 for x in bytes_ if x), len(bytes_)))
print('  按位读取置位: %d/%d' % (sum(bits), len(bits)))
