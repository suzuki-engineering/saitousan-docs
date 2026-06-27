# ADR-0008: Android SDK/Emulator用EC2 Runtime Host候補とOS方針

## Status

Proposed

## Context

Issue #17では、Android SDK、Android Emulator、Appium、FFmpeg、仮想カメラ入力をAWS上で検証するためのRuntime Host候補を整理することが求められている。

既存ADRでは、ADR-0002でYouTube LiveをAndroid実行環境へ入力するラッパー構成を採用候補とし、ADR-0006でクラウド利用は短時間・低コストの段階的PoCに限定している。`architecture/aws-youtube-to-saitousan-live.md` でも、EC2 Linux + Android Emulatorを第一候補としつつ、GPU、仮想化、カメラ入力は要検証としている。

このADRは、すぐ本番利用する確定構成ではなく、Phase 3以降の短時間検証で潰すべきEC2候補、採否条件、運用制約を定義する。

前提は次の通り。

- Android EmulatorのLinux VM accelerationはKVMに依存するため、EC2上で `/dev/kvm` と `emulator -accel-check` が通るかを最初に確認する。
- AWSは2026-06-18にC7i系をnested virtualization対応へ追加した。東京を含むcommercial regionで利用できるが、起動時に `NestedVirtualization=enabled` を明示する必要がある。
- g4dn/g5/g6のvirtual instanceはnested virtualization対応一覧に含まれないため、GPUがあることとAndroid EmulatorのVM accelerationが使えることを同一視しない。
- 斉藤さんアプリ、Android Emulator、Appium、仮想カメラ入力の成立性が未確認のため、EC2を常時起動しない。
- 東京リージョンでのインスタンス提供状況、Service Quotas、On-Demand料金は変動し得るため、起動直前にAWSコンソールまたはAWS CLIで確認する。

## Decision

Runtime Hostの第一検証は、nested virtualizationを有効にした `Ubuntu Server 24.04 LTS x86_64 + c7i.4xlarge` とする。AWS CLIでは `--cpu-options "NestedVirtualization=enabled"` を明示する。メモリ不足やEmulator/FFmpeg/Appiumの同居で余裕がない場合のみ `c7i.8xlarge` に上げる。

`c7i` はCPU-only smoke testである。nested virtualizationを有効化してもKVMまたはAndroid Emulator加速が成立しない場合は長追いしない。まずC8i/M8i/R8i系で同条件を再確認し、GPUが必要な問題とKVMが必要な問題を分離する。

候補の優先順は次の通り。

| Priority | Candidate | OS | Purpose | Initial EBS | GPU driver | Acceptance check | Stop condition |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| 1 | `c7i.4xlarge` + nested virtualization | Ubuntu Server 24.04 LTS x86_64 | CPU-only smoke。SDK/Appium/AVD構築とKVM可否の最短確認 | 100-150 GiB gp3 | 不要 | nested virtualization有効、`/dev/kvm`、`emulator -accel-check`、headless AVD boot、`adb devices`、Appium session、screenshot | KVM不可、AVD起動不可、メモリ不足が明確 |
| 1b | `c7i.8xlarge` | Ubuntu Server 24.04 LTS x86_64 | CPU-onlyでメモリ/CPU余裕を増やす | 150-200 GiB gp3 | 不要 | `c7i.4xlarge` と同じ。複数プロセス同居で安定するか | `c7i.4xlarge` と同じ |
| 2 | `c8i.4xlarge` / `m8i.4xlarge` + nested virtualization | Ubuntu Server 24.04 LTS x86_64 | C7i固有問題とnested virtualization全般を切り分ける | 100-150 GiB gp3 | 不要 | Priority 1と同じ | 同条件でKVM不可、または東京リージョンのquota/availabilityが不適 |
| 3 | `g4dn.xlarge` / `g5.xlarge` / `g6.xlarge` | Ubuntu Server 24.04 LTS x86_64 | NVIDIA GPUでFFmpegや描画だけを分離検証 | 150-200 GiB gp3 | 必要 | NVIDIA driver、FFmpeg probe、software renderingの許容性 | VM acceleration必須、またはsoftware renderingが実用外 |
| 4 | `g4dn.metal` などのbare metal | Ubuntu Server 24.04 LTS x86_64 | GPUとKVMを同一hostで必要とする場合の切り分け | 200 GiB gp3以上 | 必要 | bare metalでKVM、Emulator、GPU renderingが同時成立するか | 2-4hで解消しない、費用が大きい |
| 5 | nested virtualization対応Intel instance + Windows Server | Windows Server | Linux headlessでGUIデバッグが不足する場合の逃げ道 | 200 GiB gp3以上 | 通常不要 | Hyper-V/WHPX、Android Studio GUI、AVD、Appium、screenshot | GUIでしか進まない理由が説明できない |

