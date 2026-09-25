# -*- coding: utf-8 -*-
"""解析 AC6 paramdex XML，计算结构体字节大小，与实际 .param 行宽对照。
判定：这份 paramdex 是否真的匹配 AC6 数据。"""
import os, re, glob, importlib.util
import xml.etree.ElementTree as ET
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)

PD = r'./tools/WitchyBND/Assets/Paramdex/AC6/Defs'

TYPE_SIZE = {'u8':1,'s8':1,'u16':2,'s16':2,'u32':4,'s32':4,'f32':4,'angle32':4,
            'f64':8,'u64':8,'s64':8,'dummy8':1,'fixstr':1,'fixstrW':2,'f16':2}

def field_size(defstr):
    """'f32 camDistTarget = 4' / 'dummy8 pad[28]' / 'u8 flag:1' -> 字节数"""
    d = defstr.strip()
    m = re.match(r'^([A-Za-z0-9_]+)\s+(.+)$', d)
    if not m: return 0, ''
    typ, rest = m.group(1), m.group(2)
    base = TYPE_SIZE.get(typ)
    if base is None: return 0, typ
    name = rest.split('=')[0].strip()
    # 位域 :N -> 累积处理（简化：按 1 字节计，多个位域共用）
    bit = re.search(r':(\d+)$', name)
    if bit:
        return ('bit', base), typ
    arr = re.search(r'\[(\d+)\]$', name)
    if arr:
        return base * int(arr.group(1)), typ
    return base, typ

def struct_size(path):
    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        return None
    fields = root.find('Fields')
    if fields is None: return None
    total = 0; bit_accum = 0
    for f in fields.findall('Field'):
        d = f.get('Def') or ''
        sz, typ = field_size(d)
        if isinstance(sz, tuple):      # 位域
            bit_accum += sz[1]
            while bit_accum >= 8:
                total += 1; bit_accum -= 8
            continue
        if bit_accum: 
            total += 1; bit_accum = 0
        total += sz
    if bit_accum: total += 1
    return total

# 对照：paramdex 名 -> 实际 param 表名
pairs = [('LockCamParam','LockCamParam'),('EquipParamWeapon','EquipParamWeapon'),
         ('EquipParamProtector','EquipParamProtector'),('AtkParam','AtkParam_Pc'),
         ('NpcParam','NpcParam'),('BulletParam','Bullet'),('EquipParamBooster','EquipParamBooster'),
         ('EquipParamGenerator','EquipParamGenerator'),('EquipParamFcs','EquipParamFcs'),
         ('BehaviorParam','BehaviorParam_PC'),('JigglerBaseParam','JigglerBaseParam'),
         ('FootIKParam','FootIKParam'),('BoostParam','BoostParam')]
print('%-26s %-12s %-12s %s' % ('paramdex / 实际表','paramdex大小','实际行宽','判定'))
ok=bad=0
for pdname, tbl in pairs:
    p = os.path.join(PD, pdname + '.xml')
    if not os.path.exists(p):
        print('%-26s %-12s %-12s %s' % (pdname+'/'+tbl, 'MISSING', '', '')); continue
    sz = struct_size(p)
    f = os.path.join(pi.ROOTS['van'], tbl + '.param')
    if not os.path.exists(f): continue
    actual = pi.parse(f)['rowsize']
    v = 'MATCH' if sz == actual else ('diff %+d' % ((sz or 0)-actual))
    if sz == actual: ok+=1
    else: bad+=1
    print('%-26s %-12s %-12s %s' % (pdname+' / '+tbl, sz, actual, v))
print()
print('匹配 %d，不匹配 %d' % (ok,bad))
