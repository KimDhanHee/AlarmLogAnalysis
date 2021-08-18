START_EVENT = 'alarm_receiver_fire_alarm'
END_EVENT = 'alarm_dismissed'
ALARM_SCHEDULE_EVENT = 'alarm_promise_scheduled'
FILTERED_EVENTS = [
    'drawable',
    'ad_request',
    'ad_loaded',
    'ad_load_failed',
    'format',
    'xday_noti_canceled'
]
UNINTENTIONAL_EVENTS = ["kill_process_invoked", "kill_process_executed"]
START_END_THRESHOLD = 6 * 60 * 60
