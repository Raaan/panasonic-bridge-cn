# 接收与分享社区修改 / Sharing community changes

## 中文

欢迎其他人修改本项目，也欢迎把有用改动带回共同维护的仓库。通常流程：

1. Fork 仓库，在自己的分支修改，提交指向本仓库的 PR。PR 说明问题、受影响型号、协议来源和验证结果。允许维护者修改 PR 分支可方便共同修复。
2. 代码使用合成设备和账号数据测试。真实设备观察、App 结果和实体效果分别记录。未完成实机验证的部分明确标注。
3. 合入前检查来源、许可、敏感信息、协议边界、回归测试及现有实体兼容性。外部贡献不会自动合并，也不自动触发生产设备控制。
4. 合入时保留真实作者的 Git 归属及已有源码署名；在 Changelog 或适配说明中记录贡献。不把他人改动改署为维护者原创，不编造作者身份。
5. 其他用户可按适用许可证获取、使用和继续修改合入后的代码。正式发行仍需独立版本、发布说明及验证，不把某个贡献者的一次成功反馈当作所有设备通过。

若修改先存在于其他 fork、帖子或补丁中，先请作者通过 PR 提交，或确认其明确许可、来源及署名后再引入。没有明确可复用许可的代码不直接复制。涉及私人调试记录，先移除账号、会话、标识、网络、家庭配置及个人时间线。

共性问题适合回馈相应上游时，可先整理成独立、可验证的改动并讨论归属。本仓库不会自动向其他项目或个人发送 PR、Issue 或消息。

项目许可和贡献规则见 [CONTRIBUTING.md](../CONTRIBUTING.md) 与 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。HA 本体不属于本仓库的分发内容。

## English

Forks and modifications are welcome, and useful changes can return through pull requests:

1. Work in a fork branch and open a PR describing the problem, affected models, protocol sources, and validation. Allowing maintainer edits can make collaboration easier.
2. Use synthetic fixtures. Record observed state, app confirmation, and physical results separately; label unverified behavior.
3. Review provenance, applicable licenses, privacy, protocol boundaries, regressions, and entity compatibility before merging. Contributions are not merged automatically and do not operate production appliances.
4. Preserve actual Git authorship and existing notices, and acknowledge contributions in the changelog or model documentation. Do not relabel another person's work as the maintainer's original work or invent contributor identities.
5. Others may use and modify merged code under the applicable licenses. A formal release still needs its own version, notes, and validation.

For changes found in another fork, post, or patch, invite the author to submit a PR or establish explicit reuse permission, provenance, and attribution before importing code. Sanitize private debugging records first. Reusable upstream fixes can be prepared and discussed separately; this project does not automatically contact other projects or people. HA Core itself is not distributed here.
