"""
교실별 노드 설정. 노드마다 이 파일만 바꿔서 16개에 배포한다.

NODE_ID는 교실 번호 (예: '1-1', '2-3'). 서버 DB에서 이 ID로 노드를 구분한다.
SERVER_URL은 학교 LAN 내 라즈베리파이 서버의 주소.
"""

WIFI_SSID = "DanggokIoT"           # 학교 IoT 전용 SSID (WPA2-PSK)
WIFI_PASSWORD = "REPLACE_ME"        # 발급받은 패스워드

NODE_ID = "1-1"                     # 교실 번호 (1학년 1반)
SERVER_URL = "http://192.168.0.10:8000/reading"  # 라즈베리파이 서버 주소

INTERVAL_SEC = 30                   # 측정·전송 주기 (초)
