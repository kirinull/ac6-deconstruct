# -*- coding: utf-8 -*-
"""确定性创建 AC6Proto（复刻 UE 5.8 项目对话框的行为）

依据：Engine/Source/Editor/GameProjectGeneration/Private/GameProjectUtils.cpp
      - CreateProjectFromTemplate()   (行 1677~1975)
      - Add*ConfigValues() lambdas    (行 101~279)
      - TemplateProjectDefs.ini       (FoldersToIgnore/FilesToIgnore/FolderRenames/ReplacementsInFiles)
用法：python create_project.py [--dry-run]
"""
import io, os, sys, shutil, uuid, argparse

SRC = r"<UE_ENGINE>\Templates\TP_ThirdPerson"
DST = r"<UE_PROJECTS>\AC6Proto"
TEMPLATE_NAME = "TP_ThirdPerson"
PROJECT_NAME  = "AC6Proto"
ENGINE_GUID   = "{8BE48B4A-4983-7546-F391-D6AF967B7AD1}"   # HKCU\\...\\Unreal Engine\\Builds -> <UE_ENGINE>

# --- 来自 Templates/TP_ThirdPerson/Config/TemplateDefs.ini（%TEMPLATENAME% 已展开）---
FOLDERS_TO_IGNORE = ["Binaries", "Build", "Intermediate", "Saved", "Media",
                     "Content/ThirdPerson/Animations", "Content/ThirdPerson/Character"]
FILES_TO_IGNORE = [TEMPLATE_NAME + ".uproject", TEMPLATE_NAME + ".png",
                   "Config/TemplateDefs.ini", "Config/config.ini",
                   TEMPLATE_NAME + ".opensdf", TEMPLATE_NAME + ".sdf",
                   TEMPLATE_NAME + ".v11.suo", TEMPLATE_NAME + ".v12.suo",
                   TEMPLATE_NAME + ".sln", "Manifest.json", "contents.txt"]
FOLDER_RENAMES = [("Source/" + TEMPLATE_NAME, "Source/" + PROJECT_NAME),
                  ("Source/" + TEMPLATE_NAME + "Editor", "Source/" + PROJECT_NAME + "Editor")]
# 顺序即 ini 顺序：大写 -> 小写 -> 忽略大小写
REPLACEMENTS = [("TP_THIRDPERSON", "AC6PROTO", True),
                ("tp_thirdperson", "ac6proto", True),
                ("TP_ThirdPerson", "AC6Proto", False)]
REPL_EXTS = {"cpp", "h", "ini", "cs"}

# --- 来自 Add*ConfigValues()（模板工程路径；bIsBlankTemplate=False）---
# (section, key, value, should_replace)
CFG_ENGINE = [
    ("/Script/HardwareTargeting.HardwareTargetingSettings", "TargetedHardwareClass", "Desktop", True),
    ("/Script/HardwareTargeting.HardwareTargetingSettings", "DefaultGraphicsPerformance", "Maximum", True),
    ("/Script/Engine.RendererSettings", "r.GenerateMeshDistanceFields", "True", True),
    ("/Script/Engine.RendererSettings", "r.DynamicGlobalIlluminationMethod", "1", True),
    ("/Script/Engine.RendererSettings", "r.ReflectionMethod", "1", True),
    ("/Script/Engine.RendererSettings", "r.Shadow.Virtual.Enable", "1", True),
    ("/Script/Engine.RendererSettings", "r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange", "True", False),
    ("/Script/Engine.RendererSettings", "r.DefaultFeature.LocalExposure.HighlightContrastScale", "0.8", False),
    ("/Script/Engine.RendererSettings", "r.DefaultFeature.LocalExposure.ShadowContrastScale", "0.8", False),
    ("/Script/Engine.RendererSettings", "r.SkinCache.CompileShaders", "True", False),
    ("/Script/Engine.RendererSettings", "r.RayTracing", "True", False),
    ("/Script/Engine.RendererSettings", "r.RayTracing.RayTracingProxies.ProjectEnabled", "True", False),
    ("/Script/Engine.RendererSettings", "r.Substrate", "True", False),
    ("/Script/Engine.RendererSettings", "r.Substrate.ProjectGBufferFormat", "0", False),
    ("/Script/WindowsTargetPlatform.WindowsTargetSettings", "DefaultGraphicsRHI", "DefaultGraphicsRHI_DX12", False),
]
CFG_GAME_EXTRA = [
    ("ConsoleVariables", "CommonUI.CheckKeyboardFocusAndParentage", "1", True),
    ("ConsoleVariables", "CommonUI.DisallowUserFocusedWidgetForPendingFocusRecipient", "1", True),
    ("ConsoleVariables", "CommonUI.FallbackToDesiredOnAutoRestoreFailure", "1", True),
]


