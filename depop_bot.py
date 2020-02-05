from bs4 import BeautifulSoup
import requests
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, exists, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects import postgresql
import time
import smtplib
from email.mime.text import MIMEText

search_term = "Golf Wang"

# Send emails to these addresses based on time request            
min_email = ['depopbot01@gmail.com', 'jordanwesley2002@icloud.com', 'itsacookie12@gmail.com', 'brennan.fane@icloud.com']
five_email = []
hour_email = ['depopbot01@gmail.com', 'megan_powderlyy@hotmail.com']
day_email = ['depopbot01@gmail.com', 'Brandonnlee@icloud.com', 'Golfwangreportersv2@gmail.com', '0liv3r.bridg3@gmail.com']


# Setting up database
db_base = declarative_base()

class Item(db_base):
    __tablename__ = "golf wang02"

    id = Column('id', Integer, primary_key=True)
    url = Column('url', String, unique=True)
    username = Column('username', String)
    price = Column('price', Integer)
    size = Column('size', String)
    description = Column('description', String)

engine = create_engine('sqlite:///golfwang.db', echo=False)
db_base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)

# Base url to build links from
base_url = "https://www.depop.com"

# Golf Wang search
depop_search = "/search/?q=golf%20wang"

# Set blank for first run through
min_count= 0
min_body = ""
min_lastSent = time.time()

five_count = 0
five_body = ""
five_lastSent = time.time()

hour_count = 0
hour_body = ""
hour_lastSent = time.time()

day_count = 0
day_body = ""
day_lastSent = time.time()

