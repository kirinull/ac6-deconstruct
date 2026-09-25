# -*- coding: utf-8 -*-
# 03_ac6_render.py — 三视图正交渲染（前/左/顶）+ 膝点标注侧视图 + 26m/45° 剪影测试
#   正交图：2048 px / 10.24 m = 200 px/m（按 508 DPI 打印即 1:100），背景纯白
#   剪影：相机距离 26 m，垂直画角 45°，纯黑剪影 / 白底
import bpy, os, math, time
from array import array
from mathutils import Vector

ROOT    = r'.'
ASSETS  = os.path.join(ROOT, 'assets', 'mech')
BLEND   = os.path.join(ASSETS, 'AC6Mech.blend')
RDIR    = os.path.join(ASSETS, 'renders')
LOG     = os.path.join(ROOT, 'logs', 'render_log.txt')
_T0 = time.time()

def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def make_world(sc):
    w = bpy.data.worlds.new('AC6_White')
    w.use_nodes = False
    w.color = (1.0, 1.0, 1.0)
    sc.world = w

def make_cam(sc, name, loc, target, ortho=None, vfov=None):
    cd = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho is not None:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    else:
        cd.type = 'PERSP'
        cd.sensor_fit = 'VERTICAL'
        cd.sensor_height = 32.0
        cd.lens = 16.0 / math.tan(math.radians(vfov) / 2.0)   # 垂直画角 = vfov
    sc.camera = cam
    return cam

def render_to(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    log('渲染完成 %s (%.1fs)' % (os.path.basename(path), time.time() - _T0))

def whiten_bg(path, thresh=0.15):
    """剪影只有黑/底两个色阶：底色一律刷白（确定性后处理，不赌 Workbench 背景行为）"""
    img = bpy.data.images.load(path)
    n = len(img.pixels)
    px = array('f', [0.0]) * n
    img.pixels.foreach_get(px)
    for i in range(0, n, 4):
        if px[i] > thresh:
            px[i] = px[i + 1] = px[i + 2] = 1.0
    img.pixels.foreach_set(px)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)
    log('剪影背景刷白完成 %s' % os.path.basename(path))

def main():
    log('==== AC6 渲染开始 | blender %s ====' % bpy.app.version_string)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc = bpy.context.scene
    # 渲染只用 LOD0；LOD1/LOD2 不出图
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and '_LOD' in ob.name:
            ob.hide_render = True
    make_world(sc)
    sc.render.resolution_x = 2048
    sc.render.resolution_y = 2048
    sc.render.film_transparent = False

    # 引擎：Workbench（硬表面平涂）；后台拿不到 GL 上下文时降级 Cycles CPU
    engine = 'WORKBENCH'
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'FLAT'
    sc.display.shading.color_type = 'MATERIAL'
    sc.display.shading.background_type = 'VIEWPORT'
    sc.display.shading.background_color = (1.0, 1.0, 1.0)   # 背景纯白（显式指定）
    try:                       # 小图探针：验证当前上下文能否渲染
        sc.render.resolution_x = sc.render.resolution_y = 64
        render_to(sc, os.path.join(RDIR, '_probe.png'))
        sc.render.resolution_x = sc.render.resolution_y = 2048
    except Exception as e:
        engine = 'CYCLES'
        log('Workbench 不可用（%r），降级 Cycles CPU' % e)
        sc.render.engine = 'CYCLES'
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 24
    log('渲染引擎: %s' % engine)

    # 三视图正交（机体 +X 为前）
    make_cam(sc, 'cam_front', (25, 0, 4.75), (0, 0, 4.75), ortho=10.24)
    render_to(sc, os.path.join(RDIR, 'AC6_front_ortho.png'))
    make_cam(sc, 'cam_left', (0, -25, 4.75), (0, 0, 4.75), ortho=10.24)
    render_to(sc, os.path.join(RDIR, 'AC6_left_ortho.png'))
    make_cam(sc, 'cam_top', (0, 0, 25), (0, 0, 0), ortho=7.0)
    render_to(sc, os.path.join(RDIR, 'AC6_top_ortho.png'))

    # 膝点标注侧视图（+Y 侧，保证标注文字正向可读）
    red = bpy.data.materials.new('AC6_Marker')
    red.use_nodes = False
    red.diffuse_color = (1.0, 0.08, 0.08, 1.0)
    cu = bpy.data.curves.new('KneeLabel', type='FONT')
    cu.body = 'KNEE  X=-0.20  Z=2.50\n0.43 m behind hip-ankle line'
    cu.size = 0.34
    label = bpy.data.objects.new('KneeLabel', cu)
    sc.collection.objects.link(label)
    label.location = (3.4, 1.8, 2.15)
    label.rotation_euler = (math.radians(90), 0, math.radians(180))   # 面向 +Y 相机且正读
    cu.materials.append(red)
    anno = [label]
    for i, (dx, dy, dz) in enumerate(((0.8, 0.02, 0.02), (0.02, 0.02, 0.8))):   # 十字标
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.20, 1.8, 2.50))
        m = bpy.context.active_object
        m.scale = (dx, dy, dz)                                # 标注临时物，不入交付
        m.name = 'KneeCross%d' % i
        m.data.materials.append(red)
        anno.append(m)
    make_cam(sc, 'cam_side_anno', (0, 25, 4.75), (0, 0, 4.75), ortho=10.24)
    render_to(sc, os.path.join(RDIR, 'AC6_side_knee_annotated.png'))
    for o in anno:                                            # 标注只服务于上一张图，出完即删
        bpy.data.objects.remove(o, do_unlink=True)

    # 剪影测试：26 m / 垂直 45°，纯黑剪影白底
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1600
    if engine == 'WORKBENCH':
        sc.display.shading.color_type = 'SINGLE'
        sc.display.shading.single_color = (0.0, 0.0, 0.0)
    else:
        black = bpy.data.materials.new('AC6_Black')
        black.use_nodes = True
        bsdf = next(n for n in black.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Roughness'].default_value = 1.0
        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                for i in range(len(ob.material_slots)):
                    ob.material_slots[i].material = black
    make_cam(sc, 'cam_sil', (26, 0, 4.75), (0, 0, 4.75), vfov=45.0)
    render_to(sc, os.path.join(RDIR, 'AC6_silhouette_26m_45vfov.png'))
    whiten_bg(os.path.join(RDIR, 'AC6_silhouette_26m_45vfov.png'))
    log('渲染结束 | 用时 %.1fs' % (time.time() - _T0))

if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        log('!! 未捕获异常，原始输出:\n' + traceback.format_exc())
        raise
