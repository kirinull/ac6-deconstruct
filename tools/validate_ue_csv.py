
# -*- coding: utf-8 -*-
"""验证导出的 CSV 是否符合 UE5 DataTable 的导入要求。
UE 的常见坑：BOM、列数不一致、行名重复/空、类型不匹配、特殊字符。"""
import io, csv, os, re

D = r'./data/ue_datatables'
files = sorted(f for f in os.listdir(D) if f.endswith('.csv'))

print('=== UE5 DataTable CSV 格式校验 ===')
print()
allok = True
for fn in files:
    p = os.path.join(D, fn)
    raw = open(p, 'rb').read()
    issues = []

    # 1) BOM 检查
    has_bom = raw[:3] == b'\xef\xbb\xbf'
    if has_bom: issues.append('有 UTF-8 BOM（UE 通常可以，但建议去掉）')

    # 2) 行尾（UE 接受 \n 和 \r\n）
    crlf = b'\r\n' in raw

    # 3) 解析
    with io.open(p, encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.reader(fh))
    if not rows: issues.append('空文件'); print('%-28s FAIL %s' % (fn, issues)); continue
    header = rows[0]
    data = rows[1:]

    # 4) 首列必须是 Name
    if header[0] != 'Name':
        issues.append('首列不是 Name（UE 靠它做行名）')

    # 5) 列数一致
    bad_cols = [i for i, r in enumerate(data, 2) if len(r) != len(header)]
    if bad_cols: issues.append('第 %s 行列数不等于表头' % bad_cols[:3])

    # 6) 行名唯一且非空
    names = [r[0] for r in data]
    dup = [n for n in set(names) if names.count(n) > 1]
    if dup: issues.append('行名重复: %s' % dup[:3])
    empty = [i for i, n in enumerate(names, 2) if not n.strip()]
    if empty: issues.append('第 %s 行行名为空' % empty[:3])

    # 7) 行名非法字符（UE RowName 不接受某些字符）
    badname = [n for n in names if re.search(r'[",\n\r]', n)]
    if badname: issues.append('行名含非法字符: %s' % badname[:3])

    # 8) 列名合法性（UE 变量名规则）
    badcol = [c for c in header[1:] if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', c)]
    if badcol: issues.append('列名非法: %s' % badcol[:3])

    # 9) 重复列名（UE 会报错）
    duph = [c for c in set(header[1:]) if header[1:].count(c) > 1]
    if duph: issues.append('列名重复: %s' % duph[:3])

    # 10) 数值可解析性（抽查第一行）
    if data:
        nonnum = []
        for i, c in enumerate(data[0][1:], 1):
            if c == '': continue
            try: float(c)
            except: nonnum.append(header[i])
        if nonnum: issues.append('非数值单元格: %s' % nonnum[:3])

    status = 'OK  ' if not issues else 'ISSUE'
    if issues: allok = False
    suffix = ('; ' + ' | '.join(issues)) if issues else ''
    eol = 'CRLF' if crlf else 'LF'
    print('%-28s %-6s %4d行 %3d列 %-4s %s' % (fn, status, len(data), len(header), eol, suffix))

print()
print('结论:', '全部符合 UE5 导入要求 ✓' if allok else '存在需处理的问题（见上）')
print()
print('=== 附带信息 ===')
for fn in files[:3]:
    p = os.path.join(D, fn)
    raw = open(p,'rb').read()
    print('  %-28s %7d 字节, BOM=%s, 首行=%s' % (fn, len(raw), raw[:3]==b'\xef\xbb\xbf', raw.split(b'\n')[0][:60].decode('utf-8','replace')))
