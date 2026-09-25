# -*- coding: utf-8 -*-
"""补写 ActiveGameNameRedirects / ActiveClassRedirects

为什么需要：模板里的 .uasset（蓝图）序列化保存了 C++ 类的包路径，例如
  /Script/TP_ThirdPerson.TP_ThirdPersonCharacter
改名成 AC6Proto 后这些路径失效 -> 蓝图全断。
UE 的项目对话框靠这两个重定向表在加载时修复（源码依据）：
  - UDefaultTemplateProjectDefs::AddConfigValues  -> +ActiveGameNameRedirects（2 条）
  - CreateProjectFromTemplate 里 ClassRenames 循环 -> +ActiveClassRedirects
本脚本不硬编码，而是**从磁盘反推**应写的条目，可重复运行（幂等）。
"""
import io, os, sys, re

DST = r"<UE_PROJECTS>\AC6Proto"
TEMPLATE_NAME = "TP_ThirdPerson"
PROJECT_NAME = "AC6Proto"
DEI = os.path.join(DST, "Config", "DefaultEngine.ini")

# 找出被改名的 .h，且内容含 .generated.h"（= IsClassRename 的判据）
renames = []
for dp, dns, fns in os.walk(os.path.join(DST, "Source")):
    for fn in fns:
        if not fn.endswith(".h"):
            continue
        path = os.path.join(dp, fn)
        raw = io.open(path, "rb").read().decode("utf-8", "replace")
        if '.generated.h"' not in raw:
            continue
        # 原名 = 把 PROJECT_NAME 前缀换回 TEMPLATE_NAME
        if fn.startswith(PROJECT_NAME):
            old = TEMPLATE_NAME + fn[len(PROJECT_NAME):]
            if old != fn:
                renames.append((os.path.splitext(old)[0], os.path.splitext(fn)[0]))

lines = io.open(DEI, encoding="utf-8", errors="surrogateescape").read().split("\n")
SEC = "[/Script/Engine.Engine]"
si = None
for i, ln in enumerate(lines):
    if ln.strip() == SEC:
        si = i
        break

entries = [
    '+ActiveGameNameRedirects=(OldGameName="/Script/%s",NewGameName="/Script/%s")' % (TEMPLATE_NAME, PROJECT_NAME),
    '+ActiveGameNameRedirects=(OldGameName="%s",NewGameName="/Script/%s")' % (TEMPLATE_NAME, PROJECT_NAME),
] + ['+ActiveClassRedirects=(OldClassName="%s",NewClassName="%s")' % (o, n) for o, n in renames]

if si is None:
    if lines and lines[-1].strip() != "":
        lines.append("")
    lines.append(SEC)
    lines.extend(entries)
    print("新建段 %s" % SEC)
else:
    end = len(lines)
    for j in range(si + 1, len(lines)):
        if lines[j].startswith("[") and lines[j].rstrip().endswith("]"):
            end = j; break
    for e in entries:
        key = e.split("=")[0]
        if any(lines[j].strip() == e for j in range(si + 1, end)):
            print("  [已存在] %s" % e); continue
        lines.insert(end, e); end += 1
        print("  [已写入] %s" % e)

io.open(DEI, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write("\n".join(lines))
print("\nClassRenames 反推结果: %d 条" % len(renames))
for o, n in renames:
    print("   %s -> %s" % (o, n))