# Run continuosly
while True:

    # Get current time for checks later with email, so it stays consistent
    start_time = time.time()

    # Retry fetching website info if failed first time
    for attempt in range (0,3):
        try:
            # Fetch content from Golf search
            base_response = requests.get(base_url+depop_search, timeout=5)
            break

        # Handle timeout errors 
        except requests.exceptions.Timeout:
            print("Attempt: " + str(attempt) + " Failed")
            time.sleep(60)


    # Parse content from search
    base_content = BeautifulSoup(base_response.content, "html.parser")

    session = Session()

    # Scrape first 5 items on depop
    for listing in range(0,5):

        item = Item()
        
        # Grab each items personal URL
        item_url = base_content.find_all('a', attrs={"class":"styles__ProductCard-sc-5cfswk-2 YcaYq"})[listing]['href']

        item_exists = session.query(exists().where(Item.url == item_url))

        if not item_exists.scalar():

            # Add url to db object
            item.url = item_url

            # Changed because new items
            min_count += 1 
            five_count += 1
            hour_count += 1
            day_count += 1

            # Fetch item's page content
            item_response = requests.get(base_url+item_url, timeout=5)
            
            # Parse item's page content
            item_content = BeautifulSoup(item_response.content, "html.parser")
            
             # catch exception from no username (don't think this is possible)
            try:
                item_username = item_content.find('a', attrs={"class":"Link-sc-1urid-0 cuBKKA"}).text
                item.username = item_username
            except AttributeError:
                print("ERROR: Username could not be found")
                item.username = "N/A"

            # Catch exemption thrown from discounted price
            try:
                item_price = item_content.find('span', attrs={"class":"Pricestyles__FullPrice-sc-1vj3zjr-0 bzlnel"}).text
                item.price = item_price
            except AttributeError:
                try:
                    item_price = item_content.find('span', attrs={"class":"Pricestyles__DiscountPrice-sc-1vj3zjr-1 cUPtYA"}).text
                    item.price = item_price
                except AttributeError:
                    print("ERROR: Can't find PRICE")

            # Catch exemption thrown for no size
            try:
                item_size = item_content.find('tr', attrs={"data-testid":"product__singleSize"}).findChild("td",attrs={"class":"TableCell-zjtqe7-0 fxiPRF"}).text
                item.size = item_size
            except AttributeError:
                print("ERROR: No size for this item")
                item.size = "N/A"

            # Catch error thrown for no description
            try:
                item_description = item_content.find('p', attrs={"class":"Text-yok90d-0 styles__DescriptionContainer-uwktmu-9 gRfPzP"}).text
                item.description = item_description
            except AttributeError:
                print("ERROR: No description found")
                item.description = "N/A"

            # Catch error thrown from unicode characters that can't be converted into ASCII
            try:
                item_description = item_description.encode('ascii', 'replace')
                item_description = item_description.decode()
            except UnicodeEncodeError:
                item_description = item_description.encode('utf-8')

            # Building up the body of the email sent based off when it will be sent
            min_body += f"Item {min_count} \nwww.depop.com{item_url} \nUsername: {item_username} \nPrice: {item_price} \nSize: {item_size} \nDescription: {item_description} \n\n"
            five_body += f"Item {five_count} \nwww.depop.com{item_url} \nUsername: {item_username} \nPrice: {item_price} \nSize: {item_size} \nDescription: {item_description} \n\n"
            hour_body += f"Item {hour_count} \nwww.depop.com{item_url} \nUsername: {item_username} \nPrice: {item_price} \nSize: {item_size} \nDescription: {item_description} \n\n"
            day_body += f"Item {day_count} \nwww.depop.com{item_url} \nUsername: {item_username} \nPrice: {item_price} \nSize: {item_size} \nDescription: {item_description} \n\n"

            # Add item to database
            session.add(item)
    session.commit()

    # Close session         
    session.close()

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login('depopbot01@gmail.com', 'b2VGZENnWjnq83')

        if min_body and min_email and (start_time - min_lastSent) >= 60: 
            min_lastSent = time.time()
            
            if min_count > 1:
                subject = f"{search_term}: {min_count} new items"
            else:
                subject = f"{search_term}: {min_count} new item"
            
            min_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + min_body

            msg = f'Subject: {subject}\n\n{min_body}'

            smtp.sendmail('depopbot01@gmail.com', min_email, msg)

            min_count = 0
            min_body = "" 

        if five_body and five_email and (start_time - five_lastSent) >= 300: 
            five_lastSent = time.time()
            
            if five_count > 1:
                subject = f"{search_term}: {five_count} new items"
            else:
                subject = f"{search_term}: {five_count} new item"

            five_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + five_body

            msg = f'Subject: {subject}\n\n{five_body}'

            smtp.sendmail('depopbot01@gmail.com', five_email, msg)

            five_count = 0
            five_body = "" 
        
        if hour_body and hour_email and (start_time - hour_lastSent) >= 3600: 
            hour_lastSent = time.time()
            
            if hour_count > 1:
                subject = f"{search_term}: {hour_count} new items"
            else:
                subject = f"{search_term}: {hour_count} new item"

            hour_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + hour_body

            msg = f'Subject: {subject}\n\n{hour_body}'

            smtp.sendmail('depopbot01@gmail.com', hour_email, msg)

            hour_count = 0
            hour_body = "" 

        # TODO should I change this to send at a specific time of the day? That adds more complications...
        if day_body and day_email and (start_time - day_lastSent) >= 86400: 
            day_lastSent = time.time()
            
            if day_count > 1:
                subject = f"{search_term}: {day_count} new items"
            else:
                subject = f"{search_term}: {day_count} new item"

            day_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + day_body

            msg = f'Subject: {subject}\n\n{day_body}'

            smtp.sendmail('depopbot01@gmail.com', day_email, msg)

            day_count = 0
            day_body = ""

    # Get end time of program to modify sleep time        
    end_time = time.time()

    # How long to wait before running script again based of email needs,
    # And reset counts and email messages
    if min_email:
        try:
            time.sleep(60 - (end_time - start_time))
        except ValueError:
            time.sleep(60)

    elif five_email:
        try:
            time.sleep(300 - (end_time - start_time))
        except ValueError:
            time.sleep(300)

    elif hour_email:  
        try:
            time.sleep(3600 - (end_time - start_time))
        except ValueError:
            time.sleep(3600)

    elif day_email:
        try:
            time.sleep(86400 - (end_time - start_time))
        except ValueError:
            time.sleep(86400)

    else:
        print("ERROR: NO EMAIL")
        break
