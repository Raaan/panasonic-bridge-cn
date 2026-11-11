# Panasonic Bridge CN

[中文](README.md) | [English](README.en.md)

A community Home Assistant integration for selected Panasonic appliances using the mainland China smart-home cloud. It currently covers a specific air purifier, a new-protocol air-conditioner family, and the Fridge-19 refrigerator family.

**This is an open-source review draft based on deployed version 0.5.0. No GitHub Release has been published and HACS validation is incomplete.** This project is not affiliated with Panasonic and does not support the international Comfort Cloud service.

## Why this project exists

The project grew out of building a real Home Assistant home environment. The aim was to bring appliances from different brands—air conditioners, an air purifier, a refrigerator, and laundry appliances—into one platform for status monitoring and control, with a foundation for future cross-brand automation.

During that setup, brands such as Midea had usable built-in or established community integration paths. Panasonic was expected to fit into the same environment, but the mainland China models being used were not directly covered by the existing approaches tried at the time. Some appliance categories lacked an adapter; others used protocols that differed from already-supported controllers. This left a practical gap in the unified home setup. This describes the experience with those regions, models, and features; support for other Panasonic regions, product lines, and projects must be assessed separately.

Work therefore began on filling that gap, building on existing community projects and public protocol knowledge. The process started with login and discovery, then checked real state fields, control values, request formats, and read-back behavior. Purifier, AC, and refrigerator adapters gradually became part of the Home Assistant environment. The resulting knowledge includes successes and failure cases: incorrect category assumptions, unsuitable request envelopes, incomplete cached state, reversed lamp semantics, and ambiguous confirmation during network outages.

Opening the project is intended to make this work useful to others with similar needs. Users can reuse adapters and debugging knowledge instead of starting over, and additional models can join unified home setups when their compatibility is supported by evidence. Other brands should continue to use their own mature integrations. This repository covers the Panasonic scope listed below; cross-brand automation remains a broader home-system goal.

More participants are welcome. Device owners can contribute observations and manual checks, developers can fix bugs or add models, and other contributors can improve documentation, translations, and setup guidance. One maintainer has limited hardware and time; community participation can broaden the evidence while keeping it reviewable and reproducible.

Use, modification, forks, and contributions are welcome under the applicable licenses. Existing community attribution is retained. Supported models and verification remain limited: a result from one appliance must not be presented as compatibility with all Panasonic appliances. Publishing the code, debugging process, and known boundaries should make the work easier to continue and its reliability easier to assess.

## Supported scope

| Appliance | Discovery rule | Implemented features | Verification boundary |
| --- | --- | --- | --- |
| F-75C5PJD air purifier | Category `0810`, normalized subtype starts with `75C5PJD`, cloud model exactly `F-75C5PJD` | Power, four modes, gentle/low/medium/high airflow, NanoeX, plasma, selected boolean controls and sensors | Historical reports confirm power in both directions and a disinfection-to-gentle transition. Other writes are not comprehensively verified. |
| AC family used by CS-JM35K410Q | Category `0900`, normalized subtype starts with `AIRCONCOMMON202401` | Climate entity, cooling/heating/drying, integer 16–30°C targets, six fan settings, directions and selected auxiliary controls | Status retrieval is verified. One lamp direction has physical confirmation; other controls retain candidate mappings or incomplete validation. |
| Fridge-19 family used by NR-E411BG-NH | Category `0100`, normalized subtype equals `FRIDGE19` | Three temperature zones and six feature switches | Eco Navi has historical app confirmation in both directions. Quick-ice success was reported without separate direction results. Other writes need verification. |

Discovery matches a protocol family; it does not establish that every model in that family is compatible. Upstream ventilation and central-AC support tables are not this project's support table. See [device details](docs/DEVICES.md) for exact fields, constraints, and evidence.

## Installation and credentials

The deployed reference environment is Home Assistant 2026.10.4. Earlier versions have not been validated.

