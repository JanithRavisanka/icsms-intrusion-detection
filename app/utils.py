import math
import os
import random
import time

import boto3
from botocore.exceptions import ClientError
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongodb_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongodb_uri, port=27017)

database = "icsms-user-activity-scores"
anomalies_database = "icsms-user-activity-anomalies"
icsms_config_db = "icsms-config"

email_user = os.getenv('GMAIL_USER')
email_password = os.getenv('GMAIL_PASSWORD')
email_to = 'janithravisankax@gmail.com'
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_default_region = os.getenv('AWS_DEFAULT_REGION')
cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
cognito_pool_id = os.getenv('COGNITO_POOL_ID')

cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource(
    'dynamodb',
    region_name=aws_default_region,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)


def get_action_weights():
    db = client[icsms_config_db]
    collection = db['security_config']
    cursor = collection.find({
        "name": "weights"
    })
    return cursor[0]['value']


def get_average_activity_counts():
    db = client[icsms_config_db]
    collection = db['security_config']
    cursor = collection.find({
        "name": "average_actions"
    })
    return cursor[0]['value']


def get_senders(type):
    db = client[icsms_config_db]
    collection = db['subscribed_users']
    if type == 'activity':
        cursor = collection.find(
            {
                "type": "activity"
            }
        )
    elif type == 'alert':
        cursor = collection.find(
            {
                "type": "alert"
            }
        )
    else:
        cursor = []
    senders = []
    for document in cursor:
        senders.append(document['username'])
    # print(senders)
    return senders


def get_time_intervals():
    db = client[icsms_config_db]
    collection = db['security_config']
    cursor = collection.find({
        "name": "time_intervals"
    })
    return cursor[0]['intervals']


def get_user_list():
    try:
        response = cognito_client.list_users(UserPoolId=cognito_pool_id)
        return [user['Username'] for user in response['Users']]
    except Exception as e:
        print(e)
        return []


# These four functions are used to get the user permissions
def get_user_groups(username):
    try:
        return cognito_client.admin_list_groups_for_user(Username=username, UserPoolId=cognito_pool_id)

    except Exception as e:
        return {"error": f"Error occurred while trying to get user groups: {e}"}


def process_group_descriptions(groups):
    for group in groups['Groups']:
        group['Description'] = eval(group['Description'])
    return [group['Description'] for group in groups['Groups']]


def extract_permissions(permissions_list):
    permissions = []
    for permission in permissions_list:
        for perm in permission:
            if perm['Value'] == 'true':
                permissions.append(perm['Name'])
    # remove duplicates permission list
    permissions = list(set(permissions))

    return permissions


def get_user_permissions(username):
    action = "Get User Permissions"
    try:
        user_groups = get_user_groups(username)
        permissions_list = process_group_descriptions(user_groups)
        permissions = extract_permissions(permissions_list)
        return permissions
    except Exception as e:
        return {"error": f"Error occurred while trying to {action}: {e}"}


def get_rules():
    db = client[icsms_config_db]
    collection = db['security_config']
    cursor = collection.find({
        "name": "rules"
    })
    return cursor[0]['value']


def block_user(username):
    try:
        cognito_client.admin_disable_user(
            UserPoolId=cognito_pool_id,
            Username=username
        )
        print(f"User {username} has been blocked.")
    except Exception as e:
        print(f"An error occurred while blocking user {username}: {e}")


def format_data_points(data_points, time_interval):
    factor = int(time_interval / 0.25)
    print("Factor:", factor)
    count = len(data_points) % factor

    if count > 0:
        data_points = data_points[:-count]

    #group the data points into factor number of groups
    data_points = [sum(data_points[i:i + factor]) for i in range(0, len(data_points), factor)]
    print("Data Points:", data_points)
    return data_points


def get_z_score(mean, std_dev, value):
    z_score = (value - mean) / std_dev
    return z_score


def get_std_deviation(default_std, time_interval):
    return default_std * math.sqrt(time_interval / 0.25)


def calculate_mean(data_points):
    return sum(data_points) / len(data_points)


def generate_mean(username, time_interval):
    permissions = get_user_permissions(username)
    action_weights = get_action_weights()
    average_activity_counts_per_permission = get_average_activity_counts()
    # print("Permissions:", permissions)
    if not permissions:
        return 0
    sample_score = 0
    for permission in permissions:
        if permission not in action_weights:
            continue
        sample_score += action_weights[permission] * average_activity_counts_per_permission[permission]
    user_mean = sample_score * (time_interval / 8)

    return user_mean


if __name__ == '__main__':
    # print(get_action_weights_per_day())
    # print(get_average_activity_counts())
    # print(get_senders('activity'))
    # print(get_senders('alert'))
    # print(get_time_intervals())
    # for user in get_user_list():
    #     print(get_user_permissions(user))
    # print(get_user_list())
    # print(get_std_deviation(10, 1))
    print(generate_mean("janithravisankax@gmail.com", 1))