def apply_replacements(text):
    """两趟占位符法（与 UE 一致，避免替换结果被后续规则再命中）"""
    for i, (frm, _to, cs) in enumerate(REPLACEMENTS):
        text = text.replace(frm, "\x00PH%d\x00" % i) if cs else \
               _replace_ci(text, frm, "\x00PH%d\x00" % i)
    for i, (_frm, to, _cs) in enumerate(REPLACEMENTS):
        text = text.replace("\x00PH%d\x00" % i, to)
    return text


def _replace_ci(text, frm, to):
    import re
    return re.sub(re.escape(frm), to.replace("\\", "\\\\"), text, flags=re.IGNORECASE)


def apply_folder_renames(relpath):
    for frm, to in FOLDER_RENAMES:
        if relpath.startswith(frm + "/"):
            return to + relpath[len(frm):]
    return relpath


def patch_ini(path, section, key, value, replace):
    """返回 (动作, 是否变更)"""
    lines = io.open(path, encoding="utf-8", errors="ignore").read().split("\n") if os.path.exists(path) else []
    sec_hdr = "[" + section + "]"
    si = None
    for i, ln in enumerate(lines):
        if ln.strip() == sec_hdr:
            si = i
            break
    if si is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append(sec_hdr)
        lines.append(key + "=" + value)
        io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
        return ("added-section", True)
    # 找段尾
    end = len(lines)
    for j in range(si + 1, len(lines)):
        if lines[j].startswith("[") and lines[j].rstrip().endswith("]"):
            end = j
            break
    for j in range(si + 1, end):
        if lines[j].split("=")[0].strip() == key:
            if replace:
                lines[j] = key + "=" + value
                io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
                return ("replaced", True)
            return ("kept-existing", False)
    lines.insert(end, key + "=" + value)
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    return ("added-key", True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not os.path.isdir(SRC):
        print("ERROR: template missing: " + SRC); return 1
    if os.path.exists(DST) and os.listdir(DST):
        print("ERROR: destination not empty: " + DST); return 1

    files, skipped = [], []
    for dp, dns, fns in os.walk(SRC):
        dns[:] = [d for d in dns if d not in ("Meta",)]
        for fn in fns:
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, SRC).replace("\\", "/")
            if rel in FILES_TO_IGNORE:
                skipped.append(("file-ignore", rel)); continue
            if any(rel.startswith(f + "/") for f in FOLDERS_TO_IGNORE):
                skipped.append(("folder-ignore", rel)); continue
            files.append(rel)

    print("源文件总数      : %d" % (len(files) + len(skipped)))
    print("将复制          : %d" % len(files))
    print("将跳过          : %d" % len(skipped))
    for kind, rel in skipped[:14]:
        print("    [%s] %s" % (kind, rel))

    if a.dry_run:
        print("\n--dry-run，未写盘")
        return 0

    os.makedirs(os.path.join(DST, "Content"), exist_ok=True)
    n_copy = n_repl = 0
    for rel in files:
        dest_rel = apply_folder_renames(rel)
        dest_rel = "/".join(apply_replacements(p) if p.lower().startswith("tp_thirdperson")
                            else p for p in dest_rel.split("/"))
        dst = os.path.join(DST, dest_rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        ext = os.path.splitext(rel)[1].lstrip(".").lower()
        if ext in REPL_EXTS:
            raw = io.open(os.path.join(SRC, rel.replace("/", os.sep)), "rb").read()
            txt = raw.decode("utf-8", "surrogateescape")
            out = apply_replacements(txt)
            if out != txt: n_repl += 1
            io.open(dst, "wb").write(out.encode("utf-8", "surrogateescape"))
        else:
            shutil.copy2(os.path.join(SRC, rel.replace("/", os.sep)), dst)
        n_copy += 1
    print("\n已复制 %d 个文件（其中 %d 个做了文本替换）" % (n_copy, n_repl))

    # --- .uproject ---
    uproject = """{
\t"FileVersion": 3,
\t"EngineAssociation": "%s",
\t"Category": "",
\t"Description": "",
\t"Modules": [
\t\t{
\t\t\t"Name": "%s",
\t\t\t"Type": "Runtime",
\t\t\t"LoadingPhase": "Default",
\t\t\t"AdditionalDependencies": [
\t\t\t\t"Engine",
\t\t\t\t"AIModule",
\t\t\t\t"UMG"
\t\t\t]
\t\t}
\t],
\t"Plugins": [
\t\t{
\t\t\t"Name": "ModelingToolsEditorMode",
\t\t\t"Enabled": true,
\t\t\t"TargetAllowList": [
\t\t\t\t"Editor"
\t\t\t]
\t\t},
\t\t{
\t\t\t"Name": "StateTree",
\t\t\t"Enabled": true
\t\t},
\t\t{
\t\t\t"Name": "GameplayStateTree",
\t\t\t"Enabled": true
\t\t}
\t]
}
""" % (ENGINE_GUID, PROJECT_NAME)
    upath = os.path.join(DST, PROJECT_NAME + ".uproject")
    io.open(upath, "w", encoding="utf-8", newline="\n").write(uproject)
    print("已写 %s" % upath)

    # --- Config 值 ---
    dei = os.path.join(DST, "Config", "DefaultEngine.ini")
    dgi = os.path.join(DST, "Config", "DefaultGame.ini")
    print("\nDefaultEngine.ini 配置写入：")
    for sec, k, v, rp in CFG_ENGINE:
        act, ch = patch_ini(dei, sec, k, v, rp)
        print("   %-14s %s" % (act, k))
    # FGuid::ToString() 默认用 EGuidFormats::Digits = 32 位十六进制、无横线
    # 依据：Runtime/Core/Public/Misc/Guid.h:31  AppendString(ValueStr, EGuidFormats::Digits)
    # 写成带横线的 UUID 会让引擎报：
    #   LogObj: Error: LoadConfig (...GeneralProjectSettings): import failed for ProjectID
    pid = str(uuid.uuid4()).replace("-", "").upper()
    act, ch = patch_ini(dgi, "/Script/EngineSettings.GeneralProjectSettings", "ProjectID", pid, True)
    print("DefaultGame.ini 配置写入：")
    print("   %-14s ProjectID=%s" % (act, pid))
    for sec, k, v, rp in CFG_GAME_EXTRA:
        act, ch = patch_ini(dgi, sec, k, v, rp)
        print("   %-14s %s" % (act, k))

    # --- 模块重定向（救回引用被改名 C++ 类的那 109 个 .uasset）---
    for sec, key, val in [
        ("/Script/Engine.Engine", "+ActiveGameNameRedirects",
         '(OldGameName="/Script/%s",NewGameName="/Script/%s")' % (TEMPLATE_NAME, PROJECT_NAME)),
        ("/Script/Engine.Engine", "+ActiveGameNameRedirects",
         '(OldGameName="%s",NewGameName="/Script/%s")' % (TEMPLATE_NAME, PROJECT_NAME)),
    ]:
        act, ch = patch_ini(dei, sec, key, val, False)
        print("   %-14s %s" % (act, val[:58]))
    # 类重定向靠反推（见 fix_class_redirects.py），此处不重复

    # --- SharedContentPacks（易漏步：纯文件复制不会做这件事）---
    # 源码依据：GameProjectUtils::AddSharedContentToProject
    #           -> FFeaturePackContentSource::InsertAdditionalResources
    # 规则：<TemplateResources>/<DetailLevel>/<MountName>/Content/**
    #        ->  <Project>/Content/<MountName>/**
    print("\nSharedContentPacks（TemplateResources）：")
    TR = os.path.join(os.path.dirname(SRC), "TemplateResources")
    LEVEL = "High"   # TemplateDefs.ini: EditDetailLevelPreference="High"
    for pack in ["LevelPrototyping", "Characters", "Input"]:
        psrc = os.path.join(TR, LEVEL, pack, "Content")
        if not os.path.isdir(psrc):
            print("   [MISS] %s" % pack)
            continue
        pdst = os.path.join(DST, "Content", pack)
        cnt = 0
        for dp, dns, fns in os.walk(psrc):
            rel = os.path.relpath(dp, psrc)
            out = os.path.join(pdst, rel) if rel != "." else pdst
            os.makedirs(out, exist_ok=True)
            for fn in fns:
                shutil.copy2(os.path.join(dp, fn), os.path.join(out, fn))
                cnt += 1
        print("   %-18s %3d files -> Content/%s" % (pack, cnt, pack))

    print("\n完成。目标目录: %s" % DST)
    print("下一步：python ue5ops/fix_class_redirects.py   （反推 +ActiveClassRedirects）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
