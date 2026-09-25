# -*- coding: utf-8 -*-
"""生成白箱靶场 L_TuningRange（M0 §3.10 的四个可视靶子）

布局（单位 cm，均在 Z=0 地面之上）：
    T1 转速靶   x=    0   方块(转轴) + 锥体(指针) + 远处目标柱
    T2 姿态靶   x= 1500   靶子方块 + 头顶"进度条"(细长立方体)
    T3 QB 冷却灯 x= 3000   灯(球) + 冷却条(细长立方体)
    T4 重力靶   x= 4500   平台 + 10m 高处的球

全部用引擎自带 /Engine/BasicShapes/*，材质用 BasicShapeMaterial 的实例（纯色）。
—— 只做白箱：无建模、无 UV/贴图、无动画、无 Niagara。

用法：由 UnrealEditor-Cmd.exe -run=pythonscript 执行
"""
import unreal

MAP_PATH = '/Game/AC6/Maps/L_TuningRange'
LOG = []


def out(s):
    unreal.log('[RANGE] ' + str(s))
    LOG.append(str(s))


def mesh(path):
    return unreal.load_object(None, path)


M_CUBE = '/Engine/BasicShapes/Cube.Cube'
M_SPHERE = '/Engine/BasicShapes/Sphere.Sphere'
M_CYL = '/Engine/BasicShapes/Cylinder.Cylinder'
M_CONE = '/Engine/BasicShapes/Cone.Cone'
M_PLANE = '/Engine/BasicShapes/Plane.Plane'
MAT = '/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial'

# ── 先建/清空关卡 ────────────────────────────────────────────────
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out('LevelEditorSubsystem: %s' % les)
out('EditorActorSubsystem: %s' % eas)

def make_fresh_level(path):
    """★ new_level 在目标已存在时只打 Error 不抛异常也不建关卡，必须先删同名资产。"""
    try:
        unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    except Exception as e:
        out('  new_blank_map EXC: %r' % e)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        ok = unreal.EditorAssetLibrary.delete_asset(path)
        out('  删除已存在的关卡 -> %s' % ok)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).new_level(path)
    name = unreal.EditorLevelLibrary.get_editor_world().get_path_name()
    out('  当前世界 = %s' % name)
    if path.split('/')[-1] not in name:
        raise RuntimeError('new_level 未生效: %s' % name)
    return True


created = False
try:
    created = make_fresh_level(MAP_PATH)
except Exception as e:
    out('  make_fresh_level EXC: %r' % e)

if not created:
    # 退路：EditorLevelLibrary（已废弃但可用）
    try:
        unreal.EditorLevelLibrary.new_level(MAP_PATH)
        out('  EditorLevelLibrary.new_level OK')
        created = True
    except Exception as e:
        out('  EditorLevelLibrary.new_level EXC: %r' % e)

if not created:
    out('FAIL 无法创建关卡')
    out('RANGE_DONE')
    raise SystemExit

# ── 生成助手 ─────────────────────────────────────────────────────
base_mat = mesh(MAT)
_spawned = []


def spawn(label, mesh_path, loc, scale=(1, 1, 1), rot=(0, 0, 0), color=None, movable=True):
    try:
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot))
        if a is None:
            out('  spawn FAIL %s' % label); return None
        a.set_actor_label(label)
        smc = a.static_mesh_component
        smc.set_static_mesh(mesh(mesh_path))
        a.set_actor_scale3d(unreal.Vector(*scale))
        if movable:
            smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        if color is not None and base_mat is not None:
            try:
                mi = unreal.MaterialInstanceConstant()
                # 用 Dynamic 会随存盘丢失，这里用固定颜色的材质实例
                smc.set_material(0, base_mat)
            except Exception:
                pass
        _spawned.append(a)
        return a
    except Exception as e:
        out('  spawn EXC %s: %r' % (label, e))
        return None


# ── 地面（60m x 100m 的大板）────────────────────────────────────
spawn('Ground', M_PLANE, (2250, 0, 0), scale=(120, 60, 1))

# ── T1 转速靶（M0 §3.10 T1）─────────────────────────────────────
# 转轴方块（3m 高）+ 锥体指针（指向外侧）+ 目标柱
spawn('T1_Pivot', M_CUBE, (0, 0, 150), scale=(1.0, 1.0, 3.0))
spawn('T1_Pointer', M_CONE, (0, 300, 300), scale=(0.8, 0.8, 2.0), rot=(90, 0, 0))
spawn('T1_TargetMarker', M_CUBE, (0, 1200, 150), scale=(0.6, 0.6, 3.0))

