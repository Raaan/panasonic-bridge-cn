# 来源与致谢 / Third-party notices

这里记录项目参考的代码、协议资料及相应许可。核查日期为 2026-11-11；许可证全文保留在仓库中。

## Home Assistant

项目通过 Home Assistant 的自定义整合机制运行，使用它的实体、配置和状态更新接口。感谢 HA 社区提供的框架及开发文档。

[home-assistant/core](https://github.com/home-assistant/core) 采用 [Apache-2.0](https://github.com/home-assistant/core/blob/dev/LICENSE.md)。使用者需要自行安装 HA，本仓库只提供松下整合，没有附带 HA 源码、虚拟机镜像或家庭配置。

## 直接参考的项目

本项目参考和复用了 [rudyll/panasonic_smart_china_r](https://github.com/rudyll/panasonic_smart_china_r) 的认证和通信经验。核查版本为 `1566af4ef00df19b8dad186ea8a995f211ccf4aa`，其 MIT 许可中的版权信息为 `Copyright (c) 2026 rudyll`，原文保留在根目录及整合目录的 LICENSE 中。

该项目主要维护新风和中央空调，也建议其他品类以独立仓库继续适配。本项目在其基础上补充了所列净化器、空调和冰箱型号，具体区别见 [项目比较](docs/COMPARISON.md)。

## 更早的来源

rudyll 项目明确说明其基于 [mcdona1d/panasonic_smart_china](https://github.com/mcdona1d/panasonic_smart_china)。本次核查版本为 `2be1474cd9d2f868ce576fadcc6445f42e5a8545`，采用 Apache-2.0，全文保留在 [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt)。

两条来源的许可和署名都继续保留。核查的两个提交中未发现独立 NOTICE 文件，相关认证、token、配置流和空调文件也已检查；这项记录对应指定版本，完整开发历史仍在整理。

## 协议资料与社区贡献

- 直接上游感谢 arthurfsy 最早公开松下登录算法，本项目继续保留这项致谢。
- 空调枚举曾参考 Hassbian `tid=17153` 第 5 页的公开讨论，来源链接保留在 `protocols.py` 中。
- 净化器和 Fridge-19 的字段整理结合了官方静态控制资料及实际设备对照。厂商 APK、反编译代码、原始 JS 和抓包没有放进仓库。
- 直接上游还感谢 omegaojian、dkong5ssss 和 accpowered 的新风研究。本项目没有收录对应的新风实现，这些致谢保留其原有范围。

## 本项目的修改

适配工作包括三类设备识别、状态字段整理、请求参数检查、读回确认，以及六类 HA 实体。首次公开整理以部署版 0.5.0 为基础；后续开发稿增加了验证状态更新、英文配置文案、证书替换检查和隔离 HA 测试。

原始文件哈希见 `docs/baseline-files.json`。开发稿的逐文件修改记录保存在其 `docs/source-changes.json` 中。已知文件来源和仍待补充的历史信息见 [文件来源](docs/PROVENANCE.md)。

新增文档、贡献说明和检查工具计划采用 MIT。使用和分享时，请按对应许可保留版权信息、作者署名和已有修改说明。贡献者保留自己贡献的版权。
