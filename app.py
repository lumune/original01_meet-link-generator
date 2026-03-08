import streamlit as st
import datetime
from pathlib import Path
import json

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

# 認証情報ファイル（Streamlit Secrets から作成）
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"

# -----------------------------
# credentials.json を Secrets から作成
# -----------------------------
if not CREDENTIALS_FILE.exists():
    creds_dict = {
        "web": {
            "client_id": st.secrets["client_id"],
            "project_id": st.secrets["project_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["client_secret"],
        }
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds_dict, f)

# -----------------------------
# Google認証取得関数
# -----------------------------
def get_credentials():
    creds = None

    # トークン保持
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        # トークン保存
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds

# -----------------------------
# Meetイベント作成
# -----------------------------
def create_meet_event(service, summary, start_time, end_time):
    event_body = {
        "summary": summary,
        "start": {"dateTime": start_time.isoformat(), "timeZone": "Asia/Tokyo"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Tokyo"},
        "conferenceData": {
            "createRequest": {
                "requestId": f"meet-{start_time.timestamp():.0f}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
    created = service.events().insert(
        calendarId="primary", body=event_body, conferenceDataVersion=1
    ).execute()
    return created

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("📅 Google Meet Link Generator")
st.write("ミーティング情報を入力して **Meetリンクを生成** できます。")

summary = st.text_input("ミーティング名")
date = st.date_input("日付")

# -----------------------------
# 自由入力形式の時間選択
# -----------------------------
start_time_input = st.time_input("開始時間")
end_time_input = st.time_input("終了時間")

# Meet生成ボタン
if st.button("Meetを生成"):
    # 日付と時間を合体
    start_time = datetime.datetime.combine(date, start_time_input)
    end_time = datetime.datetime.combine(date, end_time_input)

    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        # JSTタイムゾーン設定
        tz = datetime.timezone(datetime.timedelta(hours=9))
        start_time = start_time.replace(tzinfo=tz)
        end_time = end_time.replace(tzinfo=tz)

        event = create_meet_event(service, summary, start_time, end_time)
        meet_link = event.get("hangoutLink")

        if meet_link:
            st.success("✅ Meetリンクを作成しました！")
            st.code(meet_link, language="text")
        else:
            st.error("Meetリンクを取得できませんでした")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
