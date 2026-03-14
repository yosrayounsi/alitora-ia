# app/gateway/quotas.py
import os
from collections import defaultdict
from datetime import date

MAX_PER_DAY = int(os.environ.get("MAX_TOKENS_PER_USER_PER_DAY", "200000"))
_usage = defaultdict(int)
_day = date.today()

def check_and_add(user_id: str, tokens: int) -> bool:
    global _day
    if date.today() != _day:
        _usage.clear()
        _day = date.today()

    if _usage[user_id] + tokens > MAX_PER_DAY:
        return False
    _usage[user_id] += tokens
    return True