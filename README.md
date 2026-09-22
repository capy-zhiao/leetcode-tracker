# 🧠 LeetCode Tracker — 基于记忆曲线的刷题追踪器

按**间隔重复(Spaced Repetition)**安排 NeetCode 250 的每日刷题与复习计划,
自动追踪个人错误模式,并支持带追问的模拟面试。

> 起因:手工维护的 markdown 计划表排不动了 —— 250 道题的复习时间点要靠脑子记,
> 到期一堆做不完也没有优先级。这个 app 把调度自动化了。

## ✨ 功能

| 功能 | 说明 |
| --- | --- |
| **SRS 智能调度** | 每道题按表现动态计算下次复习时间;到期超量时按优先级排序,其余自动顺延 |
| **每日队列** | 复习 + 新题 + 模板盲写,替代手工计划表 |
| **计时器 + 自动评分** | 停表后根据用时和难度推荐评分,不靠"感觉" |
| **错误模式统计** | 15 个错误标签,积累后生成**个人版提交前自查清单** |
| **代码存档 + diff** | 每次提交的代码都存档,二刷时对比上次写法 |
| **模拟面试** | 随机抽题 + 限时 + 隐藏笔记 + **面试官追问**(Claude 生成) |
| **AI Code Review** | 提交代码后由 Claude 审查,并自动推断犯了哪些错误标签 |

## 🏗 技术栈

```
React + TypeScript + Vite + Tailwind      前端 SPA
          ↓ REST
FastAPI + SQLAlchemy 2.0 + Pydantic v2    后端 API(自动生成 OpenAPI 文档)
          ↓
SQLite(开发) / PostgreSQL(生产)
          ↓
Anthropic Claude API                       追问生成 + code review(可选)
```

**设计要点:**

- **SRS 算法是纯函数**(`app/srs.py`)—— 不碰数据库、不读系统时钟(`today` 作参数传入),
  因此能被完整单元测试覆盖。17 个测试用例覆盖首次间隔、增长曲线、翻车重置、
  ease 边界、优先级排序。
- **存储层可替换** —— `DATABASE_URL` 一个环境变量在 SQLite / Postgres 间切换,代码零改动。
- **优雅降级** —— 未配置 `ANTHROPIC_API_KEY` 时,AI 功能返回兜底内容,应用其余部分照常工作。

## 🧮 SRS 算法

刷题的记忆曲线和背单词不同:Anki 一张卡 5 秒、一天能过 200 张;
刷题一道 20-45 分钟、一天顶多 6-8 道。所以做了三处改造:

**1. 评分基于实际表现,不靠自评**

| 评分 | 触发条件 | 效果 |
| --- | --- | --- |
| `again` 不会 | 看了答案 | 间隔重置为 1 天,`ease -= 0.2`,`lapses++` |
| `hard` 吃力 | 卡壳 >15min 或有 bug | `interval × 1.2` |
| `good` 会了 | 顺利(5-15min) | `interval × ease` |
| `easy` 秒杀 | <5min 一遍过 | `interval × ease × 1.3`,`ease += 0.1` |

首次间隔 1/2/4/7 天;`ease ∈ [1.3, 3.0]`,初始 2.3;**Hard 题间隔 ×0.8**(难题忘得快)。
时间阈值随题目难度缩放 —— 20 分钟做完 Hard 题算顺利,做完 Easy 题就是卡了。

**2. 每日上限 + 优先级排序**(Anki 没有,但刷题一定会撞上)

```
优先级 = 逾期天数 × 1.0
       + 历史翻车次数 × 3.0       ← 错过的题优先
       + 难度权重(Hard 2 / Medium 1 / Easy 0)
       + (20 − 章节号) × 0.1      ← 先补地基
```

**3. 新题按 roadmap 推进**,与复习题混排。

## 🚀 本地运行

**一键启动**(推荐):

```bash
./start.sh
```

会自动检查依赖、按需初始化数据库、起前后端、打印今日任务、并打开浏览器。
按 `Ctrl+C` 停止两个服务。

<details>
<summary>或者手动分别启动</summary>

```bash
# 后端
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env                  # 按需填 ANTHROPIC_API_KEY
./.venv/bin/python seed_db.py         # 导入 250 道题
./.venv/bin/uvicorn app.main:app --reload
# API 文档: http://localhost:8000/docs

# 前端(另开一个终端)
cd frontend
npm install
npm run dev                           # http://localhost:5173
```

</details>

运行测试:`cd backend && ./.venv/bin/python -m pytest -q`

## 📥 数据来源

题库从个人的 NeetCode markdown 笔记仓库抽取:

```bash
python3 scripts/extract_seed.py       # markdown → data/seed.json
```

脚本会保留已写过的**思路笔记和代码**,并把已解题目标记为「立即到期」,
同时从历史记录中恢复每道题的翻车次数 —— 让第一天的复习队列就有正确的优先级。
markdown 笔记继续更新后可随时重跑同步。

## 🌐 部署

| 组件 | 平台 | 配置 |
| --- | --- | --- |
| 前端 | Vercel | 根目录 `frontend/`,已含 `vercel.json`(SPA 路由重写) |
| 后端 | Railway / Render | 根目录 `backend/`,已含 `Procfile` |
| 数据库 | Railway Postgres / Supabase | 设 `DATABASE_URL`,并 `pip install "psycopg[binary]"` |

公网部署时在后端设 `API_KEY`,前端设 `VITE_API_KEY`,中间件会校验 `X-API-Key` 头。

## 🗺 Roadmap

- [ ] JWT 用户系统(目前是单用户 + API Key 保护)
- [ ] 数据库迁移改用 Alembic(目前靠 `create_all`)
- [ ] 每日邮件提醒(Vercel Cron + Resend)
- [ ] 代码编辑器换成 Monaco(语法高亮 + 自动缩进)
- [ ] 按 pattern(滑窗/单调栈/并查集)而非章节的熟练度视图
