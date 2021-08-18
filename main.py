"""
알라미 로그 분석기

유저 앱 사용 로그
    --> 알람 A 로그
    --> 알람 B 로그
    --> 알람 C 로그
    --> ...
"""
import pandas as pd

import matplotlib.pyplot as plt

import seaborn as sns

from datetime import datetime

import json

import sys
import os

from config import *


def get_alarm_id(props):
    props_dict = json.loads(props)
    alarm_id = str(props_dict['alarm_id']) if 'alarm_id' in props_dict else None
    return int(alarm_id.split('_')[-1]) if alarm_id else None


def merge_alarm_properties(df):
    props = {}

    for idx, row in df.iterrows():
        alarm_properties = json.loads(row['event property'])
        # property key 값 소문자로
        alarm_properties = {k.lower(): v for k, v in alarm_properties.items()}
        props.update(alarm_properties)

    return props


def get_device_id():
    return sys.argv[1].split('/')[-1].split('.')[0]


def get_alarm_log_path():
    log_path = f"./alarm_logs/{get_device_id()}"

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    return log_path


def get_alarm_normal_log_path():
    log_path = f"{get_alarm_log_path()}/normal"

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    for file in os.listdir(log_path):
        os.remove(f"{log_path}/{file}")

    return log_path


def get_alarm_abnormal_log_path():
    log_path = f"{get_alarm_log_path()}/abnormal"

    if not os.path.exists(log_path):
        os.mkdir(log_path)

    for file in os.listdir(log_path):
        os.remove(f"{log_path}/{file}")

    return log_path


def get_alarmy_log_df():
    log_df = pd.read_csv(sys.argv[1], header=None, delimiter='\t')
    log_df.columns = ['timestamps', 'event name', 'event property']
    # 필터링 할 (관심 대상 X) 이벤트 필터링
    log_df = log_df[~log_df['event name'].isin(FILTERED_EVENTS)]
    # Alarm ID 추출
    log_df['alarm id'] = log_df['event property'].apply(get_alarm_id)
    # Column 순서 재정의
    log_df = log_df[['timestamps', 'alarm id', 'event name', 'event property']]

    return log_df


def get_alarm_scheduled_logs(log_df):
    return log_df[log_df['event name'] == ALARM_SCHEDULE_EVENT]


