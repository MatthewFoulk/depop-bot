import time
from selenium import webdriver

# Open FireFox browser and navigate to page
driver = webdriver.Firefox()
driver.get("https://www.depop.com/search/?q=bonobos")

# Selenium script to scroll to true bottom of page
SCROLL_PAUSE_TIME = 0.5

lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")

while True:
    lastCount = lenOfPage
    time.sleep(SCROLL_PAUSE_TIME)
    lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    if lastCount==lenOfPage:
        break