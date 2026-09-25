# 执行须知（本文件是被派发的独立任务）

- 你是一个**独立 session**，只负责下面这一个维度。你不需要写代码，只需要产出高质量的拆解报告。
- 请先读同目录的 _shared.md，严格遵守其中的身份设定、证据分级与硬性纪律。
- 报告写成一份完整的中文 Markdown，**建议 3500~6000 字**（宁深勿泛；表格不计入字数）。
- 必须包含：结论先行要点 → 分节展开（表格优先）→ 分析三问 → TA 转化要求 → 验证路径（去查哪张数据表）。
- **必须包含「实测证据」小节**：凡声称"实测/查表得知"的，把实际执行的命令与原始输出片段贴进去；没真跑过就删掉"实测"字样、改成推断或待验证。
- 用 write 工具把报告写入：<repo>/docs/03_维度拆解/P6_动作动画与运动系统_报告.md
- 完成后只回复 6 行以内摘要：实际字数、覆盖的主要小节、你标为 D 级（不确定）的结论条数、最值得用本地数据验证的 1 条。

---

下面是本维度的具体任务：

你是动画技术总监（Animation TA）。请拆解《装甲核心6：境界天火》（AC6）的**动作、动画与运动系统**。
我是大四学生，目标技术美术（TA），这一节是我最需要吃透的部分。请把"机甲动起来"这件事拆到可实现的粒度。

【必须回答】
1. 动作集清单：移动（走/冲刺/悬浮/爬升/下降/跳跃）、Boost 系统（普通加速、Quick Boost 瞬时位移、Assault Boost 长距离突进）、近战突进、踢击、开火、换弹、被击、姿态崩溃、倒地/起身。给一张**动作优先级与互斥表**：哪些动作可以同时进行、哪些会打断、哪些有取消窗口。
2. 上下半身分离：腿部运动（移动动画）与上半身瞄准（武器朝向跟随锁定目标）如何协同？躯干扭转是否有角度上限？瞄准方向与移动方向不一致时怎么处理？
3. 位移系统：走的是"根运动（root motion）"还是"参数驱动速度 + 动画跟随"？空中悬浮的物理模型是什么（重力、升力、能量消耗的平衡）？请说明你的判断依据。
4. 地形适应：脚部 IK 如何处理不平地面与坡度？机甲这种"刚性大质量物体"的脚部接触是怎么做的？
5. 转身与惯性：机体朝向的角速度是多少量级？是否受载重影响？"重装机转不过来"是刻意设计还是物理结果？
6. 重量感是怎么来的？请拆成可实现的通道：预备动作（anticipation）、加速度曲线、伺服/液压延迟、二次运动（机械晃动/惯性摆动）、落地冲击、音效。特别说明"机甲零件之间的相对运动"是如何模拟的——这是区别于人类角色的关键。
7. 受击表现分级：轻击、重击、姿态崩溃（Stagger）分别是怎样的动作状态？击退位移如何与动画配合？是否有无敌帧？
8. 判定帧与动画的耦合：武器的"开火帧""近战判定帧""命中窗口"是怎么对齐到动画上的？谁说了算（动画通知/数据表/状态机）？
9. 分析三问：如果没有 Quick Boost 会怎样？如果把动画速度整体放慢 50% 会怎样（重量感会变强还是变糊）？如果所有动画都用根运动会怎样？
10. 验证路径：FootIKParam、FootIKSetupParam、HandIKParam、LookAtParam/LookAtHeadParam/LookAtSpineParam、ReTargetAnimSetParam（动画重定向！）、AnimMoveCorrectionParam、JigglerBaseParam/JigglerBehaviorParam/JigglerBehaviorSlideParam/JigglerBehaviorTargetBoneRateParam/JigglerBehaviorWorldFixParam（机械二次运动）、ChrProxyPhysicsParam、RigidBodyParam、RagdollParam、MovementAcTypeParam、ThrustersLocomotionParam_PC、BoostParam。请说明这几张表分别对应上面哪一条结论。

【TA 转化要求】
给一份"复刻清单（UE5）"：实现"机甲 QB 瞬移 + 机械晃动 + 脚部 IK"需要什么（Animation Blueprint 状态机与 Blend Space、Layered Blend 上下半身、IK Rig/Retargeter、Physics Asset 与约束、二次运动模块如 Jiggle/AnimDynamics、Motion Warping、动画通知与判定对齐）。请标明每项的难度和大致工作量（人日量级即可）。

【输出规范】
结论先行；表格优先；四段式；证据等级 A/B/C/D；禁止无机制支撑的形容词（"很有重量感"不算结论）；不确定就说不确定 + 验证方法。
