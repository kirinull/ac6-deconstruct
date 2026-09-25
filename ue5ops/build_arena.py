# -*- coding: utf-8 -*-
"""L_Arena —— 白箱可驾驶测试场（M0 第 1 批 · S0）

【为什么新建而不是改 L_TuningRange】
    L_TuningRange 是 M0 的验收靶场（T1 转速 / T2 姿态 / T3 QB 冷却 / T4 重力），
    四条硬验收挂在它的 4 个靶子上，不能动。L_Arena 是"能开着跑的地方"，另外一张图。

【尺寸怎么来的（全部可算，不是拍脑袋）】
    机体按 10 m 标定（DT_LockCam.Bipedal_legs.ChrOrgOffsetY = 12 m 注视高度互证）。
    推进速度 DT_Booster.DashBoostEndSpeedKMH 中位 344 km/h = 95.6 m/s；
    RoundDashMaxSpeedKMPH 550 km/h = 152.8 m/s。
      · 1500 m 见方  ->  常规推进横穿 15.7 s，圆环冲刺横穿 9.8 s   （够做一次完整机动）
      · 原 L_TuningRange 地面是 120 m x 60 m -> 横穿 1.26 s，一次 QB 就出界
      · 参照柱每 100 m 一根、每 500 m 换色 -> 给"速度"提供视觉刻度

【为什么必须放参照柱】
    白箱只有纯色材质，地面没有纹理滚动 = 速度在画面上不可见。
    P1 报告 §16 说速度感由 7 条通道叠加；白箱阶段我们只有"位移 + 参照物"两条，
    所以参照物的密度就是速度感的全部来源。

用法：UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script="<本文件>"
      ⚠️ 这个脚本会 new_level + spawn + save，命令执行完后引擎在退出阶段会崩
         （python311.dll 里 EXCEPTION_ACCESS_VIOLATION，退出码 3）——
         这是 -run=pythonscript 下做关卡编辑的固有现象，**以产物为准，不看退出码**。
"""
import unreal

MAP_PATH = '/Game/AC6/Maps/L_Arena'
LOG = []


def out(s):
    unreal.log('[ARENA] ' + str(s))
    LOG.append(str(s))


def mesh(p):
    return unreal.load_object(None, p)


def ROT(pitch, yaw, roll):
    """★ 必须用关键字构造 Rotator。

    实测（2026-09-18，ue5ops/_scratch/editor_probe4.py 回读）：
        unreal.Rotator(-42, 30, 0)  实际得到  pitch=30, yaw=0, roll=-42
    也就是说 UE Python 的 FRotator **位置参数顺序是 (roll, pitch, yaw)**，
    不是 C++ 的 (Pitch, Yaw, Roll)，也不是文档里写的那个顺序。
    本项目原先按 (pitch,yaw,roll) 传参，于是：
        DirectionalLight rot=(-42, 30, 0)  ->  实际 pitch=+30（朝上照！）
    太阳朝天照 = 地面/方块全部无直射光；天空大气把太阳算到地平线以下 = 夜空全黑。
    这就是 L_Arena 与 L_TuningRange 两张图在编辑器视口和 -game 里全黑的真正原因。
    改用关键字参数后顺序不再有歧义。
    """
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)


def mat(p):
    return unreal.load_object(None, p)


M_CUBE = '/Engine/BasicShapes/Cube.Cube'
M_PLANE = '/Engine/BasicShapes/Plane.Plane'
MAT_BODY = '/Game/AC6/Materials/MI_AC6_Body.MI_AC6_Body'
MAT_GROUND = '/Game/AC6/Materials/MI_AC6_Ground.MI_AC6_Ground'
MAT_REF = '/Game/AC6/Materials/MI_AC6_Ref.MI_AC6_Ref'
MAT_GRID = '/Game/AC6/Materials/MI_AC6_Grid.MI_AC6_Grid'
MAT_BLOCK = '/Game/AC6/Materials/MI_AC6_Block.MI_AC6_Block'
MAT_TARGET = '/Game/AC6/Materials/MI_AC6_Target.MI_AC6_Target'
MAT_ACCENT = '/Game/AC6/Materials/MI_AC6_Accent.MI_AC6_Accent'

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def begin_fresh_level(path):
    """开一张空白关卡；最后统一用 save_map(world, path) 覆盖写盘。

    ★ 为什么不用 LevelEditorSubsystem.new_level(path)（2026-09-18 实测）：
      · path 已存在时它只打一行 "Error: NewLevel. Failed to validate the destination.
        An asset already exists at this location."，**不抛异常、也不建关卡** ——
        脚本会误以为建好了，其实所有 Actor 都 spawn 进了旧关卡。
      · 而 LevelEditorSubsystem.save_current_level() 会打印成功但**不写盘**
        （.umap 的修改时间不变）。
    "new_blank_map + save_map(world, path)" 两件套幂等、可重复、且真的落盘。
    """
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    w = unreal.EditorLevelLibrary.get_editor_world()
    out('  空白关卡 = %s' % w.get_path_name())
    return w

