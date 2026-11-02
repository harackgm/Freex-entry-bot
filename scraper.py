import os
import requests

# ==========================================
# デザイン確認テスト専用設定
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
LOGO_URL = "https://raw.githubusercontent.com/harackgm/Freex-entry-bot/main/freexlogo.png"

def send_line_payload(messages_payload):
    """LINE Messaging API (Push Message) - 管理者へ直接送信"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[エラー] トークンまたはUSER_IDが未設定です")
        return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {"to": LINE_USER_ID, "messages": messages_payload}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        print("テスト通知の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")

def send_entry_flex(match_name, info, timing_msg, bg_color, text_color):
    """新デザイン版のFlex Message"""
    status_text = info.get("status", "エントリーする")
    form_url = info.get("form_url", "https://freex-areatrout.com/event/area-trout-championship-2026/schedule/")
    
    flex_payload = [{
        "type": "flex", "altText": f"{timing_msg}: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545",
                "contents": [
                    # 1. ロゴ画像
                    {"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"},
                    # 2. 新設：色付きの帯と中央寄せの大きな文字
                    {
                        "type": "box", "layout": "vertical", "paddingAll": "md", "backgroundColor": bg_color,
                        "contents": [
                            {"type": "text", "text": timing_msg, "weight": "bold", "color": text_color, "size": "md", "align": "center"}
                        ]
                    }
                ]
            },
            "body": {
                "type": "box", "layout": "vertical",
                "contents": [
                    {"type": "text", "text": match_name, "weight": "bold", "size": "xl", "wrap": True},
                    {
                        "type": "box", "layout": "vertical", "margin": "lg", "spacing": "sm",
                        "contents": [
                            {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "状態", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": status_text, "weight": "bold", "color": "#E53935", "size": "sm", "flex": 5, "wrap": True}]},
                            {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "開催日", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": info.get("date", "-"), "color": "#666666", "size": "sm", "flex": 5, "wrap": True}]},
                            {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "会場", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": info.get("location", "-"), "color": "#666666", "size": "sm", "flex": 5, "wrap": True}]},
                            {"type": "box", "layout": "baseline", "contents": [{"type": "text", "text": "受付期間", "color": "#aaaaaa", "size": "sm", "flex": 2}, {"type": "text", "text": info.get("accept_period", "-"), "color": "#666666", "size": "sm", "flex": 5, "wrap": True}]}
                        ]
                    }
                ]
            },
            "footer": {"type": "box", "layout": "vertical", "contents": [{"type": "button", "action": {"type": "uri", "label": "エントリーページを開く", "uri": form_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]}
        }
    }]
    send_line_payload(flex_payload)

def main():
    print("【デザイン確認用】4種類のテスト通知を送信します...")
    
    # テスト用のダミーデータ
    dummy_match = "2026 JAPAN OPEN 第６戦"
    dummy_info = {
        "date": "2026年12月06日（日）",
        "location": "静岡県 アルクスポンド焼津",
        "accept_period": "2026-11-01～2026-12-05エントリーする",
        "status": "エントリーする",
        "form_url": "https://freex-areatrout.com/"
    }

    # 1. 24時間前（黄帯・黒文字）
    send_entry_flex(dummy_match, dummy_info, "⏳ 【予告】エントリー開始24時間前", "#FBC02D", "#000000")
    
    # 2. 15分前（オレンジ帯・白文字）
    send_entry_flex(dummy_match, dummy_info, "⚠️ 【直前】エントリー開始15分前", "#F57C00", "#FFFFFF")
    
    # 3. 受付開始（赤帯・白文字）
    send_entry_flex(dummy_match, dummy_info, "🔥 【開始】エントリー受付開始", "#D32F2F", "#FFFFFF")
    
    # 4. 事後確認（緑帯・白文字）
    send_entry_flex(dummy_match, dummy_info, "✅ 【確認】エントリーはお済みですか？", "#388E3C", "#FFFFFF")
    
    print("テスト送信が完了しました。LINEをご確認ください。")

if __name__ == "__main__":
    main()
