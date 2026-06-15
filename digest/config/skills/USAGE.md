# HH Research Insight Pack 使用说明

这个包包含两部分：

1. `skills/hh-research-insight-writer/SKILL.md`
   - 用来生成新的 HH Research Daily insight。
   - 适合输入论文内容、论文摘要、技术新闻、产业信号，然后直接生成「标题 / 正文 / 投研视角」。

2. `agents/hh-research-insight-reviewer.md`
   - 用来审阅和改写已有 insight。
   - 适合把 Claude / Codex / 人工写出的初稿丢进去，让它按 golden style 做 review 和重写。

## 在 Codex 中使用 Skill

把整个 `hh-research-insight-writer` 文件夹复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R skills/hh-research-insight-writer ~/.codex/skills/
```

之后在对话里可以这样调用：

```text
请使用 hh-research-insight-writer，把下面这篇论文内容改写成 HH Research Daily insight：
[粘贴论文摘要/正文/事件材料]
```

## 使用 Review Agent

打开 `agents/hh-research-insight-reviewer.md`，把全文复制到你使用的 Agent / Project Instruction / 自定义助手说明里。

之后可以这样调用：

```text
请按 HH Research Daily golden style review 并改写下面这条 insight：
[粘贴初稿]
```

## 推荐工作流

1. 先用 `hh-research-insight-writer` 生成初稿。
2. 再用 `hh-research-insight-reviewer` 做一次审阅和压缩。
3. 最终人工检查三件事：
   - 技术是否只保留一条主线；
   - 证据边界是否聚焦商业化验证；
   - 投研视角是否带条件，而不是直接给结论。
