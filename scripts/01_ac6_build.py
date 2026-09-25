# -*- coding: utf-8 -*-
# 01_ac6_build.py — 类《装甲核心6》二脚 AC 参数化硬表面建模（仅建模，无绑定/动画/特效）
# 运行： blender.exe -b --python 01_ac6_build.py
# 输出： assets/mech/AC6Mech.blend
#
# 坐标口径（依据数值表 + 验收脚本，报告"冲突与取舍"一节有说明）：
#   +X = 机体前方（背包 -X、枪口 +X、脚尖 +X）
#   +Y = 右（LegL / ArmL / GunL 在 -Y 侧）
#   +Z = 上，脚底 Z = 0.00
# 关节角：模长 6°/25°/12° 保留，矢状面方向翻转 —— 大腿 6° 后倾、小腿相对大腿向前 25°、
#         脚掌前倾 12°，保证膝点落在髋-踝连线后方（验收 3）。

import bpy, bmesh, math, os, sys, time, json
from mathutils import Matrix, Vector, Euler

# ---------------------------------------------------------------- 配置
ROOT    = r'.'
ASSETS  = os.path.join(ROOT, 'assets', 'mech')
BLEND   = os.path.join(ASSETS, 'AC6Mech.blend')
LOG     = os.path.join(ROOT, 'logs', 'build_log.txt')
SUMMARY = os.path.join(ROOT, 'logs', 'build_summary.json')

M_ARMOR, M_JOINT, M_THRUST, M_HAZARD = 0, 1, 2, 3
CHAMFER      = 0.05          # 切角宽度 0.04-0.10
BEVEL_SEG    = [2, 1, 0]     # LOD0/1/2 倒角段数
SEG          = [24, 12, 8]   # LOD0/1/2 圆柱段数
SEG_S        = [16, 10, 8]   # 小圆柱段数

_ERRORS = [0]
_T0 = time.time()

def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def progress(stage, done, total, item):
    pct = 100.0 * done / max(total, 1)
    el = time.time() - _T0
    spd = done / el if el > 0 else 0.0
    eta = (total - done) / spd if spd > 0 else 0.0
    log('[%s] %d/%d %.0f%% %s  (%.2f件/s, ETA %.0fs, 错误 %d)'
        % (stage, done, total, pct, item, spd, eta, _ERRORS[0]))

