# -*- coding: utf-8 -*-
import logging

# ????? logger ?????
logger = logging.getLogger("app")

def log_api_request(method: str, path: str, status_code: int, duration_ms: float):
    """??? ???? ?????? API"""
    logger.info(f"API {method} {path} - {status_code} - {duration_ms}ms")


