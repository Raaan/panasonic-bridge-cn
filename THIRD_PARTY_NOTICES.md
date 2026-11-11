# Third-party notices / 来源与署名

核查日期：2026-11-11。此文件记录来源和实际修改范围，保留贡献者归属；不替代各许可证全文。

## 直接上游

- 项目：[rudyll/panasonic_smart_china_r](https://github.com/rudyll/panasonic_smart_china_r)
- 核查提交：`1566af4ef00df19b8dad186ea8a995f211ccf4aa`。
- [该提交的许可证](https://github.com/rudyll/panasonic_smart_china_r/blob/1566af4ef00df19b8dad186ea8a995f211ccf4aa/LICENSE)：MIT，`Copyright (c) 2026 rudyll`。原文保留于根目录 LICENSE 及整合目录 LICENSE。
- 本地交接明确以该项目为来源，登录派生、设备 token 与集成思路经本地工具和适配层复用。实际部署的整合不是该上游默认分支的原样副本。
- 上游 README 明确将主干范围限定为新风和中央空调，并鼓励其他品类独立仓库发布。本项目净化器和冰箱范围与之相符；上游未为本项目提供维护或背书。

## 运行平台 Home Assistant

- 项目：[home-assistant/core](https://github.com/home-assistant/core)。其 [LICENSE.md](https://github.com/home-assistant/core/blob/dev/LICENSE.md) 为 Apache-2.0。
- 本整合依赖 HA 的平台 API 和自定义整合加载机制；HA 本体由使用者另行安装，本包不重新分发其源码、虚拟机镜像或用户配置。
- 感谢 Home Assistant 社区提供运行平台和开发文档。本项目是独立社区整合，不代表 HA 官方收录或背书。后续如复制 HA 源文件而非仅调用其 API，应在来源表中记录该文件及适用通知。

## 更早上游

- 项目：[mcdona1d/panasonic_smart_china](https://github.com/mcdona1d/panasonic_smart_china)。由直接上游 README 明确署名。
- 当前核查提交：`2be1474cd9d2f868ce576fadcc6445f42e5a8545`。这只是核查时的版本，不等于本地代码实际继承的历史基线。
- [许可证](https://github.com/mcdona1d/panasonic_smart_china/blob/2be1474cd9d2f868ce576fadcc6445f42e5a8545/LICENSE)：Apache License 2.0。全文保留于 LICENSES/Apache-2.0.txt。
- 已读取两条核查提交的完整递归文件树（均未截断），未发现独立 NOTICE 文件；另检查了相关认证、token、配置流、空调及协调器来源文件。这个结论覆盖固定提交，不覆盖全部历史提交。逐文件归属见 [来源表](docs/PROVENANCE.md)。
- 不将直接上游的 MIT 标记理解为自动覆盖早期 Apache-2.0 贡献。对继承的 Apache 代码，保留适用版权、许可证、修改告知及若存在的 NOTICE；不得删除原权利人信息。新增文档及包装拟采用 MIT，不要求贡献者转让全部版权。

## 协议知识来源

- arthurfsy：直接上游 README 记载其最早公开松下云端登录算法。此为上游记载的致谢，未独立追溯最早原稿。
- 空调候选枚举：本地 `protocols.py` 引用 Hassbian 帖子 `tid=17153` 第 5 页。该帖内容本轮未重新获取，不把帖子及其他机型的数值当作本机全面验证，也不复制帖子正文。
- 冰箱 Fridge-19 与净化器协议：本地记录说明曾检查官方静态控制页，并以用户操作和状态对照校准。审阅包不包含厂商 APK、DEX、反编译源码、原始 JS、抓包或手册副本；不将厂商内容标成 MIT。
- 直接上游 README 还感谢 omegaojian、dkong5ssss、accpowered 的新风研究。本包不收录对应新风控制器实现，不把他们列作本项目三类设备的实测者。

## 相对上游及部署版的修改

本地适配以独立 domain `panasonic_home_readonly` 实现三类设备过滤、严格参数构造、无控制重试、缓存交叉检查、TLS 兼容及六类 HA 实体。保留原有授权与贡献者归属，不宣称上述内容全部由 Raaan 原创。

本次审阅版以已部署的 0.5.0 为基线。运行源码仅修改 manifest 的文档地址、问题地址与维护者元数据；Python 逻辑、domain、版本、实体 UID 和证书未更改。另增中英文文档、测试、CI、打包隐私检查与本来源说明。逐文件哈希见 docs/baseline-files.json；源文件保留历史只读注释，当前真实能力以实现和文档为准。个人服务器、本机与备份比较信息不放入公开包。

拟维护账号：[Raaan](https://github.com/Raaan)。社区可按适用许可证 fork、修改、提交 PR。首次公开发行前需要复核逐文件来源，不能仅凭 GitHub 自动检测的单一许可证标识宣布许可证链审查完成。

### 0.5.1.dev0 后续优化

后续开发稿增加了证书替换拦截、维护者验证状态更新、真正的英文配置流、带固定提交来源的项目比较和隔离 HA 测试。其逐文件原始/当前哈希与修改理由见 `docs/source-changes.json`；原始 0.5.0 基线保留。历史基线“Python 逻辑未修改”的描述仅适用于首次开源准备，不适用于这些已明确记录的后续变化。控制请求构造保持基线不变。
