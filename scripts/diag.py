# -*- coding: utf-8 -*-
# diag.py — 镜像/枢轴诊断：直接开成品 .blend 打印世界顶点包围盒
import bpy

bpy.ops.wm.open_mainfile(filepath=r'.\assets\mech\AC6Mech.blend')
for n in ('SM_AC6_LegL', 'SM_AC6_LegR', 'SM_AC6_ArmL', 'SM_AC6_ArmR', 'SM_AC6_GunL', 'SM_AC6_GunR'):
    ob = bpy.data.objects[n]
    pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    lt = ob.matrix_world.translation
    print('D|%s loc=(%.3f,%.3f,%.3f) mw=(%.3f,%.3f,%.3f) world=(%.3f..%.3f, %.3f..%.3f, %.3f..%.3f)'
          % (n, ob.location.x, ob.location.y, ob.location.z, lt.x, lt.y, lt.z,
             min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)), flush=True)
