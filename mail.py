import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from data import getcus_mail,savememori_mail
import time

def conver_time(t1me):
    abc = t1me.split('-')
    return abc[1]+'/'+abc[2]+'/'+abc[0]

def send_custom_email(list_mail,site):
    json_ = {
            "getcus.com": getcus_mail,
            "savememori.com": savememori_mail
        }
    faillist = []    
    with smtplib.SMTP_SSL(json_[site]['smtp_host'][0], json_[site]['smtp_host'][1]) as server:
        server.connect(json_[site]['smtp_host'][0], json_[site]['smtp_host'][1])
        server.login(json_[site]['imap_user'], json_[site]['imap_pass'])   
        site_name = site.replace('.com','').capitalize()
        
        for customer in list_mail:
            order_name = customer[3]
            order_date = customer[4]
            recipient = customer[0]
            # recipient = 'vpscoi123@gmail.com'
            name = customer[1]
            body_text = ''
            link = customer[5]
            numbers = len(link)
            links = "\n                ".join(link)
            if numbers>1:
                
                body_text = f"""    
                Dear {name},

                Thank you for visiting our website and making your purchase!
                We're contacting you today to provide you with a preview of your order {order_name} which was placed on {conver_time(order_date)}
                The followings are the links to those mockups: 
                {links}

                We will automatically fulfill this order after 12 hours from the time we send you this email

                Thank you so much for your support and we are looking forward to hearing from you!
                If you have any concerns, please do not hesitate to contact us.    
                We hope to hear your confirmation as soon as possible.

                Be safe and stay well!
                The {site_name} Team.
                """
            else:    
                date = conver_time(order_date)
                body_text = f"""\
                    Dear {name},

                    Thank you for visiting our website and making your purchase!
                    We're contacting you today to provide you with a preview of your order {order_name} which was placed on {date}
                    The following is a link to that mockup: 
                    {links}

                    We will automatically fulfill this order after 12 hours from the time we send you this email
                    Thank you so much for your support and we are looking forward to hearing from you!

                    If you have any concerns, please do not hesitate to contact us.    
                    We hope to hear your confirmation as soon as possible.
                    Be safe and stay well!

                    The {site_name} Team. 
                """
            mail = MIMEMultipart('alternative')
            mail['Subject'] = f"{order_name} - PREVIEW CONFIRMATION"
            mail['From'] = json_[site]['imap_user']
            mail['To'] = recipient
            mail.attach(MIMEText(body_text, 'plain'))
            mail_data = mail.as_bytes()
            i = 0
            sentmail = False
            while i < 4:
                try:
                    a = server.sendmail(json_[site]['imap_user'],recipient,mail_data)
                    i = 4
                    sentmail = True
                    time.sleep(0.5)
                except:
                    i+=1
            if not sentmail:
                faillist.append(order_name)
    return faillist