# ---------------------------------------------------------------- bmesh 构件
class Part(object):
    """一个部件 = 一个 bmesh。所有尺寸直接写进顶点，物体 Scale 永远 (1,1,1)。"""
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()

    # ---- 内部：收尾（材质标记 / 平滑 / 法线重算）
    def _finish(self, ret, mat, smooth, recalc=True):
        faces = set()
        for v in ret.get('verts', []):
            for f in v.link_faces:
                faces.add(f)
        fl = list(faces)
        if recalc and fl:
            bmesh.ops.recalc_face_normals(self.bm, faces=fl)
        for f in fl:
            f.material_index = mat
            f.smooth = smooth
        return fl

    # ---- 盒体（8 顶点，尺寸直接进顶点坐标）
    def box(self, c, s, rot=(0, 0, 0), mat=M_ARMOR):
        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        M = (Matrix.Translation(Vector(c))
             @ Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), 'XYZ').to_matrix().to_4x4()
             @ Matrix.Diagonal((s[0], s[1], s[2], 1.0)))
        bmesh.ops.transform(self.bm, matrix=M, verts=ret['verts'])
        return self._finish(ret, mat, False)

    # ---- 楔形/异形：8 个显式点（4 底 4 顶），用于斜面装甲、爪、肩甲外倾
    def qbox(self, pts, mat=M_ARMOR):
        vs = [self.bm.verts.new(Vector(p)) for p in pts]
        faces_idx = [(0, 1, 2, 3), (7, 6, 5, 4),
                     (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        fl = []
        for fi in faces_idx:
            fl.append(self.bm.faces.new([vs[i] for i in fi]))
        bmesh.ops.recalc_face_normals(self.bm, faces=fl)
        for f in fl:
            f.material_index = mat
            f.smooth = False
        return fl

    # ---- 圆柱/圆锥（direction = +Z 端朝向；radius1 在 -Z 端）
    def cone(self, c, r1, r2, depth, direction=(0, 0, 1), mat=M_JOINT,
             seg=None, cap=True, smooth=False, recalc=True):
        seg = SEG[0] if seg is None else seg
        ret = bmesh.ops.create_cone(self.bm, cap_ends=cap, cap_tris=False,
                                    segments=seg, radius1=r1, radius2=r2, depth=depth)
        d = Vector(direction).normalized()
        quat = Vector((0, 0, 1)).rotation_difference(d)
        M = Matrix.Translation(Vector(c)) @ quat.to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=M, verts=ret['verts'])
        return self._finish(ret, mat, smooth, recalc=recalc)

    def rod(self, p0, p1, r, mat=M_JOINT, seg=None, cap=True):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        return self.cone((p0 + p1) / 2, r, r, d.length, d, mat, seg=seg, cap=cap)

    # ---- 液压执行器：缸体 + 裸杆 + 两端接头（直径 0.16 / 0.10）
    def piston(self, p0, p1, r_body=0.08, r_rod=0.05, seg=None):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        dn = d.normalized()
        self.rod(p0, p0 + dn * L * 0.58, r_body, seg=seg)                 # 缸体
        self.rod(p0 + dn * L * 0.40, p1, r_rod, seg=seg)                  # 裸杆
        self.box(p0, (0.16, 0.16, 0.16), mat=M_JOINT)                     # 尾接头
        self.box(p1, (0.13, 0.13, 0.13), mat=M_JOINT)                     # 头接头

    # ---- 线缆/软管（分段圆柱，端点埋进装甲）
    def hose(self, pts, r=0.03, seg=None):
        for a, b in zip(pts, pts[1:]):
            self.rod(a, b, r, seg=seg or SEG_S[0])

    # ---- 百叶散热窗：凹槽 + 斜置叶片
    def louvers(self, c, w, h, n, plane='+X', rot=(0, 0, 0), lod=0):
        # c: 凹槽中心, w/h: 窗口宽/高, n: 叶片数, plane: 窗口朝向
        n = [n, max(3, n - 2), 0][lod]
        axis = {'+X': (1, 0, 0), '-X': (-1, 0, 0), '+Y': (0, 1, 0), '-Y': (0, -1, 0)}[plane]
        # 凹槽底（深 0.06，Joint 色）
        self.box(c, (abs(axis[0]) * 0.06 + w * (axis[0] == 0),
                     abs(axis[1]) * 0.06 + w * (axis[1] == 0), h), rot=rot, mat=M_JOINT)
        if n <= 0:
            return
        for i in range(n):
            t = (i + 0.5) / n - 0.5
            off = Vector((0, 0, t * h * 0.9))
            R = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), 'XYZ').to_matrix()
            cc = Vector(c) + R @ off + Vector(axis) * 0.015
            self.box(cc, (abs(axis[0]) * 0.04 + w * (axis[0] == 0),
                          abs(axis[1]) * 0.04 + w * (axis[1] == 0),
                          h / n * 0.45), rot=(rot[0], rot[1], rot[2]), mat=M_ARMOR)

    # ---- 推进器喷口（全机唯一自发光面）：外壳 + 内锥（18° 锥角，平滑，自发光）
    def thruster(self, exit_c, direction, r_exit, lod=0, seg=None):
        seg = seg or SEG[0]
        d = Vector(direction).normalized()
        cone_ang = math.radians(18.0)                 # 全锥角 18°
        L = (r_exit - r_exit * 0.5) / math.tan(cone_ang / 2)   # 喉部半径 = 0.5 出口半径
        r_throat = r_exit * 0.5
        exit_c = Vector(exit_c)
        throat_c = exit_c - d * L
        # 外壳（开口圆筒，枪灰金属）
        self.cone(exit_c - d * (L * 0.55), r_exit * 1.12, r_exit * 1.2, L * 0.9,
                  d, M_JOINT, seg=seg, cap=False)
        # 出口唇环
        self.cone(exit_c - d * 0.03, r_exit * 1.05, r_exit * 1.18, 0.07, d, M_JOINT, seg=seg, cap=False)
        # 内锥（法线朝内，平滑，自发光青蓝）
        ret = bmesh.ops.create_cone(self.bm, cap_ends=False, cap_tris=False,
                                    segments=seg, radius1=r_throat, radius2=r_exit * 0.98, depth=L * 0.95)
        quat = Vector((0, 0, 1)).rotation_difference(d)
        M = Matrix.Translation(exit_c - d * (L * 0.5)) @ quat.to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=M, verts=ret['verts'])
        fl = self._finish(ret, M_THRUST, True, recalc=False)
        bmesh.ops.reverse_faces(self.bm, faces=fl)     # 翻向内壁
        # 喉部封盖（自发光，平滑）
        self.cone(throat_c + d * 0.01, r_throat, r_throat, 0.02, d, M_THRUST, seg=seg, smooth=True)

    # ---- 装甲板缝：0.03 宽 × 0.02 深的嵌入暗条（Joint 色）
    def seam(self, c, s, rot=(0, 0, 0)):
        self.box(c, s, rot=rot, mat=M_JOINT)

    def to_object(self, name, collection):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in MATS:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        return ob

