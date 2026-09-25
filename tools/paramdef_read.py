# -*- coding: utf-8 -*-
"""从 .paramdef 提取字段名序列（WitchyBND 解出的二进制 ParamDef）。
已验证：LOCK_CAM_PARAM_ST 的前 6 个字段名与实测数据语义逐条吻合。"""
import os, glob, struct, io

PDEF = r'./ac6_merge/pdef/paramdef-paramdefbnd-dcx'

def read_str(b, off, maxlen=64):
    end = b.find(b'\x00', off)
    if end < 0 or end - off > maxlen: end = off + maxlen
    try: return b[off:end].decode('utf-8')
    except: return b[off:end].decode('latin1')

def parse_pdef(path):
    b = open(path, 'rb').read()
    if len(b) < 128: return None
    filesize = struct.unpack_from('<I', b, 0)[0]
    nfields = struct.unpack_from('<H', b, 8)[0]
    structsize = struct.unpack_from('<H', b, 10)[0]
    name = read_str(b, 12, 32)
    # 记录区从 96 开始，每条 208 字节
    fields = []
    for k in range(nfields):
        rec = 96 + k*208
        if rec + 208 > len(b): break
        # 找该记录里的字段名：最长的一条 ASCII（+104 起）
        nm = read_str(b, rec + 104, 64)
        it = read_str(b, rec + 24, 16)   # internalType: f32/u8/...
        dt = read_str(b, rec + 72, 16)   # displayType
        fields.append((nm, it, dt))
    return {'name': name, 'nfields': nfields, 'structsize': structsize, 'fields': fields, 'filesize': filesize}

if __name__ == '__main__':
    files = sorted(glob.glob(os.path.join(PDEF, '*.paramdef')))
    print('paramdef 文件数:', len(files))
    print()
    probes = ['LOCK_CAM_PARAM_ST', 'EQUIP_PARAM_WEAPON_ST', 'EQUIP_PARAM_PROTECTOR_ST',
              'ATK_PARAM_ST', 'BEHAVIOR_PARAM_ST', 'NPC_PARAM_ST', 'EQUIP_PARAM_BOOSTER_ST',
              'EQUIP_PARAM_GENERATOR_ST', 'EQUIP_PARAM_FCS_ST', 'BULLET_PARAM_ST']
    for pr in probes:
        p = os.path.join(PDEF, pr + '.paramdef')
        if not os.path.exists(p):
            print('%-32s MISSING' % pr); continue
        d = parse_pdef(p)
        print('%-32s 字段数=%-4d 定义结构大小=%-5d 文件=%d' % (pr, d['nfields'], d['structsize'], d['filesize']))
    print()
    for pr in ['EQUIP_PARAM_WEAPON_ST', 'EQUIP_PARAM_PROTECTOR_ST']:
        d = parse_pdef(os.path.join(PDEF, pr + '.paramdef'))
        print('=== %s 前 40 个字段 ===' % pr)
        for i, (nm, it, dt) in enumerate(d['fields'][:40]):
            print('  %2d  %-46s %s' % (i, nm, it))
        print()
