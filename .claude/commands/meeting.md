处理会议纪要。

输入：$ARGUMENTS（会议原始内容，可以是粘贴的文字或文件路径）

执行步骤：
1. 以 qiutian 秘书视角提取摘要：只关注 qiutian 说的内容和对方的反馈建议
2. 每个要点引用会议原文（供交叉验证）
3. 整理为结构化摘要，放在原始记录前面
4. 存入 `.claude/docs/z-meetings context/YYYY-MM-DD-主题.md`
5. 让用户 review 后：
   - 方向性校准 → 更新 `goal.md`
   - 具体任务 → 更新 `STATUS.md` 的 Action Items
