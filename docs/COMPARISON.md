# 与现有松下项目的区别 / Comparison with existing projects

核查日期：2026-11-11。比较以以下固定提交的 README 和本项目实际代码为准。范围会随项目更新改变；“未声明支持”不能扩大为“绝对无法适配”。

## 项目定位

Panasonic Bridge CN 补齐中国大陆特定松下型号的 HA 适配缺口，复用并保留既有社区的认证与协议成果。实际增量在 F-75C5PJD 净化器、CS-JM35K410Q 所属新协议空调及 Fridge-19 冰箱的控制、状态校准与验证资料。

没有重新实现 HA 平台，也没有把已有项目改名后宣称原创。品牌、HA 实体概念和部分认证算法存在重合；**本次核查未在下列项目的已声明支持范围中找到上述三套具体型号／协议组合的直接替代方案**。这是独立维护的依据，不是对所有 GitHub 仓库的穷尽证明，也不宣称“全球唯一”。

| 项目与来源 | 其已声明范围 | 与本项目的具体区别 |
| --- | --- | --- |
| [mcdona1d/panasonic_smart_china](https://github.com/mcdona1d/panasonic_smart_china/blob/2be1474cd9d2f868ce576fadcc6445f42e5a8545/README.md) | 中国区云平台；`0900` 线控风管机／中央空调，以 CZ-RD501DW2 验证；`0820` FV-RB20VL1 浴霸 | 其 profile 架构有复用价值，但未声明 F-75C5PJD、AirconCommon-2024-01 或 Fridge-19 适配；相同 `0900` 类别不等于相同空调控制协议 |
| [rudyll/panasonic_smart_china_r](https://github.com/rudyll/panasonic_smart_china_r/blob/1566af4ef00df19b8dad186ea8a995f211ccf4aa/README.md) | 中国大陆云平台；中央空调及多类新风 `0800/0850`；列出待开发 Aircle 净化器 `0830` | 本项目净化器实际为 `0810/75C5PJD`，不能套 `0830`；新协议空调和 Fridge-19 不等于其已有控制器。该项目鼓励其他品类独立发布，构成互补关系 |
| [osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app/blob/a200a21a7a1af92f07c51a2821b72736760c3d89/README.md) | Panasonic Smart App，多类家电；明确区分 Comfort Cloud 和 Smart App+；冰箱列有 NR-D611XGS 测试说明 | 品类名称相同不能证明适用于中国大陆智家账号及本项目协议。其 [状态码定义](https://github.com/osk2/panasonic_smart_app/blob/a200a21a7a1af92f07c51a2821b72736760c3d89/custom_components/panasonic_smart_app/const.py) 使用另一套设备类型及十六进制状态码；本次未核到其声明覆盖本项目三套型号／协议 |

上游 README 中未列明本项目型号，不妨碍它们未来支持更多设备。新增支持后应重新核查本表，优先协作与贡献，避免平行维护相同已解决的问题。许可证与复用归属见 [来源说明](../THIRD_PARTY_NOTICES.md)。

## 实际意义

1. **填补可复现的型号缺口**：同一中国云账号体系下，不同类别、子类型和控制器仍需专门字段与载荷适配。
2. **有现有硬件反馈**：维护者最新确认净化器基本完成核对、已有功能可控，空调现有控制也可用。此为维护者报告，不冒充独立实验室测试。
3. **保留成功和失败经验**：类别误判、请求封装、完整缓存、灯光语义、冰箱控制格式和 TLS 问题均有脱敏案例，便于贡献者复用。
4. **统一接入已有家庭平台**：保持 HA 原生实体与历史 domain，用户不需要再运行独立桥接服务器；其他品牌仍由其成熟整合负责。
5. **可由社区继续维护**：来源、许可、测试、验证边界和 PR 流程明确，其他型号的用户可贡献证据与适配。

## English

Panasonic Bridge CN targets concrete mainland China model/protocol gaps: the F-75C5PJD purifier, the AirconCommon-2024-01 AC family used by CS-JM35K410Q, and Fridge-19 refrigerators. It retains upstream attribution and reuses community authentication knowledge.

- **mcdona1d** declares Chinese-cloud ducted/central AC through the CZ-RD501DW2 controller and the FV-RB20VL1 bathroom heater. Its profile architecture is useful, but the checked revision does not declare the three combinations above. Sharing category `0900` does not establish AC protocol compatibility.
- **rudyll** focuses on central AC and ventilation. Its pending Aircle purifier entry is category `0830`; F-75C5PJD is `0810/75C5PJD`. It encourages separate projects for other appliance categories.
- **osk2** supports Panasonic Smart App and multiple appliance categories, with its own device-type/status-code scheme. Matching category names do not establish mainland China account or model compatibility. The checked revision does not declare the three target combinations above.

The comparison is bounded to the linked revisions. It does not claim zero shared code, global exclusivity, or that the other projects can never support these devices. The practical contribution is model-specific adapters, maintainer hardware feedback, sanitized troubleshooting knowledge, and an extensible community workflow. Update this comparison when upstream support changes.
