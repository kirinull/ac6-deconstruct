# -*- coding: utf-8 -*-
"""从 data/ue_datatables/*.struct.txt 生成 C++ 行结构体头文件

决策依据：用户 2026-09-18 拍板走「路线 B（C++ 结构体）」。
原因：Python 无法给 UserDefinedStruct 加字段（UserDefinedStructEditorUtils 未暴露），
      且 CSVImportFactory 在无 RowStruct 时直接放弃（CSVImportFactory.cpp:260）。
      项目本就是 C++ 类型（冻结决策 #3），模块与编译链路早已就绪。
"""
import io, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

D    = r'.\data\ue_datatables'
OUT  = r'<UE_PROJECTS>\AC6Proto\Source\AC6Proto\AC6DataRows.h'

# 结构体名覆盖（struct.txt 里已给 F*Row，直接沿用）
def parse_struct(path):
    raw = io.open(path, encoding='utf-8').read()
    # struct.txt 每行都带 '// ' 注释前缀，先剥掉再解析
    txt = chr(10).join(re.sub(r'^\s*//\s?', '', ln) for ln in raw.split(chr(10)))
    m = re.search(r'struct\s+(F\w+)\s*:\s*public\s+FTableRowBase', txt)
    if not m: return None
    name = m.group(1)
    # 字段：UPROPERTY(...) <type> <Name> = <default>;  取行前的 /** ... */ 作注释
    fields = []
    for fm in re.finditer(r'/\*\*\s*(.*?)\s*\*/\s*UPROPERTY\([^)]*\)\s+([A-Za-z0-9_]+)\s+([A-Za-z_]\w*)\s*=\s*([^;]+);', txt, re.S):
        doc, ftype, fname, dflt = fm.group(1).strip(), fm.group(2), fm.group(3), fm.group(4).strip()
        fields.append((ftype, fname, dflt, doc))
    header = re.search(r'paramdex\s+(?:结构\s+)?(\S+)\s+字节\s+vs\s+实际\s+(\S+)\s+字节\s*->\s*(\w+)', txt)
    size = header.groups() if header else ('?','?','?')
    return name, fields, size

tables = []
for f in sorted(os.listdir(D)):
    if f.endswith('.struct.txt'):
        r = parse_struct(os.path.join(D, f))
        if r: tables.append((f[:-11],) + r)
print('解析到 %d 张表：' % len(tables))
for base, sname, fields, size in tables:
    print('   %-22s %-26s %2d 字段  尺寸校验 %s' % (base, sname, len(fields), size[2]))

# ---- 生成头文件 ----
L = []
L.append('// Copyright Epic Games, Inc. All Rights Reserved.')
L.append('//')
L.append('// AC6DataRows.h —— 《装甲核心6》数据表行结构体')
L.append('//')
L.append('// 【自动生成，请勿手改】由 .\\ue5ops\\gen_data_rows.py 生成')
L.append('// 数据源：data/ue_datatables/*.struct.txt（源自 paramdex + regulation.bin 实测偏移）')
L.append('// 列名与同名 CSV 的表头逐字符一致（UE 按列名匹配结构体字段，不一致会导入失败）')
L.append('//')
L.append('// 证据等级：字段偏移 = A（paramdex 原文 + 本机 param 尺寸校验 MATCH）')
L.append('#pragma once')
L.append('')
L.append('#include "CoreMinimal.h"')
L.append('#include "Engine/DataTable.h"')
L.append('#include "AC6DataRows.generated.h"')
L.append('')
for base, sname, fields, size in tables:
    L.append('// ---------------------------------------------------------------------------')
    L.append('// %s   (paramdex 结构 %s B vs 实际 %s B -> %s)' % (base, size[0], size[1], size[2]))
    L.append('// ---------------------------------------------------------------------------')
    L.append('USTRUCT(BlueprintType)')
    L.append('struct %s : public FTableRowBase' % sname)
    L.append('{')
    L.append('\tGENERATED_BODY()')
    L.append('')
    for ftype, fname, dflt, doc in fields:
        # float 默认值带小数点时必须加 f 后缀，否则 MSVC 报 C4305（double -> float 截断）
        if ftype == 'float' and '.' in dflt and not dflt.endswith('f'):
            dflt = dflt + 'f'
        doc1 = doc.replace('*/', '* /').replace('\n', ' ')
        L.append('\t/** %s */' % doc1)
        L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
        L.append('\t%s %s = %s;' % (ftype, fname, dflt))
        L.append('')
    L.append('};')
    L.append('')
# ---- M0 3.6 D：唯一需要手写的全局配置表（不属于任何源表）----
L.append('// ---------------------------------------------------------------------------')
L.append('// GameSettings  —— M0 手写表：跨表全局常数（M0 3.6 D）')
L.append('//   值来源：M0 第 4 部分「直接抄」表；除 StaggerDurationSec / DirectHitMultPercent')
L.append('//   为占位（AC6 硬直时长随速度变化，需自行标定）外，其余均为 B 级')
L.append('// ---------------------------------------------------------------------------')
L.append('USTRUCT(BlueprintType)')
L.append('struct FGameSettingsRow : public FTableRowBase')
L.append('{')
L.append('\tGENERATED_BODY()')
L.append('')
L.append('\t/** 冲击衰减寿命[s]（= GameSystemParam.Damage_ImpactLifeTimeSec） */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tfloat ImpactLifeTimeSec = 1.5f;')
L.append('')
L.append('\t/** 部位伤害倍率（= EquipParamProtector.partsDamageRate 全表恒 1.5） */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tfloat PartsDamageMult = 1.5f;')
L.append('')
L.append('\t/** 重力[m/s^2]（= TentativePlayerParam.MovementGravity） */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tfloat GravityMPSS = 120.0f;')
L.append('')
L.append('\t/** ★占位：硬直基准时长[s]，AC6 实际随速度变化，需标定 */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tfloat StaggerDurationSec = 1.2f;')
L.append('')
L.append('\t/** ★占位：直击补正基准[%]，需标定 */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tint32 DirectHitMultPercent = 100;')
L.append('')
L.append('\t/** 基准转向速度[deg/s]（= ChrActTurnParam.baseTurnSpeedDPS 玩家件） */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tfloat BaseTurnSpeedDPS = 400;')
L.append('')
L.append('\t/** 坦克角加速度[deg/s^2]（= ChrTurnAccelDPSS） */')
L.append('\tUPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "AC6")')
L.append('\tfloat TankTurnAccelDPSS = 230;')
L.append('')
L.append('};')
L.append('')
txt = '\n'.join(L)
io.open(OUT, 'w', encoding='utf-8-sig', newline='\r\n').write(txt)
print()
print('已写 %s' % OUT)
print('  %d 行, %d 字节 (UTF-8 with BOM, CRLF)' % (len(L), len(txt.encode('utf-8-sig'))))
