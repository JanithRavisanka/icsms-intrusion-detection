import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

email_user = os.getenv('GMAIL_USER')
email_password = os.getenv('GMAIL_PASSWORD')
email_to = 'janithravisankax@gmail.com'
smtp_server = os.getenv('SMTP_SERVER')
smtp_port = int(os.getenv('SMTP_PORT'))


def send_email(subject, body, senders):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['Subject'] = subject

        # Attach the HTML version of the email
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        # senders = get_senders()
        for sender in senders:
            msg['To'] = sender
            server.sendmail(email_user, sender, text)
            print(f"Email sent to {sender} with subject: {subject}")
        server.quit()

    except Exception as e:
        print(f"Failed to send email: {e}")


def format_email_body(report_lines, start, end):
    start = start.strftime("%Y-%m-%d %H:%M:%S")
    end = end.strftime("%Y-%m-%d %H:%M:%S")
    html = """
    <html>
    <head>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <h2>User Activity Report</h2>"""

    html += f"<p>Report generated from {start} to {end}</p>"

    html += """<table>
            <tr>
                <th>User</th>
                <th>Current Score</th>
                <th>Z-Score</th>
                <th>Anomalies</th>
                <th>Action</th>
            </tr>
    """
    for line in report_lines:
        # print("x", line)
        user, current_score, z_score, anomalies, action = line.split(',')
        html += f"""
            <tr>
                <td>{user.split(': ')[1]}</td>
                <td>{current_score.split(': ')[1]}</td>
                <td>{z_score.split(': ')[1]}</td>
                <td>{anomalies.split(': ')[1]}</td>
                <td>{action.split(': ')[1]}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """
    return html


def format_anomaly_alert_email_body(anomalies, username):
    html = """
    <html>
    <head>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <h2>Anomaly Alert</h2>"""

    html += f"<p>Anomalies detected for user {username}</p>"

    html += """<table>
            <tr>
                <th>Score</th>
                <th>Z-Score</th>
                <th>Action</th>
            </tr>
    """
    for anomaly in anomalies:
        score = anomaly['score']
        z_score = anomaly['z_score']
        action = anomaly['action']
        html += f"""
            <tr>
                <td>{score}</td>
                <td>{z_score}</td>
                <td>{action}</td>

            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """
    return html


if __name__ == '__main__':
    send_email("Test Email", "This is a test email", ["janithravisankax@gmail.com"])