# ---------------------------------------------------------------- 材质（颜色只在材质里）
def make_materials():
    mats = []

    def new_mat(name, color, rough, metal):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        m.diffuse_color = (*color, 1.0)     # 视口/Workbench 色
        return m

    # 1 Armor 哑光蓝灰（0.06,0.22,0.75 的暗化版本）
    mats.append(new_mat('AC6_Armor', (0.035, 0.115, 0.385), 0.75, 0.15))
    # 2 Joint 深枪灰金属（关节与液压）
    mats.append(new_mat('AC6_Joint', (0.055, 0.058, 0.062), 0.35, 0.90))
    # 3 Thruster 青蓝自发光（全机唯一自发光）
    m = new_mat('AC6_Thruster', (0.0, 0.0, 0.0), 0.5, 0.0)
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key in ('Emission Color', 'Emission'):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = (0.0, 0.80, 1.0, 1.0)
            break
    if 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = 3.0
    m.diffuse_color = (0.0, 0.80, 1.0, 1.0)
    mats.append(m)
    # 4 Hazard 黄黑警示条（程序化条纹，不烘焙贴图，占比 < 3%）
    m = bpy.data.materials.new('AC6_Hazard')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Roughness'].default_value = 0.6
    tex = nt.nodes.new('ShaderNodeTexWave')
    tex.wave_type = 'BANDS'
    tex.inputs['Scale'].default_value = 18.0
    mapn = nt.nodes.new('ShaderNodeMapping')
    mapn.inputs['Rotation'].default_value = (0.0, 0.0, math.radians(45.0))
    coord = nt.nodes.new('ShaderNodeTexCoord')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].color = (0.85, 0.62, 0.04, 1.0)   # 黄
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (0.02, 0.02, 0.02, 1.0)  # 黑
    nt.links.new(coord.outputs['Generated'], mapn.inputs['Vector'])
    nt.links.new(mapn.outputs['Vector'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    m.diffuse_color = (0.85, 0.62, 0.04, 1.0)
    mats.append(m)
    return mats

# ---------------------------------------------------------------- 坐标工具
def frame(origin, deg_y=0.0, deg_x=0.0):
    """腿/臂的局部坐标架。返回 (P 局部→世界, 旋转元组(度))"""
    R = Euler((math.radians(deg_x), math.radians(deg_y), 0.0), 'XYZ').to_matrix()
    o = Vector(origin)

    def P(off):
        return tuple(o + R @ Vector(off))
    return P, (deg_x, deg_y, 0.0)

# ================================================================ 部件几何
# ---- 腿部关键点（髋 4.40 / 膝 2.50 / 踝 0.60，膝在髋-踝连线后方）
def leg_points(y_c):
    H = Vector((0.0, y_c, 4.40))
    R_thigh = Euler((math.radians(-3.0), math.radians(6.0), 0.0), 'XYZ').to_matrix()
    d_thigh = (R_thigh @ Vector((0, 0, -1))).normalized()
    L1 = 1.90 / -d_thigh.z
    K = H + d_thigh * L1
    R_shin = R_thigh @ Matrix.Rotation(math.radians(-25.0), 3, 'Y')
    d_shin = (R_shin @ Vector((0, 0, -1))).normalized()
    L2 = 1.90 / -d_shin.z
    A = K + d_shin * L2
    return H, K, A, R_thigh, R_shin

def build_leg(p, side, lod=0):
    """side=-1 左(L, -Y 侧)。本体在左，Right 由整体镜像生成。"""
    y_c = side * 0.85
    H, K, A, R_thigh, R_shin = leg_points(y_c)
    rot_t = (math.degrees(R_thigh.to_euler('XYZ').x), math.degrees(R_thigh.to_euler('XYZ').y), 0.0)
    rot_s = (math.degrees(R_shin.to_euler('XYZ').x), math.degrees(R_shin.to_euler('XYZ').y), 0.0)
    Pt = lambda off: tuple(H + R_thigh @ Vector(off))
    Ps = lambda off: tuple(K + R_shin @ Vector(off))

    # 髋关节轴（0.35 外露轴）+ 大腿根柱（连到腰部，Z 到 4.82 与躯干围壳搭接）
    p.cone(H, 0.175, 0.175, 0.95, (0, 1, 0), M_JOINT, seg=SEG_S[lod])
    p.box(Pt((0, 0, 0.22)), (0.55, 0.70, 0.55), rot=rot_t, mat=M_ARMOR)          # 髋甲块
    p.box(Pt((0, 0, 0.18)), (0.42, 0.55, 0.55), rot=rot_t, mat=M_JOINT)          # 根柱（顶 4.87 入躯干围壳）
    # 大腿：结构芯 + 前主甲 0.25 + 侧次甲 0.15 + 层叠板缝（沿大腿轴铺满髋→膝）
    p.box(Pt((0, 0, -0.90)), (0.55, 0.72, 1.75), rot=rot_t, mat=M_JOINT)
    p.box(Pt((0.34, 0, -0.85)), (0.25, 0.80, 1.55), rot=rot_t, mat=M_ARMOR)
    p.box(Pt((0.48, 0, -1.25)), (0.12, 0.62, 0.55), rot=rot_t, mat=M_ARMOR)      # 层叠次甲
    p.box(Pt((0.42, 0, -0.65)), (0.03, 0.55, 0.02), rot=rot_t, mat=M_JOINT) if lod == 0 else None
    p.box(Pt((0, 0.40, -0.85)), (0.42, 0.15, 1.55), rot=rot_t, mat=M_ARMOR)
    p.box(Pt((0, -0.40, -0.85)), (0.42, 0.15, 1.55), rot=rot_t, mat=M_ARMOR)
    # 大腿液压 ×2（0.16 缸 / 0.10 杆）
    if lod < 2:
        p.piston(Pt((0.16, 0.22, -0.15)), Pt((0.20, 0.18, -1.35)), seg=SEG_S[lod])
        if lod == 0:
            p.piston(Pt((0.16, -0.22, -0.15)), Pt((0.20, -0.18, -1.35)), seg=SEG_S[lod])
    # 膝关节轴 0.32 + 膝甲盖 + 后置百叶散热窗
    p.cone(K, 0.16, 0.16, 0.88, (0, 1, 0), M_JOINT, seg=SEG_S[lod])
    p.box(tuple(K + R_thigh @ Vector((0.24, 0, 0.02))), (0.55, 0.78, 0.50), rot=rot_t, mat=M_ARMOR)
    # 小腿：结构芯 + 前甲 0.22 + 腿肚块 + 散热窗（沿小腿轴铺满膝→踝）
    p.box(Ps((0, 0, -1.05)), (0.42, 0.55, 1.75), rot=rot_s, mat=M_JOINT)
    p.box(Ps((0.28, 0, -1.00)), (0.22, 0.62, 1.55), rot=rot_s, mat=M_ARMOR)
    p.box(Ps((-0.30, 0, -0.75)), (0.32, 0.60, 1.00), rot=rot_s, mat=M_ARMOR)     # 腿肚块
    if lod < 2:
        p.louvers(Ps((-0.47, 0, -0.75)), 0.42, 0.55, 5, plane='-X', rot=rot_s, lod=lod)
        p.piston(Ps((-0.28, 0.24, -0.25)), Ps((-0.30, 0.20, -1.75)), seg=SEG_S[lod])   # 小腿外露液压
    # 脚踝关节 0.30
    p.cone(A, 0.15, 0.15, 0.80, (0, 1, 0), M_JOINT, seg=SEG_S[lod])
    # 足部：三点爪 + 装甲踵刺。脚长 1.60 (-0.55..1.05)，脚宽 0.90
    ay = A.y
    p.box((A.x + 0.05, ay, 0.38), (0.62, 0.58, 0.40), mat=M_JOINT)                # 踝块
    p.box((0.42, ay, 0.24), (1.05, 0.55, 0.30), rot=(0, 8, 0), mat=M_ARMOR)       # 足体（前倾观感）
    # 前爪 ×2（楔形，趾尖底面 Z=0.00）
    for cy in (ay - 0.33, ay + 0.33):
        p.qbox([(0.62, cy - 0.12, 0.00), (1.05, cy - 0.10, 0.00),
                (1.05, cy + 0.10, 0.00), (0.62, cy + 0.12, 0.00),
                (0.55, cy - 0.14, 0.30), (1.00, cy - 0.11, 0.16),
                (1.00, cy + 0.11, 0.16), (0.55, cy + 0.14, 0.30)], M_ARMOR)
        if lod < 2:
            p.cone((0.60, cy, 0.20), 0.10, 0.10, 0.24, (0, 1, 0), M_JOINT, seg=SEG_S[lod])  # 爪枢轴
    # 踵刺（单点，向后下，底面 Z=0.00）
    p.qbox([(-0.55, ay - 0.10, 0.00), (-0.18, ay - 0.16, 0.00),
            (-0.18, ay + 0.16, 0.00), (-0.55, ay + 0.10, 0.00),
            (-0.45, ay - 0.07, 0.14), (-0.10, ay - 0.18, 0.34),
            (-0.10, ay + 0.18, 0.34), (-0.45, ay + 0.07, 0.14)], M_ARMOR)
    if lod < 2:
        p.piston((A.x - 0.02, ay + 0.20, 0.72), (0.72, ay + 0.18, 0.34), seg=SEG_S[lod])   # 足部执行器
    if lod == 0:
        p.box((0.30, ay - 0.28, 0.42), (0.34, 0.02, 0.10), mat=M_HAZARD)          # 警示条（微量）
    # 线缆束：髋→膝→踝（后外侧走线）
    if lod < 2:
        pts = [Pt((-0.30, 0.30, -0.05)), Pt((-0.38, 0.32, -0.85)),
               Ps((-0.32, 0.30, -0.35)), Ps((-0.28, 0.28, -1.45)), (A.x - 0.15, ay + 0.25, 0.72)]
        p.hose(pts if lod == 0 else [pts[0], pts[2], pts[4]], 0.03, seg=SEG_S[lod])
    # 小腿姿态喷口（vernier，内壁自发光）
    if lod < 2:
        p.thruster((-0.28, -1.15, 1.60), (-0.9659, 0, 0.2588), 0.075, lod=lod, seg=SEG_S[lod])

def build_torso(p, lod=0):
    # 腰围壳（宽 1.90）+ 腰枢轴 0.35 + 下躯干
    p.box((0.0, -0.475, 4.90), (1.50, 0.95, 0.40), mat=M_JOINT)                  # 髋围壳（下探 4.70）
    p.box((0.0, -0.175, 5.20), (0.35, 0.35, 0.42), mat=M_JOINT)                  # 腰枢轴（0.35 方柱，镜像面齐平）
    p.box((0.0, -0.475, 5.32), (1.70, 0.95, 0.55), mat=M_ARMOR)
    # 胸部主体（胸宽 3.00 → 半宽 1.35 芯 + 甲板到 1.50；胸厚 2.60 → X ±1.30）
    p.box((-0.10, -0.60, 6.55), (2.25, 1.20, 2.30), mat=M_JOINT)                  # 胸结构芯
    # 前胸 V 形楔形装甲（0.25 厚，镜像后成箭头面）
    p.qbox([(1.30, 0.0, 5.85), (1.05, -1.45, 5.85), (1.05, -1.45, 7.35), (1.30, 0.0, 7.35),
            (1.05, 0.0, 5.85), (0.80, -1.45, 5.85), (0.80, -1.45, 7.35), (1.05, 0.0, 7.35)], M_ARMOR)
    p.box((0.55, -1.10, 6.55), (0.25, 0.75, 1.45), mat=M_ARMOR)                  # 前主甲 0.25
    p.box((0.72, -1.15, 6.95), (0.12, 0.60, 0.55), mat=M_ARMOR)                  # 层叠次甲
    if lod == 0:
        p.seam((0.70, -1.10, 6.55), (0.03, 0.55, 0.02))                          # 板缝 0.03×0.02
        p.seam((0.70, -1.10, 7.22), (0.03, 0.55, 0.02))
    # 胸部进气格栅（前下方，百叶）
    if lod < 2:
        p.louvers((1.15, -0.55, 5.95), 0.55, 0.45, 5, plane='+X', lod=lod)
    # 侧散热窗（胸部两翼，贴芯块侧面）
    if lod < 2:
        p.louvers((-0.35, -1.22, 6.85), 0.75, 0.55, 5, plane='-Y', rot=(0, 0, 0), lod=lod)
    # 背甲 + 背包接口
    p.box((-1.15, -0.625, 6.55), (0.30, 1.25, 2.20), mat=M_ARMOR)
    p.box((-1.05, -0.45, 7.10), (0.45, 0.75, 0.85), mat=M_JOINT)                 # 背包挂载座
    # 肩关节轴 0.35（桥接躯干↔手臂）
    p.cone((0.0, -1.675, 7.10), 0.175, 0.175, 0.53, (0, 1, 0), M_JOINT, seg=SEG_S[lod])
    p.box((0.0, -1.55, 7.10), (0.72, 0.42, 0.50), mat=M_JOINT)                   # 肩基座
    # 颈：0.35 方柱，颈底 8.10 → 与头部搭接 8.38
    p.box((0.0, -0.175, 8.22), (0.35, 0.35, 0.32), mat=M_JOINT)
    p.box((0.0, -0.275, 7.95), (1.10, 0.55, 0.30), mat=M_ARMOR)                  # 领甲
    # 背包→肩线缆
    if lod < 2:
        p.hose([(-1.10, -0.95, 7.55), (-0.70, -1.25, 7.45), (-0.35, -1.45, 7.30)], 0.035, seg=SEG_S[lod])
    if lod == 0:
        p.box((0.90, -0.75, 5.85), (0.02, 0.35, 0.10), mat=M_HAZARD)             # 警示条

def build_head(p, lod=0):
    # 传感器头：无五官。面罩前倾 8°
    p.box((-0.05, -0.275, 8.85), (0.95, 0.55, 0.85), mat=M_JOINT)               # 头体芯
    # 面罩楔块（前倾 8°）
    p.qbox([(0.35, -0.55, 8.60), (0.58, -0.55, 8.68), (0.58, 0.0, 8.68), (0.35, 0.0, 8.60),
            (0.35, -0.55, 9.05), (0.50, -0.55, 9.12), (0.50, 0.0, 9.12), (0.35, 0.0, 9.05)], M_ARMOR)
    # 传感器狭缝（凹陷 0.02，不发光）
    p.box((0.58, -0.25, 8.84), (0.02, 0.50, 0.10), mat=M_JOINT)
    # 顶脊（头顶 Z=9.50）
    p.box((0.0, -0.16, 9.32), (0.70, 0.32, 0.36), mat=M_ARMOR)
    # 侧传感舱（非人眼造型）
    p.cone((0.15, -0.60, 8.85), 0.09, 0.07, 0.18, (0, 1, 0), M_JOINT, seg=SEG_S[lod])
    # 颈侧装甲
    p.box((-0.15, -0.35, 8.42), (0.55, 0.70, 0.22), mat=M_ARMOR)

def build_backpack(p, lod=0):
    # 主体（背包后缘 X=-2.20 由喷口唇环收口）
    p.box((-1.50, -0.525, 7.30), (1.30, 1.05, 1.95), mat=M_JOINT)               # 主体芯
    p.box((-1.55, -0.55, 7.65), (1.15, 1.10, 1.15), mat=M_ARMOR)                 # 上甲
    p.box((-1.55, -0.55, 6.70), (1.15, 1.10, 0.75), mat=M_ARMOR)                 # 下甲
    p.box((-0.95, -0.35, 7.10), (0.35, 0.70, 0.85), mat=M_JOINT)                 # 挂载耳（入躯干）
    # 大口径喷口 ×2（0.55，Y=±0.45，轴向后上 15°）—— 本体只建 -Y 侧，右侧由镜像生成
    p.thruster((-2.02, -0.45, 7.72), (-0.9659, 0, 0.2588), 0.275, lod=lod)
    # 小口径喷口 ×2（0.32，Y=±0.95，外侧）
    if lod < 2:
        p.thruster((-1.95, -0.95, 7.05), (-0.9659, 0, 0.2588), 0.16, lod=lod, seg=SEG_S[lod])
    # 侧面散热窗（贴主体侧面）
    if lod < 2:
        p.louvers((-1.55, -1.07, 7.30), 0.65, 0.80, 4, plane='-Y', lod=lod)
    # 线缆引出
    if lod < 2:
        p.hose([(-1.05, -0.85, 7.60), (-0.85, -1.05, 7.55), (-0.62, -1.22, 7.46)], 0.04, seg=SEG_S[lod])
    if lod == 0:
        p.box((-1.60, -1.06, 6.95), (0.35, 0.02, 0.10), mat=M_HAZARD)

def build_arm(p, side, lod=0):
    """side=-1 左（-Y）。肩甲归 Arm：外缘 Y=±2.80，顶 Z=7.60。"""
    y_c = side * 2.30
    # 上臂：结构芯 + 前甲 0.18
    p.box((0.0, y_c, 6.60), (0.55, 0.85, 1.30), mat=M_JOINT)
    p.box((0.32, y_c, 6.55), (0.18, 0.75, 1.05), mat=M_ARMOR)
    p.box((-0.28, y_c, 6.85), (0.18, 0.65, 0.55), mat=M_ARMOR)                   # 层叠次甲
    # 肩甲（Pauldron，归 Arm）：外缘下倾 10°、外张 5°；外缘 Y=±2.80，顶 Z=7.60
    y_in = y_c - 0.55 * side          # 靠中线一侧
    y_ot = y_c + 0.50 * side          # 外缘下（外张 5°）
    y_tt = y_c + 0.45 * side          # 外缘上（下倾 10° 收进）
    p.qbox([(-0.55, y_in, 6.75), (0.55, y_in, 6.75), (0.55, y_ot, 6.60), (-0.55, y_ot, 6.60),
            (-0.55, y_in, 7.60), (0.55, y_in, 7.60), (0.55, y_tt, 7.42), (-0.55, y_tt, 7.42)], M_ARMOR)
    if lod < 2:
        p.louvers((-0.35, (y_in + y_tt) / 2, 7.25), 0.55, 0.35, 3, plane='-Y', lod=lod)
        if lod == 0:
            p.box((0.20, (y_in + y_ot) / 2, 6.95), (0.35, 0.02, 0.12), mat=M_HAZARD)
    # 肩→肘液压 + 线缆
    if lod < 2:
        p.piston((-0.30, y_c + 0.15, 6.95), (-0.28, y_c + 0.15, 6.05), seg=SEG_S[lod])
        p.hose([(0.25, y_c - 0.25, 6.95), (0.32, y_c - 0.28, 6.35), (0.28, y_c - 0.25, 5.95)],
               0.03, seg=SEG_S[lod])
    # 肘关节轴 0.30 + 肘甲
    p.cone((0.0, y_c, 5.95), 0.15, 0.15, 0.78, (0, 1, 0), M_JOINT, seg=SEG_S[lod])
    p.box((0.10, y_c, 5.95), (0.45, 0.70, 0.35), mat=M_ARMOR)
    # 前臂：结构芯 + 侧甲 0.22
    p.box((0.05, y_c, 5.45), (0.50, 0.62, 0.85), mat=M_JOINT)
    p.box((0.35, y_c, 5.45), (0.22, 0.68, 0.75), mat=M_ARMOR)
    # 腕/手：掌块 + 抱箍（握住 Gun 握把，枪为独立对象）
    p.box((0.15, y_c, 5.02), (0.45, 0.55, 0.38), mat=M_JOINT)
    p.box((0.32, y_c, 5.35), (0.42, 0.42, 0.55), mat=M_ARMOR)                    # 掌甲
    p.box((0.58, y_c, 5.42), (0.16, 0.50, 0.30), mat=M_JOINT)                    # 抱箍（压住枪握把）

def build_gun(p, side, lod=0):
    """side=-1 左（-Y）。手持独立武器：枪口 X=3.00 收口。"""
    y_c = side * 2.60
    # 机匣（长轴 X）
    p.box((1.45, y_c, 5.42), (1.70, 0.44, 0.34), mat=M_ARMOR)                    # 主机匣
    p.box((1.45, y_c, 5.62), (1.20, 0.36, 0.10), mat=M_JOINT)                    # 上导轨
    p.box((1.45, y_c, 5.22), (1.20, 0.36, 0.10), mat=M_JOINT)                    # 下导轨
    # 枪管（0.16）+ 制退器，枪口止于 X=3.00
    p.rod((2.15, y_c, 5.42), (2.92, y_c, 5.42), 0.08, seg=SEG[lod])
    p.box((2.86, y_c, 5.42), (0.26, 0.24, 0.24), mat=M_JOINT)                    # 制退器（止 2.99）
    if lod == 0:
        for i in range(3):
            p.box((2.80 + i * 0.05, y_c, 5.55), (0.02, 0.18, 0.02), mat=M_JOINT)
    # 后托/机柄（连到手，X=0.40 起）
    p.box((0.52, y_c, 5.40), (0.28, 0.40, 0.42), mat=M_JOINT)
    p.box((0.62, y_c, 5.10), (0.24, 0.20, 0.34), rot=(0, -12, 0), mat=M_JOINT)  # 握把（入抱箍）
    # 弹匣 + 瞄具块
    p.box((1.25, y_c, 5.14), (0.40, 0.26, 0.26), mat=M_ARMOR)
    if lod < 2:
        p.box((1.55, y_c, 5.70), (0.45, 0.18, 0.10), mat=M_JOINT)                # 瞄具（顶 5.75 内）
    if lod == 0:
        p.box((1.45, y_c - side * 0.23, 5.42), (0.30, 0.02, 0.10), mat=M_HAZARD)

# ================================================================ 装配
PARTS = [
    ('Torso',   build_torso,   True,  (0.00,  0.00, 6.50)),
    ('Head',    build_head,    True,  (0.00,  0.00, 8.90)),
    ('Backpack',build_backpack,True,  (-1.50, 0.00, 7.30)),
    ('LegL',    lambda p, l: build_leg(p, -1, l),  False, (0.00, -0.85, 2.40)),
    ('LegR',    'MIRROR_LegL', False, (0.00,  0.85, 2.40)),
    ('ArmL',    lambda p, l: build_arm(p, -1, l),  False, (0.00, -2.30, 6.40)),
    ('ArmR',    'MIRROR_ArmL', False, (0.00,  2.30, 6.40)),
    ('GunL',    lambda p, l: build_gun(p, -1, l),  False, (1.70, -2.60, 5.40)),
    ('GunR',    'MIRROR_GunL', False, (1.70,  2.60, 5.40)),
]

def finish_object(ob, lod, half_mirror):
    """倒角 → 法线 → 应用 → 枢轴归包围盒中心 → UV"""
    # Mirror（居中部件的左右对称：只建 Y≤0 半边）
    if half_mirror:
        md = ob.modifiers.new('Mirror', 'MIRROR')
        md.use_axis = (False, True, False)
        md.use_clip = True
        md.use_mirror_merge = True
        md.merge_threshold = 0.001
    # Bevel（Segments 1-2 / Width=CHAMFER / Clamp Overlap）
    if BEVEL_SEG[lod] > 0:
        bv = ob.modifiers.new('Bevel', 'BEVEL')
        bv.width = CHAMFER
        bv.segments = BEVEL_SEG[lod]
        bv.limit_method = 'ANGLE'
        bv.angle_limit = math.radians(30)
        bv.use_clamp_overlap = True
    # Weighted Normal
    if lod < 2:
        wn = ob.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL')
        wn.keep_sharp = True
    # 全部 Apply（Boolean 规则同理：不留残留修改器）
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.context.view_layer.update()
    for md in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=md.name)
    # 清理退化面（倒角 clamp 可能压出零面积面，会产生 UV 退化三角）
    _bm = bmesh.new()
    _bm.from_mesh(ob.data)
    bmesh.ops.dissolve_degenerate(_bm, dist=1e-6, edges=list(_bm.edges))
    _bm.to_mesh(ob.data)
    _bm.free()
    # 枢轴 = 包围盒几何中心
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    # UV0 贴图用 / UV1 Lightmap
    me = ob.data
    for layer_name, margin in (('UVMap', 0.003), ('Lightmap', 0.004)):
        if layer_name not in me.uv_layers:
            me.uv_layers.new(name=layer_name)
        me.uv_layers.active = me.uv_layers[layer_name]
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        try:
            bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margin,
                                     area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        except Exception as e:
            _ERRORS[0] += 1
            log('!! UV smart_project 失败 %s: %s' % (ob.name, e))
        bpy.ops.object.mode_set(mode='OBJECT')
    me.uv_layers.active = me.uv_layers['UVMap']
    # 硬边：除喷口内壁（已标 smooth）外全部 Flat
    for poly in me.polygons:
        if poly.material_index != M_THRUST:
            poly.use_smooth = False

def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def bbox_of(ob):
    """世界坐标顶点包围盒。对象只有平移，直接用 location 组矩阵，规避 matrix_world 缓存陈旧。"""
    m = Matrix.Translation(ob.location)
    pts = [m @ v.co for v in ob.data.vertices]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

def mirror_object(src, name, coll):
    """左件整体镜像为右件：世界顶点 Y 取反 + 翻法线，枢轴=实算包围盒中心。零算子依赖。"""
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.transform(Matrix.Translation(src.location))              # → 世界坐标（对象只有平移）
    bm.transform(Matrix.Diagonal((1.0, -1.0, 1.0, 1.0)))        # 关于 Y=0 镜像
    uvlayers = list(bm.loops.layers.uv)                        # UVMap / Lightmap 两层都要回贴
    saved = {f: [[l[uv].uv.copy() for l in f.loops] for uv in uvlayers] for f in bm.faces} if uvlayers else None
    bmesh.ops.reverse_faces(bm, faces=bm.faces)                 # 负行列式 → 翻法线
    if saved:                                                   # UV 逐面回贴，消除镜像导致的 UV 翻转
        for f, per_layer in saved.items():
            for uv, uvs in zip(uvlayers, per_layer):
                for l, uvco in zip(f.loops, uvs):
                    l[uv].uv = uvco
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(-c), verts=list(bm.verts))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in MATS:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    ob.location = c
    coll.objects.link(ob)
    return ob

