# -*- coding: utf-8 -*-
import unreal
def out(s): unreal.log('[LVL] ' + str(s))

out('is_commandlet: %s' % unreal.SystemLibrary.is_unattended())
for n in ['LevelEditorSubsystem','EditorActorSubsystem','EditorLevelLibrary','EditorAssetLibrary',
          'EditorUtilityLibrary','StaticMeshActor','StaticMesh','MaterialInstanceConstant',
          'World','LevelStreamingDynamic']:
    out('has %-26s = %s' % (n, hasattr(unreal, n)))

# 尝试拿子系统
for name in ['LevelEditorSubsystem','EditorActorSubsystem']:
    cls = getattr(unreal, name, None)
    if cls is None: continue
    try:
        ss = unreal.get_editor_subsystem(cls)
        out('get_editor_subsystem(%s) -> %s' % (name, ss))
        ms = [m for m in dir(ss) if not m.startswith('_')]
        out('   方法: %s' % str(ms[:22]))
    except Exception as e:
        out('get_editor_subsystem(%s) EXC: %r' % (name, e))

# Engine 内容里的 BasicShapes 是否可加载
for p in ['/Engine/BasicShapes/Cube.Cube', '/Engine/BasicShapes/Sphere.Sphere',
          '/Engine/BasicShapes/Cylinder.Cylinder', '/Engine/BasicShapes/Cone.Cone',
          '/Engine/BasicShapes/Plane.Plane', '/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial']:
    try:
        a = unreal.load_object(None, p)
        out('load %-52s -> %s' % (p, 'OK' if a else 'None'))
    except Exception as e:
        out('load %-52s EXC %r' % (p, e))
out('LVL_DONE')
