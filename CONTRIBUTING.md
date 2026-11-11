# 贡献指南 / Contributing

欢迎修改、fork、提交 Issue 和 Pull Request。遵守适用 MIT / Apache-2.0 许可证并保留原署名。提交者保留其贡献版权；不要求独家授权或转让版权。请仅提交有权贡献的代码，并按相关文件既有许可授权贡献。

项目希望通过开放代码和调试经验帮助更多松下设备用户，并邀请更多人共同维护。贡献不限于写代码：设备状态对照、手动验收、可复现的问题报告、文档、翻译和使用说明都能帮助项目。没有设备实测条件的贡献，也请明确说明验证边界。

## 本地开发

1. Fork 仓库，建立独立分支。
2. 使用 Python 3.12 或 3.14 运行离线协议测试。基础测试无需安装 HA，也不应登录云端。
3. 修改涉及 HA API 时，另在隔离的 HA 2026.10.4 或所声称支持的版本测试配置、导入及生命周期。
4. 更新设备矩阵、来源说明和 Changelog。无法完成实机验证时明确标注“未验证”，不要改成“完全支持”。

```sh
python test_readonly.py
python -m unittest discover -s tests -v
python tools/review_check.py
```

## 新设备适配

在 Issue 中提供型号、类别、子类型、端点名称及脱敏的字段/枚举表。不要提供账号、SSID、设备 MAC、deviceId、token、原始云端响应、HA 配置或家庭截图。使用 `AABBCCDDEEFF_...` 等合成标识编写测试，不能使用真实标识的哈希代替完整脱敏。

先验证发现和只读状态，再核对写入字段、范围、跳过值、互斥规则及读回确认。每项控制分别记录方向、App 结果与实体结果。新增写入不得自动重试、猜测端点、隐式开机或顺带复位滤网。维护者不会因收到报告自动控制报告者设备。

保留现有 domain、unique_id、实体字段与配置版本兼容性。涉及迁移时单独说明旧安装如何升级及回退。不要顺带提交个人仪表盘、自动化、凭据、调试采样或厂商反编译产物。

## PR 需要的信息

- 具体问题及触发条件。
- 改动后行为，受影响型号/协议族。
- 纯离线验证结果，以及另列的实机验证范围。
- 协议或代码来源、许可证及署名。
- 已知限制与无法验证的情况。

CI 仅进行离线测试和包检查，不能证明设备控制成功，也不能代替 HACS/hassfest 验证。测试不使用生产账号，不在 CI 保存松下账号 secret。

## English

Forks and pull requests are welcome. Retain applicable copyright, license and
attribution notices. Contributors retain copyright in their contributions.
Use synthetic fixtures and offline tests. Report model, protocol category and
subtype without accounts, session IDs, MACs, device IDs or raw responses.
Separate implemented functionality, observed states and physically verified
controls. Document provenance and compatibility. Never add automatic command
retries or unrequested power-on behavior. Existing domain and entity IDs must
remain compatible unless an explicit migration is provided.
