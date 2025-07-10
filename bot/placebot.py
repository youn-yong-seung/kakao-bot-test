import logging
import requests
from bs4 import BeautifulSoup
import json
import traceback
import re

logger = logging.getLogger(__name__)

def placebot_run(data):
    """플레이스봇 처리"""
    try:
        allow_chat_list = ["18444706541881108", "18453992993191424"]
        chat_id = data["json"]["chat_id"]
        if chat_id not in allow_chat_list:
            return None
        
        msg = data["json"]["message"].strip()

        if msg.startswith("/지도"):
            send_msg = get_naver_map_keyword(data)
            if send_msg:
                result = {
                    "chat_id": chat_id,
                    "type": "text",
                    "data": send_msg
                }
                return result
        
        return None
    except Exception as e:
        logger.error(traceback.format_exc())
        return None

def get_naver_map_keyword(data):
    room = data["room"]
    sender = data["sender"]
    msg = data["msg"]
    keyword = msg.replace("/지도", "").strip()
    if not keyword:
        return f"{sender}님 /지도 뒤에 키워드를 입력해주세요."

    send_msg = f"🗺️{keyword} Top 20😎"
    
    results =get_naver_map_api(keyword)
    if not results:
        return f"{sender}님 {keyword} 지도 검색결과가 없어요ㅠㅠ"

    for i, r in enumerate(results):
        if i >= 20:
            break
        for key, item in r.items():
            if i < 5:
                result = get_naver_map_place_id_api(key.split(':')[1])
                extract_item = extract_restaurant_item(result)
                send_msg += f"\n\n{i+1}. {item['name']}"
                if 'visitorReviewCount' in item and item['visitorReviewCount'] is not None:
                    send_msg += f"\n💬방문자리뷰 {item['visitorReviewCount']}"
                if 'category' in item and item['category'] is not None:
                    send_msg += f"\n🏢{item['category']}"
                if 'keywords' in extract_item and extract_item['keywords']:
                    send_msg += "\n💬대표키워드"
                    send_msg += f"\n{','.join(extract_item['keywords'])}"
                if 'saveCount' in item and item['saveCount'] is not None:
                    send_msg += f"\n⭐저장수 {item['saveCount']}"
                if 'fullAddress' in item and item['fullAddress'] is not None:
                    send_msg += f"\n📍{item['fullAddress']}"
                elif 'roadAddress' in item and item['roadAddress'] is not None:
                        send_msg += f"\n📍{item['roadAddress']}"
                if 'virtualPhone' in item and item['virtualPhone'] is not None:
                    send_msg += f"\n☎️{item['virtualPhone']}"
                if 'status' in item:
                    if 'newBusinessHours' in item and 'status' in item['newBusinessHours'] and 'description' in item['newBusinessHours']:
                        send_msg += f"\n⏰{item['newBusinessHours']['status']} - {item['newBusinessHours']['description']}"
                if 'menuInfo' in extract_item and extract_item['menuInfo']:
                    send_msg += f"\n{'|'.join(extract_item['menuInfo'])}"
                send_msg += f"\nhttps://map.naver.com/p/entry/place/{key.split(':')[1]}"
            else:
                send_msg += f"\n\n{i+1}. {item['name']}"
                if 'visitorReviewCount' in item and item['visitorReviewCount'] is not None:
                    send_msg += f"\n💬방문자리뷰 {item['visitorReviewCount']}"
                if 'category' in item and item['category'] is not None:
                    send_msg += f"\n🏢{item['category']}"
                if 'saveCount' in item and item['saveCount'] is not None:
                    send_msg += f"\n⭐저장수 {item['saveCount']}"
                if 'fullAddress' in item and item['fullAddress'] is not None:
                    send_msg += f"\n📍{item['fullAddress']}"
                elif 'roadAddress' in item and item['roadAddress'] is not None:
                        send_msg += f"\n📍{item['roadAddress']}"
                if 'virtualPhone' in item and item['virtualPhone'] is not None:
                    send_msg += f"\n☎️{item['virtualPhone']}"
                if 'status' in item:
                    if 'newBusinessHours' in item and 'status' in item['newBusinessHours'] and 'description' in item['newBusinessHours']:
                        send_msg += f"\n⏰{item['newBusinessHours']['status']}-{item['newBusinessHours']['description']}"
                send_msg += f"\nhttps://map.naver.com/p/entry/place/{key.split(':')[1]}"
            if i == 0:
                send_msg += '\n[열어서 모두 보기]' + '\u200B'*500
    print(send_msg)
    return send_msg

