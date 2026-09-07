import os
import json
import requests

# ==========================================
# 本番さながらのエントリー通知 テスト送信専用設定
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

def send_line_payload(messages_payload):
    """LINE Messaging API (Push Message) 送信関数"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[エラー] LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が未設定です。")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": messages_payload
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        print("本番想定エントリーテスト通知の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")
        if 'response' in locals() and response.text:
            print(f"エラー詳細: {response.text}")

def test_send_entry_flex():
    """本番さながらのエントリー用Flex Message送信"""
    # 実際のWebサイトから取得される本番同等データ
    match_name = "2026 JAPAN OPEN 第４戦"
    event_date = "2026年10月25日（日）"
    location = "長野県 平谷湖フィッシングスポット"
    accept_period = "2026-09-01～2026-10-24"
    status_change = "募集開始前 ➔ エントリー受付中"
    entry_form_url = "https://forms.gle/T44vL4fd5tSchF8V7"  # 実際のフォームURL

    flex_payload = [{
        "type": "flex",
        "altText": f"🔔 エントリー状況更新: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#0288D1",
                "contents": [
                    {
                        "type": "text",
                        "text": "🔔 エントリー状況更新",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "sm"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": match_name,
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {"type": "text", "text": "状態", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                    {"type": "text", "text": status_change, "weight": "bold", "color": "#E53935", "size": "sm", "flex": 5, "wrap": True}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {"type": "text", "text": "開催日", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                    {"type": "text", "text": event_date, "color": "#666666", "size": "sm", "flex": 5, "wrap": True}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {"type": "text", "text": "会場", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                    {"type": "text", "text": location, "color": "#666666", "size": "sm", "flex": 5, "wrap": True}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {"type": "text", "text": "受付期間", "color": "#aaaaaa", "size": "sm", "flex": 2},
                                    {"type": "text", "text": accept_period, "color": "#666666", "size": "sm", "flex": 5, "wrap": True}
                                ]
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "エントリーフォームを開く",
                            "uri": entry_form_url
                        },
                        "style": "primary",
                        "color": "#00B900",
                        "height": "sm"
                    }
                ]
            }
        }
    }]
    
    send_line_payload(flex_payload)

def main():
    print("【本番想定エントリー通知のテスト送信を開始します】")
    test_send_entry_flex()

if __name__ == "__main__":
    main()
