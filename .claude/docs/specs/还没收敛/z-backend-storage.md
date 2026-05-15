---
status: backlog
created: 2026-05-12
complexity: 🟡中等
---

# 后端数据存储重构：硬编码 → 外部数据源

## 背景

当前论文数据硬编码在 `backend/app/data/world_model_data.py`（~83 篇，Python 对象）。问题：
- 每次加论文要改代码
- 团队无法直接贡献数据
- 无法和团队 network 数据库打通 entity taxonomy

## 目标

论文数据可被非工程师编辑，最终链接到飞书多维表格。

## 分步方案

1. **Python 硬编码 → JSON/YAML 文件** — 数据和代码分离，Claude/人都能直接编辑
2. **JSON → 飞书多维表格 + 同步脚本** — 团队在飞书加论文，定期 sync
3. **实时对接（webhook / 定时拉取）** — 图谱自动刷新

## 待定问题

- 飞书表结构怎么设计？（字段 = EvolutionPaper 的属性？还是更扁平？）
- builds_on 关系在飞书里怎么表达？（多选关联字段？）
- entity taxonomy 统一后，机构字段怎么校验？
