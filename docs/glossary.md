# 术语表（Algebraic Progression 简体中文汉化）

> 版本：v1.0 / 更新日期：2026-11-21
> 本表是唯一权威。所有分片翻译、审校、短语表生成都以此为准；新增词先改本表再改译文。

## 1. 绝对保留原文

| 词 | 类型 | 原因 |
|---|---|---|
| `x` / `y` / `z` / `a` / `b` / `c` / `d` / `e` / `f` | 数学变量 | 游戏玩法本体，改了看不懂公式 |
| `f(n)` / `g(n)` / `h(n)` / `dx` / `x²` / `x^y` | 数学表达式 | 代码与显示同源 |
| `RE` / `CE` / `IP` / `QP` / `PP` / `UP` / `ME` / `PE` / `GP` / `CC` | 资源缩写 | 玩家习惯，且常作为字段名 |
| `IC` / `YC` / `QC` / `CU` / `QU` / `LI` / `AP` | 层级/升级缩写 | ID 与显示同源 |
| `log10` / `ceil` / `floor` / `max` / `min` | 数学函数 | 代码语义 |
| `K` / `M` / `B` / `T` / `Qa` / `Qi` | 大数后缀 | 玩家习惯 |
| `randomtuba` / `TheMKeyHolder` / `downvoid` / `gapples2` / `DEMEMZEA` / `yhvr` | 人名 | 原作者与贡献者署名 |
| `Vue.js` / `jQuery` / `break_eternity.js` / `notify.js` / `panzoom.js` / `Discord` / `Twitter` / `TI-84` / `Galaxy` | 品牌/库名 | 专有名词 |
| `APSaveSlot` / `APSaveMetaData` / `APLang` / `player.*` / `tmp.*` | 存档键与代码字段 | 改了存档损坏 |
| URL、文件名、CSS 类名、HTML 标签、`\n`、`{{0}}`、`%s`、`[red]` / `[rainbow]` 标记 | 结构与格式 | 原样保留 |

## 2. 必译统一表

| 原文 | 译文 | 备注 |
|---|---|---|
| Point / Points | 点数 | 全篇统一，不用「积分」 |
| Slope | 斜率 | |
| Building / Buildings | 建筑 | |
| Autoclicker / Autoclickers | 自动点击器 | |
| Upgrade / Upgrades | 升级 | |
| Buyable / Buyables | 可购买项 | |
| Challenge / Challenges | 挑战 | |
| Prestige | 威望 | 不用「转生」 |
| Reset | 重置 | |
| Achievement / Achievements | 成就 | |
| Milestone / Milestones | 里程碑 | |
| Textbook | 教科书 | |
| News Ticker | 新闻滚动条 | |
| Generation / Statistics / Options / Achievements | 生成 / 统计 / 选项 / 成就 | 主标签栏 |
| Option | 选项 | 全角冒号：`选项：` |
| Cost | 消耗 | `消耗：12 点数` |
| Effect | 效果 | |
| Boost / Boosts | 加成 | |
| Multiplier / mult | 倍率 | |
| Gain / Production | 获得 / 产出 | |
| Efficiency | 效率 | |
| Unlock | 解锁 | |
| Softcap / Hardcap | 软上限 / 硬上限 | |
| Sacrifice | 献祭 | |
| Quadratic / Complex / Integration / Sinusoidal / Polynomial / Derivative | 二次 / 复数 / 积分 / 正弦 / 多项式 / 导数 | 层级名 |
| Transformation / Alteration / Flune / Liminal | 变换 / 改动 / 弗鲁恩 / 阈限 | 特殊层级名 |
| Y-Quadratic | Y-二次 | 层级名，保留连字符 |
| Lost Integration | 遗失积分 | 层级名，不用「迷失」 |
| Root Essence | 根精华 | |
| Root Epicenter | 根震中 | |
| Mandelbrot | 曼德博 | 分形层级名 |
| Generator | 生成器 | |
| Quantum | 量子 | 不用「量子力学」 |
| Power (资源名) | 能量 | 与数学「幂」区分；`x-power` 保留为 `x-power` |
| revolution / revolutions | 圈 / 圈数 | |
| triangle / triangles | 三角形 | |
| trigonometric waves | 三角波 | |
| Secret Achievement | 隐藏成就 | |
| Save / Load / Export / Import | 保存 / 读取 / 导出 / 导入 | |
| ON / OFF / Shown / Hidden | 开启 / 关闭 / 显示 / 隐藏 | 选项值 |
| Currently / Currently Selected | 当前 / 当前选中 | |
| Level / Levels | 等级 | |
| Amount | 数量 | |
| Reward | 奖励 | |
| Requirement | 要求 | |
| Goal | 目标 | |
| Speed | 速度 | |
| Time / Timer | 时间 / 计时器 | |
| Next / Previous | 下一项 / 上一项 | |
| Close / Cancel / Confirm | 关闭 / 取消 / 确认 | 按钮 |
| Click / Buy / Sell | 点击 / 购买 / 出售 | |

## 3. 标点与排版

- 译文统一用全角冒号 `：`，避免命中 `/^xxx: yyy$/` 兜底模板二次翻译。
- 术语并列用 `、` 不用 `-`，避免被 id 掩码误伤。
- 保留原文的占位符（`{{0}}`、`%s`、`{0}`）、HTML 标签、`\n`、新闻 `[red]` / `[rainbow]` 标记。
- 数字与单位之间加一个半角空格：`消耗：12 点数`；中文句子里的英文变量前后保留半角空格。
- 保留原文前导/尾随空格（Vue 会把它作为独立文本节点渲染）。
- 数学表达式 `x^2`、`f(n)` 等不做替换，即使出现在中文句子里也保留原样。
- 玩家昵称、用户生成内容一律不译。

## 4. 审校清单

- [x] 专名与本表一致
- [ ] 占位符 / 色码 / 标签与原文一致（翻译完成后统一脚本校验）
- [ ] 无半角冒号导致的模板二次翻译
- [ ] 无单字/虚词词条（缩写白名单除外）
- [ ] 新词已回写本表并登记版本
