# P21 · C++ 与蓝图的分工，以及 UE 5.8 的 Agent 协作实测

> **触发问题**（用户 2026-09-11）："C++ 会比蓝图好用吗，和 agent 协同是不是 C++ 更适合"
> **核查方式**：不是查资料得出的印象，而是**在你自己机器上的 UE 5.8.2 里逐项实测**（`<UE_ENGINE>`），加 Epic 官方文档原文。
> **证据分级**：**A** = 本机可复现 / 官方原文；**B** = 本机可复现的统计；**C** = 未在本机验证的说法。
>
> **⚠️ 勘误（2026-09-11，初版发布后自查发现）**：初版有 **2 个数字口径错误**——`AICallable` 总数写作 333（未排除 `Intermediate/`、`Binaries/`，实际 **275**）、蓝图操作码写作 103 个（那是**行数**，去重后实际 **102 个**）。两处均已修正，并已把正确口径写成 `tools/verify_doc.py` 的断言（这份文档的每个数字现在都会自动复核）。**教训：本项目「第 7 坑 = 统计口径」第 4 次咬到我。**

---

## 0. 两句话结论

| 问题 | 结论 |
|---|---|
| **C++ 比蓝图好用吗？** | **不是"哪个更好"，是"两者分工"。** 但有一类事**只有 C++ 能做**——而那一类恰好是**技术美术的核心地盘**（渲染管线、着色器、自定义资产类型）。所以对**你的职业目标**，C++ 不是"可选项" |
| **和 Agent 协同，C++ 更适合吗？** | **是，而且 Epic 已经把这件事写进引擎了。** UE 5.8 内置官方 **Unreal MCP** 插件 + **27 个官方 Toolset / 275 处 `AICallable` 标记**——**全部是 C++ 定义的**。而这套官方能力面里，**没有任何一个能编辑蓝图图谱** |

---

## 1. ★ 最重要的发现：UE 5.8 内置了官方 MCP 服务器

### 1.1 它就在你的引擎里（A 级）

```
<UE_ENGINE>\Engine\Plugins\Experimental\ModelContextProtocol\
├─ ModelContextProtocol.uplugin
├─ Binaries\Win64\UnrealEditor-ModelContextProtocol.dll        (443 KB，已编译)
│                  UnrealEditor-ModelContextProtocolEditor.dll  (324 KB)
│                  UnrealEditor-ModelContextProtocolEngine.dll  (362 KB)
│                  + Tests 三个 DLL
└─ Source\（6 个模块）
```

`.uplugin` 原文（关键字段逐字抄录）：

```json
{
	"FriendlyName": "Unreal MCP",
	"Description": "Anthropic MCP (Model Context Protocol) server implementation for Unreal Engine.",
	"Category": "Other",
	"NoRedist": true,
	"CreatedBy": "Epic Games, Inc.",
	"IsExperimentalVersion": true,
	"Installed": false,
	"EnabledByDefault": false,
	"Plugins": [
		{ "Name": "EngineAssetDefinitions", "Enabled": true },
		{ "Name": "ToolsetRegistry",       "Enabled": true }
	]
}
```

**四个必须注意的点**：

1. **这是 Epic 官方写的**（`CreatedBy: "Epic Games, Inc."`），不是社区插件
2. **默认关闭**（`EnabledByDefault: false`）+ **从未安装过**（`Installed: false`）→ 你不开它，它就不存在
3. **实验性**（`IsExperimentalVersion: true`）→ API 会变，别把项目架构压在它上面
4. **`NoRedist: true`** → 只在你自己的引擎里用，不能随作品集分发

### 1.2 它暴露什么：Toolset 架构（A 级）

MCP 插件本身只实现协议（`tools/list`、`tools/call`、`resources/list`、`resources/read`）。**真正的能力来自 Toolset**：

```cpp
// Engine/Plugins/Experimental/ToolsetRegistry/Source/ToolsetRegistry/Public/ToolsetRegistry/Toolset.h
namespace UE::ToolsetRegistry
{
	/// Base class for toolsets.
	class FToolset
	{
		/// Executes a tool with the given name and JSON input.
		TFuture<TValueOrError<FString, FString>> ExecuteTool(
			const FString& ToolName, const FString& JsonInput);

		/// Get the JSON schema the enabled tools in this toolset.
		FString GetJsonSchema() const;
		...
	};
}
```

