# 维护路线 / Maintenance roadmap

本路线结合当前代码、维护者最新实机反馈和公开审阅中的问题。其他对话的旧结论不直接覆盖当前证据。

## 已有基础

- F-75C5PJD：维护者确认基本完成核对，现有功能可控。
- CS-JM35K410Q：维护者同样确认现有空调控制可用。
- Fridge-19：保留已有节能导航、快速制冰反馈；其他控制仍需单独记录。
- 保留 HA 自定义整合结构、domain 与实体标识；不新增独立服务器，不改生产环境。

## 这轮改进

- 校正中英支持表和界面中的旧验证标签；新增可机器读取的验证状态，明确维护者报告与独立复测的区别。
- 补齐与现有 GitHub 松下项目的来源化比较，说明具体增量而非宣称完全无重合。
- 完成英文配置流文案，修正不支持设备提示中遗漏的冰箱协议。
- 在建立 TLS 上下文前校验内置证书指纹，替换或损坏即失败；不改变已确认设备控制载荷。
- 增加隔离 HA 运行时的配置、实体创建及生命周期测试；没有真实云端或设备操作。

## 正式发行前

1. 继续独立核验历史证书来源。指纹检查只能阻止静默替换，不能证明最初信任正确。
2. 为尚未确认的冰箱写入和未来新型号设计默认关闭的实验性策略。不能因旧对话的过期状态把已确认的净化器、空调控制一并关掉。
3. 归档按功能及方向划分的验证记录，尤其冰箱温控、不同固件和外部用户反馈。维护者的总体确认不等于每项双向日志齐备。
4. 完成隔离环境安装、升级、卸载和 HACS/hassfest 检查，再选择正式版本并发布。当前不申请目录收录。
5. 持续补历史逐文件归属；对新增复制代码明确来源及许可。

## OpenAI 开源支持材料

使用真实公开提交、测试和维护工作说明项目价值，不制造用户量、Stars、下载量或“已广泛采用”的印象。取得正式发行与外部反馈后再更新材料是本项目的推进建议，不是官方申请硬门槛。当前只准备材料，不提交账户或同意条款。

## English

The priorities are model-specific reliability, accurate evidence, installability, and reproducible maintenance. The maintainer confirms the existing purifier and AC controls work; that supersedes older blanket “unverified” labels. Refrigerator gaps, unknown models, certificate provenance, formal packaging validation, and external-user feedback remain separate work. This cycle changes evidence labels, setup translations, certificate replacement checks, and isolated runtime tests without changing validated control payloads or deploying to production.
