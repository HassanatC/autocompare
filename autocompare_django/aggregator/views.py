from django.shortcuts import render, redirect
from .forms import CarURLForm
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver import Chrome
import re
import time
import json
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

# Create your views here.

@api_view(['POST'])
def main_view(request):

    if request.method == 'POST':
        form = CarURLForm(request.data)
        if form.is_valid():
            url = form.cleaned_data['url']
            driver = Chrome()
            data = scrape_car_data(url, driver)
            motors_data = search_motors_similar(data, driver)
            search_fb(data, driver)

            driver.quit()
            return Response({"data": data, "motors_data": motors_data}, status=200)
        else:
            return Response({"error": "Invalid form"}, status=400)
    else:
        return Response({"error": "Method not allowed"}, status=405)

def scrape_car_data(url, driver):
    data = {}
    driver.get(url)
    wait = WebDriverWait(driver, 1)

    try:
        price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h2[data-testid="advert-price"]')))
        data["price"] = price_element.text
    except Exception as e:
        data["price"] = f"Error: {e}"

    try:
        image_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img')))
        data["image_url"] = image_element.get_attribute('src')
    except Exception as e:
        data["image_url"] = f"Error: {e}"

    try:
        brand_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'p[data-testid="advert-title"]')))
        data["brand"] = brand_element.text
    except Exception as e:
        data["brand"] = f"Error: {e}"

    try:
        mileage_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Mileage')]/following-sibling::p")))
        data["mileage"] = mileage_element.text
    except Exception as e:
        data["mileage"] = f"Error: {e}"

    try:
        registration_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Registration')]/following-sibling::p")))
        data["registration"] = registration_element.text
    except Exception as e:
        data["registration"] = f"Error: {e}"

    try:
        previous_owners_element = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Previous')]/following-sibling::p")))
        full_text = previous_owners_element.text
        owner_count_match = re.search(r'\d+', full_text)
        if owner_count_match:
            owner_count = owner_count_match.group() 
            data["previous_owners"] = owner_count
        else:
            data["previous_owners"] = "Could not determine"
    except Exception as e:
        data["previous_owners"] = f"Not Available"

    return data

def search_motors_similar(data, driver):
    trusted_domain = "motors.co.uk"
    query = f"{data['brand']} {data['registration']} with {data['mileage']} for sale Motors UK"
    driver.get("https://www.google.com")

    handle_cookie_popup(driver)

    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3")))
    
    #finds the relevant motors link
    search_results = driver.find_elements(By.XPATH, "//h3/ancestor::a")
    all_links = [link.get_attribute("href") for link in search_results if link.get_attribute("href")]

    motors_links = [link for link in all_links if link and trusted_domain in link]

    scraped_data = {}
    #if motors link is found, proceed to scrap the price. rudimentary currently
    
    if motors_links:
        scraped_data_list = []
        motors_link_to_click = motors_links[0]
        link_element = driver.find_element(By.XPATH, f"//a[@href='{motors_link_to_click}']")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@href='{motors_link_to_click}']")))
        link_element.click()
    
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".title-3")))
      
            print("Trying to find price elements...")
            price_elements = driver.find_elements(By.CSS_SELECTOR, ".title-3")

            # loops through the price elements in motors. finds them and scrapes
            for price_element in price_elements:
                parent_element = price_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'result-card box-shadow-hover')]")

                price = price_element.text
                print(f"Price element found. Text: {price}")

                link_element = parent_element.find_element(By.CSS_SELECTOR, "a.result-card__link")
                link = link_element.get_attribute("href")

                mileage_element = parent_element.find_element(By.CSS_SELECTOR, "span.vehicle-info__mileage")
                mileage = mileage_element.text
                print(f"Mileage element found. Text: {mileage}")

                image_element = parent_element.find_element(By.CSS_SELECTOR, ".result-card__image-container .lazy img")
                #grabs first image
                thumbnail_image = image_element.get_attribute('src')

                scraped_data = {
                'price': price,
                'link': link,
                'mileage': mileage,
                'thumbnail_image': thumbnail_image
                }
                scraped_data_list.append(scraped_data)

        except Exception as e:
            print(f"Error while scraping price: {e}")
            scraped_data = {
                'price': 'Error',
                'link': 'Error'
            }

    print("Motors Link:", motors_links)

    scraped_data_list = sort_scraped_data_by_price(scraped_data_list)
    return scraped_data_list



def search_fb(data, driver):
    #todo: fix the query system and link clicking. way too basic
    trusted_domain = "facebook.com/marketplace"
    query = f"facebook marketplace london used {data['brand']} {data['registration']} {data['mileage']} for sale"

    driver.get("https://www.google.com")
    # search for relevant fb marketplace listing
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(query)
    search_box.submit()

    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3")))

    search_results = driver.find_elements(By.XPATH, "//h3/ancestor::a")
    all_links = [link.get_attribute("href") for link in search_results if link.get_attribute("href")]

    fb_links = [link for link in all_links if link and trusted_domain in link]
    scraped_data_list = []

    #access fb link similar to how motors does it

    if fb_links:
        fb_link_to_click = fb_links[1]
        link_element = driver.find_element(By.XPATH, f"//a[@href='{fb_link_to_click}']")
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@href='{fb_link_to_click}']")))
        link_element.click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.x78zum5')))

        price_elements = driver.find_elements(By.CSS_SELECTOR, "span.x78zum5 div span[dir='auto']")
        model_elements = driver.find_elements(By.XPATH, '//span[@class="x1lliihq x6ikm8r x10wlt62 x1n2onr6"]')
        mileage_elements = driver.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6.xlyipyv.xuxw1ft.x1j85h84")
        link_elements = driver.find_elements(By.XPATH, "//div[@class='x3ct3a4']//a[contains(@class, 'x1i10hfl')]")




        if price_elements and model_elements and mileage_elements and link_elements:
            #goes through elements and returns the data
            scraped_data = []
            for price, model, mileage, link in zip(price_elements, model_elements, mileage_elements, link_elements):

                relative_link = link.get_attribute("href")
                absolute_link = urljoin("https://www.facebook.com", relative_link)
                scraped_data.append({
                    "Price": price.text,
                    "Model": model.text,
                    "Mileage": mileage.text,
                    "Link": absolute_link
                })
                scraped_data_list.append(scraped_data)

            print(scraped_data_list)
        else:
            print("Elements not found")
        
        return scraped_data_list

"""
def handle_fb_cookie(driver):
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Allow all cookies']"))
        )

        accept_button.click()
    except Exception as e:
        print(f"Error handling cookie popup: {e}")
"""
def sort_scraped_data_by_price(scraped_data_list):
    #method to sort the returned data by cheapest first. currently the standard
    scraped_data_list = [
        {k: float(v.replace('£', '').replace(',', '')) if k == 'price' else v for k, v in item.items()}
        for item in scraped_data_list
    ]

    #sort the list of dictionaries
    sorted_list = sorted(scraped_data_list, key=lambda x: x['price'])
    return sorted_list[:10]

def handle_cookie_popup(driver):
    try:
        accept_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='none'][class='QS5gu sy4vM']"))
        )
        accept_button.click()
    except Exception as e:
        print(f"Error handling cookie popup: {e}")

# will work on soon