1. Back up your HA configuration and existing integration directory.
2. Copy `custom_components/panasonic_home_readonly` to `/config/custom_components/`.
3. Restart Home Assistant.
4. Open Settings → Devices & services → Add integration and search for **松下智家（本地验证）**.
5. Enter your mainland China Panasonic account credentials only in the HA form.

To change credentials, use the integration entry's Reconfigure option. Existing credentials are replaced only after successful login and supported-device discovery. Preserve the historical `panasonic_home_readonly` domain and entity IDs when upgrading. Do not rename the directory to match the repository name.

The domain contains `readonly` for compatibility, but this version has real control methods. “Locally validated” describes the development process, not local-only communication: the integration uses Panasonic's cloud. Some interface strings, including the existing `en.json`, remain Chinese; this English README does not claim a fully translated HA interface.

## Behavior and limits

- Polls every 60 seconds. Import, setup, discovery, and normal polling do not send device SET commands. Explicit entity/service calls can control appliances, including calls made by user-created HA automations. Installation does not create household automations.
- Credentials are stored by HA's configuration-entry mechanism, not encrypted by this integration. Protect configuration files and backups.
- Login can invalidate the mobile app session. Polling does not automatically log in again; reload or reconfigure when necessary.
- Commands are sent once. A queued task or successful cloud response is not proof of physical execution. Read-back failure must not trigger an automatic resend.
- AC `current_temperature` deliberately returns `None`: the room-temperature encoding is unverified, and raw value 128 is not a usable room reading.
- Some purifier state comes from a device-list cache cross-checked against live fields. Cache freshness remains uncertain.
- The bundled public certificate was historically trusted but its origin was not independently verified. Certificate and hostname checks remain enabled, with a compatibility exception scoped to the exact legacy certificate.
- Candidate controls are currently exposed without a single experimental-feature switch. Physical verification is incomplete. See [known limitations](docs/LIMITATIONS.md).

## Architecture and contributing

A configuration flow handles credentials and discovery. A client filters supported devices and numeric state fields. A shared coordinator polls state and serializes manual control/read-back operations. Six HA platforms expose sensors, binary sensors, switches, climate, selects, and numbers. Separate protocol modules validate purifier, AC, and refrigerator payloads; the transport fixes the HTTPS destination, rejects redirects and system proxies, and does not retry controls.

Contributions may include code, model-specific observations, manual verification, reproducible bug reports, documentation, or translation. Use synthetic fixtures and retain provenance. Separate implementation, observed state, app confirmation, and physical confirmation. Do not add guessed control endpoints, automatic command retries, implicit power-on behavior, or reset actions.

Offline checks require no credentials or network access:

```sh
python test_readonly.py
python -m unittest discover -s tests -v
python tools/privacy_scan.py
python tools/review_check.py
```

The review records 55 passing offline tests. GitHub Actions results must be checked separately. Offline tests do not prove physical behavior or HACS acceptance.

- [Bilingual project overview](docs/PROJECT_OVERVIEW.md)
- [Contribution guide, including English guidance](CONTRIBUTING.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Sanitized debugging cases](docs/DEBUGGING_CASES.md)
- [Security and privacy](SECURITY.md)
- [Validation](docs/VALIDATION.md)

Detailed technical notes are currently primarily Chinese. English contributions are welcome.

## Licensing and attribution

The direct upstream, [rudyll/panasonic_smart_china_r](https://github.com/rudyll/panasonic_smart_china_r), uses MIT. Its original copyright and license remain in [LICENSE](LICENSE). The acknowledged earlier upstream, [mcdona1d/panasonic_smart_china](https://github.com/mcdona1d/panasonic_smart_china), uses Apache-2.0; that license is included in [LICENSES/Apache-2.0.txt](LICENSES/Apache-2.0.txt).

Preserve applicable upstream notices and modification history. Do not relabel inherited work as entirely original MIT code. New review documentation and packaging are intended to use MIT; historical file-level attribution is not fully resolved. See [third-party notices](THIRD_PARTY_NOTICES.md) and the [provenance review](docs/PROVENANCE.md). Contributors retain copyright in their contributions; ownership is not transferred to the maintainer.