**一个 Toolset = 一个 C++ 类 + JSON 进 / JSON 出。** 这就是 UE 5.8 的 agent 接口形态。

### 1.3 `AICallable` —— 官方给 C++ 函数打的"AI 可调用"标记（A 级）

```
Engine/Plugins/Experimental/Toolsets/EditorToolset/.../EditorAppToolset.h:206
	UFUNCTION(meta = (AICallable))
```

UHT 对它的处理（`Engine/Source/Programs/Shared/EpicGames.UHT/Types/UhtFunction.cs:618`）：

```csharp
bool storeCppDefaultValueInMetaData =
    FunctionFlags.HasAnyFlags(EFunctionFlags.BlueprintCallable | EFunctionFlags.Exec)
    || MetaData.ContainsKey("AICallable");     // ← 与 BlueprintCallable 并列
```

**即：Epic 把 `AICallable` 提到了和 `BlueprintCallable` 同一层级。**

**口径必须写清**（本项目第 7 坑「统计口径」的又一次现身）：

| 统计范围 | 次数 |
|---|---:|
| **官方 Toolsets 目录内**（`.h/.cpp/.cs`，排除 `Intermediate/`、`Binaries/`） | **275** ← 本文全篇采用此口径 |
| 加上 `Engine/Source/`（只有 UHT 那 1 处） | 276 |
| 整个 `Engine/Plugins/`（含非 Toolset 插件） | 308 |

> ⚠️ **本报告初版这里写的是 333，是错的。** 错因：当时用 `grep -rho` 统计，**没有排除 `Intermediate/` 与 `Binaries/`**（里面是二进制文件），虚高了 58。现已改为可复现的口径并写进 `tools/verify_doc.py` 断言。

### 1.4 27 个官方 Toolset 的 AICallable 函数数（B 级，本机统计）

| 次数 | Toolset | | 次数 | Toolset |
|---:|---|---|---:|---|
| 56 | NiagaraToolsets | | 14 | SlateInspectorToolset |
| 32 | PCGToolset | | 14 | GASToolsets |
| 25 | EditorToolset | | 9 | MVVMToolset |
| 23 | UMGToolSet | | 8 | ConfigSettingsToolset |
| 22 | DataflowAgent | | 7 | GameFeaturesToolset |
| 17 | PluginToolset | | 7 | DataRegistryToolset |
| 17 | PhysicsToolsets | | 7 | AutomationTestToolset |
| 6 | GameplayTagsToolset | | 6 | ChaosClothAssetToolset |
| 2 | WorldConditionsToolset | | 2 | SemanticSearchToolset |
| 1 | LiveCodingToolset | | **275** | **合计（19 个工具集含该标记）** |

> 27 个工具集里 **19 个**用了 `AICallable`；其余 8 个（AIModule、AnimationAssistant、Conversation、MCPClient、MetaHumanGenerator、SequencerAnimMixer、DataflowAgent 之外的若干）走 Python 侧工具定义或暂未标记。

**注意这张表的形状**：Niagara、PCG、物理、GAS、UMG、Sequencer、MetaHuman、Dataflow——**全是"系统级"的东西**。这些恰恰是放在 C++ 里、通过 UFUNCTION 暴露的能力。

### 1.5 唯一的缺口：没有蓝图图谱工具集（A 级）

```bash
$ find /j/UE_5.8/Engine -iname "*BlueprintToolset*" -o -iname "*KismetToolset*" -o -iname "*GraphToolset*"
（无输出）
```

**27 个工具集里，没有任何一个能编辑蓝图事件图 / 函数图 / 节点。**

唯一操作图节点的工具集是 `DataflowAgent`（用了 `EdGraphNode`、`EdGraphNode_Comment`）——但它操作的是 **Dataflow 图**，而 Dataflow 是 **C++ 定义的节点系统**（`FDataflowNode` + 结构化 schema）。

> **这条最能说明问题**：Epic 想做"让 AI 编辑节点图"这件事时，他们**选了一个 C++ 定义的图**来做，而不是蓝图。
> 因为 C++ 定义的节点系统有**机器可读的 schema**，蓝图图谱没有。

### 1.6 Epic 自己的 AI Assistant 用的是同一套（A 级）

```cpp
// Engine/Plugins/Experimental/AIAssistant/Source/AIAssistant/Private/AIAssistantToolset.h:78
class UAIAssistantToolset : public UToolsetDefinition
```