OS方針は次の通り。

- 第一候補はLinux headless、具体的にはUbuntu Server 24.04 LTS x86_64にする。
- Android SDK、Emulator、Appium、driver周辺で互換性問題が出る場合のみUbuntu Server 22.04 LTSに下げる。
- Windows ServerはGUIデバッグが必要になるまで初手にしない。
- EC2 MacはmacOS固有要件が出るまで候補外にする。
- Graviton/arm64系は、対象APK、Android system image、Appium周辺のx86_64前提を崩すため初期候補外にする。

## Validation Plan

各候補は2-4時間の上限で起動し、次を順に確認する。

1. AWS起動前チェック
   - 東京リージョンのavailability、Service Quotas、On-Demand料金、EBS料金を確認する。
   - 対象instance familyがAWSのnested virtualization対応一覧に含まれることを確認する。
   - `NestedVirtualization=enabled` を指定し、instance metadataまたは起動設定で有効化を確認する。
   - EC2 tagとして `owner`、`purpose=android-runtime-poc`、`phase=poc`、`expire_at` を必須にする。
   - AWS Budgetsまたは請求アラート、自動停止を先に設定する。
2. Host capability check
   - `egrep -c '(vmx|svm)' /proc/cpuinfo`
   - `test -e /dev/kvm`
   - `emulator -accel-check`
   - GPU候補では `nvidia-smi` とdriver状態を確認する。
3. Android runtime check
   - Android SDK、platform-tools、emulator、system imageをインストールする。
   - headless AVDを起動する。
   - `adb devices` で認識する。
4. Automation/media check
   - Appium sessionを作成する。
   - screenshotを取得する。
   - FFmpegで入力/出力のprobeを行う。
   - カメラ入力または仮想カメラ入力の列挙・制約を確認する。
5. Decision gate
   - 成功/失敗を `research/validation-log.md` に記録する。
   - 失敗がインスタンス種別由来か、Android/アプリ/仮想カメラ由来かを切り分ける。
   - 次候補へ進むか、EC2以外のRemote Hostまたはローカル実機へ切り替えるかを判断する。

## Acceptance Criteria

PoCでEC2 Runtime Host候補として残す条件は次の通り。

- 2-4時間以内にAndroid SDK/Emulator/Appiumの最小セットアップが再現できる。
- `/dev/kvm` と `emulator -accel-check` が期待通りに通る、またはKVMなしでも許容できる理由と性能見込みを説明できる。
- headless AVD boot、`adb devices`、Appium session、screenshot取得まで到達できる。
- GPU候補ではdriver導入、Emulator rendering、FFmpeg実行の追加価値が確認できる。
- 常時起動せず、タグ、自動停止、Budget、secret非保存の運用条件を満たせる。

## Rejection Criteria

次のいずれかに該当する候補は初期PoC候補から外す。

