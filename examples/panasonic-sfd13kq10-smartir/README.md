# Panasonic CS-SFD13KQ10 · BroadLink / SmartIR 红外接入记录

本目录记录一套独立于 Panasonic Bridge CN 云端集成的红外接入方案。它使用 BroadLink RM4C mini、Home Assistant 官方 BroadLink 集成与 SmartIR。红外控制不需要松下云端账号。

## 设备与范围

- 室内机：Panasonic CS-SFD13KQ10；室外机：CU-SF13KQ10。
- 原装遥控器：ACXA75C14560，电池盒编码 TL830C。
- 红外发射器：BroadLink RM4C mini，固件 62092。
- 环境：Home Assistant 2026.10.4，SmartIR 1.18.1。
- 支持制冷、制热、抽湿、关机，温度 16–30°C、步长 1°C；风量为自动、超静、1–5 档、超强；上下风向为自动和五个固定位置。
- 左右风向需要手动调节。自动上下风向在不同模式下可能停在某个角度，不代表一定持续摆动。

型号、支持档位和温度范围参考 [松下原厂说明书](https://papagz.panasonic.cn/download/198) 第 19、21、23 页。遥控器制冷键可切换普通制冷与柔湿制冷；强速冷、强速暖分别有独立按键。

## 验证状态

| 项目 | 结果 |
| --- | --- |
| 制冷 28°C、自动风量、自动上下风向 | HA 发送生成码后，用户确认空调显示 28°C。 |
| 制冷 27°C、自动风量、自动上下风向 | 用户确认空调显示 27°C，导风板上下摆动。 |
| 制热 24°C、自动风量、自动上下风向 | HA 发送原始码后，用户确认 24°C、制热，出风位置有变化。 |
| 关机 | HA 发送生成码后，用户确认空调关闭。 |
| 风量、风向样本 | 已采集自动、超静、1 档、5 档、超强及最高、最低风向；生成结果与采集的字段一致。 |
| 强速冷、强速暖、制冷柔湿 | 已采集原始码；强速冷 25°C、强速暖 24°C、柔湿 26°C。强速暖采集时空调开机，完整效果待测试。 |
| 其他温度、抽湿、其余风量和风向组合 | 已生成并完成离线回解；具体组合仍需实机验证。 |
| Apple 家庭与 Siri | 尚未验证此实体的 HomeKit Bridge 接入。 |

BroadLink 手机 App 中的模式 3 不能假定已导入 HA。上述样本通过 HA 和原装遥控器采集，不包含用户账号或网络配置。

## 生成码表

需要 Python 和 [pyhvac 0.2.0](https://github.com/frawau/pyhvac/tree/v0.2.0)。在本目录运行：

```sh
python -m pip install pyhvac==0.2.0
python generate.py 99993.json
```

生成器使用 `samples.json` 中的基准码，生成 2,160 个状态码及关机码。生成时逐条检查 BroadLink 格式和校验和，并检查八组生成状态与原始样本字段一致。风量中间档和抽湿模式依赖成熟编码器生成，实机兼容性尚未确认。

超静与普通 1 档、超强与普通 5 档有额外差异，不能把它们简单合并。强速冷、强速暖和柔湿是单独采集的固定状态码，位于 `samples.json`，不包含在 SmartIR 码表的普通模式选择中。改变普通温度或模式会发送新的完整状态。

## HA 配置示例

安装适用于自身 HA 版本的 [SmartIR](https://github.com/smartHomeHub/SmartIR)，并按其说明配置 BroadLink。将生成的 `99993.json` 复制到 `/config/custom_components/smartir/codes/climate/`。选择未冲突的设备码，按实际情况更改配置：

```yaml
smartir:
  check_updates: false

climate:
  - platform: smartir
    name: Bedroom Panasonic IR
    unique_id: bedroom_panasonic_ir_climate
    device_code: 99993
    controller_data: remote.broadlink
```

上述内容需要合并到现有配置，避免重复的顶层键。配置检查通过后重启 HA。自动更新检查关闭可避免启动时因网络等待；实际升级前应另行确认 SmartIR 与 HA 版本兼容，并保留自定义码表备份。

强速冷、强速暖和柔湿可通过 HA 的 `remote.send_command` 使用各自样本，命令加上 `b64:` 前缀。样本包含温度、风量与风向，直接发送固定状态，不能作为任意温度或任意风量的指令。独立发送这些码不会同步更新 SmartIR 的状态。

红外是单向通信。HA 显示的是自己记录的设定，既不能确认指令被接收，也不能读取空调真实状态。实际温度需要独立传感器。测试前确认设备状态，结果不明时不要盲目重复发送。

## 来源

- [SmartIR](https://github.com/smartHomeHub/SmartIR) 提供 HA climate 接入及 BroadLink 发送。
- [pyhvac](https://github.com/frawau/pyhvac) 的 Panasonic 编码、BroadLink 转换和解码用于生成和离线校验。pyhvac 使用 MIT 许可证，版权归原作者 François Wautier 所有。
- [IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) 的 Panasonic 空调实现为协议字段提供参考。