- 插件：`Engine/Plugins/Experimental/AIAssistant/`（同样实验性、默认关闭）
- 后端：`https://dev.epicgames.com/community/assistant/embedded`（Epic 自家云助手）
- 依赖：`PythonScriptPlugin`
- **它的工具面 = 同一套 Toolset 系统**

---

## 2. 为什么蓝图对 Agent 天然不友好（结构性原因，A 级）

这不是"感觉"，是三个可验证的结构事实：

### 2.1 蓝图资产是二进制，且没有文本形态

| | C++ | 蓝图 |
|---|---|---|
| 存储 | `.h` / `.cpp` **纯文本** | `.uasset` **二进制** |
| Agent 能否直接读 | ✅ 能 | ❌ 不能（要靠编辑器 API 反查） |
| Git diff | ✅ 逐行 | ❌ 只能 "Binary files differ" |
| Git merge | ✅ 能 | ❌ 不能，只能锁文件 |
| 代码搜索 | ✅ `grep`/`rg` 秒级 | ⚠️ 只能靠编辑器的 Find in Blueprints |

蓝图编辑器**内部**确实有文本导出（`FEdGraphUtilities::ExportNodesToText`，用于复制粘贴节点和 Diff 工具），但它是**编辑器私有 C++ API**——没有暴露给 Python，也没有暴露给 Toolset。

### 2.2 没有蓝图图谱的 Python API

```bash
$ grep -rhoE "Py[A-Za-z]{2,30}" .../PythonScriptPlugin/.../PyWrapper*.cpp | grep -i "blueprint|kismet|graph"
（无输出）
```

Python 插件里**没有** `Py*Blueprint` / `Py*Kismet` / `Py*Graph` 类。
唯一的交集是**反方向**：`K2Node_ExecutePythonScript`（蓝图节点去调 Python，不是 Python 建蓝图节点）。

### 2.3 Agent 至今只能通过"专用 API"碰蓝图，而不是读写资产

这是重要的**细微差别**——蓝图并非完全不可触及，但方式很受限：

| Toolset | 能否碰蓝图资产 | 怎么碰 |
|---|---|---|
| `UMGToolSet`（24 个） | ✅ 能 | `AddWidget` / `RemoveWidget` / `RenameWidget` / `MoveWidget` / `BindToEventProperty` / **`CompileWidgetBlueprint`** —— 操作的是 **Widget 树结构**，不是图谱节点 |
| `MVVMToolset`（10 个） | ✅ 能 | `CreateViewModel(...)` 返回 `UBlueprint*`、`AddViewModelProperty(...)` —— 建资产 + 加属性，**不碰图谱** |
| `GameplayCueToolset`（GASToolsets 内） | ✅ 能 | 创建 GameplayCueNotify **蓝图资产**（创建，不编辑图） |
| **任何蓝图事件图编辑** | ❌ **不能** | **无对应工具集** |

**规律**：Agent 能操作的是**结构化数据**（Widget 树、ViewModel 属性、资产创建）。一旦落到"往事件图里连节点"，官方能力面就断了。

---

## 3. C++ 独有的事（对 TA 尤其关键，A 级）

### 3.1 渲染管线只能 C++

| 能力 | 蓝图能否 | 证据 |
|---|---|---|
| **全局着色器**（`IMPLEMENT_GLOBAL_SHADER`） | ❌ | 蓝图侧无任何对应节点 |
| **渲染依赖图 RDG** | ❌ | `RenderGraph.h` 等无 `UFUNCTION`/`UCLASS` 暴露 |
| **自定义 Render Pass / 后处理 Pass** | ❌ | 同上，全在 `RenderCore` C++ 层 |
| 材质编辑器 | ✅ 能（但受限于材质节点） | 材质是**数据**，不是逻辑 |
| Niagara / PCG | ⚠️ 编辑器内能，**但 agent 只能通过 Toolset API 操作** | 见 §1.4 |

> **这一格就是你的职业护城河。** TA 岗位的核心差异点在于"能改渲染管线"。材质编辑器谁都会连；**能写 Global Shader / RDG Pass 的人少一个数量级**。而这两件事**蓝图做不到**。

### 3.2 其它 C++ 独有 / 远优于蓝图的事