def get_abnormal_case(log_df, properties):
    # Case1. 마지막 이벤트가 설정에서 명시한 마지막 이벤트가 아닌 경우
    if log_df.iloc[-1]['event name'] != END_EVENT:
        return 'case_1'

    # Case2. 스누즈가 아닌고 후속 알람이 없는데 첫 alarm id 와 마지막 alarm id 가 다른 경우
    if 'snoozed_count' in properties and \
            properties['snoozed_count'] == 0 and \
            log_df.iloc[0]['alarm id'] != log_df.iloc[-1]['alarm id'] and \
            len(log_df[log_df['event name'] == START_EVENT]) != len(log_df[log_df['event name'] == END_EVENT]):
        return 'case_2'

    # Case3. START_EVENT 와 END_EVENT 사이에 의도하지 EVENT 가 발생한 경우
    if log_df['event name'].isin(UNINTENTIONAL_EVENTS).sum() > 0:
        return 'case_3'

    # Case4. "alarm_receiver_to_service" 이벤트와 "start_foreground_in_alarm_notify" 이벤트 사이에 5초 이상의 시간이 걸릴 경우
    if 'start_foreground_in_alarm_notify' in log_df['event name']:
        preceding_events = log_df[log_df['event name'] == 'alarm_receiver_to_service']
        trailing_events = log_df[log_df['event name'] == 'start_foreground_in_alarm_notify']

        idx = 0
        trail = trailing_events.iloc[idx]

        for _, pre in preceding_events.iterrows():
            pre_time = pre['timestamps']
            trail_time = trail['timestamps']

            if (datetime.strptime(trail_time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(pre_time, '%Y-%m-%d %H:%M:%S')) \
                    .seconds >= 5:
                return 'case_4'

            try:
                idx += 1
                if trailing_events.iloc[idx] is not None:
                    trail = trailing_events.iloc[idx]
            except:
                break

    # Case5. START_EVENT 에서 END_EVENT 까지 임계치 이상의 시간이 소요될 경우
    if START_EVENT in log_df['event name'] and END_EVENT in log_df['event name']:
        start_time = log_df[log_df['event name'] == START_EVENT].iloc[0]
        end_time = log_df[log_df['event name'] == END_EVENT].iloc[0]
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        if (end_time - start_time).seconds >= START_END_THRESHOLD:
            return 'case_5'

    return None


if __name__ == "__main__":
    normal_alarm_log_path = get_alarm_normal_log_path()
    abnormal_alarm_log_path = get_alarm_abnormal_log_path()

    alarmy_log_df = get_alarmy_log_df()
    # 알람 예약 이벤트만 별도 추출
    alarm_scheduled_logs = get_alarm_scheduled_logs(alarmy_log_df)

    start_event_idxes = list(alarmy_log_df[alarmy_log_df['event name'] == START_EVENT].index)
    end_event_idxes = list(alarmy_log_df[alarmy_log_df['event name'] == END_EVENT].index)

    end_idx = end_event_idxes[0]
    last_end_idx = end_idx

    for start_idx in start_event_idxes:
        while end_idx < start_idx and len(end_event_idxes) > 0:
            end_idx = end_event_idxes.pop(0)

        alarm_log_df = alarmy_log_df.loc[start_idx:end_idx]
        alarm_log_df = alarm_log_df[alarm_log_df['event name'] != ALARM_SCHEDULE_EVENT]

        tmp_idx = 0
        start_alarm_id = alarm_log_df.iloc[tmp_idx]['alarm id']
        while start_alarm_id is None:
            tmp_idx += 1
            start_alarm_id = alarm_log_df.iloc[tmp_idx]['alarm id']

        tmp_idx = -1
        end_alarm_id = alarm_log_df.iloc[tmp_idx]['alarm id']
        while start_alarm_id is None:
            tmp_idx -= 1
            start_alarm_id = alarm_log_df.iloc[tmp_idx]['alarm id']

        alarm_log_df.iloc[0]['alarm id'] = start_alarm_id
        alarm_log_df.iloc[-1]['alarm id'] = end_alarm_id

        ring_alarm_scheduled_logs = alarm_scheduled_logs.loc[:start_idx][
            alarm_scheduled_logs['alarm id'] == start_alarm_id]

        if len(ring_alarm_scheduled_logs) > 0:
            scheduled_alarm_id = ring_alarm_scheduled_logs.iloc[-1]['alarm id']

            if scheduled_alarm_id == start_alarm_id:
                # 해당 알람 예약 이벤트 알람 로그 가장 앞에 append
                alarm_log_df = pd.concat([ring_alarm_scheduled_logs.iloc[[-1]], alarm_log_df])

        alarm_properties = merge_alarm_properties(alarm_log_df)

        alarm_id = alarm_log_df.iloc[-1]['alarm id']
        # 0 인덱스는 알람 예약 이벤트
        alarm_time = alarm_log_df.iloc[1]['timestamps']

        # visualize alarm logs
        alarm_log_df['event name (alarm id)'] = list(
            map(lambda e: f'{e[0]} ({e[1]})',
                zip(alarm_log_df['event name'], alarm_log_df['alarm id'])))
        y = alarm_log_df['event name (alarm id)'].unique()
        x = alarm_log_df['event name (alarm id)'].value_counts()[y]

        figure, ax = plt.subplots(figsize=(20, len(alarm_properties) / 2 + len(alarm_log_df) / 3))
        # 알람 속성 알파벳 순 정렬
        alarm_properties = dict(sorted(alarm_properties.items()))
        properties_str = str(alarm_properties).replace(',', '\n')
        plt.title(f"{alarm_time} Alarm {alarm_id}\n{properties_str}", size=16, loc='left')
        plt.xticks(range(100))
        plt.yticks(size=14)
        graph = sns.barplot(x=x, y=y)
        for event, count in enumerate(x):
            graph.text(count, event, count, ha='center', size=16)
        plt.xlabel('event count', size=16)
        plt.ylabel('event name', size=16)
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        plt.tight_layout()

        # logging alarm logs
        file_name = f'{alarm_time}_alarm_{end_alarm_id}'
        abnormal_case = get_abnormal_case(alarm_log_df, alarm_properties)

        if abnormal_case is not None:
            alarm_log_df.to_csv(f'{abnormal_alarm_log_path}/{abnormal_case}_{file_name}.csv')
            plt.savefig(f'{abnormal_alarm_log_path}/{abnormal_case}_{file_name}.png', dpi=150)
        else:
            alarm_log_df.to_csv(f'{normal_alarm_log_path}/{file_name}.csv')
            plt.savefig(f'{normal_alarm_log_path}/{file_name}.png', dpi=150)
