import logging
import requests
import json
import urllib.parse
import traceback
from bs4 import BeautifulSoup
import re
import random
import os
import asyncio
from typing import Dict, List, Tuple, Any
#import main

logger = logging.getLogger

def run(data):
    """플레이스봇 처리"""
    try:
        allow_chat_list = ["18455306023804070"]
        chat_id = data["json"]["chat_id"]
        if chat_id not in allow_chat_list:
            return None
        
        msg = data["json"]["message"].strip()

        if msg.startswith("/지도"):
            send_msg = get_naver_map_keyword(data)
            if send_msg:
                result = {
                    "room": chat_id,
                    "type": "text",
                    "data": send_msg
                }
                #main.send_message(result)
                return result
        
        return None
    except Exception as e:
        logger.error(traceback.format_exc())
        return False
    


def get_naver_map_keyword(data):
    room = data["room"]
    sender = data["sender"]
    msg = data["msg"]
    keyword = msg.replace("/지도", "").strip()
    if not keyword:
        return f"{sender}님 /지도 뒤에 키워드를 입력해주세요."
    
    
    encode_keyword = urllib.parse.quote(keyword)
    
    result = get_naver_map_api(keyword)
    #save_count_list = get_save_count_list(keyword)

    if "result" not in result:
        return f"{sender}님 {keyword} 지도 검색결과가 없어요ㅠㅠ"
    elif "place" not in result["result"]:
        return f"{sender}님 {keyword} 지도 검색결과가 없어요ㅠㅜ"
    elif not result["result"]["place"]:
        return f"{sender}님 {keyword} 지도 검색결과가 없어요ㅜㅠ"
    elif "list" not in result["result"]["place"]:
        return f"{sender}님 {keyword} 지도 검색결과가 없어요ㅜㅜ"

    items = result["result"]["place"]["list"]
    if len(items) == 0:
        send_msg = f"{sender}님 {keyword} 지도 검색결과가 없어요ㅠ.ㅠ"

    elif items[0]["name"] == keyword or len(items) == 1:
        item = items[0]
        send_msg = f"{keyword} 지도 검색 결과🤩"
        send_msg += f"\n✅ {item['name']}"
        if "bizhourInfo" in item:
            send_msg += f"\n⏰ {item['bizhourInfo']}"
        if "address" in item:
            send_msg += f"\n📍 {item['address']}"
        if "telDisplay" in item:
            send_msg += f"\n☎️ {item['telDisplay']}"
        if "reviewCount" in item:
            send_msg += f"\n💞리뷰 {item['reviewCount']} 개"
        if "menuInfo" in item:
            send_msg += f"\n🍛 {item['menuInfo']}"
        if "microReview" in item:
            if item["microReview"]:
                send_msg += "\n😃".join(item["microReview"])
        send_msg += f"\nhttps://map.naver.com/v5/search/{encode_keyword}"

    else:
        send_msg = f"🗺️{keyword} Top 20😎"
        
        for i, item in enumerate(items[:20]):
            rank = item["rank"]
            name = item["name"]
            send_msg += f"\n\n{rank}. {name}"
            
            if "placeReviewCount" in item:
                if item["placeReviewCount"]:
                    send_msg += f"\n💬방문자리뷰 {item['placeReviewCount']:,}"

            if "category" in item:
                # category가 list면 join해서 문자열로 변환
                if type(item["category"]) == list:
                    item["category"] = ", ".join(item["category"])
                if item["category"]:
                    send_msg += f"\n🏢{item['category']}"
            
            if i < 5:
                keyword_list = get_keyword_list(item["id"])
                if keyword_list:
                    send_msg += "\n💬대표키워드"
                    send_msg += f"\n{','.join(keyword_list)}"

            if "address" in item:
                send_msg += f"\n📍{item['address']}"

            if "telDisplay" in item:
                if item["telDisplay"]:
                    send_msg += f"\n☎️{item['telDisplay']}"

            if "businessStatus" in item:
                if "status" in item["businessStatus"]:
                    if "detailInfo" in item["businessStatus"]["status"]:
                        if item["businessStatus"]["status"]["detailInfo"]:
                            send_msg += f"\n⏰{item['businessStatus']['status']['detailInfo']}"
            
            if "menuInfo" in item:
                if item["menuInfo"]:
                    send_msg += f"\n📋{item['menuInfo']}"
            
            send_msg += f"\nhttps://map.naver.com/p/entry/place/{item['id']}"
            
            # if "homePage" in item:
            #     if item["homePage"]:
            #         send_msg += f"\n🌐홈페이지\n{item['homePage']}"

            # if "naverBookingUrl" in item:
            #     if item["naverBookingUrl"]:
            #         send_msg += f"\n🌐네이버예약\n{item['naverBookingUrl']}"            

            if i == 0:
                send_msg += '\n[열어서 모두 보기] ' + '\u200B'*500
    return send_msg

    
def get_keyword_list(place_id):
    try:
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': 'https://map.naver.com',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'iframe',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        }

        url = f'https://pcmap.place.naver.com/place/{place_id}/home'
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'

        text = response.text
        text = text.split('"keywordList":')[1]
        text = text.split(']')[0]
        text = text + ']'

        result = json.loads(text)
        
        return result
    except Exception as e:
        print(e)
        return None

