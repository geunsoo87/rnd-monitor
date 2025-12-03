"""
설정 관리 모듈
config.json 파일을 읽고 쓰는 기능 제공
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """설정 파일 관리 클래스"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.default_config = {
            "last_work_folder": "",
            "date_format": "YYYY-MM-DD",
            "currency_format": "ko_KR"
        }
    
    def load(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 기본값과 병합하여 누락된 키 보완
                return {**self.default_config, **config}
            except (json.JSONDecodeError, IOError) as e:
                print(f"설정 파일 읽기 오류: {e}")
                return self.default_config.copy()
        else:
            # 설정 파일이 없으면 기본값으로 생성
            self.save(self.default_config.copy())
            return self.default_config.copy()
    
    def save(self, config: Dict[str, Any]) -> bool:
        """설정 파일 저장"""
        try:
            # 기본값과 병합
            merged_config = {**self.default_config, **config}
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"설정 파일 저장 오류: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        config = self.load()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """설정 값 설정"""
        config = self.load()
        config[key] = value
        return self.save(config)
    
    def update_last_work_folder(self, folder_path: str) -> bool:
        """마지막 작업 폴더 업데이트"""
        return self.set("last_work_folder", folder_path)


# 전역 설정 관리자 인스턴스
config_manager = ConfigManager()

