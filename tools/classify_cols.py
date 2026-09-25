# -*- coding: utf-8 -*-
"""按列做类型推断：浮点连续量 / 整数ID / 全零。
用途：判断一张表里"真正需要建模的游戏参数"有多少。"""
import importlib.util, os, struct
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)

def classify(tbl, sub='van'):
    p = pi.parse(os.path.join(pi.ROOTS[sub], tbl + '.param'))
    n, w, ds, b = p['rowcount'], p['rowsize'], p['datastart'], p['b']
    kinds = {'float': [], 'int': [], 'zero': [], 'other': []}
    for c in range(w // 4):
        offs = [ds + i*w + c*4 for i in range(n) if ds + i*w + c*4 + 4 <= len(b)]
        if not offs: continue
        f = [struct.unpack_from('<f', b, o)[0] for o in offs]
        u = [struct.unpack_from('<I', b, o)[0] for o in offs]
        if all(v == 0.0 for v in f):
            kinds['zero'].append(c); continue
        weird = sum(1 for v in f if v != v or abs(v) > 1e7 or abs(v) == float('inf'))
        frac = sum(1 for v in f if v == v and abs(v) <= 1e7 and abs(v - round(v)) > 1e-6)
        if weird > 0 or frac == 0:
            # 全整数或含NaN -> 多半是整数/ID 字段
            if len(set(u)) > 1 and all(v < 2**31 for v in u):
                kinds['int'].append(c)
            else:
                kinds['other'].append(c)
        else:
            kinds['float'].append(c)
    return kinds, p

rows = []
for tbl in ['EquipParamWeapon', 'EquipParamProtector', 'AtkParam_Pc', 'NpcParam', 'Bullet',
            'EquipParamBooster', 'EquipParamGenerator', 'EquipParamFcs', 'SpEffectParam']:
    k, p = classify(tbl)
    tot = p['rowsize'] // 4
    print('== %-22s %5d 行 x %3d 槽 | 浮点 %3d | 整数/ID %3d | 全零 %3d | 存疑 %3d'
          % (tbl, p['rowcount'], tot, len(k['float']), len(k['int']), len(k['zero']), len(k['other'])))
    rows.append((tbl, tot, len(k['float']), len(k['int']), len(k['zero'])))
print()
print('结论：AC6 单条武器记录 389 槽中约 %d 个是浮点连续量，其余是 ID/引用/未用。'
      % rows[0][2])
print('这直接决定 UE5 DataTable：不需要 389 个字段，只需建模浮点量 + 必要的 ID 引用。')
