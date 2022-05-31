from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
from pprint import pprint

#C:\Users\latyw\Parse1\lesson3\
options = Options()
options.add_argument("--start-maximized")

s = Service('./chromedriver.exe')
driver = webdriver.Chrome(service=s)
driver.get('https://www.mvideo.ru/')

#//mvid-shelf-group

driver.implicitly_wait(2)
html = driver.find_element(By.TAG_NAME, 'html')
for i in range(10):
    time.sleep(1)
    html.send_keys(Keys.PAGE_DOWN)
    if driver.find_element(By.XPATH, "//span[contains(text(), ' В тренде ')]"):
        botton = driver.find_element(By.XPATH, "//span[contains(text(), ' В тренде ')]")
        botton.click()
        break
    else:
        i=-1

strelka = driver.find_element(By.XPATH, "//mvid-carousel[@class='carusel ng-star-inserted']//button[@class='btn forward mv-icon-button--primary mv-icon-button--shadow mv-icon-button--medium mv-button mv-icon-button']//mvid-icon//*[local-name()='svg']")

for i in range(3):
    time.sleep(1)
    strelka.click()
    i=-1



time.sleep(10)
#elements = driver.find_element(By.XPATH, "//mvid-personal-block-collection[@class='page-carousel-padding personal-container ng-star-inserted']")
#pprint(elements)
driver.close()
