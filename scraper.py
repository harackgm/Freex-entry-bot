import os
import json
import time
import requests
import urllib.parse

# ==========================================
# テスト送信専用設定（外部アクセス・DB操作なし）
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

# GitHub Rawのロゴ画像URL
LOGO_URL = "https://raw.githubusercontent.com/harackgm/Freex-entry-bot/main/freexlogo.png"

def safe_encode_url(url):
    """日本語ファイル名を含むURLをLINE API規格へ安全にエンコード"""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path)
    return urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        encoded_path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

def send_line_payload(messages_payload):
    """LINE Messaging API (Push Message) 送信"""
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
        print("テスト通知の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")
        if 'response' in locals() and response.text:
            print(f"エラー詳細: {response.text}")

def test_send_entry_flex():
    """エントリー通知（ロゴ＋濃い青デザイン）"""
    match_name = "2026 JAPAN OPEN 第４戦"
    event_date = "2026年10月25日（日）"
    location = "長野県 平谷湖フィッシングスポット"
    accept_period = "2026-09-01～2026-10-24"
    status_change = "募集開始前 ➔ エントリー受付中"
    entry_form_url = "https://forms.gle/T44vL4fd5tSchF8V7"

    flex_payload = [{
        "type": "flex",
        "altText": f"🔔 エントリー状況更新: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "none",
                "backgroundColor": "#0B2545",
                "contents": [
                    {
                        "type": "image",
                        "url": LOGO_URL,
                        "size": "full",
                        "aspectRatio": "20:7",
                        "aspectMode": "cover"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🔔 エントリー状況更新",
                                "weight": "bold",
                                "color": "#FFFFFF",
                                "size": "sm"
                            }
                        ]
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
                        "color": "#0B2545",
                        "height": "sm"
                    }
                ]
            }
        }
    }]
    send_line_payload(flex_payload)

def test_send_result_carousel():
    """大会結果カルーセル通知（各カード最上段ロゴ＋濃い青デザイン）"""
    match_name = "2026 JAPAN OPEN 第１戦_キングフィッシャー"
    match_url = "https://freex-areatrout.com/event/area-trout-championship-2026/result/"
    
    sample_results = [
        {"name": "横井 晃義 選手", "image": "https://freex-areatrout.com/wp-content/uploads/2026/02/横井.jpg"},
        {"name": "佐々木 陽進 選手", "image": "https://freex-areatrout.com/wp-content/uploads/2026/02/佐々木.jpg"},
        {"name": "関口 達也 選手", "image": "https://freex-areatrout.com/wp-content/uploads/2026/02/関口.jpg"}
    ]

    bubbles = []
    for idx, player in enumerate(sample_results):
        rank_label = "🥇 優勝" if idx == 0 else "🥈 第2位" if idx == 1 else "🥉 第3位"
        img_url = safe_encode_url(player["image"])

        bubble = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "none",
                "backgroundColor": "#0B2545",
                "contents": [
                    {
                        "type": "image",
                        "url": LOGO_URL,
                        "size": "full",
                        "aspectRatio": "20:7",
                        "aspectMode": "cover"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "sm",
                        "paddingStart": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🏆 大会結果速報",
                                "weight": "bold",
                                "color": "#FFFFFF",
                                "size": "xs"
                            }
                        ]
                    }
                ]
            },
            "hero": {
                "type": "image",
                "url": img_url,
                "size": "full",
                "aspectRatio": "1:1",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": rank_label, "weight": "bold", "size": "sm", "color": "#1DB446"},
                    {"type": "text", "text": player["name"], "weight": "bold", "size": "lg", "margin": "xs", "wrap": True},
                    {"type": "text", "text": match_name, "size": "xs", "color": "#888888", "margin": "sm", "wrap": True}
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
                            "label": "結果詳細を見る",
                            "uri": match_url
                        },
                        "style": "primary",
                        "color": "#0B2545",
                        "height": "sm"
                    }
                ]
            }
        }
        bubbles.append(bubble)

    flex_payload = [{
        "type": "flex",
        "altText": f"🏆 大会結果更新: {match_name}",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }]
    send_line_payload(flex_payload)

def main():
    print("【ロゴ入り濃紺デザインのテスト送信を開始します】")
    # 1. エントリー通知のテスト送信
    test_send_entry_flex()
    time.sleep(2)
    # 2. 大会結果カルーセル通知のテスト送信
    test_send_result_carousel()

if __name__ == "__main__":
    main()
