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
### 2. 스누즈 알람이 아님에도 첫 event 의 alarm id 와 끝 event 의 alam id 가 일치하지 않는 경우