# ── 建新关卡 ────────────────────────────────────────────────────
try:
    begin_fresh_level(MAP_PATH)
except Exception as e:
    out('begin_fresh_level EXC: %r' % e)
    out('ARENA_DONE')
    raise SystemExit

spawned = []


def spawn(label, mesh_path, loc, scale=(1, 1, 1), rot=(0, 0, 0), mat_path=None):
    try:
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(*rot))
        if a is None:
            out('  spawn FAIL %s' % label)
            return None
        a.set_actor_label(label)
        smc = a.static_mesh_component
        smc.set_static_mesh(mesh(mesh_path))
        a.set_actor_scale3d(unreal.Vector(*scale))
        # ★ 必须 Movable：Static 网格在没构建光照时会渲染成黑，白箱看不出东西
        smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        smc.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        if mat_path:
            m = mat(mat_path)
            if m is not None:
                smc.set_material(0, m)
        spawned.append(a)
        return a
    except Exception as e:
        out('  spawn EXC %s: %r' % (label, e))
        return None


M2CM = 100.0     # m -> cm

# ── 1. 地面 1500 m x 1500 m ─────────────────────────────────────
spawn('Ground', M_PLANE, (0, 0, 0), scale=(1500, 1500, 1), mat_path=MAT_GROUND)
out('地面 1500 m x 1500 m')

# ── 2. 参照柱网格：每 100 m 一根，|x| 或 |y| == 500 的换成亮色（500 m 刻度）──
n_pillar = 0
n_tick = 0
for xi in range(1, 8):           # 100 .. 700
    for sign_x in (1, -1):
        for yi in range(1, 8):
            for sign_y in (1, -1):
                x = sign_x * xi * 100.0
                y = sign_y * yi * 100.0
                is_tick = (xi == 5) or (yi == 5)
                spawn('P_%d_%d%s%s' % (xi, yi, 'p' if sign_x > 0 else 'n', 'p' if sign_y > 0 else 'n'),
                      M_CUBE, (x * M2CM, y * M2CM, 400),
                      scale=(4, 4, 8), mat_path=(MAT_GRID if is_tick else MAT_REF))
                n_pillar += 1
                n_tick += 1 if is_tick else 0
out('参照柱 %d 根（其中 500 m 刻度亮色 %d 根）' % (n_pillar, n_tick))

# ── 3. 掩体块：20 块 40 x 40 x 60 m ─────────────────────────────
BLOCKS = [
    (250, 250), (-250, 250), (250, -250), (-250, -250),
    (400, 100), (-400, 100), (400, -100), (-400, -100),
    (100, 400), (-100, 400), (100, -400), (-100, -400),
    (600, 300), (-600, 300), (600, -300), (-600, -300),
    (300, 600), (-300, 600), (300, -600), (-300, -600),
]
for i, (bx, by) in enumerate(BLOCKS):
    spawn('Block_%02d' % i, M_CUBE, (bx * M2CM, by * M2CM, 3000),
          scale=(40, 40, 60), mat_path=MAT_BLOCK)
out('掩体块 %d 块（40 x 40 x 60 m）' % len(BLOCKS))

# ── 4. 平台：3 m（跳得上去，用于验证跳跃/落地）+ 30 m / 60 m（第 2 批飞行用）──
spawn('LowPlatform_3m', M_CUBE, (0, 300 * M2CM, 0), scale=(60, 60, 0.6), mat_path=MAT_BLOCK)
spawn('MidPlatform_30m', M_CUBE, (300 * M2CM, 0, 2700), scale=(60, 60, 6), mat_path=MAT_BLOCK)
spawn('HighPlatform_60m', M_CUBE, (-300 * M2CM, 0, 5400), scale=(60, 60, 6), mat_path=MAT_BLOCK)
spawn('HighPlatform_60m_B', M_CUBE, (0, -300 * M2CM, 5400), scale=(60, 60, 6), mat_path=MAT_BLOCK)
out('平台 4 块：3 m / 30 m / 60 m x2')