"""
def get_save_count_list(keyword):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ko,en-US;q=0.9,en;q=0.8,ar;q=0.7',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }

    params = {
        'query': keyword,
    }

    response = requests.get('https://pcmap.place.naver.com/restaurant/list', params=params, headers=headers)
    response_decode = response.content.decode('utf-8')
    soup = BeautifulSoup(response_decode, 'html.parser')

    script_tag = soup.find('script', string=re.compile(r'window\.__APOLLO_STATE__\s*='))

    if not script_tag:
        print("❌ 못 찾음")
        return []
    
    # 2. 텍스트만 추출
    text = script_tag.string

    # 3. JSON 텍스트만 남기기
    raw_json = text.split('window.__APOLLO_STATE__ = ')[1].rstrip(';')

    # 4. split으로 나누기
    chunks = raw_json.split('"RestaurantListSummary:')
    
    result = []
    for chunk in chunks[1:]:  # 첫 번째는 쓰레기
        full_chunk = '"RestaurantListSummary:' + chunk
        # 중괄호 세는 방식으로 JSON 끝 찾기
        brace_count = 0
        json_part = ""
        for char in full_chunk:
            json_part += char
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    break
        try:
            parsed = json.loads('{' + json_part + '}')
            result.append(parsed)
            for i, r in enumerate(result):
                if i >= 20:
                    break
                for item in r.items():
                    save_count_list = item['saveCount']
        except:
            continue

    return save_count_list
"""

def get_naver_map_api(keyword):
    cookies = {
        'NACT': '1',
        'NNB': 'HVAVPHBWJPRGM',
        'ASID': 'da9b849000000192dd21a77e00000065',
        'nstore_session': 'f3tE3l7h3IGTb8raSdi+PzFN',
        '_tt_enable_cookie': '1',
        '_ttp': 'vLJLZCmexorHGtGiUsXBjrsTXIs.tt.1',
        'ba.uuid': '09b1a6c4-4268-426d-abe9-02b3d238211f',
        '_ga_J5CZVNJNQP': 'GS1.1.1735519248.1.0.1735519248.0.0.0',
        '_ga_451MFZ9CFM': 'GS1.1.1736297197.1.0.1736297199.0.0.0',
        'BNB_FINANCE_HOME_TOOLTIP_MYASSET': 'true',
        '_ga_6Z6DP60WFK': 'GS1.2.1741078123.1.0.1741078123.60.0.0',
        '_ga': 'GA1.1.1054701045.1735519249',
        '_ga_RCM29786SD': 'GS1.1.1742872121.1.0.1742872121.0.0.0',
        'nstore_pagesession': 'juUmCdqWadk3EssMNKG-087773',
        'NAC': 'VBXyBgwyb4nT',
        'NDV_SHARE': 'j23OxEg7JY62FvLO68P3fPxcV1oqlfRqJRpA10qVqJ8TkGHnW90CivnnMuMiqwzGVJOuKNEvjogE6C6vMk0uRC8jAx3MqK1g4Ha5Ar/vWMEH',
        'page_uid': 'jbK3LwqVOZCssa00ez8ssssssmK-395801',
        'JSESSIONID': '563C3ACEC0E5B78B88210E37DD2DE847.jvm1',
        'SRT30': '1751409994',
        'SRT5': '1751409994',
        'BUC': 'BJD-SBubSG6ee9PfuYVXaNv5rwzkptctNQBDQr0t0XQ=',
        'page_uid': '14665240-dca5-431f-b0f4-15d731e44584',
    }

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4',
        'cache-control': 'no-cache',
        'expires': 'Sat, 01 Jan 2000 00:00:00 GMT',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://map.naver.com/p/search/%EA%B0%95%EB%82%A8%20%EB%A7%9B%EC%A7%91?c=15.00,0,0,0,dh',
        'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        # 'cookie': 'NACT=1; NNB=HVAVPHBWJPRGM; ASID=da9b849000000192dd21a77e00000065; nstore_session=f3tE3l7h3IGTb8raSdi+PzFN; _tt_enable_cookie=1; _ttp=vLJLZCmexorHGtGiUsXBjrsTXIs.tt.1; ba.uuid=09b1a6c4-4268-426d-abe9-02b3d238211f; _ga_J5CZVNJNQP=GS1.1.1735519248.1.0.1735519248.0.0.0; _ga_451MFZ9CFM=GS1.1.1736297197.1.0.1736297199.0.0.0; BNB_FINANCE_HOME_TOOLTIP_MYASSET=true; _ga_6Z6DP60WFK=GS1.2.1741078123.1.0.1741078123.60.0.0; _ga=GA1.1.1054701045.1735519249; _ga_RCM29786SD=GS1.1.1742872121.1.0.1742872121.0.0.0; nstore_pagesession=juUmCdqWadk3EssMNKG-087773; NAC=VBXyBgwyb4nT; NDV_SHARE=j23OxEg7JY62FvLO68P3fPxcV1oqlfRqJRpA10qVqJ8TkGHnW90CivnnMuMiqwzGVJOuKNEvjogE6C6vMk0uRC8jAx3MqK1g4Ha5Ar/vWMEH; page_uid=jbK3LwqVOZCssa00ez8ssssssmK-395801; JSESSIONID=563C3ACEC0E5B78B88210E37DD2DE847.jvm1; SRT30=1751409994; SRT5=1751409994; BUC=BJD-SBubSG6ee9PfuYVXaNv5rwzkptctNQBDQr0t0XQ=; page_uid=14665240-dca5-431f-b0f4-15d731e44584',
    }

    params = {
        'query': '강남 맛집',
        'type': 'all',
        'token': '1UTZF_bRRocNpJZ_0fflvcl5zRpppIDCw32z6wlxHV0=',
        'searchCoord': '127.15171494606346;37.27246100000093',
        'boundary': '',
    }

    response = requests.get('https://map.naver.com/p/api/search/allSearch', params=params, headers=headers)
    
    return response.json()