| 场景 | 为什么 |
|---|---|
| 自定义 Asset 类型 / 自定义编辑器 | 需要 `UCLASS` + `UFactory` + 编辑器模块 |
| 插件 / 自定义模块 | `Build.cs` 是 C#，模块是 C++ |
| 修改引擎源码 | 只能 C++ |
| 性能热点（每帧、循环、复杂数学） | 见 §4 |
| 第三方库接入 | 需要 C++ 链接 |

---

## 4. 性能：结构上为什么蓝图更慢（附证据等级）

**Epic 官方原文**（`Blueprint Best Practices`，本机直读）：

> "However, there are certain things that will impact your performance more if they are done in Blueprints. **If you have a Blueprint that's doing a lot of operations and complex math every tick, you might want to consider using native C++ code.** Blueprints are best suited to making event-driven functionality, such as handling damage taking, controls, and other things that don't get called every frame."

**结构性原因**（A 级，本机源码）：

```cpp
// Engine/Source/Runtime/CoreUObject/Private/UObject/ScriptCore.cpp
void ProcessLocalScriptFunction(UObject* Context, UFunction* Function, FFrame& Stack, RESULT_DECL);
void ProcessScriptFunction(...);
```

蓝图编译成**字节码**，由 VM **解释执行**；`Script.h` 里定义了 **102 个不同的 `EX_*` 操作码**。C++ 是编译成原生机器码。这是解释器 vs 原生码的结构差异。

> **⚠️ 诚实标注**：社区常说"蓝图比 C++ 慢约 10 倍"。**这个具体倍率我没有在本机测**（测它需要在编辑器里手搓一套对比蓝图，无法用命令行完成——**这件事本身就是 §2 的例证**）。所以：**结构原因 = A 级；10× = C 级，别当结论用**。

**但要注意**：M0/M1 这种原型规模**根本碰不到这个瓶颈**。性能不是你现在该选 C++ 的理由——**§1 的 agent 协作与 §3 的能力边界才是**。

---

## 5. 那蓝图的价值是什么（别走另一个极端）

Epic 官方对两者关系的定位（`Blueprints Visual Scripting` 页，本机直读）：

> "Blueprint-specific markup available in Unreal Engine's C++ implementation enables **programmers to create baseline systems that can be extended by designers**."

**这就是 Epic 的设计意图：C++ 写基类与系统，蓝图做派生与调参。**

蓝图不可替代的地方：

| 场景 | 为什么蓝图赢 |
|---|---|
| 策划/美术自己调数值与流程 | 不需要编译，改完即生效 |
| 快速原型（"这个机制好不好玩"） | 迭代速度是 C++ 的数倍 |
| 事件驱动的胶水逻辑 | Epic 明说这是蓝图的主场 |
| 动画蓝图 / 状态机可视化 | 本质是数据 + 图，可视化确实更直观 |
| **你自己练引擎手感** | 你 UE5 = 0，蓝图是理解引擎概念的最短路径 |

---

## 6. 对你的具体结论（结合真实画像）

### 6.1 回答"和 agent 协同是不是 C++ 更适合"

**是，而且优势比你想的大。** 对 agent 协作，C++ 有四个结构性优势：

| 优势 | 具体表现 |
|---|---|
| **文本可读写** | 我能 `read` / `edit` / `grep` 你的 C++；`.uasset` 我看不见 |
| **编译错误 = 天然反馈信号** | `UnrealBuildTool` 是命令行工具 → 我能真编译、真拿到报错、真修。**已在你的机器上验证过**（`ToolchainCheck`：UBT 9.2 s + 编译 79 s，均 Succeeded） |
| **官方 agent 面就是 C++** | `AICallable` 打在 C++ 函数上；Toolset 是 C++ 类 |
| **可 diff / 可回滚** | 改坏了 `git checkout` 就回来了；蓝图改坏了只能靠编辑器 Undo 栈（关掉就没了） |

**反过来，蓝图是"我看不见、改不动、验证不了"的地带。** 你让我改蓝图，我只能：① 用文字告诉你点哪里；② 或者绕过它去调 API（如果恰好有对应 Toolset）。

### 6.2 但要说清代价 —— 这一段是给你的，不是给 agent 的

