import os
import time
import requests

# ==========================================
# テスト送信専用設定（外部アクセス・DB操作なし）
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

def send_line_message(text, image_url=None):
    """LINE Messaging API を使用してテストメッセージを送る"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("エラー: LINEのトークンまたはユーザーIDが設定されていません。")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    messages = [{"type": "text", "text": text}]
    if image_url:
        messages.append({
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
        })

    data = {
        "to": LINE_USER_ID,
        "messages": messages
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        print("LINEへのテストメッセージ送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")

def main():
    print("【デザイン確認用テスト送信を開始します】")
    
    # 1. エントリー状況更新の通知デザイン確認
    schedule_msg = (
        "🔔 エントリー状況更新\n"
        "2026 JAPAN OPEN  第５戦\n"
        "状態: 募集開始前 ➔ エントリーする\n"
        "https://freex-areatrout.com/event/area-trout-championship-2026/schedule/"
    )
    send_line_message(schedule_msg)
    
    # 連続送信による制限を防ぐための1秒待機
    time.sleep(1)
    
    # 2. 大会結果（写真付き）の通知デザイン確認
    result_msg = (
        "🏆 大会結果が更新されました\n"
        "2026 JAPAN OPEN  第１戦_アングラーズパークキングフィッシャー\n"
        "https://freex-areatrout.com/event/area-trout-championship-2026/result/"
    )
    # 公式サイト掲載のサンプル画像URL
    sample_image = "https://freex-areatrout.com/wp-content/uploads/2026/02/横井.jpg"
    
    send_line_message(result_msg, sample_image)

if __name__ == "__main__":
    main()
