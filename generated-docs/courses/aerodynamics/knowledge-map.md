> 同步日期：2026-10-17。经用户授权发布的学习记录快照；原始课程文件、sources.json 和本机数据库未上传。学习日期以正文为准。

# Aerodynamics · 基础知识地图

版本：初始映射。下列优先级是学习建议，不是预测考试分数。P1 表示已见考试提示或具体 Tutorial 支持；P2 表示已见 Lecture 的先修/主干内容；没有证据的覆盖范围保留未知。概念关联是组织建议，与课程原文陈述分开。

所有 L/T 页号为 PDF 页序。A = Anderson 课本，节号从已核对目录定位；X = 用户提供的手写考试提示图。文件版本见 sources.json。

| concept_id | English / 中文 | 先修与关联 | 已核对定位 | 学习优先级依据 |
|---|---|---|---|---|
| control-volume | Control volume / 控制体 | 向量积分 → 守恒方程 | L1 p1；A §2.3–2.5 | P2，基础 |
| stream-function | Stream function / 流函数 | 速度场、流线、质量守恒 | T1 p1；A §2.14 | P1，练习；X 相关手写加减号不清，不据此定公式 |
| vorticity | Vorticity / 涡量 | 旋度、局部旋转；关联环量 | L2 p1；A §2.12 | P2，基础 |
| circulation | Circulation / 环量 | 线积分、涡量；关联升力 | L2 p1、L7 p1；A §2.13、§4.6 | P2，主干 |
| velocity-potential | Velocity potential / 速度势 | 梯度、无旋条件；关联流函数 | L3 p1；A §2.15–2.16 | P2，势流基础 |
| elementary-flows | Source/sink superposition / 基本流叠加 | 速度势、流函数；关联圆柱流 | L4 p1、T2 p1；A §3.9–3.12 | P1，练习 |
| bernoulli | Bernoulli assumptions / 伯努利适用条件 | 动量方程、流线；关联压力系数 | A §3.2（目录）；X 条目 4 | P1，提示；要区分沿流线与跨流线，不把手写条件表当完整定理 |
| cylinder-flow | Cylinder flow / 圆柱绕流 | 叠加、环量、压力系数 | L5 p1；A §3.13–3.16；X 条目 3/5 | P1，提示；理想流与黏性真实流区分 |
| lift-curve | Lift curve / 升力曲线 | 迎角、系数、适用范围 | L6 p1；A §4.3；X 条目 8 | P1，提示；线性理论不能描述失速 |
| kelvin-starting-vortex | Kelvin theorem / 环量守恒与起动涡 | circulation → 升力建立 | L7 p1；A §4.6 | P2，主干 |
| camber-center | Camber and aerodynamic center / 弯度与气动中心 | lift-curve、力矩、薄翼假设 | L8 p1；A §4.7–4.9；X 条目 7/9 | P1，提示；压力中心与气动中心不能普遍等同 |
| wall-shear | Wall shear stress / 壁面剪应力 | 速度梯度、黏性、无滑移 | L9 p1；A §4.12 | P2，阻力基础 |
| boundary-layer-growth | Boundary-layer thickness / 边界层增长 | 局部 Reynolds number、距离依赖 | L9 p2；A §4.12.1–4.12.2 | P2，讲义公式；x 与 Re_x 不是独立变量 |
| skin-friction | Skin friction / 摩擦阻力 | wall-shear → 沿程积分 | L9 p3；A §4.12.1–4.12.3 | P2，讲义；区分局部/平均、单面/双面 |
| adverse-pressure-gradient | Adverse pressure gradient / 逆压梯度 | bernoulli、外缘减速、动量 | L9 p4–5；A §4.12.4；X 条目 6 | P1，提示 |
| separation | Flow separation / 流动分离 | wall-shear、adverse-pressure-gradient → pressure-drag | L9 p5；A §4.12.4 | P1，关联考试提示；定常二维判据有适用范围 |
| pressure-drag | Pressure drag / 压差阻力 | separation、表面压力合力 | L9 p3、p5–7；A §4.12.4、§3.18 | P2，课程主干；不能用“存在分离”替代受力积分 |
| stall | Airfoil stall / 翼型失速 | separation、lift-curve | L10 p1；A §4.13 | P1，X 条目 8 与讲义 |
| finite-wing | Finite wing / 有限翼 | 环量、尾涡、诱导角、有效迎角 | L11–12 p1；T3 p1；A §5.1–5.3 | P1，练习 |
| lifting-line | Lifting-line distribution / 升力线分布 | finite-wing、Fourier 系数、展弦比 | L13 p1；T4 p1；A §5.3.2–5.3.3 | P1，练习和 X 下半页 |
| compressibility | Compressibility / 可压缩性 | 热力学、等熵过程、密度 | L14 p1；A §7.2–7.3 | P2，讲义 |
| pg-correction | Prandtl–Glauert correction / 压缩性修正 | compressibility、翼型小扰动 | L15 p1 | P2，讲义；明确薄翼、小迎角等条件 |

## 本次学习主题的依赖链

黏性与无滑移 → 近壁速度梯度 → 壁面剪应力 → 摩擦阻力。
外缘速度变化 → 压力梯度 → 近壁动量变化 → 分离 → 压力分布变化 → 压差阻力与升力变化。
层流/湍流速度分布 → 摩擦阻力变化与抗分离能力 → 圆柱 Reynolds number 效应。

## 尚未核对

完整各 Lecture/Tutorial 页面的题目覆盖、正式考试题和分值、老师口头提示原始出处、L15 对应精确课本节号。当前仅提供有依据的优先级，不给章节百分比。
