import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

from settings import email_address, email_password

def send_email(to_address, html, text='TEXT backup'):
    port = 587  # For SSL
    sender_email = email_address
    # check to_address for valid email
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    receiver_email = to_address
    if(re.search(regex,receiver_email) is None):
        return False
    # Create a secure SSL context
    #context = ssl.create_default_context()
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Tasty Email for your personal scores"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    # Create the plain-text and HTML version of your message
    # text = """\
    # New Test"""
    # html = """\
    # <html>
    #   <body>
    #     <p>Hi,<br>
    #        New Test<br>
    #        <a href="http://www.realpython.com">Real Python</a> 
    #        has many great tutorials.
    #     </p>
    #   </body>
    # </html>
    # """
    
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)
    
    
    server = smtplib.SMTP("smtp.gmail.com:{}".format(port))
    server.starttls()
    try:
        server.login(sender_email, email_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except smtplib.SMTPHeloError:
        print("Something weird with login")
    except smtplib.SMTPAuthenticationError:
        print("Login Failure")
    except smtplib.SMTPException:
        print("Something really bad")
    
    return False
        
if __name__ == '__main__':
    send_email('king.bink', "HTML test section", "text test")