def main():
    global MATS
    log('==== AC6 建模开始 | blender %s ====' % bpy.app.version_string)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    # 清掉启动场景默认对象（Cube/Camera/Light），交付只留机体
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    MATS = make_materials()

    root_coll = bpy.data.collections.new('AC6Mech')
    sc.collection.children.link(root_coll)

    built = {}
    n = len(PARTS)
    summary = {}
    for i, (name, fn, half, pivot) in enumerate(PARTS, 1):
        try:
            coll = bpy.data.collections.new('%02d_%s' % (i, name))
            root_coll.children.link(coll)
            for lod in range(3):
                obj_name = 'SM_AC6_%s' % name if lod == 0 else 'SM_AC6_%s_LOD%d' % (name, lod)
                if isinstance(fn, str):                     # 右侧 = 左侧整体镜像（手动，确定性）
                    src = built[fn.replace('MIRROR_', '')][lod]
                    ob = mirror_object(src, obj_name, coll)
                else:
                    p = Part(obj_name)
                    fn(p, lod)
                    ob = p.to_object(obj_name, coll)
                    finish_object(ob, lod, half)
                built.setdefault(name, []).append(ob)
                tris = tris_of(ob)
                summary[obj_name] = {'tri': tris, 'bbox': [round(v, 3) for v in bbox_of(ob)],
                                     'loc': [round(v, 3) for v in ob.location]}
            progress('BUILD', i, n, name + ' (LOD0 %d tri)' % summary['SM_AC6_%s' % name]['tri'])
        except Exception as e:
            _ERRORS[0] += 1
            log('!! %s 构建失败: %r' % (name, e))
            raise

    # 汇总
    _H, _K, _A, _, _ = leg_points(-0.85)
    summary['_joints_LegL'] = {'hip': [round(v, 4) for v in _H],
                               'knee': [round(v, 4) for v in _K],
                               'ankle': [round(v, 4) for v in _A]}
    # L/R 镜像自检（世界顶点包围盒关于 Y=0 镜像，容差 0.01）
    for a, b in (('LegL', 'LegR'), ('ArmL', 'ArmR'), ('GunL', 'GunR')):
        ba, bbv = bbox_of(built[a][0]), bbox_of(built[b][0])
        dev = max(abs(ba[0] - bbv[0]), abs(ba[3] - bbv[3]),
                  abs(ba[1] + bbv[4]), abs(ba[4] + bbv[1]),
                  abs(ba[2] - bbv[2]), abs(ba[5] - bbv[5]))
        log('镜像自检 %s/%s 最大偏差 %.4f m  %s' % (a, b, dev, 'PASS' if dev <= 0.01 else 'FAIL'))
    tot = {}
    for k, v in summary.items():
        if k.startswith('_'):
            continue
        lvl = 2 if k.endswith('_LOD2') else (1 if k.endswith('_LOD1') else 0)
        tot[lvl] = tot.get(lvl, 0) + v['tri']
    for lvl in range(3):
        log('LOD%d 合计三角面: %d' % (lvl, tot.get(lvl, 0)))
    with open(SUMMARY, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    log('已保存 %s | 错误 %d | 用时 %.1fs' % (BLEND, _ERRORS[0], time.time() - _T0))

MATS = None
if __name__ == '__main__':
    try:
        main()
    except Exception:
        import traceback
        log('!! 未捕获异常，原始输出:\n' + traceback.format_exc())
        raise
