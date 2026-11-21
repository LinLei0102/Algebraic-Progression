# Algebraic Progression（简体中文汉化版）

原作：[Algebraic Progression](https://github.com/LinLei0102/Algebraic-Progression) by randomtuba。
本仓库基于上游默认分支 `glitch` 的提交 `5502337ad6197388ba7617d78f61083846c62e1d`（v3.0.3 Fix 3）制作简体中文汉化，保留原作者及贡献者署名与全部玩法内容。

## 原版信息

- 类型：数学主题增量游戏（浏览器运行，Vue 2 + 原生 JS）。
- 上游分支：`glitch`；原作者：randomtuba。
- 贡献者：TheMKeyHolder、Yahtzee Master、gapples2、downvoid、DEMEMZEA、yhvr。
- 测试者与灵感来源见游戏内 `Options` → 制作人员信息。
- 原版使用 jsdelivr 加载 Vue 与 jQuery；本仓库改为本地 `vendor/` 以便离线稳定运行，逻辑未改。

## 运行

直接用静态服务器打开仓库根目录即可，例如：

```bash
python -m http.server 8765
# 浏览器访问 http://127.0.0.1:8765/index.html
```

存档使用浏览器 `localStorage`：`APSaveSlot1/2/3`，当前槽记录在 `APSaveMetaData`。语言偏好独立记录在 `APLang`，不影响存档兼容。

## 简体中文汉化

### 路线与实现

- **路线 B + O 混合**：构建期从 HTML/JS 提取展示文本到词典；运行时在 DOM 写入边界按原英文整串查表翻译，避免逐字改写 27k 行源码，ID/存档字段/数学符号零改动。
- 词典：`i18n/dict.js`（整串 4781、模板 187、短语 4528 条，含教科书长段、嵌套条件块、DOM 拆分片段、Vue 插值字面量、运行时文本写入钩子与新闻整串的补充译文）。
- 引擎：`i18n/engine.js`，仅当 `APLang === 'zh'` 时激活；英文模式完全透传原版。
- 入口：`index.html` / `changelog.html` 均加载词典与引擎。

### 中英切换

- 游戏内 **Options（选项）** 面板顶部的「语言 / Language」按钮，切换后刷新页面生效，默认中文。
- `changelog.html` 无设置面板，使用右上角浮动按钮（降级理由见 `docs/汉化方案.md`）。
- 英文模式不注入任何译文，可与原版逐字对照。

### 残局存档

- `save/endgame-v3.0.3.json`：自动生成的功能验证存档，数值拉满、全系统解锁，用于检查后期界面翻译。
- `save/import.html`：免安装导入页，离线双击可用；**只写入第 3 存档位**，不会覆盖第 1、2 位。
- 使用步骤：先在游戏 Options → Export 备份原档；打开 `save/import.html` 点击导入；再打开 `index.html`，自动读取第 3 位并默认中文。要恢复原档，用 Options → Import 粘贴之前导出的文本。

### 跟版

1. `git fetch origin glitch`，记录新 commit。
2. `python tools/extract_texts.py` 重新提取，对比 key 集合。
3. 新增条目补译到 `tools/translations/part_*.json`，再运行 `python tools/build_i18n.py`。
4. 重跑 `node tools/verify.mjs zh`（需先在项目外安装 `playwright-core` 并启动本地服务器）。

### 文档

- `docs/汉化方案.md`：路线判定、文本载体、术语与不译清单。
- `docs/glossary.md`：术语表（唯一权威）。
- `docs/汉化验收报告.md`：验收数据与残留白名单。
- `docs/译法冲突.md`：合并校验报告。

### 已知限制

- 极端大数格式周围的动态拼接文本可能保留英文语序，不影响玩法。
- 未执行完整「干净重放」流水线；可复现性由提取 → 译文 → 构建三步保证。
- 本汉化版不包含额外授权文件；原作版权归 randomtuba 及原贡献者所有。
