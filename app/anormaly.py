from utils import get_rules, block_user


def detect_anomalies(z_score, username):
    rules = get_rules()
    alert_threshold = rules['activity_alert_threshold']
    block_threshold = rules['activity_block_threshold']

    if z_score > block_threshold:
        return "block"
        # block_user(username)
    elif z_score > alert_threshold:
        return "alert"
    else:
        return "normal"




