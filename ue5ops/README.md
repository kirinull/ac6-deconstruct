# ue5ops/ — UE5 实操 session 的引擎内操作脚本

> **归属**：本目录由 **UE5 实操 session** 创建并维护。
> 文档 session（写拆解报告的那个）**只读**，不修改这里的脚本。
>
> **与 `tools/` 的区别**：
> - `tools/`（仓库根）= **离线取证**脚本：解析 `regulation.bin`、查 paramdex、验文档数字。
> - `ue5ops/`（本目录）= **引擎内**脚本：跑在 UE 5.8 的 Python 环境 / 编辑器上下文里，操作 `<UE_PROJECTS>\AC6Proto`。

## 脚本清单

### 建工程（复刻项目对话框行为）

| 脚本 | 作用 |
|---|---|
| `create_project.py` | 确定性创建 `AC6Proto`；依据 `GameProjectUtils.cpp` 的 `CreateProjectFromTemplate()`（行 1677~1975）与 `Add*ConfigValues()`（行 101~279） |
| `add_shared_content.py` | 补齐 `SharedContentPacks`——项目对话框会做、纯文件复制不会做的一步 |
| `fix_class_redirects.py` | 补写 `ActiveGameNameRedirects` / `ActiveClassRedirects`；否则模板 `.uasset` 里序列化的 C++ 类包路径失效、蓝图全断 |

### 数据层（CSV → DataTable）

| 脚本 | 作用 |
|---|---|
| `prepare_csv.py` | 修正「行名去重用了大小写敏感键」的缺陷。**背景**：`tools/export_ue_datatables.py:186` 的 `if nm in used:` 用大小写敏感字典去重，但 UE 的 `FName` 行名大小写**不**敏感，于是仅大小写不同的两个行名双双通过去重、在 UE 侧撞名 |
| `gen_data_rows.py` | 从 `data/ue_datatables/*.struct.txt` 生成 C++ 行结构体头文件（路线 B；Python 无法给 `UserDefinedStruct` 加字段，且 `CSVImportFactory` 无 RowStruct 时直接放弃） |
| `import_datatables.py` | **编辑器上下文**里把 CSV 导入为 DataTable。源目录取 `<UE_PROJECTS>\AC6Proto\data\ue_datatables`（`prepare_csv.py` 修正过的副本；仓库里的原目录归文档 session，不改） |
| `verify_datatables.py` | 数值级验证：从 DataTable 逐格读值与源 CSV 比对 |
| `test_datahub.py` | 验证 `AC6DataHub` 读取层：逐个 getter 调用 + 契约检查 |

### 关卡与验证

| 脚本 | 作用 |
|---|---|
| `build_tuning_range.py` | 生成白箱靶场 `L_TuningRange`（M0 §3.10 的四个可视靶子；T1 转速靶 / T2 姿态靶 / …） |
| `check_tuning_range.py` | 只读验证 `L_TuningRange`：Actor 清单 + 静态网格 + 变换 |
| `check_struct_vs_csv.py` | 比对已导入的 Struct 与源 CSV |
| `probe_level.py` | 探查编辑器/关卡子系统可用性（`LevelEditorSubsystem`、`EditorActorSubsystem` 等） |

## 运行前提

这些脚本里有 `import unreal` 的必须在 **UE 编辑器内的 Python 环境**跑（Output Log → Cmd 输入 `py <脚本路径>`，或用 Editor Utility Widget）；
没有 `import unreal` 的（如 `prepare_csv.py`、`gen_data_rows.py`、`check_struct_vs_csv.py`）可直接用系统 Python 跑。

## 回填

实操中量到任何与文档不符的值 → **不改文档**，按 `docs/02_实施/UE5_开工简报.md` §7.2 的格式回填到 `handback/`。
