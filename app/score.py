from utils import get_action_weights
from db import fetch_dynamodb_logs
def score_logs(username, time_interval):
    scores = []
    activity_logs = fetch_dynamodb_logs(username, time_interval)
    action_weights = get_action_weights()
    for log in activity_logs:
        action = log['action'].split(':')[0].strip()
        if action not in action_weights:
            continue
        score = action_weights[action]
        scores.append(score)
    # print("Scores:", scores)
    result = sum(scores)

    return result

