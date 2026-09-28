# アナログホラー自動投稿Bot(GitHub Actions版)セットアップ手順

この版は、**あなたのPCを一切起動しなくても、GitHub側のサーバーで毎日自動実行される**構成。

## 全体像

- 毎日決まった時刻に、GitHubが用意する仮想サーバー上でこの処理が動く
- そのサーバー上でVOICEVOXのDockerコンテナが一時的に起動する
- Gemini APIでニュース生成 → VOICEVOXで音声化 → Discordに投稿
- 処理が終わるとサーバーは自動的に片付けられる(何も残らない、課金も発生しない)

## 1. GitHubにリポジトリを作る

1. GitHubにログインし、新しいリポジトリを作成(例: `analog-horror-bot`)
   - **Private(非公開)でも動くが、GitHub Actionsの無料枠がPublicより少ないので、内容的に問題なければPublicがおすすめ**
2. このフォルダの中身(`analog_horror_bot.py` と `.github/workflows/daily-horror-news.yml` を含むフォルダごと)を、そのリポジトリにアップロード
   - Claude Codeに「このフォルダの中身を、新しく作ったGitHubリポジトリ(URLを伝える)にpushして」と頼めば自動でやってくれる

## 2. Gemini APIキーを取得する

1. `https://aistudio.google.com/` にアクセスし、Googleアカウントでログイン
2. 「Get API key」→「Create API key」でキーを発行してコピー

## 3. Discord Webhookを作る

1. 投稿したいチャンネルの設定(歯車アイコン)→「連携サービス」→「ウェブフックを作成」
2. 「ウェブフックURLをコピー」

## 4. GitHubにキーを安全に登録する(Secrets)

**ここが今回の一番大事なポイント。** APIキーやWebhook URLは、コード(config.json等)に直接書かず、GitHubの「Secrets」という暗号化された場所に保存する。

1. GitHubのリポジトリ画面で「Settings」タブを開く
2. 左メニューの「Secrets and variables」→「Actions」
3. 「New repository secret」で、以下の2つを登録:
   - Name: `GEMINI_API_KEY` / Value: (取得したGeminiのキー)
   - Name: `DISCORD_WEBHOOK_URL` / Value: (取得したDiscordのURL)

これで、コード上には一切キーが書かれない状態を保ったまま、実行時だけ安全に読み込まれる。

## 5. 実行時刻を調整する

`.github/workflows/daily-horror-news.yml` の中の、この行:

```
- cron: "0 11 * * *"
```

これは「UTC(世界標準時)の11:00」という意味で、**日本時間だと20:00**にあたる。もし違う時間にしたければ、日本時間から9時間引いた時刻をUTCとして指定する(例: 日本時間の朝7時に投稿したいなら `0 22 * * *` で前日のUTC22:00)。

## 6. 試しに手動実行してみる

1. GitHubのリポジトリで「Actions」タブを開く
2. 「毎日のアナログホラー自動投稿」というワークフローを選ぶ
3. 右側の「Run workflow」ボタンを押す
4. 数分待って、Discordのチャンネルに投稿されるか確認

これで動けば成功。あとは毎日、自動で同じことが繰り返される。

## 注意点

- **リポジトリをPublicにする場合、コードの中身は誰でも見られる**。ただしSecretsの中身(実際のキー)は他人には見えない仕組みなので安全。
- GitHub Actionsの無料枠は、Publicリポジトリなら実質無制限、Privateでも月2,000分まで無料(1日1回・数分の処理なら余裕で収まる)。
- Gemini無料枠にはリクエスト数の上限があるが、1日1回の実行なら問題にならないはず。
