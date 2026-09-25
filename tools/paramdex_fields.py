# -*- coding: utf-8 -*-
"""从 AC6 paramdex 提取某张表的字段名 + 字节偏移 + 类型。
已验证：13/13 张表的 paramdex 结构大小 与 实际 .param 行宽 精确匹配。
用法：python tools/paramdex_fields.py <表名> [--values]
"""
import os, re, sys, struct, importlib.util
import xml.etree.ElementTree as ET
spec = importlib.util.spec_from_file_location('pi', r'./tools/param_inspect.py')
pi = importlib.util.module_from_spec(spec); spec.loader.exec_module(pi)

PD = r'./tools/WitchyBND/Assets/Paramdex/AC6'
TYPE_SIZE = {'u8':1,'s8':1,'u16':2,'s16':2,'u32':4,'s32':4,'f32':4,'angle32':4,
             'f64':8,'u64':8,'s64':8,'dummy8':1,'fixstr':1,'fixstrW':2,'f16':2}
TYPE_FMT  = {'u8':'B','s8':'b','u16':'H','s16':'h','u32':'I','s32':'i','f32':'f'}

def fields_of(path):
    root = ET.parse(path).getroot()
    fs = root.find('Fields')
    out = []; off = 0; bit_used = 0; bit_base = 'u8'
    for f in fs.findall('Field'):
        d = (f.get('Def') or '').strip()
        m = re.match(r'^([A-Za-z0-9_]+)\s+(.+)$', d)
        if not m: continue
        typ, rest = m.group(1), m.group(2)
        base = TYPE_SIZE.get(typ, 0)
        name = rest.split('=')[0].strip()
        disp = f.findtext('DisplayName') or ''
        m_bit = re.search(r':(\d+)$', name)
        if m_bit:
            bits = int(m_bit.group(1))
            if bit_used == 0:
                bit_base = typ          # 开一个新位域组，记录基类型
            out.append((off, typ, name, disp)); bit_used += bits
            # 修正：同基类型的连续位域共享一个 TYPE_SIZE[base] 大小的存储单元
            if bit_used >= TYPE_SIZE.get(bit_base, 1) * 8:
                off += TYPE_SIZE.get(bit_base, 1); bit_used = 0
            continue
        if bit_used:                    # 位域组结束：补齐到基类型大小
            off += TYPE_SIZE.get(bit_base, 1); bit_used = 0
        arr = re.search(r'\[(\d+)\]$', name)
        size = base * int(arr.group(1)) if arr else base
        out.append((off, typ, name, disp)); off += size
    return out, off

if __name__ == '__main__':
    tbl = sys.argv[1]
    pdname = tbl
    for cand in [tbl, tbl.replace('_Pc','').replace('_NPC','').replace('_Npc',''),
                 tbl + 'Param', tbl.replace('Param','')]:
        if os.path.exists(os.path.join(PD, 'Defs', cand + '.xml')): pdname = cand; break
    p = os.path.join(PD, 'Defs', pdname + '.xml')
    if not os.path.exists(p):
        # 模糊找
        import glob
        c = [f for f in glob.glob(os.path.join(PD,'Defs','*.xml')) if tbl.lower()[:8] in os.path.basename(f).lower()]
        if c: p = c[0]; pdname = os.path.basename(c[0])[:-4]
    print('# %s  <-  paramdex: %s.xml' % (tbl, pdname))
    fl, total = fields_of(p)
    print('# 字段数 %d, 计算结构大小 %d 字节' % (len(fl), total))
    real = None
    for cand in [tbl]: 
        f = os.path.join(pi.ROOTS['van'], cand + '.param')
        if os.path.exists(f): real = pi.parse(f)
    if real:
        print('# 实际: %d 行 x %d 字节  -> %s' % (real['rowcount'], real['rowsize'],
              'SIZE MATCH' if real['rowsize']==total else 'SIZE DIFF %+d' % (total-real['rowsize'])))
    print()
    print('%-6s %-10s %-46s %s' % ('偏移','类型','字段名','日文显示名'))
    for off, typ, name, disp in fl:
        if typ == 'dummy8' and not name.startswith('pad'): continue
        print('%-6d %-10s %-46s %s' % (off, typ, name[:46], disp[:38]))

def bitfield_map(fields):
    """返回 {字段名: (字节偏移, bit 起点, bit 宽度)}，用于正确读取 :N 位域。
    背景：u8 isEnableAutoHoming:1 在偏移 172 的 bit4；按整字节读会误判为"全部置位"。"""
    out = {}
    cur_off = None; bit = 0
    for o, t, n, disp in fields:
        base = n.split(':')[0].split('[')[0]
        if ':' in n:
            w = int(n.split(':')[1])
            if o != cur_off:
                cur_off = o; bit = 0
            out[base] = (o, bit, w)
            bit += w
            if bit >= TYPE_SIZE.get(t, 1) * 8:
                cur_off = None; bit = 0
        else:
            cur_off = None; bit = 0
    return out


def read_bitfield(param, bf):
    """bf = (byte_off, bit_start, bit_width) -> 逐行取位的列表。"""
    o, bs, bw = bf
    mask = (1 << bw) - 1
    buf = param['b']; ds = param['datastart']; rs = param['rowsize']
    out = []
    for i in range(param['rowcount']):
        off = ds + i * rs + o
        if off + 1 > len(buf): break
        out.append((buf[off] >> bs) & mask)
    return out
