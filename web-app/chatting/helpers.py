from django.template.loader import render_to_string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import certifi

def send_html_email(subject, recipient_list, html_message):
    try:
        sender_email = ""
        password = ""

        # Create a secure SSL context
        context = ssl.create_default_context(cafile=certifi.where())

        # Create the email content
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = ", ".join(recipient_list)

        # Add HTML content
        message.attach(MIMEText(html_message, "html"))

        # Connect to the server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(
                sender_email, recipient_list, message.as_string()
            )

        return True
    except Exception as e:
        print(e)
        return False
    
def forget_password_mail(domain, email, token):
    subject = "Your Forget password Link"

    # Get the current domain
    # domain = current_site
    print(domain)
    context = {
        "token": token,
        "domain": domain,  # Pass the domain to the template
    }
    html_message = render_to_string("forget_password_mail.html", context)

    recipient_list = [email]
    send_html_email(subject, recipient_list, html_message)
    return True
