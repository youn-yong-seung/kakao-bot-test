import logging
import requests
from bs4 import BeautifulSoup
import json
import traceback
import re
import main

logger = logging.getLogger(__name__)

def run(data):
    """날씨봇 처리"""

    result = {
        "chat_id": data["room"],
        "type": "text",
        "data": data["msg"]
    }
    main.send_message(result)