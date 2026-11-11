# 项目介绍 / Project overview

## 中文

Panasonic Bridge CN 是面向中国大陆松下智家云端的 Home Assistant 社区整合。它起于搭建统一家庭环境的实际需求：希望让不同品牌的家电进入同一个 HA 平台，便于查看状态、操作设备，并为未来跨品牌联动打基础。

搭建时，美的等设备已有可用的内置或成熟社区接入路径，手头使用的中国大陆松下型号却在当时尝试的方案中遇到了适配缺口。类别支持不足、协议与已有控制器不同等问题，使这些设备无法直接加入原先设想的统一环境。因此开始复用已有社区成果，补充净化器、空调和 Fridge-19 冰箱的适配、离线测试与脱敏调试经验。这是特定地区与型号的实际经历，不代表所有松下产品都没有 HA 接入方式。

开源的目标是让已有工作可以被复用，帮助更多松下设备用户，也让更多人参与维护。设备用户可以提供状态对照和手动验收，开发者可以修复问题或适配新型号，其他贡献者可以完善文档、翻译与使用说明。我们希望把分散的排障经验变成可审阅、可复现的社区资料。

当前版本处于早期公开审阅阶段。代码实现、状态对照、App 确认和实体确认分别记录，未验证的功能明确标注。项目保留上游许可证及署名，支持按适用许可证 fork、修改和贡献，不把已有社区成果据为原创。

本次准备使用 Codex 协助源码比较、离线测试、隐私检查、文档整理和公开审阅流程。后续希望继续用于问题分诊、回归测试、协议边界检查及文档维护。设备真实效果仍依赖具备对应型号的贡献者验证，不能由 AI 或离线测试替代。

项目不依赖 OpenAI API 运行设备整合，也不宣称已获得 OpenAI 支持、资助、认可或任何申请资格。社区规模、使用量和维护数据应以实际公开记录为准。

## English

Panasonic Bridge CN is a community Home Assistant integration for Panasonic's mainland China smart-home cloud. It grew out of building a unified home environment: bringing different appliance brands into one HA platform for status monitoring, control, and a foundation for future cross-brand automation.

During setup, brands such as Midea had usable built-in or established community integration paths, while the mainland China Panasonic models being used encountered gaps in the approaches tried at the time. Missing appliance-category adapters and protocols that differed from existing controllers prevented those devices from fitting directly into the intended setup. Work began on extending existing community knowledge with purifier, AC, and Fridge-19 refrigerator adapters, offline tests, and sanitized debugging notes. This is a model- and region-specific experience, not a claim that all Panasonic products lack HA integration.

The goal of opening the project is to make existing work reusable, help more Panasonic appliance owners, and invite more people to maintain it. Device owners can contribute state observations and manual verification; developers can fix bugs or add model support; other contributors can improve documentation, translation, and setup guidance. We want to turn isolated troubleshooting experience into reviewable, reproducible community knowledge.

The project is in an early public-review stage. Implementation, state observations, app confirmation, and physical confirmation are recorded separately. Unverified behavior is explicitly labeled. Upstream licenses and attribution are retained, and forks, modifications, and contributions are welcome under the applicable licenses.

Codex assisted this preparation with source comparison, offline tests, privacy checks, documentation, and the public review workflow. Planned maintainer uses include issue triage, regression tests, protocol-boundary checks, and documentation maintenance. Actual appliance behavior still requires verification by contributors with the relevant hardware; AI and offline tests cannot replace it.

The integration does not require the OpenAI API to operate appliances. It does not claim OpenAI sponsorship, endorsement, funding, or application eligibility. Adoption, usage, and maintenance metrics must be supported by actual public records.
