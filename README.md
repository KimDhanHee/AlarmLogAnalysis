# AlarmLogAnalysis

## 알라미 앱 사용 로그 -> 알람 앱 로그 시각화

### 알라미 앱 사용 로그
### normal
### --> 알람 A 로그
### --> 알람 B 로그
### abnormal
### --> 알람 C 로그
### --> 알람 D 로그

## Abnormal Case
### 1. AlarmLog 의 마지막 row 가 설정 (config.py) 에서 명시한 end event 가 아닌 경우 
(ex. 'alarm_dismissed' event 로 끝나지 않는 경우)
### 2. 스누즈 알람이 아니고 겹침 알람이 아님에도 첫 event 의 Alarm ID 와 끝 event 의 Alarm ID 가 일치하지 않는 경우
겹침 알람: 선행 알람이 해제 전 후속 알람이 울리는 경우
### 3. START_EVENT 와 END_EVENT 사이에 의도하지 EVENT 가 발생한 경우
(ex. UNINTENTIONAL_EVENTS = ["KILL_PROCESS_INVOKED", "KILL_PROCESS_EXECUTED"])
### 4. "alarm_receiver_to_service" 이벤트와 "start_foreground_in_alarm_notify" 이벤트 사이에 5초 이상의 시간이 걸릴 경우
ACTIVITY_THREAD 발생 원인
### 5. START_EVENT 에서 END_EVENT 까지 임계치 이상의 시간이 소요될 경우