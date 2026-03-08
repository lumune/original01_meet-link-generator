"""
Google Meet Link Generator (Streamlit版)

このアプリは Google Calendar API を使って
ブラウザからボタン1つで Google Meetリンクを生成するツールです。

流れ
1. Google認証を行う
2. ミーティング情報を入力
3. ボタンを押す
4. Google Calendarイベントを作成
5. Meetリンクを表示
"""

import streamlit as st
import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# -----------------------------
# Google Calendar API の権限
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# スクリプトと同じフォルダを取得
SCRIPT_DIR = Path(__file__).resolve().parent

# Google Cloudからダウンロードした認証ファイル
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"

# 認証後に保存されるトークン
TOKEN_FILE = SCRIPT_DIR / "token.json"


# -----------------------------
# Google認証を取得する関数
# -----------------------------
def get_credentials():
    """
    Google APIを使用するための認証処理

    初回：
    ブラウザが開きGoogleログインを求められる

    2回目以降：
    token.json を使用して自動ログイン
    """

    creds = None

    # すでにログイン済みなら token.json を読み込む
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # 認証が無い or 無効なら再ログイン
    if not creds or not creds.valid:

        # 有効期限切れの場合は自動更新
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            # 初回ログイン
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 認証情報を保存
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


# -----------------------------
# Meetイベント作成
# -----------------------------
def create_meet_event(service, summary, start_time, end_time):
    """
    Google Calendarにイベントを作成し
    Google Meetリンクを生成する
    """

    event_body = {
        "summary": summary,  # ミーティング名
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Asia/Tokyo",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Asia/Tokyo",
        },
        "conferenceData": {
            "createRequest": {
                # Meet生成リクエスト
                "requestId": f"meet-{start_time.timestamp():.0f}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created = (
        service.events()
        .insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
        )
        .execute()
    )

    return created


# -----------------------------
# Streamlit UI
# -----------------------------

st.title("📅 Google Meet Link Generator")

st.write(
    "ミーティング情報を入力して **Meetリンクを生成** できます。"
)

# ミーティング名
summary = st.text_input("ミーティング名")

# 日付
date = st.date_input("日付")

# 開始時間
start_time_input = st.time_input("開始時間")

# 終了時間
end_time_input = st.time_input("終了時間")


# Meet生成ボタン
if st.button("Meetを生成"):
    
    # 日付と時間を合体
    start_time = datetime.datetime.combine(date, start_time_input)
    end_time = datetime.datetime.combine(date, end_time_input)

    try:
        # Google認証
        creds = get_credentials()

        # Calendar API接続
        service = build("calendar", "v3", credentials=creds)

        # JSTタイムゾーン設定
        tz = datetime.timezone(datetime.timedelta(hours=9))

        start_time = start_time.replace(tzinfo=tz)
        end_time = end_time.replace(tzinfo=tz)

        # Meet作成
        event = create_meet_event(service, summary, start_time, end_time)

        meet_link = event.get("hangoutLink")

        if meet_link:

            st.success("✅ Meetリンクを作成しました！")

            # Meetリンク表示
            st.write(meet_link)

            # コピーボタン
            st.code(meet_link, language="text")

        else:
            st.error("Meetリンクを取得できませんでした")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
