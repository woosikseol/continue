"""
설정 핸들러
원본 TypeScript ConfigHandler의 Python 포팅
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigHandler:
    """설정 핸들러 - 원본 TypeScript ConfigHandler의 Python 포팅"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        logger.info("설정 핸들러 초기화 완료")
    
    def get_config(self) -> Dict[str, Any]:
        """설정 반환"""
        return self.config
    
    def set_config(self, config: Dict[str, Any]):
        """설정 설정"""
        self.config = config
        logger.info("설정 업데이트 완료")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """설정 값 반환"""
        return self.config.get(key, default)
    
    def set_value(self, key: str, value: Any):
        """설정 값 설정"""
        self.config[key] = value
