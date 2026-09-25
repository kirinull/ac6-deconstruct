# -*- coding: utf-8 -*-
# 验证 AC6DataHub 读取层：逐个 getter 调用 + 契约检查
import unreal

def out(s): unreal.log('[HUB] ' + str(s))

out('AC6DataHub 存在: %s' % hasattr(unreal, 'AC6DataHub'))
if not hasattr(unreal, 'AC6DataHub'):
    out('FAIL 类未暴露给 Python'); raise SystemExit

# --- 1) 单行表：GetGameSettings ---
try:
    r = unreal.AC6DataHub.get_game_settings()
    out('get_game_settings() -> %s' % (str(r)[:200],))
except Exception as e:
    out('get_game_settings EXC: %r' % e)

# --- 2) 逐表 getter：先拿行名，再取第一行 ---
CASES = [
    ('Booster',      'get_booster_row',   'DT_Booster'),
    ('Protector',    'get_protector_row', 'DT_Protector'),
    ('Weapon',       'get_weapon_row',    'DT_Weapon'),
    ('Generator',    'get_generator_row', 'DT_Generator'),
    ('Fcs',          'get_fcs_row',       'DT_Fcs'),
    ('Attack',       'get_attack_row',    'DT_Attack'),
    ('Bullet',       'get_bullet_row',    'DT_Bullet'),
    ('Npc',          'get_npc_row',       'DT_Npc'),
]
for label, fn_name, dt_name in CASES:
    dt = unreal.load_object(None, '/Game/AC6/Data/Tables/%s.%s' % (dt_name, dt_name))
    if dt is None:
        out('%-10s 表缺失 %s' % (label, dt_name)); continue
    rows = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
    if not rows:
        out('%-10s 无行' % label); continue
    fn = getattr(unreal.AC6DataHub, fn_name, None)
    if fn is None:
        out('%-10s 函数缺失 %s' % (label, fn_name)); continue
    try:
        res = fn(rows[0])
        ok = res[0] if isinstance(res, tuple) else res
        out('%-10s 行=%-24s -> %s' % (label, str(rows[0])[:24], str(res)[:150]))
    except Exception as e:
        out('%-10s EXC: %r' % (label, e))

# --- 3) 契约：不存在的行名必须返回 False，不能静默返回全 0 ---
try:
    r2 = unreal.AC6DataHub.get_booster_row(unreal.Name('__NOT_EXIST__'))
    ok2 = r2[0] if isinstance(r2, tuple) else r2
    out('不存在的行名 -> 返回 %s  (应为 False)' % ok2)
except Exception as e:
    out('不存在的行名 EXC: %r' % e)

# --- 4) GetRowNames ---
try:
    dt = unreal.load_object(None, '/Game/AC6/Data/Tables/DT_Booster.DT_Booster')
    names = unreal.AC6DataHub.get_row_names(dt)
    out('get_row_names(DT_Booster) -> %d 个，前 3: %s' % (len(names), str(list(names)[:3])))
except Exception as e:
    out('get_row_names EXC: %r' % e)
out('HUB_DONE')
