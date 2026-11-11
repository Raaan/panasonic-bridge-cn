# 文件来源

这里整理已有代码与社区项目的关系，方便后续维护和继续核对历史。部分开发记录早于当前仓库，暂时没有完整提交链，因此无法逐行还原最初作者和当时版本。

## 已核查的来源

- `rudyll/panasonic_smart_china_r@1566af4ef00df19b8dad186ea8a995f211ccf4aa`：MIT。
- `mcdona1d/panasonic_smart_china@2be1474cd9d2f868ce576fadcc6445f42e5a8545`：Apache-2.0。这里是核查版本，不一定是最初复用时的提交。

两个指定提交的完整文件树中没有独立 NOTICE。相关认证、token、配置流、协调器和空调文件已查看，未发现额外文件头版权声明；项目级许可和署名继续保留。

## 文件整理

| 文件 | 已知来源或用途 |
| --- | --- |
| `transport.py`、`client.py` | 登录及设备 token 与上游算法对应；本地补充传输、设备筛选、参数检查和状态整理 |
| `__init__.py`、`config_flow.py` | HA 生命周期与配置适配，包含命令锁、读回确认及凭据更换保护 |
| `climate.py`、`protocols.py` | 本机新协议空调适配；枚举另参考文件中注明的社区资料 |
| `purifier_protocol.py` | 净化器完整状态检查与 skip 模板，结合静态资料和实机对照整理 |
| `fridge_protocol.py` | Fridge-19 字段、温区范围和互斥处理 |
| `entity.py` 及各实体平台 | 本地 HA 实体映射与稳定标识 |
| `calibration.py` | 默认关闭的脱敏诊断和一次性读取工具 |
| `manifest.json`、语言文件 | 整合元数据与界面文字，后续变化按版本记录 |
| `LICENSE` | 直接上游 MIT 原文，保留 rudyll 版权信息 |
| `panasonic-cloud.pem` | 历史接入时保存的公开证书，来源仍需独立核对 |

新增文档、测试和检查工具随开源准备继续完善。原始 21 文件哈希保存在 `baseline-files.json`；开发分支的后续变更另有 `source-changes.json` 和控制方法基线记录。

已确认的许可全文和修改说明会持续保留。后续找到更早的提交或资料时，再补充这份记录，不根据文本相似度直接推定作者。项目维护账号与各项贡献的版权作者分别记录。
