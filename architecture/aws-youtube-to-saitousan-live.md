# AWS Architecture: YouTube to Saitousan LIVE Wrapper

ADR-0002の構想をAWS上で実現する場合の初期アーキテクチャ案。

## System Diagram

```mermaid
flowchart LR
  yt[YouTube Live<br>or Test Video] --> fetcher[Stream Fetch / Transcode Worker<br>EC2 or ECS Task]
  fetcher --> vcamera[Virtual Camera / Media Bridge<br>FFmpeg + v4l2loopback or equivalent]
  vcamera --> android[Android Runtime Host<br>EC2 GPU / Bare Metal Candidate]
  android --> saitou[斉藤さん App<br>Android Emulator or Device]
  saitou --> live[斉藤さんLIVE]

  admin[Next.js Admin UI<br>Amplify or ECS] --> api[Control API<br>API Gateway + Lambda or ECS]
  api --> appium[Appium Controller<br>EC2 or ECS Task]
  appium --> android

  api --> jobs[Job Queue<br>SQS]
  jobs --> fetcher

  android --> logs[Logs / Screenshots<br>CloudWatch Logs + S3]
  fetcher --> logs
  appium --> logs
  api --> logs

  secrets[Secrets Manager<br>Accounts / Tokens / Stream Keys] --> api
  secrets --> appium
  secrets --> fetcher
```

## AWS Component View

```mermaid
flowchart TB
  subgraph public[Public Access]
    user[Operator Browser]
    youtube[YouTube Live]
  end

  subgraph edge[AWS Edge / Web]
    cf[CloudFront]
    web[Next.js Admin UI]
  end

  subgraph control[Control Plane]
    auth[Cognito or Basic Auth]
    api[Control API]
    sqs[SQS Job Queue]
    secrets[Secrets Manager]
  end

  subgraph runtime[Runtime Plane]
    appium[Appium Controller]
    worker[Stream Fetch / FFmpeg Worker]
    host[Android Runtime Host]
    emulator[Android Emulator / Device]
    saitosan[斉藤さん App]
  end

  subgraph observability[Observability]
    cw[CloudWatch Logs / Metrics]
    s3[S3 Screenshots / Artifacts]
    alarm[CloudWatch Alarms]
  end

  user --> cf --> web
  web --> auth
  web --> api
  api --> sqs
  api --> secrets
  sqs --> appium
  sqs --> worker
  youtube --> worker
  worker --> host
  appium --> emulator
  host --> emulator --> saitosan
  saitosan --> saitousanLive[斉藤さんLIVE]

  api --> cw
  appium --> cw
  worker --> cw
  host --> cw
  appium --> s3
  host --> s3
  cw --> alarm
```

## Main Data Flows

| Flow | Path | Notes |
| --- | --- | --- |
| 配信映像入力 | YouTube Live -> Stream Worker -> Virtual Camera -> Android Runtime | 最初はYouTubeではなく固定動画で検証してよい |
| アプリ操作 | Admin UI -> Control API -> SQS -> Appium -> Android App | 配信開始/停止、ログイン確認、画面遷移を自動化 |
| 状態監視 | Runtime/Appium/Worker -> CloudWatch/S3 -> Admin UI | スクリーンショット、ログ、異常状態を保存 |
| 秘密情報 | Secrets Manager -> Control API/Appium/Worker | YouTube情報、アプリ認証情報、配信キーを直接コードに置かない |

## Suggested Phase 0/1 AWS Boundary

最初から全AWS化しない。Phase 0/1では、AWS構成図のうち次だけを検証対象にする。

- Android Runtime Host
- Appium Controller
- Stream Fetch / FFmpeg Worker
- Logs / Screenshots

Next.js Admin UI、API Gateway、SQS、Secrets Managerは、カメラ入力差し替えが成立してから導入する。

## Runtime Host Candidates

| Candidate | Pros | Cons | Use |
| --- | --- | --- | --- |
| EC2 Linux + Android Emulator | AWS内で完結しやすい | GPU/仮想化/カメラ入力が難しい | 第一候補だが要検証 |
| EC2 Windows + Android Emulator | GUI/デバッグしやすい | コストが高くなりやすい | 初期検証向き |
| EC2 Mac | Android Studio系の検証がしやすい可能性 | 高コスト、調達制約 | 必要時のみ |
| ローカル実機 + AWS Control Plane | アプリ互換性が高い | 完全クラウド化ではない | Emulatorが失敗した場合の代替 |

## Open Architecture Questions

- EC2上のAndroid Emulatorで斉藤さんアプリが起動するか。
- EC2上で仮想カメラ入力をAndroidアプリに渡せるか。
- 音声入力をどう扱うか。映像より難しい可能性がある。
- Appiumと配信ワーカーを同一ホストに置くか、分離するか。
- Runtime Hostを常時起動にするか、配信時だけ起動するか。
- CloudWatch/S3へ保存するスクリーンショットに個人情報が含まれないようにできるか。
