# -*- coding: utf-8 -*-
# diag2.py — 列出 .blend 内全部对象（名字/类型/位置/尺寸/材质槽）
import bpy

bpy.ops.wm.open_mainfile(filepath=r'.\assets\mech\AC6Mech.blend')
print('D2|对象总数 = %d' % len(bpy.data.objects), flush=True)
for ob in sorted(bpy.data.objects, key=lambda x: x.name):
    mats = ','.join(s.material.name if s.material else '-' for s in ob.material_slots)
    d = ob.dimensions
    print('D2|%s type=%s loc=(%.2f,%.2f,%.2f) dim=(%.2f,%.2f,%.2f) mats=[%s]'
          % (ob.name, ob.type, ob.location.x, ob.location.y, ob.location.z, d.x, d.y, d.z, mats), flush=True)