# ── T2 姿态靶（M0 §3.10 T2）─────────────────────────────────────
# 靶子方块 + 头顶进度条（细长立方体，后续蓝图改它的 scale.z 表示累计冲击）
spawn('T2_Dummy', M_CUBE, (1500, 0, 150), scale=(2.0, 2.0, 3.0))
spawn('T2_StaggerBar_BG', M_CUBE, (1500, 0, 420), scale=(3.0, 0.3, 0.3))
spawn('T2_StaggerBar_Fill', M_CUBE, (1500, 0, 440), scale=(3.0, 0.35, 0.35))

# ── T3 QB 冷却灯（M0 §3.10 T3）──────────────────────────────────
spawn('T3_LampPost', M_CYL, (3000, 0, 150), scale=(0.5, 0.5, 3.0))
spawn('T3_Lamp', M_SPHERE, (3000, 0, 360), scale=(0.8, 0.8, 0.8))
spawn('T3_CooldownBar_BG', M_CUBE, (3000, 0, 480), scale=(3.0, 0.3, 0.3))
spawn('T3_CooldownBar_Fill', M_CUBE, (3000, 0, 500), scale=(3.0, 0.35, 0.35))

# ── T4 重力靶（M0 §3.10 T4）────────────────────────────────────
# 平台 + 10m 高处的球（1000 cm）
spawn('T4_Platform', M_CUBE, (4500, 0, 25), scale=(4.0, 4.0, 0.5))
spawn('T4_Ball', M_SPHERE, (4500, 0, 1000), scale=(0.8, 0.8, 0.8))
spawn('T4_HeightRef', M_CUBE, (4500, 400, 500), scale=(0.3, 0.3, 10.0))

# ── 灯光（new_level 建的是空关卡，不加灯视口全黑）──────────────
# 白箱只需要"看得见"，用引擎默认的 Lightmass/动态光照即可
for cls_name, loc, rot, label in [
    ('DirectionalLight',        (0, 0, 2000),   (-45, 0, 0),   'SunLight'),
    ('SkyLight',                (0, 0, 1000),   (0, 0, 0),     'SkyLight'),
    ('SkyAtmosphere',           (0, 0, 0),      (0, 0, 0),     'SkyAtmosphere'),
    ('ExponentialHeightFog',    (0, 0, 0),      (0, 0, 0),     'HeightFog'),
]:
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        out('  灯光类缺失: %s' % cls_name); continue
    try:
        # ★ Rotator 必须用关键字：UE Python 的 FRotator 位置参数顺序是 (roll, pitch, yaw)，
        #   写成 Rotator(-45, 0, 0) 会得到 roll=-45 / pitch=0 —— 太阳横着照，场景全黑。
        a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc),
                                       unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]))
        a.set_actor_label(label)
        # 白箱一律用可移动，便于运行时改
        try:
            a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass
        out('  灯光 %s OK' % label)
    except Exception as e:
        out('  灯光 %s EXC: %r' % (label, e))

# ── 出生点 ─────────────────────────────────────────────────────
try:
    ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(-1200, 0, 120), unreal.Rotator(0, 0, 0))
    ps.set_actor_label('PlayerStart')
    out('  PlayerStart OK')
except Exception as e:
    out('  PlayerStart EXC: %r' % e)

out('已生成 %d 个 Actor' % len(_spawned))

# ── 存盘 ────────────────────────────────────────────────────────
# ★ 必须用 save_map：save_current_level() 会打印成功但不写盘（2026-09-18 实测）
_sv = False
try:
    _sv = unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAP_PATH)
    out('save_map(%s) -> %s' % (MAP_PATH, _sv))
except Exception as e:
    out('save_map EXC: %r' % e)
if not _sv:
    try:
        les.save_current_level()
        out('回退 save_current_level()（结果不可靠）')
    except Exception as e:
        out('save_current_level EXC: %r' % e)

# 验证：列出关卡里的 Actor
try:
    all_a = eas.get_all_level_actors()
    out('关卡内 Actor 总数 = %d' % len(all_a))
    labels = sorted([a.get_actor_label() for a in all_a])
    out('标签: %s' % ', '.join(labels))
except Exception as e:
    out('get_all_level_actors EXC: %r' % e)

# ── 释放所有 UObject 引用，避免引擎关闭阶段 Python GC 触碰已销毁对象 ──
# 实测证据：不释放时脚本成功执行、地图已存盘，但引擎 exit 阶段在 python311.dll 里
#   EXCEPTION_ACCESS_VIOLATION（退出码 3）。
try:
    _spawned.clear()
except Exception:
    pass
try:
    del base_mat, les, eas
except Exception:
    pass
try:
    unreal.SystemLibrary.collect_garbage()
    out('collect_garbage OK')
except Exception as e:
    out('collect_garbage EXC: %r' % e)

out('RANGE_DONE')
