# -*- coding: utf-8 -*-
# 在编辑器上下文里运行：把 data/ue_datatables/*.csv 导入为 DataTable
import unreal, os

# 用 prepare_csv.py 修正过行名冲突的副本（原目录归文档 session，不改）
CSV_DIR  = r'<UE_PROJECTS>\\AC6Proto\\data\\ue_datatables'
DEST     = '/Game/AC6/Data/Tables'
MODULE   = 'AC6Proto'

TABLES = [
    ('EquipParamBooster',   'FEquipParamBoosterRow',   'DT_Booster'),
    ('EquipParamProtector', 'FEquipParamProtectorRow', 'DT_Protector'),
    ('EquipParamWeapon',    'FEquipParamWeaponRow',    'DT_Weapon'),
    ('EquipParamGenerator', 'FEquipParamGeneratorRow', 'DT_Generator'),
    ('EquipParamFcs',       'FEquipParamFcsRow',       'DT_Fcs'),
    ('AtkParam_Pc',         'FAtkParam_PcRow',         'DT_Attack'),
    ('Bullet',              'FBulletRow',              'DT_Bullet'),
    ('NpcParam',            'FNpcParamRow',            'DT_Npc'),
    ('GameSettings',        'FGameSettingsRow',        'DT_GameSettings'),
    # ---- 第 1 批新增：镜头 / 移动 / 转向 / 玩家 / 抖动 / 推进 六张表 ----
    ('LockCamParam',        'FLockCamParamRow',        'DT_LockCam'),
    ('MovementAcTypeParam', 'FMovementAcTypeParamRow', 'DT_MovementAc'),
    ('ChrActTurnParam',     'FChrActTurnParamRow',     'DT_Turn'),
    ('TentativePlayerParam','FTentativePlayerParamRow','DT_PlayerParam'),
    ('PadRumble',           'FPadRumbleRow',           'DT_Rumble'),
    ('BoostParam',          'FBoostParamRow',          'DT_BoostParam'),
    # ---- 第 2 批新增：攻击 ID 映射（本项目自建，见 ue5ops/build_attack_id_map.py）----
    ('AttackIdMap',         'FAttackIdMapRow',         'DT_AttackIdMap'),
    ('BulletCombat',        'FBulletCombatRow',        'DT_BulletCombat'),
]

def out(s): unreal.log('[IMPORT] ' + str(s))

at = unreal.AssetToolsHelpers.get_asset_tools()
ok = fail = 0
for csv_base, struct_name, dt_name in TABLES:
    csv_path = os.path.join(CSV_DIR, csv_base + '.csv')
    if not os.path.exists(csv_path):
        out('MISS csv: ' + csv_path); fail += 1; continue
    # UE 会剥掉 USTRUCT 名的 F 前缀：FEquipParamBoosterRow -> /Script/AC6Proto.EquipParamBoosterRow
    short = struct_name[1:] if struct_name.startswith('F') else struct_name
    row_struct = None; struct_path = ''
    for cand in (short, struct_name):
        struct_path = '/Script/%s.%s' % (MODULE, cand)
        row_struct = unreal.load_object(None, struct_path)
        if row_struct is not None: break
    if row_struct is None:
        out('MISS struct: ' + struct_path); fail += 1; continue

    task = unreal.AssetImportTask()
    task.set_editor_property('filename', csv_path)
    task.set_editor_property('destination_path', DEST)
    task.set_editor_property('destination_name', dt_name)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)

    fac = unreal.CSVImportFactory()
    settings = fac.get_editor_property('automated_import_settings')
    settings.set_editor_property('import_row_struct', row_struct)
    settings.set_editor_property('import_type', unreal.CSVImportType.ECSV_DATA_TABLE)
    fac.set_editor_property('automated_import_settings', settings)
    task.set_editor_property('factory', fac)

    try:
        at.import_asset_tasks([task])
        paths = task.get_editor_property('imported_object_paths')
        if paths:
            dt = unreal.load_object(None, paths[0])
            n = len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)) if dt else 0
            out('OK   %-20s -> %-14s rows=%d' % (csv_base, dt_name, n))
            ok += 1
        else:
            out('FAIL %-20s 无 imported_object_paths' % csv_base); fail += 1
    except Exception as e:
        out('EXC  %-20s %r' % (csv_base, e)); fail += 1

out('DONE ok=%d fail=%d' % (ok, fail))
