"""
アナログホラー・ニュース自動生成 & Discord投稿スクリプト(GitHub Actions版)
================================================================

前バージョンとの違い:
  - config.json を使わず、環境変数からAPIキー等を読み込む
    (GitHub Actions上では「Secrets」という安全な場所に保管し、それが環境変数として渡される)
  - VOICEVOXは、GitHub Actionsのワークフロー側でDockerコンテナとして立ち上げておく前提
    (このスクリプト自身はDockerを起動しない、すでに動いてるものに接続するだけ)

必要な環境変数:
  GEMINI_API_KEY        Gemini APIキー
  DISCORD_WEBHOOK_URL   DiscordのWebhook URL
  VOICEVOX_SPEAKER_ID   話者ID(省略時は3=ずんだもん)
"""

import json
import os
import random
import sys
from datetime import datetime

import requests


# ------------------------------------------------------------
# 1. Gemini APIでニュース生成
# ------------------------------------------------------------
def generate_news(api_key: str) -> dict:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    mode = random.choice(["real", "real", "fiction"])

    if mode == "real":
        instruction = (
            "実在する都市伝説・怪談・未確認生物(UMA)・SCP財団的なモチーフを1つ選び、"
            "それを『本当にあったニュース速報』風にアレンジして創作してください。"
            "元ネタが分かるくらいの雰囲気は残しつつ、完全な事実ではなく創作として書いてください。"
        )
    else:
        instruction = (
            "完全にオリジナルの、架空のオカルト事件・怪異現象を1つ考えて、"
            "『本当にあったニュース速報』風に創作してください。"
        )

    prompt = f"""
あなたはアナログホラー系のニュース速報を作る作家です。
{instruction}

条件:
- 「見出し」と「本文」に分けて出力する
- 本文は日本語で、合計およそ500文字程度
- 緊急放送・ニュース速報のような硬めの文体
- 読み上げ音声にする前提なので、記号(★や絵文字)は使わない
- 出力は次のJSON形式のみ。説明文は一切付けない:

{{"title": "見出しをここに", "body": "本文をここに"}}
"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {"title": "本日のオカルト速報", "body": text}

    return data


# ------------------------------------------------------------
# 2. VOICEVOXで音声合成(GitHub Actions上のDockerコンテナに接続)
# ------------------------------------------------------------
def synthesize_voice(text: str, speaker_id: int, out_path: str, voicevox_url: str = "http://127.0.0.1:50021"):
    query_res = requests.post(
        f"{voicevox_url}/audio_query",
        params={"text": text, "speaker": speaker_id},
        timeout=30,
    )
    query_res.raise_for_status()
    query_data = query_res.json()

    synth_res = requests.post(
        f"{voicevox_url}/synthesis",
        params={"speaker": speaker_id},
        json=query_data,
        timeout=60,
    )
    synth_res.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(synth_res.content)


# ------------------------------------------------------------
# 3. Discordに投稿
# ------------------------------------------------------------
def post_to_discord(webhook_url: str, title: str, body: str, audio_path: str):
    today = datetime.now().strftime("%Y年%m月%d日")

    message_content = (
        f"📺 **アナログホラー速報 - {today}**\n"
        f"### {title}\n\n"
        f"{body}"
    )

    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        payload = {"content": message_content}
        res = requests.post(webhook_url, data=payload, files=files, timeout=60)
        res.raise_for_status()


# ------------------------------------------------------------
# メイン処理
# ------------------------------------------------------------
def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    speaker_id = int(os.environ.get("VOICEVOX_SPEAKER_ID", "3"))

    if not gemini_api_key or not discord_webhook_url:
        print("エラー: 環境変数 GEMINI_API_KEY と DISCORD_WEBHOOK_URL が必要です。")
        sys.exit(1)

    print("1/3 ニュースを生成中...")
    news = generate_news(gemini_api_key)
    print(f"  見出し: {news['title']}")

    print("2/3 音声を合成中...")
    audio_path = os.path.join(os.path.dirname(__file__), "output.wav")
    synthesize_voice(text=news["body"], speaker_id=speaker_id, out_path=audio_path)

    print("3/3 Discordに投稿中...")
    post_to_discord(
        webhook_url=discord_webhook_url,
        title=news["title"],
        body=news["body"],
        audio_path=audio_path,
    )

    print("完了しました。")


if __name__ == "__main__":
    main()