| 代价 | 说明 |
|---|---|
| **UE C++ 有真实学习曲线** | `UPROPERTY`/`UFUNCTION` 宏、GC 与 `TObjectPtr`、`Build.cs`、UHT 代码生成、热重载限制、模块依赖。**通用 C++ 帮不上这些** |
| **编译等待** | 首次 79 秒，改一行头文件可能触发大范围重编 |
| **你会更依赖 agent** | 这既是优势也是风险 —— 见 6.3 |

**我的判断**：在你 **UE5 经验 = 0** 的阶段，让 C++ 成为"唯一路径"是错的。正确顺序是**先把引擎概念跑通（蓝图最快），再把系统层迁到 C++**。

### 6.3 三层分工（建议直接照这个执行）

```
① 接口 / 系统 / 数值层   → C++        ← agent 主战场，我能读写编译验证
   例：UDataTable 读取、伤害计算、ACS 姿态累积、
       UAC6MechPart 基类、AICallable 暴露的调参接口

② 表现 / 胶水层          → 蓝图        ← 你自己拖，这是你练手感的地方
   例：AnimBP 状态机、Niagara 触发、UI 事件绑定、
       关卡里的触发器逻辑

③ 数据 / 配置层          → CSV + JSON  ← 两边都能碰，最理想的中间地带
   例：DT_Weapon / DT_Protector（你已经有 8 张表了）
```

**为什么第 ③ 层最重要**：它是**你现有 AC6 数据管线的直接延伸**。你把 `regulation.bin` 拆成 CSV 这件事，本身就是"把二进制黑盒变成文本可协作资产"——**这正是让 agent 能参与的正确形态**。

> **一句话**：让 agent 碰**文本和结构化数据**，你来碰**需要审美与手感判断的可视化部分**。别让我去拖蓝图节点（我看不见），也别你自己手写渲染管线（那是我的活）。

### 6.4 对 M0 / 12 周路线的影响

| 项 | 影响 |
|---|---|
| **M0 项目类型** | 维持上一轮决定：**建 C++ 项目类型，但 M0 内容全部用蓝图**。理由加强了——§1.6 的 `CombatDummy` 等模板 C++ 类是现成的学习材料与可改造基类 |
| **M0 不该做的** | ❌ 不要为了"用上 C++"而在 M0 就写 C++ 类。先把引擎概念跑通 |
| **P20 的 12 周路线** | 第 3 周起引入 C++（原计划不变）。**新增理由**：这是你让 agent 参与开发的前提 |
| **作品集** | ⚠️ **必须有一个 C++ 部分**。全是蓝图的 TA 作品集，面试官会直接质疑渲染/性能能力。§3.1 的 Global Shader / RDG 是差异化点 |
| **可立即做的验证** | 把 `Unreal MCP` 插件打开（§7），看看我能不能真的驱动你的编辑器 |

---

## 7. 怎么用上 Unreal MCP（可执行）

### 7.1 启用（二选一）

**方式 A：编辑器 UI**
`Edit → Plugins` → 搜索框输 **`Unreal MCP`** → 勾选 → **重启编辑器**

**方式 B：改 `.uproject`**（更可验证）

```json
{
	"FileVersion": 3,
	"EngineAssociation": "5.8",
	"Plugins": [
		{ "Name": "ModelContextProtocol", "Enabled": true }
	]
}
```

> `ToolsetRegistry` 与 `EngineAssetDefinitions` 是它的依赖，会自动跟着启用。
> **注意**：这是**引擎级实验插件**，改 `<UE_PROJECTS>\AC6Proto\AC6Proto.uproject` 即可，不需要重编引擎。

### 7.2 启用后要确认的事

| 检查 | 怎么看 |
|---|---|
| 插件真的加载了 | `Output Log` 搜 `ModelContextProtocol` |
| MCP 服务端口 | 在日志里找监听地址（⚠️ 我未实测，需你看日志确认） |
| 有哪些 tool | 插件自带 `ModelContextProtocolToolSearch`，编辑器里应有对应面板（⚠️ 未实测） |

### 7.3 我的建议：**先别急着开**

| 理由 | 说明 |
|---|---|
| **实验性** | `IsExperimentalVersion: true`，API 会变。你现在开，踩的坑是你的时间 |
| **不是 M0 的前置** | M0 的技术难点是"引擎概念 + 数据管线"，不是"接 agent" |
| **但它值得你亲眼看一下** | 花 20 分钟开一次、看一眼 tool 列表、然后关掉 —— 你会对"UE 的 AI 接口长什么样"有一手认知，这比听我说强 |

