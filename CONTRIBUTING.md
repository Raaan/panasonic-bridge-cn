# 参与项目 / Contributing

欢迎一起完善这个项目。除了代码，设备测试、问题复现、文档和翻译都很有帮助。我的实机条件有限，其他型号的支持需要对应设备的用户参与。

## 报告问题

请提供 HA 和整合版本、设备型号、类别与子类型，以及出现问题的步骤。尽量分别说明 HA、官方 App 和设备实际表现，便于判断是显示、同步还是控制问题。

提交前请删除账号、会话、token、MAC、deviceId、真实实体标识及家庭信息。完整配置、数据库和原始云端响应不适合公开；保留必要字段的脱敏片段通常更有用。

## 修改代码

1. Fork 仓库并建立分支。
2. 使用合成数据编写或更新测试，保留现有 domain 和实体 ID 的兼容性。
3. 运行下列检查。涉及 HA API 的修改，还需要在隔离环境中检查配置和生命周期。
4. 提交 PR，说明解决的问题、受影响型号、来源和测试结果，并同步相关文档。

```sh
python test_readonly.py
python -m unittest discover -s tests -v
python tools/review_check.py
```

基础测试可在 Python 3.12 或 3.14 上运行，无需松下账号。隔离 HA 运行时测试使用固定版本和模拟云端，不会操作实际设备。代码检查与实机结果请分别填写。

## 新型号适配

建议先核对设备发现和状态读取，再确认控制字段、取值、跳过值及互斥关系。控制前后请分别记录读回、App 和设备结果，尚未测试的部分直接注明即可。

控制请求维持一次发送，不自动重试、不猜测其他端点，也不附带用户没有选择的开机或复位动作。已经验证的载荷如需改动，请单独说明原因，便于检查对原有设备的影响。

## 来源与署名

请注明引用代码和协议资料的来源，并确认可以按相应许可使用。合入时保留作者归属和原有许可，贡献者继续保有自己贡献的版权。若改动来自其他 fork 或帖子，欢迎请作者提交 PR，或先确认其许可和署名方式。

具体流程见 [分享社区修改](docs/SHARING_CHANGES.md)，已知来源见 [第三方说明](THIRD_PARTY_NOTICES.md)。

## English

Code, hardware tests, reproducible reports, documentation and translations are all welcome. Please describe the affected model and separate HA state, app state and physical behavior. Remove credentials and identifying data before sharing a report.

Work in a fork branch, use synthetic fixtures, run the checks above and explain sources and validation in the PR. Preserve the domain and existing entity IDs. Commands should be sent once, without automatic retries, guessed fallback endpoints or unrelated actions.

Contributors retain their copyright. Existing notices and authorship are kept when changes are merged. For code from another fork or post, establish its reuse terms and attribution first.
