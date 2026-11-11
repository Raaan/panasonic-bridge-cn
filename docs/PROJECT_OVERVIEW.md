# 项目介绍 / Project overview

## 中文

我在搭建家里的 Home Assistant 时，希望把不同品牌的家电统一管理。美的等设备已有可用方案，而我使用的中国大陆松下型号还缺少直接适配，因此开始在已有社区工作的基础上补齐这部分功能。

目前 F-75C5PJD 净化器、CS-JM35K410Q 空调和 NR-E411BG-NH 冰箱的现有功能均已实际核对，并在家中稳定运行。我也使用独立的微信 AI 工具作为 HA 控制入口；这部分单独维护，不是松下整合的必需组件。

开源是希望其他用户能够复用已有成果，也希望有更多人参与修复、测试新型号和整理文档。项目的具体补充及与其他松下项目的关系见 [比较说明](COMPARISON.md)。原有许可与署名继续保留。

开发和整理过程中，Codex 帮助我检查代码、补充测试及完善中英文档。实际设备结果仍来自对应型号的使用和测试。仓库公开时间较短，后续希望通过更多用户的反馈逐步扩大支持范围。

## English

I started this while bringing different appliance brands into my home Home Assistant setup. Existing integrations worked for brands such as Midea, but did not directly cover the mainland China Panasonic models I owned. I built on existing community work to fill that gap.

The implemented controls for my F-75C5PJD purifier, CS-JM35K410Q AC and NR-E411BG-NH refrigerator have been checked on the devices and are running reliably at home. I also use a separate AI WeChat tool to control HA. That tool is maintained independently and is not required by this integration.

Sharing the project should help other owners reuse the work and contribute fixes, tests on more models, or documentation. The [comparison](COMPARISON.md) explains the model-specific additions. Upstream licenses and attribution are retained.

Codex has helped me inspect the code, add tests and improve the documentation. Physical results come from using and testing the relevant devices. The public repository is new, and I hope more users' feedback will help extend its support.
