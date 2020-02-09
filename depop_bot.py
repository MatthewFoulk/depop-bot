from bs4 import BeautifulSoup
import requests
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, exists, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects import postgresql
import time
import smtplib
from email.mime.text import MIMEText
import sys

def main():

    if not len(sys.argv) == 2:
        print("Missing password")
        sys.exit()

    # What search is being tracked on depop
    search_term = "golf wang"

    # Send emails to these addresses based on time request            
    min_email = ['depopbot01@gmail.com', 'jordanwesley2002@icloud.com', 'itsacookie12@gmail.com', 'brennan.fane@icloud.com']
    five_email = []
    hour_email = ['depopbot01@gmail.com', 'megan_powderlyy@hotmail.com']
    day_email = ['depopbot01@gmail.com', 'Brandonnlee@icloud.com', 'Golfwangreportersv2@gmail.com', '0liv3r.bridg3@gmail.com']


    # Setting up database
    db_base = declarative_base()

    # define columns of sql database and table name
    class Item(db_base):
        __tablename__ = search_term

        id = Column('id', Integer, primary_key=True)
        url = Column('url', String, unique=True)
        username = Column('username', String)
        price = Column('price', Integer)
        size = Column('size', String)
        description = Column('description', String)

    # Configure engine and setup session
    engine = create_engine('sqlite:///' + search_term + '.db', echo=False)
    db_base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    # Building search url
    base_url = "https://www.depop.com"
    search_url = build_search(search_term)

    # Starting values for various time-related variables
    min_count = five_count = hour_count = day_count = 0
    min_body = five_body = hour_body = day_body = ""

    # TODO may not need to have these in main method
    min_last_sent = five_last_sent = hour_last_sent = day_last_sent = time.time()

    # Run script continuously
    while True:
        
        # Time that script begins running each time through
        start_time = time.time()

        # Get search url response
        base_response = get_search_response(base_url, search_url)

        # Parse reponse from search using beautiful soup and html parser
        base_content = BeautifulSoup(base_response.content, "html.parser")

        # start session
        session = Session()

        # Scrape first item listings on search url
        for listing in range(0,5):

            item = Item()

            # Store listings url
            item_url = base_content.find_all('a', attrs={"class":"styles__ProductCard-sc-5cfswk-2 YcaYq"})[listing]['href']

            # Check if listing is new
            if not check_exists(session, Item.url, item_url):
                
                # Add to database
                item.url = item_url

                # Increase each count by 1 for the new item 
                min_count += 1 
                five_count += 1
                hour_count += 1
                day_count += 1

                # Get item listing url response
                item_response = get_item_response(base_url, item_url)

                # Parse item listing content
                item_content = BeautifulSoup(item_response.content, "html.parser")

                # Fetch and set item username
                item.username = get_username(item_content)

                # Fetch and set item price
                item.price = get_price(item_content)

                # Fetch and set item size
                item.size = get_size(item_content)

                # Fetch and set item description
                item.description = get_description(item_content)

                # Add new item to email body (This likely is currently vulnerable to SQL injection attacks... should look to fix)
                min_body += f"Item {min_count} \nwww.depop.com{item.url} \nUsername: {item.username} \nPrice: {item.price} \nSize: {item.size} \nDescription: {item.description} \n\n"
                five_body += f"item {five_count} \nwww.depop.com{item.url} \nUsername: {item.username} \nPrice: {item.price} \nSize: {item.size} \nDescription: {item.description} \n\n"
                hour_body += f"item {hour_count} \nwww.depop.com{item.url} \nUsername: {item.username} \nPrice: {item.price} \nSize: {item.size} \nDescription: {item.description} \n\n"
                day_body += f"item {day_count} \nwww.depop.com{item.url} \nUsername: {item.username} \nPrice: {item.price} \nSize: {item.size} \nDescription: {item.description} \n\n"

                # Add item to database
                session.add(item)

        session.commit()
        session.close()

        # Setup secure connection for email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.ehlo()
            
            # TODO replace password with sys.argv[1]
            # Login into account, password is passed as the second cmd line argument
            smtp.login('depopbot01@gmail.com', sys.argv[1])

            # Send email to people asking for every minute updates if a minute has passed
            # and new items where scraped (check min_body) and people exist (min_email)
            if min_body and min_email and (start_time - min_last_sent) >= 60:
                
                # Update last sent time
                min_last_sent = time.time()

                # Build message
                msg = get_min_msg(min_count, search_term, min_body)
                
                # Send email
                smtp.sendmail('depopbot01@gmail.com', min_email, msg)

                # Reset email body and item count
                min_count = 0
                min_body = ""

            # Repeat previous steps for 5 minute emails
            if five_body and five_email and (start_time - five_last_sent) >= 300:
                
                five_last_sent = time.time()

                msg = get_five_msg(five_count, search_term, five_body)

                smtp.sendmail('depopbot01@gmail.com', five_email, msg)

                five_count = 0
                five_body = ""

            # Repeat previous steps for hourly emails
            if hour_body and hour_email and (start_time - hour_last_sent) >= 3600:
                
                hour_last_sent = time.time()

                msg = get_hour_msg(hour_count, search_term, hour_body)

                smtp.sendmail('depopbot01@gmail.com', hour_email, msg)

                hour_count = 0
                hour_body = ""
            
             # Repeat previous steps for daily emails
            if day_body and day_email and (start_time - day_last_sent) >= 86400:
                
                day_last_sent = time.time()

                msg = get_day_msg(day_count, search_term, day_body)

                smtp.sendmail('depopbot01@gmail.com', day_email, msg)

                day_count = 0
                day_body = ""

        # Determine length of rest before running program again
        get_rest_time(min_email, five_email, hour_email, day_email)



