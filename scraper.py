import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from datetime import datetime, timedelta, timezone

# ==========================================
# 設定項目
# ==========================================
# GitHub SecretsからLINE Messaging APIの情報を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
STATE_FILE = "freex_state.json"
MAX_NOTIFY_LIMIT = 5  # 一度に通知する最大件数（これを超えると通知スキップ）

# JSTタイムゾーン
JST = timezone(timedelta(hours=+9), 'JST')

# 監視対象URL
URLS = {
    "schedule": "https://freex-areatrout.com/event/area-trout-championship-2026/schedule/",
    "result": "https://freex-areatrout.com/event/area-trout-championship-2026/result/"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def send_line_message(text, image_url=None):
    """LINE Messaging API (Push Message) を使用して通知を送る"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print(f"[TEST NOTIFY]\n{text}")
        if image_url:
            print(f"[IMAGE URL] {image_url}")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    # メッセージオブジェクトの構築
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
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"LINE通知エラー: {e}")
        if response.text:
            print(f"エラー詳細: {response.text}")

def load_state():
    """過去のデータを読み込む"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"schedule": {}, "result": {}}

def save_state(state):
    """最新のデータを保存する"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def fetch_html(url):
    """HTMLを取得し、ゆらぎのスリープを入れる"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        time.sleep(random.uniform(2.0, 5.0))  # サーバー負荷軽減のゆらぎ
        return response.text
    except Exception as e:
        print(f"取得エラー ({url}): {e}")
        return None

def scrape_schedule(html):
    """スケジュール（エントリー状況）のスクレイピング"""
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
    """大会結果のスクレイピング"""
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
                notifications.append({"msg": f"🆕 新規大会追加\n{match}\n開催日: {info['date']}\n状態: {info['status']}\n{URLS['schedule']}", "img": None})
            elif old_info["status"] != info["status"]:
                notifications.append({"msg": f"🔔 エントリー状況更新\n{match}\n状態: {old_info['status']} ➔ {info['status']}\n{URLS['schedule']}", "img": None})

    # 2. 大会結果の監視
    html_result = fetch_html(URLS["result"])
    if html_result:
        new_state["result"] = scrape_result(html_result)
        
        for match, results in new_state["result"].items():
            old_results = old_state["result"].get(match, [])
            if len(results) > len(old_results):
                msg = f"🏆 大会結果が更新されました\n{match}\n{URLS['result']}"
                img_url = results[0]["image"] if results else None
                notifications.append({"msg": msg, "img": img_url})

    # ==========================================
    # 大量通知ストッパー（MAX_LIMIT制御）
    # ==========================================
    if len(notifications) > MAX_NOTIFY_LIMIT:
        print(f"⚠️ 検知数が {len(notifications)} 件となり上限({MAX_NOTIFY_LIMIT}件)を超えました。通知をスキップしてDBのみ更新します。")
    else:
        for notify in notifications:
            send_line_message(notify["msg"], notify["img"])
            time.sleep(1)  # 通知間のゆらぎ

    # 状態の保存
    save_state(new_state)
    print("監視処理が完了しました。")

if __name__ == "__main__":
    main()