def extract_restaurant_item(html):
    item = {}

    """
    restaurant_name_pattern = r'<span class="GHAhO">([^<]+)</span>'
    restaurant_name_match = re.search(restaurant_name_pattern, html)
    if restaurant_name_match:
        item['name'] = restaurant_name_match.group(1)
    
    category_pattern = r'<span class="lnJFt">([^<]+)</span>'
    category_match = re.search(category_pattern, html)
    if category_match:
        item['category'] = category_match.group(1)

    review_pattern = r'방문자 리뷰 ([\\d,]+)'
    review_match = re.search(review_pattern, html)
    if review_match:
        item['placeReviewCount'] = review_match.group(1).replace(',', '')
    
    lastorder_pattern = r'<span class="U7pYf"><time[^>]*>([^<]+)</time>'
    lastorder_match = re.search(lastorder_pattern, html)
    if lastorder_match:
        item['bizhourInfo'] = lastorder_match.group(1)

    address_pattern = r'<span class="LDgIH">([^<]+)</span>'
    address_match = re.search(address_pattern, html)
    if address_match:
        item['address'] = address_match.group(1)

    tel_pattern = r'<span class="xlx7Q">([^<]+)</span>'
    tel_match = re.search(tel_pattern, html)
    if tel_match:
        item['telDisplay'] = tel_match.group(1)

    micro_review_pattern = r'<div class="XtBbS">([^<]+)</div>'
    micro_review_match = re.search(micro_review_pattern, html)
    if micro_review_match:
        item['microReview'] = micro_review_match.group(1)
    """

    keyword_pattern = r'"keywordList":\[([^\]]+)\]'
    keyword_match = re.search(keyword_pattern, html)
    if keyword_match:
        keyword_string = keyword_match.group(1)
        keywords = re.findall(r'"([^"]+)"', keyword_string)
        item['keywords'] = keywords
    
    menu_pattern = r'"__typename":"Menu"[^}]*"name":"([^"]+)"[^}]*"price":"([^"]+)"'
    menu_matches = re.findall(menu_pattern, html)
    if menu_matches:
        item['menuInfo'] = []
        for name, price in menu_matches:
            item['menuInfo'].append(f'{name} {price}')
    
    return item

def get_naver_map_place_id_api(place_id):
    cookies = {
        'NACT': '1',
        'NAC': 'rxILBsQAskiX',
        'NNB': 'KEFULMRZLFRWQ',
        '_fwb': '226jCiIm1fuLeKemiic7yED.1751356819771',
        'SRT30': '1751415660',
        'page_uid': 'jbftIdqVN8CssR3aM3hssssstMG-192630',
        'PLACE_LANGUAGE': 'ko',
        'NACT': '1',
        'SRT5': '1751420784',
        'wcs_bt': 'sp_96c07a8dab4ae8:1751421228|sp_197c063aa1d1970:1751418878|sp_90b303cf9230:1751356819',
        'BUC': 'jn3FIRdcWoehFtmNRSkJqQw1pTggeTTVGt2NhuJW6D8=',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=0, i',
        'referer': 'https://map.naver.com/p/search/%EA%B0%95%EB%82%A8%20%EB%A7%9B%EC%A7%91/place/693144763?c=13.00,0,0,0,dh&placePath=%3Fentry%253Dbmp%2526n_ad_group_type%253D10%2526n_query%253D%2525EA%2525B0%252595%2525EB%252582%2525A8%2525EB%2525A7%25259B%2525EC%2525A7%252591',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'iframe',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-site',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }
    
    url = f'https://pcmap.place.naver.com/restaurant/{place_id}/home'
    response = requests.get(url, cookies=cookies, headers=headers)
    response_decode = response.content.decode('utf-8')
    
    return response_decode

def get_naver_map_api(keyword):
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

    response = requests.get('https://pcmap.place.naver.com/place/list', params=params, headers=headers)
    response_decode = response.content.decode('utf-8')
    
    soup = BeautifulSoup(response_decode, 'html.parser')

    script_tag = soup.find('script', string=re.compile(r'window\.__APOLLO_STATE__\s*='))

    if not script_tag:
        return []
        
    # 2. 텍스트만 추출
    text = script_tag.get_text()

    # 3. JSON 텍스트만 남기기
    raw_json = text.split('window.__APOLLO_STATE__ = ')[1].rstrip(';')
    
    result = []
    # 정규표현식으로 '"SomethingSummary:' 패턴을 찾아서 시작 위치 기준으로 쪼개기
    for match in re.finditer(r'"[^"]+Summary:', raw_json):
        start_index = match.start()
        full_chunk = raw_json[start_index:]

        # 중괄호 세서 JSON 객체만 추출
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
        except Exception as e:
            # 디버깅이 필요하면 여기에 print(e) 추가
            continue

    return result


# data = {
#     "room": "18444706541881108",
#     "sender": "윤자동",
#     "msg": "/지도 술집"
# }


# get_naver_map_keyword(data)