# Build search portion of url using the search term
def build_search(search_term):

    # Initialize search url
    search_url = "/search/?q="

    # Count words/iterations
    counter = 0

    # Build the seach_url 
    for word in search_term.split():

        # Only add word if this is the first/only word
        if counter == 0:
            search_url += word

        # Otherise add %20 before the word
        else:
            search_url += "%20" + word

        # increase counter for each word
        counter += 1
    
    return  search_url

# Fetch the content from sarch url
def get_search_response(base_url, search_url):

    # Try three times if failed
    for attempt in range (0,3):

        try:
            base_response = requests.get(base_url + search_url, timeout=5)
            return base_response

        # Handle timeout errors 
        except requests.exceptions.Timeout:
            print("Attempt: " + str(attempt) + " Failed")
            time.sleep(60)

    # Break out of script if failure to get URL after 3 tries
    sys.exit("Failed to get response from search url") 

# Check if item already exists in database
def check_exists(session, db_url, item_url):
     return session.query(exists().where(db_url == item_url)).scalar()

# Fetch the content from item url
def get_item_response(base_url, item_url):

    try:
        item_response = requests.get(base_url + item_url, timeout=5)
        return item_response

    # Handle timeout errors
    except requests.exceptions.Timeout:
        print("Failed to get item urls information from: " + base_url + item_url)

# Fetch item username
def get_username(item_content):

    # catch exception from no username (don't think this is possible)
    try:
        item_username = item_content.find('a', attrs={"class":"Link-sc-1urid-0 cuBKKA"}).text
        return item_username
    except AttributeError:
        print("ERROR: Username could not be found")
        return "N/A"

# Fetch item price
def get_price(item_content):
    
    # Catch exemption thrown from discounted price
    try:
        item_price = item_content.find('span', attrs={"class":"Pricestyles__FullPrice-sc-1vj3zjr-0 bzlnel"}).text
        return item_price
    except AttributeError:
        try:
            item_price = item_content.find('span', attrs={"class":"Pricestyles__DiscountPrice-sc-1vj3zjr-1 cUPtYA"}).text
            return item_price
        except AttributeError:
            print("ERROR: Can't find PRICE")
            return "N/A"


def get_size(item_content):

    # Catch exemption thrown for no size
    try:
        item_size = item_content.find('tr', attrs={"data-testid":"product__singleSize"}).findChild("td",attrs={"class":"TableCell-zjtqe7-0 fxiPRF"}).text
        return item_size
    except AttributeError:
        print("ERROR: No size for this item")
        return "N/A"

def get_description(item_content):

     # Catch error thrown for no description
    try:
        item_description = item_content.find('p', attrs={"class":"Text-yok90d-0 styles__DescriptionContainer-uwktmu-9 gRfPzP"}).text
        
        # Catch error thrown from unicode characters that can't be converted into ASCII
        try:
            item_description = item_description.encode('ascii', 'replace')
            item_description = item_description.decode()
        except UnicodeEncodeError:
            item_description = item_description.encode('utf-8')

        return item_description

    except AttributeError:
        print("ERROR: No description found")
        return "N/A"

# Build message for minute email
def get_min_msg(min_count, search_term, min_body):
            
    if min_count > 1:
        subject = f"{search_term}: {min_count} new items"
    else:
        subject = f"{search_term}: {min_count} new item"
    
    min_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + min_body

    return f'Subject: {subject}\n\n{min_body}'

# Build message for five minute email
def get_five_msg(five_count, search_term, five_body):
            
    if five_count > 1:
        subject = f"{search_term}: {five_count} new items"
    else:
        subject = f"{search_term}: {five_count} new item"
    
    five_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + five_body

    return f'Subject: {subject}\n\n{five_body}'

# Build message for hourly email
def get_hour_msg(hour_count, search_term, hour_body):
            
    if hour_count > 1:
        subject = f"{search_term}: {hour_count} new items"
    else:
        subject = f"{search_term}: {hour_count} new item"
    
    hour_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + hour_body

    return f'Subject: {subject}\n\n{hour_body}'

# Build message for daily email
def get_day_msg(day_count, search_term, day_body):
            
    if day_count > 1:
        subject = f"{search_term}: {day_count} new items"
    else:
        subject = f"{search_term}: {day_count} new item"
    
    day_body = "Please Provide Feedback: https://forms.gle/hEWHXaXJhrZFX7Dt6 \n\n" + day_body

    return f'Subject: {subject}\n\n{day_body}'

def get_rest_time(min_email,five_email,hour_email, day_email):

    if min_email:
        time.sleep(60)

    elif five_email:
        time.sleep(300)

    elif hour_email:  
        time.sleep(3600)

    elif day_email:
        time.sleep(86400)




if __name__ == "__main__":
    main()