# -*- coding: utf-8 -*-
"""补齐 SharedContentPacks（UE 项目对话框会做、但纯文件复制不会做的一步）

规则（源码依据 GameProjectUtils::AddSharedContentToProject ->
      FFeaturePackContentSource::InsertAdditionalResources）：
  <TemplateResources>/<DetailLevel>/<MountName>/Content/**  ->  <Project>/Content/<MountName>/**
DetailLevel 由 EditDetailLevelPreference 决定（TP_ThirdPerson = High）。
已用参照工程逐包核对文件数：Characters 128/128、Input 9/9、LevelPrototyping 29/29。
"""
import io, os, shutil, sys

TR   = r"<UE_ENGINE>\Templates\TemplateResources"
DST  = r"<UE_PROJECTS>\AC6Proto\Content"
LEVEL = "High"          # TemplateDefs.ini: EditDetailLevelPreference="High"
PACKS = ["LevelPrototyping", "Characters", "Input"]   # TemplateDefs.ini: SharedContentPacks

def main():
    if not os.path.isdir(TR):
        print("ERROR: TemplateResources missing: " + TR); return 1
    total = 0
    for pack in PACKS:
        src = os.path.join(TR, LEVEL, pack, 'Content')
        if not os.path.isdir(src):
            print("  [MISS] %s -> %s" % (pack, src)); continue
        dst = os.path.join(DST, pack)
        n = 0
        for dp, dns, fns in os.walk(src):
            rel = os.path.relpath(dp, src)
            out = os.path.join(dst, rel) if rel != '.' else dst
            os.makedirs(out, exist_ok=True)
            for fn in fns:
                shutil.copy2(os.path.join(dp, fn), os.path.join(out, fn))
                n += 1
        print("  [OK] %-18s %3d files -> Content/%s" % (pack, n, pack))
        total += n
    print("\n合计复制 %d 个文件" % total)
    return 0

if __name__ == "__main__":
    sys.exit(main())
