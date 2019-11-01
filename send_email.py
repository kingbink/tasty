import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import re

from settings import email_address, email_password

def send_email(to_address, summary_data, winner_data):
    port = 587  # For SSL
    sender_email = email_address
    # check to_address for valid email
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    receiver_email = to_address
    # if(re.search(regex,receiver_email) is None):
    #     return False
    # Create a secure SSL context
    #context = ssl.create_default_context()
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Tasty Email for {}".format(summary_data.keys()[0])
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
    html = ""
    for name in summary_data:
        html_name = "<h1>Name: {}</h1>".format(name.title())
        html += html_name
        for wine in summary_data[name]:
            html_wine = "<h2>{:40}</h2><p>".format(wine.title())
            html += html_wine
            if "rating" in summary_data[name][wine]:
                html_rating = "rating: {}<br>".format(summary_data[name][wine]["rating"])
                html += html_rating
            if "brought" in summary_data[name][wine]:
                html += "  Mine<br>"
            if "guessed" in summary_data[name][wine]:
                html += "  My Guess<br>"
            if "notes" in summary_data[name][wine]:
                html += "Notes: {}<br>".format(summary_data[name][wine]["notes"])
            html += "</p>"
    html += "<br><h1>From Winners to Losers</h1>"
    cnt = 1
    for wine in winner_data:
        html += "<h2>{}: {}</h2><p>".format(cnt, wine.title())
        html += "Total Points: {}   Brought By: {}".format(winner_data[wine]['score'], winner_data[wine]['brought_by'].title())
        if "tie" in winner_data[wine]:
            html += " TIE"
        html += "</p>"
        cnt += 1
    
    print(html)    
    part1 = MIMEText(json.dumps(summary_data) + json.dumps(winner_data), "plain")
    part2 = MIMEText(html, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)
    
    #print(message)
    
    
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
    send_email('king', "HTML test section", "text test")