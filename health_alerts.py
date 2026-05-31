import smtplib, os, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(subject, body):
    try:
        sender = os.getenv("ALERT_EMAIL", "alerts@slh-nft.com")
        password = os.getenv("ALERT_EMAIL_PASS", "")
        receiver = "osif.e.u@gmail.com"
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"📧 Alert sent to {receiver}")
    except Exception as e:
        print(f"Email error: {e}")

def send_sms_alert(message):
    try:
        account_sid = os.getenv("TWILIO_SID", "")
        auth_token = os.getenv("TWILIO_TOKEN", "")
        from_num = os.getenv("TWILIO_PHONE", "")
        to_num = "+972584203384"
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        requests.post(url, data={"From": from_num, "To": to_num, "Body": message}, auth=(account_sid, auth_token))
    except Exception as e:
        print(f"SMS error: {e}")

def check_and_alert():
    """Run health checks and alert if issues found."""
    issues = []
    try:
        conn = get_db()
        conn.close()
    except:
        issues.append("❌ Database connection failed")
    try:
        r = requests.get("https://api.telegram.org", timeout=5)
        if r.status_code != 200:
            issues.append("⚠️ Telegram API unreachable")
    except:
        issues.append("❌ Telegram API unreachable")
    if issues:
        body = "<h2>🚨 SLH Health Alert</h2><ul>" + "".join(f"<li>{i}</li>" for i in issues) + "</ul>"
        send_email_alert("🚨 SLH System Alert", body)
        send_sms_alert("SLH Alert: " + "; ".join(issues))
