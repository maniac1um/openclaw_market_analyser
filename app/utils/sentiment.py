def sentiment_from_text(text: str) -> str:
    lower = text.lower()
    positive = ("上涨", "走强", "利好", "增持", "突破", "反弹", "上调", "紧张", "减产")
    negative = ("下跌", "走弱", "利空", "抛售", "回落", "暴跌", "下调", "宽松", "增产")
    p = sum(1 for token in positive if token in lower)
    n = sum(1 for token in negative if token in lower)
    if p > n:
        return "bullish"
    if n > p:
        return "bearish"
    return "neutral"
