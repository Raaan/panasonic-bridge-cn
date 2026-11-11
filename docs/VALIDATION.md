# 验证记录

更新日期：2026-11-11。

## 实际使用

F-75C5PJD 净化器、CS-JM35K410Q 空调和 NR-E411BG-NH 冰箱的现有功能已由我在实际设备上核对，部署版本在家中稳定使用。设备型号及确认范围见 [统一记录](VERIFICATION_STATUS.json)。

当前公开的开发改动与已经部署使用的版本分别记录，不能把分支测试结果直接当成新版本已经实机部署。

## 自动化与环境检查

| Check | Result |
| --- | --- |
| 0.5.0 offline checks | 55 passing tests: 33 protocol/privacy, 10 refrigerator, 12 privacy-scanner regressions |
| Python CI | Python 3.12 and 3.14 passed for the published source |
| Deployed HA environment | HA 2026.10.4 module imports and `ha core check` passed |
| Development PR #2 | 59 offline tests and 8 isolated HA-runtime checks passed on its recorded public commit |

开发 PR #2 的结果对应提交 `d6c2b88037dd9ca8c32ecc16b33d8ade900308e6`。其后仅在本地修改的内容尚未重新上传；当前状态以对应分支和 CI 记录为准。

测试覆盖参数范围、互斥处理、状态过滤、隐私保护及不自动重发等行为。HA 环境测试和模拟配置检查用于发现接口兼容问题，不会连接真实云端或操作设备。

## 文件检查

Python AST、JSON、证书指纹和敏感格式扫描已检查。公开目录没有账号、会话、真实设备标识、家庭网络和备份位置。扫描结果只显示位置与规则，仍需在发布前人工复核。

`baseline-files.json` 保留首次部署基线，包内 `FILE_MANIFEST.json` 记录交付文件哈希。详细排障过程见 [排障记录](DEBUGGING_CASES.md)。HACS/hassfest、其他固件和外部用户的长期使用结果还需要继续补充。
