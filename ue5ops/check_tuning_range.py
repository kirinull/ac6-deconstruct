# -*- coding: utf-8 -*-
# 只读验证 L_TuningRange：Actor 清单 + 每个的静态网格 + 变换
import unreal
def out(s): unreal.log('[CHK] ' + str(s))

MAP = '/Game/AC6/Maps/L_TuningRange'
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    out('load_map OK: ' + MAP)
except Exception as e:
    out('load_map EXC: %r' % e)

actors = eas.get_all_level_actors()
out('Actor 总数 = %d' % len(actors))
stat = {}
for a in sorted(actors, key=lambda x: x.get_actor_label()):
    label = a.get_actor_label()
    cls = a.get_class().get_name()
    mesh_name = '-'
    loc = a.get_actor_location()
    scl = a.get_actor_scale3d()
    try:
        smc = a.get_editor_property('static_mesh_component')
        m = smc.get_editor_property('static_mesh')
        mesh_name = m.get_name() if m else 'NONE'
    except Exception:
        pass
    stat[mesh_name] = stat.get(mesh_name, 0) + 1
    out('  %-22s %-16s mesh=%-14s loc=(%.0f,%.0f,%.0f) scale=(%.2f,%.2f,%.2f)' % (
        label, cls, mesh_name, loc.x, loc.y, loc.z, scl.x, scl.y, scl.z))
out('网格使用统计: %s' % str(stat))
out('CHK_DONE')
