
# -*- coding: utf-8 -*-
import os, re, io, importlib.util
spec = importlib.util.spec_from_file_location('pf', r'./tools/paramdex_fields.py')
pf = importlib.util.module_from_spec(spec); spec.loader.exec_module(pf)
BT = chr(96)

SKIP2 = ['faceScale','originEquipPro','originEquipWep','dummy','pad','vagrant','qwcId','residentSpEffect',
         'correctStrength','correctAgility','corretMagic','corretFaith','magGuardCutRate','fireGuardCutRate',
         'thunGuardCutRate','physGuardCutRate','enableSorcery','enableMiracle','enableVowMagic','enableMagic',
         'antiDemonDamageRate','attackBaseMagic','attackBaseFire','attackBaseThunder','defenseMagic','defenseFire',
         'defenseThunder','resistBurn','resistCurse','resistHighPlasma','defenseSlash','defenseBlow','defenseThrust',
         'resistStun','defenseDark','defenseMaterial','iconIdM','iconIdF','equipModelGender','equipModelCategory']
KEY = re.compile(r'stability|impact|attitude|attack|damage|defen|weight|energy|heat|cool|boost|thrust|'
                 r'speed|bullet|shoot|reload|magazine|ammo|charge|recoil|range|lock|fov|camera|shake|rumble|'
                 r'homing|blade|melee|guard|parry|stagger|break|hit|sfx|sound|jitter|ik|lookat|aim|turn|'
                 r'walk|run|jump|fly|hover|gravity|accel|brake|damp|spring|track|search|think|action|behavior|'
                 r'price|value|slot|equip|parts|stamina|durability|cost|consum|recover|en$|_en', re.I)

TABLES = [
 ('EquipParamWeapon','武器 389 槽 / 1556 B'),
 ('EquipParamProtector','护甲部件 225 槽 / 900 B'),
 ('EquipParamBooster','推进器 96 槽 / 384 B'),
 ('EquipParamGenerator','发电机 85 槽 / 340 B'),
 ('EquipParamFcs','火控 FCS 52 槽 / 208 B'),
 ('AtkParam','攻击参数（对应 AtkParam_Pc）260 槽 / 1040 B'),
 ('BulletParam','弹丸 222 槽 / 888 B'),
 ('BoostParam','推进 32 槽 / 128 B'),
 ('LockCamParam','相机锁定 94 槽 / 376 B'),
 ('PadRumble','震动/抖动 21 槽 / 84 B'),
 ('JigglerBaseParam','机械二次运动（惯性晃动）'),
 ('FootIKParam','脚部 IK'),
 ('NpcParam','敌人 480 槽 / 1920 B'),
 ('BehaviorParam','行为 52 槽 / 208 B'),
]
def keep_fields(tbl):
    p = os.path.join(pf.PD, 'Defs', tbl + '.xml')
    if not os.path.exists(p): return None, None
    fl, total = pf.fields_of(p)
    keep = []
    for off, typ, name, disp in fl:
        base = name.split(':')[0].split('[')[0]
        lo = base.lower()
        if any(s.lower() in lo for s in SKIP2): continue
        if typ == 'dummy8' and not KEY.search(base): continue
        if not KEY.search(base) and not KEY.search(disp or ''): continue
        keep.append((off, typ, base, (disp or '').strip()))
    return keep, total

out = ['# AC6 → UE5 字段参考（由 AC6 paramdex 提取，2026-09-11）', '',
       '> 来源：本机 AC6 专用 paramdex，结构大小已与实测 .param 行宽校验一致。',
       '> **偏移 = 该字段在一条记录内的字节偏移**，可直接用于 DataTable 建模。',
       '> 已过滤 dummy / pad / 魂系残留字段。完整字段见 @@@python tools/paramdex_fields.py <表名>@@@。', '']
summary = []
for tbl, desc in TABLES:
    keep, total = keep_fields(tbl)
    if keep is None:
        out.append('## %s（%s）' % (tbl, desc)); out.append(''); out.append('*paramdex 无此表*'); out.append(''); continue
    out.append('## %s' % tbl)
    out.append('')
    out.append('%s｜结构 **%d 字节**｜命中关键字段 **%d** 个' % (desc, total, len(keep)))
    out.append('')
    out.append('| 偏移 | 类型 | 字段名 | 日文说明 |')
    out.append('|---:|---|---|---|')
    for off, typ, name, disp in keep[:55]:
        out.append('| %d | %s | @@@%s@@@ | %s |' % (off, typ, name, disp[:44]))
    if len(keep) > 55:
        out.append('| … | | *（另有 %d 个，见工具完整输出）* | |' % (len(keep)-55))
    out.append('')
    summary.append((tbl, len(keep), total))
txt = '\n'.join(out).replace('@@@', BT)
path = r'./data/字段参考.md'
io.open(path, 'w', encoding='utf-8').write(txt)
print('已写出 %s （%d 字符）' % (path, len(txt)))
print()
for t, n, tot in summary:
    print('  %-24s 结构 %-6d 关键字段 %d' % (t, tot, n))
