# 봇은 어떻게 실행하나요?
1. 의존성들을 모두 설치합니다. (`pip install -r requirements.txt`)
2. [FFmpeg](https://github.com/BtbN/FFmpeg-Builds/releases)를 다운로드 해서 ffmpeg.exe를 main.py에 같이 넣습니다.
3. `bot_settings.json`에 설정값을 넣어주세요.

# 봇 실행이 안되는데요?
1. 토큰을 제대로 입력했나요?
2. `main.py`에 건드린 부분이 있나요?
3. `bot_settings.json`에서 지운 키가 있나요?  

-> 이 3가지를 점검하고 `Issue`에 문제를 넣어주세요.

# 음악을 재생할 때 오류가 뜨는데요?
1. `youtube_dl` 관련 오류인가요?  
-> `pip install -U youtube-dl`로 youtube-dl을 업데이트 해주시고 그래도 안되면 유튜브에서 막힌겁니다. 이건 저도 어떻게 할 수 없어요.
2. 뭔 dll이 없다는데요?  
-> FFmpeg를 다른 버전으로 다운로드 해보세요.

# bot_settings.json은 어떻게 편집하면 되나요?
```json
{
    "bot_name": "봇 이름을 여기에 넣어주세요",
    "stable_token": "토큰을 입력해주세요",
    "canary_token": "굳이 넣을 필요는 없습니다",
    "default_prefix": "프리픽스를 넣어주세요",
    "debug": false,
    "whitelist": [자신의 ID를 int로 넣어주세요],
    "presence": ["봇 상태 메시지로 넣을 것을 작성해주세요"]
}
```