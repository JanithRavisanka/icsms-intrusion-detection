from datetime import timedelta, datetime
import numpy as np

from utils import (get_user_list, get_z_score, format_data_points, get_std_deviation,
                   calculate_mean, generate_mean, block_user, get_senders, get_time_intervals)
from anormaly import detect_anomalies
from db import fetch_previous_scores_from_mongodb, get_current_time, save_to_activity_logs, save_anomalies_to_mongodb, \
    save_report_to_mongodb
from score import score_logs
from mail import format_email_body, send_email
import threading
import schedule
import time


def run_test(time_interval, save=False):
    # time_interval = 8
    default_std_dev = 10  # we assume this one is true

    current_time = get_current_time()
    # Calculate the start time by subtracting the time interval from the current time
    start_time = get_current_time() - timedelta(hours=time_interval)

    # Convert times to ISO 8601 format
    current_time_str = current_time
    end_time_str = start_time

    user_list = get_user_list()
    report_lines = []
    for username in user_list:

        # for username in ["janithravisankax@gmail.com"]:

        # get 15m interval scores from mongodb
        previous_score_array = fetch_previous_scores_from_mongodb(username, time_interval)
        count_previous_score_array = len(previous_score_array)

        # adjust with time interval
        previous_score_array = format_data_points(previous_score_array, time_interval)

        mean = 0
        std_deviation = 0
        # check data enough - at least 5 days of data
        if count_previous_score_array < 200:
            mean = generate_mean(username, time_interval)
            std_deviation = get_std_deviation(default_std_dev, time_interval)
        else:
            mean = np.mean(previous_score_array)
            std_deviation = np.std(previous_score_array)

        # get current score
        current_score = score_logs(username, time_interval)

        # calculate z score
        z_score = get_z_score(mean, std_deviation, current_score)
        # z_score = 6

        report_line = f"User: {username}, Current Score: {current_score}, Z-Score: {z_score:.2f}, "

        # detect anomalies
        result = detect_anomalies(z_score, username)
        if result == "block":
            print("Block user")
            report_line += "Anomalies: Yes, Action: Block"
            # block_user(username)
        elif result == "alert":
            print("Alert user")
            report_line += "Anomalies: Yes, Action: Alert"
        elif result == "normal":
            print("Normal user")
            report_line += "Anomalies: No, Action: None"

            # to only save 15m interval data
            if save:
                save_to_activity_logs(username, current_score, datetime.now())

        report_lines.append(report_line)
        print(report_line)

        # send mails
        if result == "block" or result == "alert":
            alert_senders = get_senders('alert')
            email_body = format_email_body([report_line], end_time_str, current_time_str)
            send_email(subject="Anomaly Alert", body=email_body, senders=alert_senders)
            save_anomalies_to_mongodb(username, current_score, z_score, "Yes", result, datetime.now(), time_interval)

    # send report
    activity_senders = get_senders('activity')
    email_body = format_email_body(report_lines, end_time_str, current_time_str)
    send_email(subject="User Activity Report", body=email_body, senders=activity_senders)
    save_report_to_mongodb(report_lines, datetime.now(), time_interval)


# run_test()


def run_main_in_thread(time_interval, save=False):
    run_test(time_interval, save)


def setup_and_run_threads():
    time_intervals = get_time_intervals()

    threads = []

    # Create threads for each main function call with different time intervals
    thread1 = threading.Thread(target=run_main_in_thread, args=(0.25, True))  # this one should run every 15 minutes
    threads.append(thread1)

    for interval in time_intervals:
        thread = threading.Thread(target=run_main_in_thread, args=(interval, False))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


schedule.every(15).minutes.do(setup_and_run_threads)
# while True:
#     schedule.run_pending()
#     time.sleep(1)

run_test(0.25, False)