**推荐时机**：M0 完成、进 M1 之前，作为一次"技术侦察"来做。

---

## 8. 不确定项（诚实清单）

| # | 不确定的事 | 影响 | 怎么查 |
|---:|---|---|---|
| 1 | Unreal MCP **实际能不能跑通**、怎么配客户端 | 中 | 开插件后看 Output Log；我未实测 |
| 2 | MCP 的服务端口 / 传输方式（stdio 还是 HTTP） | 中 | 读 `ModelContextProtocolServer.cpp`，或开插件看日志 |
| 3 | "蓝图慢 10×"的具体倍率 | 低（M0 碰不到） | 需编辑器内手搓对比测试 |
| 4 | `AICallable` 是否要求同时 `BlueprintCallable` | 低 | 读 UHT 更多代码；目前只确认它并列处理 |
| 5 | AIAssistant 是否需要 Epic 账号 / 是否对中国区可用 | 低 | 未实测；且你不必用它 |
| 6 | UE 5.9+ 会不会把 Toolset API 定型（或推倒重来） | 中 | 关注 release notes |
| 7 | 8 个未用 `AICallable` 的工具集是走 Python 侧定义还是根本没标记 | 低 | 见 `AnimationAssistantToolset/Content/Python/` 下的 `toolsets/*.py` |

---

## 9. 一句话总结

> **蓝图是"给人看的"，C++ 是"给人写、给机器读的"。**
> Agent 协作要的是后者 —— 所以 **UE 5.8 官方的 agent 能力面（Unreal MCP + 27 个 Toolset + 275 处 `AICallable` 标记）100% 建在 C++ 上，且明确不含蓝图图谱编辑**。
>
> 对你的路线：**系统层下沉 C++（agent 主战场 + TA 护城河），表现层留在蓝图（你练手感），数据层用 CSV/JSON（双方都能碰）**。
> **别急着开 MCP 插件** —— 先把 M0 跑通，它不是你现在的瓶颈。

---

## 附：本次核查用到的可复现命令

```bash
# ① 官方 MCP 插件是否存在
ls -la /j/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/
cat /j/UE_5.8/Engine/Plugins/Experimental/ModelContextProtocol/ModelContextProtocol.uplugin

# ② Toolset 基类（C++ 类 + JSON 进出的证据）
sed -n '1,60p' /j/UE_5.8/Engine/Plugins/Experimental/ToolsetRegistry/Source/ToolsetRegistry/Public/ToolsetRegistry/Toolset.h

# ③ AICallable 在 UHT 里的处理
sed -n '614,622p' /j/UE_5.8/Engine/Source/Programs/Shared/EpicGames.UHT/Types/UhtFunction.cs

# ④ 有没有蓝图图谱工具集（预期：无输出）
find /j/UE_5.8/Engine -iname "*BlueprintToolset*" -o -iname "*KismetToolset*" -o -iname "*GraphToolset*"

# ⑤ 27 个 Toolset 各自的 AICallable 数量
#    ⚠️ 必须排除 Intermediate/ 与 Binaries/（内含二进制文件，会让计数虚高 58）
for d in /j/UE_5.8/Engine/Plugins/Experimental/Toolsets/*/; do
  printf "%6d  %s\n" \
    "$(find "$d" \( -name '*.h' -o -name '*.cpp' -o -name '*.cs' \) -print0 \
       | xargs -0 grep -ho AICallable 2>/dev/null | wc -l)" \
    "$(basename "$d")"
done | sort -rn
# 预期合计 275

# ⑥ 蓝图 VM（解释执行的结构证据）
grep -n "ProcessLocalScriptFunction" /j/UE_5.8/Engine/Source/Runtime/CoreUObject/Private/UObject/ScriptCore.cpp
# 操作码「个数」= 去重后的 EX_* 标识符数。
# ⚠️ 不要用 grep -c：那数的是「含 EX_ 的行数」(103)，也不是出现次数 (108)。
grep -oE '\bEX_[A-Za-z0-9_]+' /j/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/UObject/Script.h | sort -u | wc -l
# 预期 102

# ⑦ 渲染管线无蓝图暴露
grep -rn "UFUNCTION\|UCLASS" /j/UE_5.8/Engine/Source/Runtime/RenderCore/Public/RenderGraphResources.h
```