# ── 5. 边界墙（跑出 750 m 会掉下去，白箱先围起来）──────────────
W = 750.0
spawn('Wall_N', M_CUBE, (0, W * M2CM, 2000), scale=(1500, 4, 40), mat_path=MAT_BLOCK)
spawn('Wall_S', M_CUBE, (0, -W * M2CM, 2000), scale=(1500, 4, 40), mat_path=MAT_BLOCK)
spawn('Wall_E', M_CUBE, (W * M2CM, 0, 2000), scale=(4, 1500, 40), mat_path=MAT_BLOCK)
spawn('Wall_W', M_CUBE, (-W * M2CM, 0, 2000), scale=(4, 1500, 40), mat_path=MAT_BLOCK)
out('边界墙 4 面（±750 m，高 40 m）')

# ── 6. 刻度标记：原点四向 100 m 处的黄柱，给"我离原点多远"一个锚点 ──
for i, (dx, dy) in enumerate([(100, 0), (-100, 0), (0, 100), (0, -100)]):
    spawn('OriginMark_%d' % i, M_CUBE, (dx * M2CM, dy * M2CM, 600),
          scale=(2, 2, 12), mat_path=MAT_ACCENT)
out('原点标记 4 根')

# ── 7. 灯光（new_level 建的是空关卡，不加灯视口全黑）──────────
for cls_name, loc, rot, label in [
    ('DirectionalLight',     (0, 0, 2000), ROT(-42.0, 30.0, 0.0), 'SunLight'),   # 俯角 42° 朝下
    ('SkyLight',             (0, 0, 1000), (0, 0, 0),    'SkyLight'),
    ('SkyAtmosphere',        (0, 0, 0),    (0, 0, 0),    'SkyAtmosphere'),
    ('ExponentialHeightFog', (0, 0, 0),    (0, 0, 0),    'HeightFog'),
]:
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        out('  灯光类缺失: %s' % cls_name)
        continue
    try:
        a = eas.spawn_actor_from_class(cls, unreal.Vector(*loc), rot)
        a.set_actor_label(label)
        # ★ 自校验：把太阳的实际朝向读回来。太阳必须朝下（pitch < 0），否则场景全黑。
        if cls_name == 'DirectionalLight':
            got = a.get_actor_rotation()
            gv = (got.pitch, got.yaw, got.roll)
            want = (rot.pitch, rot.yaw, rot.roll)
            out('  SunLight 旋转 期望=%s 实际=%s %s' % (want, gv, 'OK' if abs(gv[0]-want[0]) < 0.01 else '★ 不符!'))
            if abs(gv[0] - want[0]) > 0.01:
                try:
                    a.set_actor_rotation(unreal.Rotator(pitch=want[0], yaw=want[1], roll=want[2]), False)
                    got = a.get_actor_rotation()
                    out('  已强制修正 -> pitch=%.1f' % got.pitch)
                except Exception as e2:
                    out('  强制修正失败 %r' % e2)
        try:
            a.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        except Exception:
            pass
        # ★ SkyLight 必须开实时捕获。
        #   默认 SourceType = CapturedScene 且 bRealTimeCapture = False —— 不捕获就是"没有环境光"，
        #   运行时报 "Cached lighting is used and real-time sky capture is enabled or can be cleared"，
        #   整个场景会黑。实测于 2026-09-18 第 1 批。
        if cls_name == 'SkyLight':
            # ★ SkyLight 必须开实时捕获，且必须回读确认。
            #   默认 SourceType=CapturedScene + bRealTimeCapture=False：静态捕获要在编辑器里
            #   "烘焙"一次并随关卡存盘。而本关卡是 **commandlet** 建的 —— commandlet 不渲染，
            #   recapture_sky() 永远不会完成，立方体贴图是空的 => 环境光为 0。
            #   所以 commandlet 建的关卡只能用 RealTimeCapture。
            lc = a.get_editor_property('light_component')
            ok = False
            for how in ('set_editor_property', 'set_real_time_capture'):
                try:
                    if how == 'set_editor_property':
                        lc.set_editor_property('real_time_capture', True)
                    else:
                        lc.set_real_time_capture(True)
                except Exception as e2:
                    out('  SkyLight %s EXC: %r' % (how, e2))
                try:
                    if lc.get_editor_property('real_time_capture'):
                        ok = True
                        out('  SkyLight real_time_capture=True 已确认（via %s）' % how)
                        break
                except Exception as e2:
                    out('  SkyLight 回读 EXC: %r' % e2)
            if not ok:
                out('  ★ SkyLight real_time_capture 设置失败，环境光会是 0')
            try:
                lc.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
            except Exception:
                pass
        spawned.append(a)
        out('  灯光 %s OK' % label)
    except Exception as e:
        out('  灯光 %s EXC: %r' % (label, e))

