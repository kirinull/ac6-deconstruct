# -*- coding: utf-8 -*-
import importlib.util, os
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)

def profile(tbl, sub='van', topn=None):
    p = pi.parse(os.path.join(pi.ROOTS[sub], tbl + '.param'))
    n, w = p['rowcount'], p['rowsize']
    slots = w // 4
    cols = []
    for c in range(slots):
        vs = []
        for i in range(n):
            off = p['datastart'] + i*w + c*4
            if off+4 <= len(p['b']):
                vs.append(__import__('struct').unpack_from('<f', p['b'], off)[0])
        if not vs: continue
        nz = sum(1 for v in vs if v != 0.0)
        cols.append((c, nz, min(vs), max(vs), len(set(vs))))
    used = [x for x in cols if x[1] > 0]
    print('== %s : %d 行 x %d 槽' % (tbl, n, slots))
    print('   非全零列: %d / %d  (占 %.0f%%)' % (len(used), slots, 100*len(used)/slots))
    print('   全零列  : %d  (UE5 里可直接不建模)' % (slots - len(used)))
    if topn:
        print('   取值最丰富的列（信息量最大）:')
        for c, nz, mn, mx, uniq in sorted(cols, key=lambda x: -x[4])[:topn]:
            print('     col%-4d 唯一值%-4d 非零%-5d 值域[%.2f, %.2f]' % (c, uniq, nz, mn, mx))
    return cols

profile('EquipParamWeapon', topn=14)
print()
profile('EquipParamProtector', topn=10)
print()
profile('AtkParam_Pc', topn=8)
print()
profile('NpcParam', topn=6)
