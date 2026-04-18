# utils/log_filter.py
import re

def filter_tokens(text):
    token_pattern = re.compile(r'\b\d{9,10}:[A-Za-z0-9_-]{35}\b')
    text = token_pattern.sub('[BOT_TOKEN_FILTERED]', text)
    url_token_pattern = re.compile(r'/bot\d{9,10}:[A-Za-z0-9_-]{35}/')
    text = url_token_pattern.sub('/bot[BOT_TOKEN_FILTERED]/', text)
    return text