- `/dev/kvm` またはEmulator accelerationが成立せず、代替手段の性能見込みもない。
- セットアップに4時間以上かかり、問題がインスタンス固有かどうか切り分けられない。
- 東京リージョンのquota/availabilityがPoCに不向き。
- Windows GUIやGPUが必要な理由を説明できない段階で、Linux CPU-onlyより大幅に高コストになる。
- secrets、Cookie、配信キー、アカウント情報をAMI、user-data、ログに残す必要がある。

## Consequences

良くなること:

- EC2検証を「nested virtualization対応CPU instance → 世代差の再確認 → GPU単体 → GPU bare metal → Windows GUI」の順に絞れる。
- KVM/Emulator加速を最初のゲートに置くため、成立しない環境を長追いしにくい。
- ADR-0006のコスト制御と整合し、常時起動や高額GPUの先行利用を避けられる。
- GPUやWindowsが必要になった場合も、なぜ次候補へ進むのかを検証ログで説明できる。

難しくなること:

- 初期のLinux headlessではGUIデバッグがしづらい。
- `c7i` でCPU-onlyが通っても、仮想カメラ入力やGPU renderingの問題は別途残る。
- AWS側のquota、availability、料金は起動時点で再確認が必要になる。

リスク:

- AWSのnested virtualization対応familyは更新され得る。GPU virtual instanceは2026-06-27時点の対応一覧に含まれないため、KVMが必要ならbare metalまたは対応Intel familyへ分離する。
- Android Emulatorの一般ドキュメントはVM内のVM accelerationを制限事項としているため、AWS側がVT-xを公開していても `emulator -accel-check` の実測を最終判定にする。
- 斉藤さんアプリがEmulator、root、仮想カメラ、screen captureを検知してブロックする可能性がある。
- GPU driver、X/Wayland/headless rendering、v4l2loopback、音声入力はOS/driver/kernel依存が大きい。
- Windows ServerはGUI切り分けには有効だが、ライセンスと運用コストが増える。

## Alternatives Considered

| Option | Pros | Cons | Judgment |
| --- | --- | --- | --- |
| 最初からGPU Linuxで検証する | rendering/FFmpegまで一気に見られる | driver、quota、料金、切り分け点が増える | CPU-only smoke失敗後またはGPU必要性が出た後に採用 |
| 最初からWindows Serverで検証する | Android Studio GUIで見やすい | 高コスト、headless本番方針と乖離、ライセンス考慮が必要 | 初手では不採用 |
| bare metalから始める | KVM/仮想化切り分けに強い | 高コスト、起動枠/availability制約、PoCとして重い | 通常EC2 VMで詰まった場合のみ採用 |
| EC2 Macを使う | macOS固有のGUI検証ができる | Android Runtime HostにmacOS必須要件がない、高コスト | 候補外 |
| ローカル実機/ローカルPCのみで継続 | 低コストで切り分けやすい | Remote Host運用、AWS制約、復旧性が検証できない | Phase 0-2では採用、Phase 3以降でEC2短時間検証へ進む |

## Notes

関連Issue:

- GitHub Issue #17: Android SDK/Emulator 用 EC2 Runtime Host のインスタンス候補と OS 方針を検討する

関連ADR/メモ:

- `adr/0002-youtube-to-saitousan-live-wrapper.md`
- `adr/0006-cloud-cost-phased-poc.md`
- `architecture/aws-youtube-to-saitousan-live.md`
- `research/validation-log.md`

参考:

- AWS EC2 compute optimized instance specs: <https://docs.aws.amazon.com/ec2/latest/instancetypes/co.html>
- AWS EC2 accelerated computing instance specs: <https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html>
- AWS EC2 nested virtualization: <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/amazon-ec2-nested-virtualization.html>
- AWS nested virtualization additional Intel platforms announcement (2026-06-18): <https://aws.amazon.com/about-aws/whats-new/2026/06/nested-virtualization-intel-us-gov-cloud/>
- AWS EC2 instance types by Region: <https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-regions.html>
- Android Emulator acceleration: <https://developer.android.com/studio/run/emulator-acceleration>
