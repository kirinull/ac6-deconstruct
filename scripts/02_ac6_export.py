# -*- coding: utf-8 -*-
# 02_ac6_export.py — FBX 导出
#   每部件每级 LOD 一个 FBX（LOD0 → fbx\，LOD1 → fbx\lod1\，LOD2 → fbx\lod2\）
#   整机合并版 AC6Mech_Assembled.fbx（9 个 LOD0 对象，按枢轴位置摆好）
# 导出设置：Forward = -Z，Up = Y，Apply Unit = ON，Scale = 1.0，三角化 = ON
import bpy, os, time

ROOT   = r'.'
ASSETS = os.path.join(ROOT, 'assets', 'mech')
BLEND  = os.path.join(ASSETS, 'AC6Mech.blend')
FBXDIR = os.path.join(ASSETS, 'fbx')
LOG    = os.path.join(ROOT, 'logs', 'export_log.txt')

PARTS = ['Torso', 'Head', 'Backpack', 'LegL', 'LegR', 'ArmL', 'ArmR', 'GunL', 'GunR']
_T0 = time.time()
_ERRORS = [0]

def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def progress(stage, done, total, item):
    el = time.time() - _T0
    spd = done / el if el > 0 else 0.0
    eta = (total - done) / spd if spd > 0 else 0.0
    log('[%s] %d/%d %.0f%% %s  (%.2f件/s, ETA %.0fs, 错误 %d)'
        % (stage, done, total, 100.0 * done / max(total, 1), item, spd, eta, _ERRORS[0]))

def export_fbx(path, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={'MESH'},
        use_mesh_modifiers=True,
        mesh_smooth_type='SMOOTH_GROUP',
        use_triangles=True,              # 三角化 ON
        use_custom_props=False,
        apply_unit_scale=True,           # Apply Unit ON
        apply_scale_options='FBX_SCALE_ALL',
        global_scale=1.0,                # Scale 1.0
        axis_forward='-Z',              # Forward = -Z
        axis_up='Y',                    # Up = Y
        bake_anim=False,                 # 无动画
    )
    return os.path.getsize(path)

def main():
    log('==== AC6 FBX 导出开始 | blender %s ====' % bpy.app.version_string)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    objs = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
    lod0 = []
    jobs = []
    for name in PARTS:
        jobs.append(('SM_AC6_%s' % name, os.path.join(FBXDIR, 'SM_AC6_%s.fbx' % name)))
        jobs.append(('SM_AC6_%s_LOD1' % name, os.path.join(FBXDIR, 'lod1', 'SM_AC6_%s_LOD1.fbx' % name)))
        jobs.append(('SM_AC6_%s_LOD2' % name, os.path.join(FBXDIR, 'lod2', 'SM_AC6_%s_LOD2.fbx' % name)))
    n = len(jobs) + 1
    for i, (obj_name, path) in enumerate(jobs, 1):
        try:
            if obj_name not in objs:
                raise KeyError('对象不存在: %s' % obj_name)
            size = export_fbx(path, [objs[obj_name]])
            if obj_name.count('_LOD') == 0:
                lod0.append(objs[obj_name])
            progress('EXPORT', i, n, '%s -> %s (%.1f KB)' % (obj_name, os.path.basename(path), size / 1024))
        except Exception as e:
            _ERRORS[0] += 1
            log('!! 导出失败 %s: %r' % (obj_name, e))
    # 整机合并版（作品集渲染用，9 个 LOD0 对象按枢轴摆好）
    try:
        path = os.path.join(FBXDIR, 'AC6Mech_Assembled.fbx')
        size = export_fbx(path, lod0)
        progress('EXPORT', n, n, 'AC6Mech_Assembled.fbx (%.1f KB)' % (size / 1024))
    except Exception as e:
        _ERRORS[0] += 1
        log('!! 整机导出失败: %r' % e)
    log('导出结束 | 错误 %d | 用时 %.1fs' % (_ERRORS[0], time.time() - _T0))

if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        log('!! 未捕获异常，原始输出:\n' + traceback.format_exc())
        raise
