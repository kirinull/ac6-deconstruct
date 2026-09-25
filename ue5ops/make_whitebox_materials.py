# -*- coding: utf-8 -*-
"""白箱纯色材质（M0 第 1 批）

为什么需要这一步：
    /Engine/BasicShapes/* 自带的是灰色 BasicShapeMaterial，全灰分不出玩家/靶子/参照物。
    白箱允许"纯色材质"，但不允许手搓材质节点图。这里用 MaterialEditingLibrary
    以代码方式建一个只有 1 个 VectorParameter 的母材质，再派生若干颜色实例 ——
    全程没有打开材质编辑器，也没有 HLSL。

产出：
    /Game/AC6/Materials/M_AC6_Whitebox     母材质（VectorParameter "Color" -> BaseColor）
    /Game/AC6/Materials/MI_AC6_Body        机体（冷蓝灰）
    /Game/AC6/Materials/MI_AC6_Ground      地面（深灰）
    /Game/AC6/Materials/MI_AC6_Ref         参照柱（中灰）
    /Game/AC6/Materials/MI_AC6_Grid        500m 粗刻度（亮灰）
    /Game/AC6/Materials/MI_AC6_Block       掩体块（暖灰）
    /Game/AC6/Materials/MI_AC6_Target      靶子（红）
    /Game/AC6/Materials/MI_AC6_Accent      标记（黄）
"""
import unreal

MAT_DIR = '/Game/AC6/Materials'
LOG = []


def out(s):
    unreal.log('[MAT] ' + str(s))
    LOG.append(str(s))


def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


ensure_dir(MAT_DIR)

# ── 母材质 ────────────────────────────────────────────────────────
MASTER = MAT_DIR + '/M_AC6_Whitebox'
master = unreal.load_object(None, MASTER)
if master is None:
    master = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'M_AC6_Whitebox', MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    out('创建母材质 %s' % MASTER)
    expr = unreal.MaterialEditingLibrary.create_material_expression(
        master, unreal.MaterialExpressionVectorParameter, -400, 0)
    expr.set_editor_property('parameter_name', 'Color')
    expr.set_editor_property('default_value', unreal.LinearColor(0.75, 0.75, 0.78, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        expr, '', unreal.MaterialProperty.MP_BASE_COLOR)

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        master, unreal.MaterialExpressionConstant, -400, 220)
    rough.set_editor_property('r', 0.85)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, '', unreal.MaterialProperty.MP_ROUGHNESS)

    unreal.MaterialEditingLibrary.recompile_material(master)
    unreal.EditorAssetLibrary.save_loaded_asset(master)
else:
    out('母材质已存在 %s' % MASTER)

# ── 颜色实例 ──────────────────────────────────────────────────────
COLORS = [
    ('MI_AC6_Body',   (0.06, 0.22, 0.75, 1.0)),   # 机体：冷蓝
    ('MI_AC6_Ground', (0.17, 0.18, 0.21, 1.0)),   # 地面：中深灰
    # ★ 2026-09-18 修正：原先给的是 (0.06,0.07,0.09) 近黑，
    #   1500 m 见方的近黑地面会把自动曝光的画面整体压暗到看不清；
    #   白箱要的是"看得见"，不是"好看"。
    ('MI_AC6_Ref',    (0.30, 0.31, 0.34, 1.0)),   # 参照柱
    ('MI_AC6_Grid',   (0.62, 0.63, 0.66, 1.0)),   # 500m 粗刻度
    ('MI_AC6_Block',  (0.42, 0.36, 0.30, 1.0)),   # 掩体块
    ('MI_AC6_Target', (0.85, 0.13, 0.10, 1.0)),   # 靶子：红
    ('MI_AC6_Accent', (0.95, 0.80, 0.10, 1.0)),   # 标记：黄
]

made = 0
for name, rgb in COLORS:
    path = '%s/%s' % (MAT_DIR, name)
    mi = unreal.load_object(None, path)
    if mi is None:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        made += 1
    mi.set_editor_property('parent', master)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, 'Color', unreal.LinearColor(rgb[0], rgb[1], rgb[2], rgb[3]))
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    out('  %-18s parent=%s color=%s' % (name, master.get_name(), rgb))

out('新建实例 %d 个 / 共 %d 个' % (made, len(COLORS)))
out('MAT_DONE')
