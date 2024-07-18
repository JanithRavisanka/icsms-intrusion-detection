import os
from pymongo import MongoClient
import boto3
import pytz
from dateutil import tz
from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv()

mongodb_uri = os.getenv('MONGODB_URI')
print(mongodb_uri)
client = MongoClient(mongodb_uri)

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_default_region = os.getenv('AWS_DEFAULT_REGION')

cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource(
    'dynamodb',
    region_name=aws_default_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
dynamodb_table_logs = dynamodb.Table('icsms-user-activity-logs')
dynamodb_table_scores = dynamodb.Table('isms-user-log-scores')

target_timezone = tz.gettz('Asia/Colombo')

database = "icsms-user-activity-scores"
anomalies_database = "icsms-user-activity-anomalies"
icsms_config_db = "icsms-config"
user_report_db = "icsms-user-reports"


# def fetch_cognito_auth_events(username: str):
#     try:
#         response = cognito_client.admin_list_user_auth_events(
#             UserPoolId=Config.cognito_pool_id,
#             Username=username,
#             MaxResults=20  # Adjust as needed
#         )
#         auth_events = [
#             {
#                 "action": auth_event['EventType'],
#                 "is_success": True if (
#                         auth_event['EventResponse'] == "Pass" or auth_event['EventType'] == "SignUp") else False,
#                 "time": auth_event["CreationDate"],
#                 "event_data": auth_event["EventContextData"]
#             }
#             for auth_event in response['AuthEvents']
#         ]
#         return auth_events
#     except Exception as e:
#         print(f"Error retrieving auth events: {e}")
#         return []


# [{'is_success': True, 'action': 'View Users: Success', 'time': '2024-07-10T21:19:14.663438+05:30'}]
def fetch_dynamodb_logs(username: str, time_interval: int):
    try:
        # Define the timezone for accurate time calculations
        # timezone = pytz.timezone("Asia/Colombo")
        current_time = get_current_time()

        # Calculate the start time by subtracting the time interval from the current time
        start_time = get_current_time() - timedelta(hours=time_interval)

        # Convert times to ISO 8601 format
        current_time_str = current_time.isoformat()
        time_15_minutes_ago_str = start_time.isoformat()

        # Query DynamoDB table for logs within the specified time interval
        response = dynamodb_table_logs.query(
            KeyConditionExpression='username = :username',
            ExpressionAttributeValues={
                ':username': username,
            },
            ScanIndexForward=False,  # Retrieve the most recent logs first
            Limit=40,  # Adjust the limit as needed
        )
        # print(response)
        if 'Items' not in response:
            return []

        # Extract logs from the response
        logs = response['Items'][0]['events']
        # print(logs)

        filtered_logs = []
        for log in logs:
            log_time_str = log['time']
            if time_15_minutes_ago_str <= log_time_str <= current_time_str:
                filtered_logs.append(log)

        # Reverse the order of filtered_logs
        filtered_logs = filtered_logs[::-1]

        return filtered_logs
    except Exception as e:
        print(f"Error retrieving DynamoDB logs: {e}")
        return []


def fetch_previous_scores_from_mongodb(username: str, time_interval: float):
    # Get the current time in UTC and subtract the time interval
    current_time = get_current_time()
    start_time = current_time - timedelta(hours=time_interval)
    colombo_zone = pytz.timezone('Asia/Colombo')

    # Convert times to ISO 8601 format
    try:
        if time_interval == 0.25:
            db = client[database]
            collection = db[username]

            # Fetch all documents from MongoDB
            cursor = collection.find()
            all_scores = []
            for document in cursor:
                all_scores.append(document['score'])
            return all_scores
        else:
            # print("hi")
            db = client[database]
            collection = db[username]

            # Fetch all documents from MongoDB
            cursor = collection.find()

            all_scores = []
            for document in cursor:
                document_time = document['timestamp']
                if document_time.replace(tzinfo=colombo_zone) <= start_time:
                    all_scores.append(document['score'])
            return all_scores

    except Exception as e:
        print(f"Error retrieving previous scores from MongoDB: {e}")
        return []

def save_to_activity_logs(username, current_scores, end):
    try:
        db = client[database]
        collection = db[username]
        collection.insert_one({
            'username': username,
            'timestamp': end,
            'score': current_scores,
        })
    except Exception as e:
        print(f"Error storing scores in MongoDB: {e}")

def save_anomalies_to_mongodb(username, current_score, z_score, anomalies, action, start_time, time_interval):
    try:
        db = client[anomalies_database]
        collection = db[username + "_anomalies"]
        collection.insert_one({
            "username": username,
            "current_score": current_score,
            "z_score": z_score,
            "anomalies": anomalies,
            "action": action,
            "timestamp": start_time,
            "time_interval": time_interval,
        })
    except Exception as e:
        print(f"Error storing anomalies in MongoDB: {e}")

def save_report_to_mongodb(report_lines, start_time, time_interval):
    report_data = []
    for line in report_lines:
        user, current_score, z_score, anomalies, action = line.split(',')
        username = user.split(': ')[1]
        current_score = current_score.split(': ')[1]
        z_score = z_score.split(': ')[1]
        anomalies = anomalies.split(': ')[1]
        action = action.split(': ')[1]

        report_data.append({
            "username": username,
            "current_score": current_score,
            "z_score": z_score,
            "anomalies": anomalies,
            "action": action,
            "timestamp": start_time,
            "time_interval": time_interval,
        })


    try:
        db = client[user_report_db]
        collection = db['user_reports']
        collection.insert_one({
            "timestamp": start_time,
            "report": report_data
        })
    except Exception as e:
        print(f"Error storing anomalies in MongoDB: {e}")

def get_current_time():
    return datetime.now(pytz.timezone("Asia/Colombo"))


if __name__ == '__main__':
    username = "janithravisankax@gmail.com"
    print(fetch_dynamodb_logs(username, 4))
    print(fetch_previous_scores_from_mongodb(username, 1))
    print(get_current_time())


