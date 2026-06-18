# H Link 平台锚点期望（5.21 产品会议产出）

> 来源：HH Research × 高瓴 H Link 团队对接需求清单
> 日期：2026-05-21
> 上下文：HRes' aha moment 推送链路 C（H Link 1-on-1）已 code-ready，本文档列出我们对 H Link 平台**功能侧**的期望，供 Max / Leon 团队参考产品演进。

## 用户 draft（必备）

### 1. Bot 消息可 mute

**需求：** 用户可对 HRes' aha moment bot 设置免打扰（mute），不再收到 push notification，但仍能在 H Link bot 会话历史里翻阅日报。

**场景：** 周末或会议中不希望被打扰，但不想错过历史日报。

### 2. H Link 上的已读 / 未读检测 API

**需求：** H Link 平台暴露已读 / 未读状态 API，让 HRes 服务端能：
- 知道某条日报某个用户是否已读
- 拿到首次打开时间（用于"停留时间"间接推断）
- （进阶）拿到点击到具体链接 / section 的事件

**场景：** 接 TODO-09 阅读监控埋点系统，对比 3 通道（群报 / 飞书 bot / H Link）的触达效果。

## HH Research 建议补充

### 3. 消息分类标签

**需求：** Bot 发送的消息可带分类标签（日报 / Alert / 系统通知），用户在 H Link 设置中可分类配置免打扰策略（例：日报关 push，Alert 保持 push）。

**场景：** Alert（实时重大事件推送，TODO-05）与日常日报应有不同的打扰优先级。

### 4. 卡片富文本渲染

**需求：** H Link 卡片支持除 `<a>` `<br>` 之外更多富文本元素：
- `<b>` `<i>` 等强调
- 链接预览卡（即"hover 出释义"的基础，TODO-08）
- 图片内联

**当前限制：** H Link textcard ≤ 1000 字符 + 仅 `<a>` `<br>`（来源：H Link [basic-concepts.html](https://docs-ushu.hillinsight.tech/dev/serverapi/basic-concepts.html)）。TL;DR 5 条剥锚点后已用 529 / 1000 字符，buffer 471 字符。富文本会增加字符占用，需配合提高字符上限（建议 ≥ 2000）。

### 5. Push 优先级

**需求：** API 调用时可传 `priority` 字段（high / normal / low），高优消息触发更显著的 push（声音 / 横幅）。

**场景：** Alert 走 high，常规日报走 normal。

### 6. 用户订阅偏好 API

**需求：** H Link 提供用户级订阅偏好 API：
- 用户可选关注的赛道（认知模型 / 多模态智能 / 世界模型 / AI infra / ai4s）
- 用户可选关注的实体（OpenAI / Anthropic / Meta 等）
- HRes 服务端调用偏好 API 决定该用户接收什么内容

**场景：** TODO-12 个性化推送实现。

### 7. API rate limit 与重试机制

**需求：**
- 公开 rate limit 阈值（QPS / 日 quota）
- 失败响应明确区分"可重试"（5xx / 限流）vs "不可重试"（4xx 鉴权失败）
- 提供 token 刷新接口的频率限制说明（当前 `/cgi/token/get` 频限不明，已在 publisher 内存缓存 7200s 兜底）

### 8. 离线消息持久化

**需求：** 用户在 H Link 上不在线（未启动客户端）时，消息可暂存至服务端，用户上线后正常拉取，不会丢失。

**场景：** 早 12:00 推送日报时部分用户可能尚未启动 H Link 客户端，需保证不丢消息。

## 优先级建议

| 序号 | 期望 | 紧迫度 | 阻塞性 |
|---|---|---|---|
| 1 | Bot 消息 mute | 中 | 不阻塞，用户体验问题 |
| 2 | 已读 / 未读 API | 高 | 阻塞 TODO-09 阅读监控 |
| 3 | 消息分类标签 | 中 | 阻塞 Alert 上线后免打扰策略 |
| 4 | 富文本渲染 | 高 | 阻塞日报呈现质量 |
| 5 | Push 优先级 | 中 | 阻塞 Alert 与日报区分体验 |
| 6 | 用户订阅偏好 API | 低 | 个性化是远期 |
| 7 | Rate limit 文档 | 中 | 阻塞批量推送容量规划 |
| 8 | 离线消息 | 高 | 阻塞推送可靠性 |

## 后续行动

1. **HH Research 侧**：把这份文档转飞书 docx 共享给 Max / Leon 团队
2. **H Link 侧**：评估这 8 项的可行性 + 排期反馈
3. **联调节点**：等 IT 给 HH 开通 H Link 开发者权限 + 提供管理后台 URL

## 关联

- 推送链路状态：`/Users/haolinguo/.claude/projects/-Users-haolinguo-claude-code-HH-research/memory/push_channels_hres_aha_moment.md`
- 产品路线图：`../roadmap/2026-05-21-product-roadmap.md`
