# Panasonic Bridge CN · 松下智家桥接

[中文](README.md) | [English](README.en.md)

面向中国大陆松下智家云端的 Home Assistant 自定义整合，覆盖指定净化器、空调协议族和冰箱协议族。

**当前为开源审阅稿，来源为实际部署的 0.5.0。尚未发布 GitHub Release，也未完成 HACS 验证。** 本项目是社区作品，与松下无隶属关系；不适用于国际版 Comfort Cloud。

## 项目背景与目标

这个项目起于将松下家电接入 Home Assistant 的实际需求。适配过程中积累了设备识别、云端协议、状态校准和控制验证的经验。希望把这些代码和调试经验整理开放，让有相同需求的人能够复用，减少重复排障，也让更多松下设备用户受益。

开源也希望让更多人参与进来：拥有不同设备的用户可以补充状态对照和手动验证，开发者可以修复问题、改进代码或适配新型号，其他贡献者可以完善文档、翻译和使用说明。项目不应只依赖一个人的设备与精力，而应逐步积累可审阅、可复现的社区经验。

欢迎按适用许可证使用、修改和贡献。当前支持范围与验证仍有限；新增设备与功能需要明确证据，不能把某一型号的结果推广成全部松下设备兼容。希望通过公开记录这些边界，让参与者更容易接手，也让使用者清楚哪些能力可以依赖。

## 支持范围

| 设备 | 识别条件 | 已实现 | 验证边界 |
| --- | --- | --- | --- |
| F-75C5PJD 净化器 | `0810`；子类型以 `75C5PJD` 开头；云端型号严格等于 `F-75C5PJD` | 电源、四模式、轻柔/低/中/高风量、NanoeX、等离子体及部分布尔功能；状态传感器 | 历史记录确认电源双向、消毒切轻柔；其余写入不能推定全部通过 |
| CS-JM35K410Q 所属空调协议族 | `0900`；规范化子类型以 `AIRCONCOMMON202401` 开头 | climate、制冷/制热/除湿、16–30℃整数设定、六档风速、风向、辅热、NanoeX、灯光、睡眠、强智冷暖、柔湿制冷 | 实时状态已验证；灯光有单方向实体确认；其余存在候选值与未完成的逐项验收 |
| NR-E411BG-NH 所属 Fridge-19 冰箱 | `0100`；规范化子类型严格为 `FRIDGE19` | 三区温度读数与设定；速冻、快速制冰、制冰停止、新鲜冻结、节能导航、NanoeX | 历史记录确认节能导航双向 App 同步；快速制冰有用户成功反馈，未区分双向；其余写入待验收 |

以上识别条件来自代码。协议族匹配成功不等于其他型号控制已验证。上游的新风、中央空调支持表不适用于本项目。详细边界见 [设备与协议](docs/DEVICES.md)。

## 安装与配置

已部署环境为 Home Assistant 2026.10.4。更早版本尚未验证，不承诺兼容。

1. 备份现有 HA 配置和整合目录。
2. 将本仓库 `custom_components/panasonic_home_readonly` 复制到 HA 的 `/config/custom_components/` 下。
3. 重启 Home Assistant。
4. 设置 → 设备与服务 → 添加集成 → **松下智家（本地验证）**。
5. 只在 HA 页面输入松下智家账号和密码。登录和设备发现成功后生成实体。

更换凭据：条目菜单 → 重新配置。登录及设备发现成功后才更新原条目。已有安装升级时保留 `panasonic_home_readonly` 目录名和实体标识；不要根据项目名重命名 domain 或删除重加条目。

`panasonic_home_readonly` 是历史兼容名称，当前版本已有真实控制能力。这里的“本地验证”指开发验证环境，通信仍通过松下云端。每 60 秒轮询，导入、配置、发现和正常轮询不下发设备 SET；显式实体操作可发送真实指令。HA 自动化同样可以调用这些实体，安装时不会创建家庭自动化。

## 使用前须知

- 账号密码由 HA 配置条目保存，并非本整合加密；请保护配置和备份。
- 登录可能挤掉手机 App 会话。轮询不会自动重登，失效时需重新加载或重新配置。
- 不自动重发控制。云端受理或返回任务号不等于实体执行；读回未确认时需核对 App 与实体。
- 空调 `current_temperature` 固定为空，因为室温编码未验证；原始值 128 不能当作室温。
- 部分状态来自设备列表缓存；虽然与实时基础状态交叉检查，缓存新鲜度仍有限。
- 内置证书为历史信任的公开证书，来源未独立核验。继续检查证书与主机名；详见 [安全说明](SECURITY.md)。

## 文档与贡献

- [架构](docs/ARCHITECTURE.md)
- [设备、端点与验证矩阵](docs/DEVICES.md)
- [已知限制](docs/LIMITATIONS.md)
- [脱敏调试案例](docs/DEBUGGING_CASES.md)：发现过滤、请求封装、缓存、灯光、冰箱和 TLS 排障经验。
- [文件来源与归属](docs/PROVENANCE.md)
- [中英项目介绍](docs/PROJECT_OVERVIEW.md)
- [许可证与来源](THIRD_PARTY_NOTICES.md)
- [贡献指南](CONTRIBUTING.md)：欢迎修改、适配、问题报告和 Pull Request。

离线验证，无账号、无网络：

```sh
python test_readonly.py
python -m unittest discover -s tests -v
python tools/privacy_scan.py
python tools/review_check.py
```

## 许可与署名

直接上游 [rudyll/panasonic_smart_china_r](https://github.com/rudyll/panasonic_smart_china_r) 使用 MIT，原始版权与许可全文保留于 [LICENSE](LICENSE)。其更早上游 [mcdona1d/panasonic_smart_china](https://github.com/mcdona1d/panasonic_smart_china) 使用 Apache-2.0，全文另存于 [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt)。保留两条来源链及适用的署名、修改说明；不要把全部历史贡献改署为本项目作者。

本审阅包的新增文档、贡献规范与离线检查拟沿用 MIT。历史协议来源的逐文件归属仍有待补证，见来源说明。允许按适用许可证使用、修改和贡献，不设置额外的禁止修改或禁止分发条款。
