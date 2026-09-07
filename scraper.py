import os
import json
import requests
import urllib.parse

# ==========================================
# カルーセル表示確認用テストコード（DB操作・サイト負荷ゼロ）
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

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
        print("カルーセルテスト通知の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")
        if 'response' in locals() and response.text:
            print(f"エラー詳細: {response.text}")

def test_send_carousel():
    """大会結果のカルーセル（Flex Message）テスト送信"""
    match_name = "2026 JAPAN OPEN 第１戦_キングフィッシャー"
    match_url = "https://freex-areatrout.com/event/area-trout-championship-2026/result/"
    
    # 実際の大会結果サンプルデータ（1位〜3位）
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
                        "color": "#00B900",
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
    print("【カルーセル表示のテスト送信を開始します】")
    test_send_carousel()

if __name__ == "__main__":
    main()