# ── 7.5 后处理体积 + WorldSettings（对齐模板关卡的已知可用配置）──────
# 实测对比（2026-09-18，editor_probe5.py）：
#   Lvl_ThirdPerson（能正常渲染）: WorldSettings.forceNoPrecomputedLighting=True
#                                  + 一个 unbound 的 PostProcessVolume（直方图自动曝光, bias=1.0）
#   L_Arena（全黑）              : forceNoPrecomputedLighting=False，且**没有后处理体积**
# 项目已设 r.AllowStaticLighting=False，此时关卡应声明"无预计算光照"；
# 否则渲染器会走"有静态光照"的分支，而本关卡从未构建过光照 -> 全黑。
try:
    w = unreal.EditorLevelLibrary.get_editor_world()
    ws = w.get_world_settings()
    ws.set_editor_property('force_no_precomputed_lighting', True)
    out('  WorldSettings.force_no_precomputed_lighting = True')
except Exception as e:
    out('  WorldSettings EXC: %r' % e)

try:
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume,
                                     unreal.Vector(0, 0, 20000), ROT(0.0, 0.0, 0.0))
    ppv.set_actor_label('PostProcess_Global')
    ppv.set_editor_property('unbound', True)
    st = ppv.get_editor_property('settings')
    st.set_editor_property('auto_exposure_method', unreal.AutoExposureMethod.AEM_HISTOGRAM)
    st.set_editor_property('auto_exposure_bias', 1.0)
    st.set_editor_property('auto_exposure_min_brightness', 0.03)
    st.set_editor_property('auto_exposure_max_brightness', 8.0)
    ppv.set_editor_property('settings', st)
    spawned.append(ppv)
    out('  PostProcessVolume(unbound) OK  bias=1.0 / AEM_HISTOGRAM')
except Exception as e:
    out('  PostProcessVolume EXC: %r' % e)

# ── 8. 出生点（机体胶囊半高 500 cm，抬高一点让它落地）──────────
try:
    ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 700), unreal.Rotator(0, 0, 0))
    ps.set_actor_label('PlayerStart')
    out('  PlayerStart OK')
except Exception as e:
    out('  PlayerStart EXC: %r' % e)

out('已生成 %d 个几何/灯光 Actor' % len(spawned))

# ★ 存盘必须用 EditorLoadingAndSavingUtils.save_map，不能只靠 LevelEditorSubsystem.save_current_level。
#   实测（2026-09-18）：save_current_level() 会打印成功、且不抛异常，
#   但 .umap 的修改时间**根本不变** —— 关卡实际上没写盘。
#   于是后续所有"我改了光照/加了后处理体积"的修复都停留在内存里，
#   编辑器/游戏读到的仍是旧关卡，白白排查了两小时。
saved_ok = False
try:
    wcur = unreal.EditorLevelLibrary.get_editor_world()
    saved_ok = unreal.EditorLoadingAndSavingUtils.save_map(wcur, MAP_PATH)
    out('save_map(%s) -> %s' % (MAP_PATH, saved_ok))
except Exception as e:
    out('save_map EXC: %r' % e)
if not saved_ok:
    try:
        les.save_current_level()
        out('回退 save_current_level() 已调用（结果不可靠）')
    except Exception as e:
        out('save_current_level EXC: %r' % e)

try:
    all_a = eas.get_all_level_actors()
    out('关卡内 Actor 总数 = %d' % len(all_a))
except Exception as e:
    out('get_all_level_actors EXC: %r' % e)

try:
    spawned.clear()
except Exception:
    pass
try:
    del les, eas
except Exception:
    pass
try:
    unreal.SystemLibrary.collect_garbage()
    out('collect_garbage OK')
except Exception as e:
    out('collect_garbage EXC: %r' % e)

out('ARENA_DONE')
