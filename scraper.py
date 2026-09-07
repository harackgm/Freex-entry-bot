import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import urllib.parse
from datetime import datetime, timedelta, timezone

# ==========================================
# 設定項目
# ==========================================
# GitHub SecretsからLINE Messaging APIの情報を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
STATE_FILE = "freex_state.json"
MAX_NOTIFY_LIMIT = 5  # 一度に通知する最大件数（これを超えると自動スキップ）

# JSTタイムゾーン（日本時間）
JST = timezone(timedelta(hours=+9), 'JST')

# 監視対象URL
URLS = {
    "schedule": "https://freex-areatrout.com/event/area-trout-championship-2026/schedule/",
    "result": "https://freex-areatrout.com/event/area-trout-championship-2026/result/"
}

# サーバー負荷対策：ブラウザ情報の擬装
HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1"
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def safe_encode_url(url):
    """日本語ファイル名等を含むURLをLINE API規格へ安全にエンコードする"""
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
    """LINE Messaging API (Push Message) の汎用送信関数"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[LOG ONLY - トークン未設定]")
        print(json.dumps(messages_payload, ensure_ascii=False, indent=2))
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
        print("LINE通知の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")
        if 'response' in locals() and response.text:
            print(f"エラー詳細: {response.text}")

def send_text_message(text):
    """通常テキストメッセージの送信"""
    payload = [{"type": "text", "text": text}]
    send_line_payload(payload)

def send_result_carousel(match_name, results, match_url):
    """大会結果をカルーセル形式（Flex Message）で送信"""
    bubbles = []
    # LINE Carousel上限（最大10カード）に対応
    for idx, player in enumerate(results[:10]):
        rank_label = "🥇 優勝" if idx == 0 else "🥈 第2位" if idx == 1 else "🥉 第3位" if idx == 2 else f"第{idx+1}位"
        img_url = safe_encode_url(player.get("image", ""))
        
        if not img_url:
            img_url = "https://freex-areatrout.com/wp-content/themes/theme/ogp_img.jpg"

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
                    {"type": "text", "text": player.get("name", "選手名未設定"), "weight": "bold", "size": "lg", "margin": "xs", "wrap": True},
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
                            "label": "大会結果を見る",
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

    if not bubbles:
        send_text_message(f"🏆 大会結果が更新されました\n{match_name}\n{match_url}")
        return

    flex_payload = [{
        "type": "flex",
        "altText": f"🏆 大会結果更新: {match_name}",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }]
    send_line_payload(flex_payload)

def load_state():
    """過去のデータを読み込む"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"schedule": {}, "result": {}}

def save_state(state):
    """最新のデータを保存する"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def fetch_html(url):
    """HTMLを取得（ゆらぎ待機・短時間タイムアウト）"""
    headers = HEADERS_BASE.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    
    time.sleep(random.uniform(3.0, 6.0))
    
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"取得エラー ({url}): {e}")
        return None

def scrape_schedule(html):
    """スケジュール（エントリー状況）の解析"""
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    table = soup.find("table", class_="schedules-table")
    if not table:
        return data

    rows = table.find("tbody").find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            match_name = cols[0].get_text(strip=True)
            date_info = cols[1].get_text(strip=True)
            status_badge = cols[4].find("span", class_="status-badge")
            status_text = status_badge.get_text(strip=True) if status_badge else "ステータス不明"
            
            data[match_name] = {
                "date": date_info,
                "status": status_text
            }
    return data

def scrape_result(html):
    """大会結果の解析"""
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    
    titles = soup.find_all("h3", class_="result-item-title")
    for title in titles:
        match_name = title.get_text(strip=True)
        results = []
        
        result_list = title.find_next_sibling("div", class_="result-list")
        if result_list:
            items = result_list.find_all("div", class_="result-item")
            for item in items:
                img_tag = item.find("img")
                name_tag = item.find("h3")
                if img_tag and name_tag:
                    img_url = img_tag.get("src")
                    player_name = name_tag.get_text(strip=True)
                    results.append({"name": player_name, "image": img_url})
        
        data[match_name] = results
    return data

def main():
    print(f"[{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')}] 監視を開始します。")
    old_state = load_state()
    new_state = {"schedule": {}, "result": {}}
    notifications = []

    # 1. スケジュールの監視
    html_schedule = fetch_html(URLS["schedule"])
    if html_schedule:
        new_state["schedule"] = scrape_schedule(html_schedule)
        
        for match, info in new_state["schedule"].items():
            old_info = old_state["schedule"].get(match)
            if not old_info:
                notifications.append({
                    "type": "schedule",
                    "text": f"🆕 新規大会追加\n{match}\n開催日: {info['date']}\n状態: {info['status']}\n{URLS['schedule']}"
                })
            elif old_info["status"] != info["status"]:
                notifications.append({
                    "type": "schedule",
                    "text": f"🔔 エントリー状況更新\n{match}\n状態: {old_info['status']} ➔ {info['status']}\n{URLS['schedule']}"
                })
    else:
        print("⚠️ スケジュールの取得に失敗したため、過去データを維持します。")
        new_state["schedule"] = old_state.get("schedule", {})

    # 2. 大会結果の監視
    html_result = fetch_html(URLS["result"])
    if html_result:
        new_state["result"] = scrape_result(html_result)
        
        for match, results in new_state["result"].items():
            old_results = old_state["result"].get(match, [])
            if len(results) > len(old_results):
                notifications.append({
                    "type": "result_carousel",
                    "match_name": match,
                    "results": results,
                    "url": URLS["result"]
                })
    else:
        print("⚠️ 大会結果の取得に失敗したため、過去データを維持します。")
        new_state["result"] = old_state.get("result", {})

    # ==========================================
    # 大量通知ストッパー（MAX_LIMIT制御）
    # ==========================================
    if len(notifications) > MAX_NOTIFY_LIMIT:
        print(f"⚠️ 検知数が {len(notifications)} 件となり上限({MAX_NOTIFY_LIMIT}件)を超えました。LINE送信を自動スキップしDBのみ更新します。")
    else:
        for item in notifications:
            if item["type"] == "schedule":
                send_text_message(item["text"])
            elif item["type"] == "result_carousel":
                send_result_carousel(item["match_name"], item["results"], item["url"])
            time.sleep(2)

    # 状態の保存
    save_state(new_state)
    print("監視処理が完了しました。")

if __name__ == "__main__":
    main()
