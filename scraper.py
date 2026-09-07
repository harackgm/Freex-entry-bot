import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import urllib.parse
import re
from datetime import datetime, timedelta, timezone

# ==========================================
# 設定項目
# ==========================================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")
STATE_FILE = "freex_state.json"
MAX_NOTIFY_LIMIT = 5  # 大量誤通知ストッパー

LOGO_URL = "https://raw.githubusercontent.com/harackgm/Freex-entry-bot/main/freexlogo.png"
FALLBACK_IMG = "https://freex-areatrout.com/wp-content/themes/theme/ogp_img.jpg"
JST = timezone(timedelta(hours=+9), 'JST')

URLS = {
    "schedule": "https://freex-areatrout.com/event/area-trout-championship-2026/schedule/",
    "result": "https://freex-areatrout.com/event/area-trout-championship-2026/result/"
}

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
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
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

def safe_encode_url(url):
    if not url: return ""
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, encoded_path, parsed.params, parsed.query, parsed.fragment))

def send_line_payload(messages_payload):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[LOG ONLY - トークン未設定]")
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
        print("LINE通知の送信に成功しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")

def send_entry_flex(match_name, info, timing_msg="🔔 エントリー状況更新"):
    status_text = info.get("status", "ステータス更新")
    form_url = info.get("form_url", URLS["schedule"])
    
    flex_payload = [{
        "type": "flex",
        "altText": f"{timing_msg}: {match_name}",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545",
                "contents": [
                    {"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"},
                    {
                        "type": "box", "layout": "vertical", "paddingAll": "md",
                        "contents": [{"type": "text", "text": timing_msg, "weight": "bold", "color": "#FFFFFF", "size": "sm"}]
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
            "footer": {
                "type": "box", "layout": "vertical",
                "contents": [{"type": "button", "action": {"type": "uri", "label": "エントリーページを開く", "uri": form_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]
            }
        }
    }]
    send_line_payload(flex_payload)

def send_result_carousel(match_name, results, match_url, timing_msg="🏆 大会結果速報"):
    bubbles = []
    for idx, player in enumerate(results[:10]):
        rank_label = "🥇 優勝" if idx == 0 else "🥈 第2位" if idx == 1 else "🥉 第3位" if idx == 2 else f"第{idx+1}位"
        img_url = safe_encode_url(player.get("image", ""))
        if not img_url: img_url = FALLBACK_IMG

        bubble = {
            "type": "bubble",
            "header": {
                "type": "box", "layout": "vertical", "paddingAll": "none", "backgroundColor": "#0B2545",
                "contents": [
                    {"type": "image", "url": LOGO_URL, "size": "full", "aspectRatio": "20:7", "aspectMode": "cover"},
                    {"type": "box", "layout": "vertical", "paddingAll": "sm", "paddingStart": "md",
                     "contents": [{"type": "text", "text": timing_msg, "weight": "bold", "color": "#FFFFFF", "size": "xs"}]}
                ]
            },
            "hero": {"type": "image", "url": img_url, "size": "full", "aspectRatio": "1:1", "aspectMode": "cover"},
            "body": {
                "type": "box", "layout": "vertical",
                "contents": [
                    {"type": "text", "text": rank_label, "weight": "bold", "size": "sm", "color": "#1DB446"},
                    {"type": "text", "text": player.get("name", "選手名未設定"), "weight": "bold", "size": "lg", "margin": "xs", "wrap": True},
                    {"type": "text", "text": match_name, "size": "xs", "color": "#888888", "margin": "sm", "wrap": True}
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "contents": [{"type": "button", "action": {"type": "uri", "label": "結果詳細を見る", "uri": match_url}, "style": "primary", "color": "#0B2545", "height": "sm"}]
            }
        }
        bubbles.append(bubble)
    if bubbles:
        send_line_payload([{"type": "flex", "altText": f"{timing_msg}: {match_name}", "contents": {"type": "carousel", "contents": bubbles}}])

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"schedule": {}, "result": {}}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=4)

def fetch_html(url):
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

def parse_entry_start(accept_period):
    if not accept_period: return None
    match = re.search(r'(\d{4}-\d{2}-\d{2})', accept_period)
    if match:
        try:
            dt = datetime.strptime(f"{match.group(1)} 19:00:00", "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=JST)
        except ValueError:
            pass
    return None

def scrape_schedule(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    table = soup.find("table", class_="schedules-table")
    if not table: return data
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 5:
            match_name = cols[0].get_text(strip=True)
            accept_col = cols[4]
            status_badge = accept_col.find("span", class_="status-badge")
            link_tag = accept_col.find("a")
            data[match_name] = {
                "date": cols[1].get_text(strip=True),
                "location": cols[2].get_text(strip=True),
                "accept_period": accept_col.get_text(strip=True).split('\n')[0].strip(),
                "status": status_badge.get_text(strip=True) if status_badge else "ステータス不明",
                "form_url": link_tag.get("href") if link_tag else URLS["schedule"]
            }
    return data

def scrape_result(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    for title in soup.find_all("h3", class_="result-item-title"):
        match_name = title.get_text(strip=True)
        results = []
        result_list = title.find_next_sibling("div", class_="result-list")
        if result_list:
            for item in result_list.find_all("div", class_="result-item"):
                img = item.find("img")
                name = item.find("h3")
                if img and name:
                    results.append({"name": name.get_text(strip=True), "image": img.get("src")})
        data[match_name] = results
    return data

def has_valid_photo(players):
    """写真が正しく掲載されているかを判定（ダミー画像を排除）"""
    if not players: return False
    for p in players:
        img_url = p.get("image", "")
        if img_url and "ogp_img" not in img_url and "no_image" not in img_url:
            return True
    return False

def main():
    now = datetime.now(JST)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 監視を開始します。")
    old_state = load_state()
    new_state = {"schedule": {}, "result": {}}
    notifications = []

    # ==========================================
    # 1. スケジュール（エントリー）の監視
    # ==========================================
    html_schedule = fetch_html(URLS["schedule"])
    if html_schedule:
        new_state["schedule"] = scrape_schedule(html_schedule)
        for match, info in new_state["schedule"].items():
            old_info = old_state["schedule"].get(match, {})
            entry_start_dt = parse_entry_start(info.get("accept_period", ""))
            
            if "notified" not in old_info:
                if entry_start_dt:
                    notified_flags = {
                        "24h": now >= entry_start_dt - timedelta(hours=24),
                        "15m": now >= entry_start_dt - timedelta(minutes=15),
                        "0m": now >= entry_start_dt,
                        "next_m": now >= entry_start_dt + timedelta(hours=14)
                    }
                else:
                    notified_flags = {"24h": True, "15m": True, "0m": True, "next_m": True}
            else:
                notified_flags = old_info["notified"]

            if entry_start_dt:
                if now >= entry_start_dt - timedelta(hours=24) and not notified_flags["24h"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【予告】エントリー開始24時間前"})
                    notified_flags["24h"] = True
                if now >= entry_start_dt - timedelta(minutes=15) and not notified_flags["15m"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【直前】エントリー開始15分前"})
                    notified_flags["15m"] = True
                if now >= entry_start_dt and not notified_flags["0m"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【開始】エントリー受付開始"})
                    notified_flags["0m"] = True
                if now >= entry_start_dt + timedelta(hours=14) and not notified_flags["next_m"]:
                    notifications.append({"type": "schedule", "match_name": match, "info": info, "timing_msg": "🔔 【確認】エントリーはお済みですか？"})
                    notified_flags["next_m"] = True
            
            info["notified"] = notified_flags
    else:
        new_state["schedule"] = old_state.get("schedule", {})

    # ==========================================
    # 2. 大会結果の監視（48時間写真待機・再通知制御）
    # ==========================================
    html_result = fetch_html(URLS["result"])
    if html_result:
        scraped_results = scrape_result(html_result)
        
        # 古いデータ構造からの安全移行（過去分はすべて写真通知済み扱いとする）
        for match, data in old_state.get("result", {}).items():
            if isinstance(data, list):
                old_state["result"][match] = {"players": data, "first_detected": now.isoformat(), "photo_notified": True}
            elif isinstance(data, dict) and "photo_notified" not in data:
                data["photo_notified"] = True
                old_state["result"][match] = data

        for match, current_players in scraped_results.items():
            old_match_data = old_state["result"].get(match, {})
            old_players = old_match_data.get("players", [])
            
            first_detected = old_match_data.get("first_detected", now.isoformat())
            photo_notified = old_match_data.get("photo_notified", True)

            # 選手が追加されたか（新規結果または入賞者追加）
            is_new_or_updated = len(current_players) > len(old_players)
            has_photo = has_valid_photo(current_players)

            should_notify = False
            timing_msg = "🏆 大会結果速報"

            if is_new_or_updated:
                # 新規検知またはデータ追加時は即時通知
                should_notify = True
                first_detected = now.isoformat()
                photo_notified = has_photo  # 写真があればTrue、なければFalse(待機開始)
            
            elif not photo_notified:
                # 既に通知済みだが写真待ちの場合
                first_det_dt = datetime.fromisoformat(first_detected)
                if now < first_det_dt + timedelta(hours=48):
                    if has_photo:
                        # 48時間以内に写真が追加されたため再通知
                        should_notify = True
                        photo_notified = True
                        timing_msg = "📸 写真が追加されました"
                else:
                    # 48時間経過したため写真待機を諦める（タイムアウト）
                    print(f"[{match}] 48時間経過したため、写真の待機を終了します。")
                    photo_notified = True

            if should_notify:
                notifications.append({"type": "result_carousel", "match_name": match, "results": current_players, "url": URLS["result"], "timing_msg": timing_msg})

            new_state["result"][match] = {
                "players": current_players,
                "first_detected": first_detected,
                "photo_notified": photo_notified
            }
    else:
        new_state["result"] = old_state.get("result", {})

    # ==========================================
    # 大量通知ストッパー（MAX_LIMIT制御）
    # ==========================================
    if len(notifications) > MAX_NOTIFY_LIMIT:
        print(f"⚠️ 検知数が {len(notifications)} 件となり上限を超えました。LINE送信をスキップします。")
    else:
        for item in notifications:
            if item["type"] == "schedule":
                send_entry_flex(item["match_name"], item["info"], item["timing_msg"])
            elif item["type"] == "result_carousel":
                send_result_carousel(item["match_name"], item["results"], item["url"], item["timing_msg"])
            time.sleep(2)

    save_state(new_state)
    print("監視処理が完了しました。")

if __name__ == "__main__":
    main()
