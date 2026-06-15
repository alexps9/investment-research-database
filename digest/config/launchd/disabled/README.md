# disabled launchd jobs

本目录存放**按用户要求停用、不应自动安装**的 launchd plist。

## com.hh-research.broadcast-main.plist
- **停用时间**：2026-06-03（用户要求关闭 12:00 自动群广播）。
- **原行为**：BJT 12:00 触发 `scripts/broadcast_today_main.sh` 自动广播日报到群。
- **⚠️ 仅停用自动触发，不影响手动广播**：disabled 只表示**不再自动 12:00 触发**；**手动广播能力完整保留** —— 仍可随时
  `cd "/Users/haolinguo/claude code/HH research/daily-digest" && bash scripts/broadcast_today_main.sh` 做三路广播（企业群 / 飞书 1-1 bot / H Link）。
  脚本 `scripts/broadcast_today_main.sh` 与三路 sender（`send_digest_to_enterprise.py` / `send_digest_to_feishu_bot.py` / `send_digest_to_hlink.py`）**均保留、未删未改**。
- **已装 job 处理**：已 `launchctl bootout` 并把 `~/Library/LaunchAgents/com.hh-research.broadcast-main.plist`
  移至 `~/Library/LaunchAgents/hh-backup-2026-06-03/`（不在 LaunchAgents 中，登录/重启不会重载）。
- **install.sh 影响**：`config/launchd/install.sh` 用硬编码列表安装（不含 broadcast-main、非 glob），本就不会安装它；移到此处为双保险。
- **如需恢复**：手动 `cp config/launchd/disabled/com.hh-research.broadcast-main.plist ~/Library/LaunchAgents/`
  然后 `launchctl load ~/Library/LaunchAgents/com.hh-research.broadcast-main.plist`（并经用户显式许可，见广播安全规则）。
