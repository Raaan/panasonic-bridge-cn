# Panasonic Bridge CN

[中文](README.md) | [English](README.en.md)

A Home Assistant integration for the mainland China Panasonic appliances I use at home: an air purifier, an air conditioner and a refrigerator.

The deployed version is 0.5.0. A formal GitHub Release has not been published, and HACS release checks are still being completed.

## Why I started this

When setting up Home Assistant at home, I wanted to manage appliances from different brands in one place. My Midea devices had usable integrations, but the existing projects I found did not directly cover my mainland China Panasonic models.

Those projects had already done useful work on authentication and device communication. I built on that work to add the state reading and controls my devices needed. The purifier, AC and refrigerator now run reliably in my home, and I have checked their implemented controls on the actual devices.

I am sharing the code and troubleshooting notes so other owners can reuse the work instead of starting over. Contributions are welcome, whether they are fixes, tests on another model, or clearer documentation. I can only test the devices I own, so community participation is important to extending support.

## Supported devices

| Device | Implemented features | Status |
| --- | --- | --- |
| F-75C5PJD purifier | Power, four modes, airflow, NanoeX, plasma, child lock, lights, display and state readings | Tested on my device and in use at home |
| CS-JM35K410Q AC | Power, cooling/heating/drying, integer 16–30°C targets, six fan settings, directions, auxiliary heat, NanoeX, lights, sleep, powerful heating/cooling and soft cooling | Tested on my device and in use at home |
| NR-E411BG-NH refrigerator | Three-zone temperatures and targets; quick freeze, quick ice, ice stop, fresh freezing, Eco Navi and NanoeX | Tested on my device and in use at home |

These results apply to the listed models. Similar names or category numbers may still use different protocols. See [device details](docs/DEVICES.md) for discovery rules and limitations. Reliable AC room temperature and unimplemented app features are outside the current support scope.

## Relationship to other Panasonic projects

This project reuses existing Chinese-cloud authentication and protocol knowledge while adding specific model support. The checked mcdona1d project supports controller-based central AC and a bathroom heater; rudyll focuses on ventilation and central AC; osk2 uses its Panasonic Smart App device definitions.

The main additions here are the `0810/75C5PJD` purifier, `AirconCommon-2024-01` AC and `Fridge-19` refrigerator. The [comparison](docs/COMPARISON.md) links the revisions checked. I would welcome collaboration when an existing adapter can solve the same problem.

## Installation

My reference environment is Home Assistant 2026.10.4. Other versions have not been fully tested.

1. Back up your HA configuration and existing integration directory.
2. Copy `custom_components/panasonic_home_readonly` to `/config/custom_components/`.
3. Restart Home Assistant.
4. Under Settings → Devices & services → Add integration, search for **松下智家（本地验证）**.
5. Enter your Panasonic account credentials in the HA form. Supported devices are discovered after login.

Use Reconfigure on the integration entry to change the account or password. New credentials are saved only after login and discovery succeed; a failed check leaves the old configuration in place.

Keep the historical `panasonic_home_readonly` folder name when upgrading. It preserves existing entity IDs and automations. The integration now includes controls despite that older name.

## Everyday use

- Communication uses Panasonic's mainland China cloud, with state polling every 60 seconds. An internet connection is required.
- Startup and normal polling only read state. Entity actions and HA automations that call them can control devices.
- A command is sent once, followed by state confirmation. If it is not confirmed, check the app and appliance before trying again.
- The mobile app and HA can invalidate each other's sessions. Reload or reconfigure the integration when the session expires.
- HA stores credentials in its configuration entries. Protect the configuration directory and backups. See [security notes](SECURITY.md) for connection and certificate details.

I also use a separate AI WeChat tool to control the HA setup. That is an optional way of using the integration; the WeChat tool is maintained separately and is not included here.

## Contributing

Bug reports, fixes, model-specific tests and documentation improvements are welcome. For another model, start with its model name, protocol category and sanitized state fields so we can check whether an existing adapter fits.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes. [Troubleshooting notes](docs/DEBUGGING_CASES.md) and the [maintenance plan](docs/ROADMAP.md) explain the current work. Detailed technical notes are primarily Chinese; English improvements are welcome.

The basic checks need no account or network access:

```sh
python test_readonly.py
python -m unittest discover -s tests -v
python tools/privacy_scan.py
python tools/review_check.py
```

See [validation records](docs/VALIDATION.md) for test results and environments. Automated tests check code behavior; appliance compatibility still needs users with the relevant hardware.

## Thanks and licensing

This integration uses [Home Assistant](https://www.home-assistant.io/)'s custom-integration framework. Thanks to the HA community for the platform and development resources. Install Home Assistant separately before installing this adapter.

I have used and built on work from [rudyll/panasonic_smart_china_r](https://github.com/rudyll/panasonic_smart_china_r), which acknowledges [mcdona1d/panasonic_smart_china](https://github.com/mcdona1d/panasonic_smart_china) as an earlier source. Their work and the wider community's contributions are appreciated. The applicable [MIT](LICENSE) and [Apache-2.0](LICENSES/Apache-2.0.txt) license texts are retained. See [third-party notices](THIRD_PARTY_NOTICES.md) for sources and changes. HA Core also uses [Apache-2.0](https://github.com/home-assistant/core/blob/dev/LICENSE.md).

Use, modification and sharing are welcome under the applicable licenses, with the original copyright and contributor attribution retained. New documentation and checking tools are intended to use MIT. I am still tracing some historical file-level sources; the information available is recorded in the [provenance notes](docs/PROVENANCE.md).

This is an independent community project, not an official Panasonic or Home Assistant integration. It does not support international Comfort Cloud.
