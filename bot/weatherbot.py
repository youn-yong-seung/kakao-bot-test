import logging
import requests
from bs4 import BeautifulSoup
from ai.gemini import gemini_free
import traceback

logger = logging.getLogger(__name__)

def weatherbot_run(room):
    """날씨봇 처리"""
    try:
        weather_msg = get_whether_summary()

        result = {
            "chat_id": room,
            "type": "text",
            "data": weather_msg
        }

        return result
    except Exception as e:
        logger.error(traceback.format_exc())
        return None

def get_whether_summary():
    url = f"https://www.weather.go.kr/w/weather/forecast/short-term.do"
    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')
    dt_span = soup.select_one('.cmp-view-announce > span')
    if dt_span is not None:
        dt = dt_span.get_text()[6:-2].replace('월 ','/').replace(' ','').replace('요일',' ').replace('일', '')
    else:
        dt = "날짜 정보 없음"
    spans = soup.select(".summary > span")

    raw_msg = ''
    for span in spans:
        depth = span['class'][0][-1]
        space = " " * (int(depth) * 1)
        text = span.get_text(separator="\n").replace('\n\n', '\n').replace('  ',' ').strip()
        raw_msg += f'\n{space}{text}'
    
    system = '다음 기상청 예보중 오늘 날씨만 1줄로 요약해줘'
    question = f'{raw_msg}'
    
    answer = gemini_free(system, question)
    answer = answer.replace('.','.\n')

    result = f"""🌞AI 전국 날씨 요약🌞
({dt} 기준)

{answer}👇 자세히 보기 👇{'\u200C'*500}
[기상청 원문]
{raw_msg}

🤖 카카오톡봇 만드는법이 궁금하다면?
https://vo.la/QGXCp
"""
    return result