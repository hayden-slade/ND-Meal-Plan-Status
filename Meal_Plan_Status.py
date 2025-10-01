# !/usr/bin/env python3

import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

##################
#  Helper Functions
##################

def clear_console():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')

def parse_flexible_date(date_str, year):
    date_str = date_str.replace('.', '')
    match = re.match(r'^([A-Za-z]+) (\d+)', date_str)
    if match:
        month, day = match.groups()
        return datetime.strptime(f"{month} {day} {year}", "%b %d %Y")
    raise ValueError(f"Unrecognized date format: {date_str}")

def get_semester_dates(url, today):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    result = {}
    for head in soup.find_all('h3'):
        semester = head.get_text().strip()
        if ('Fall' in semester and str(today.year) in semester) or \
           ('Spring' in semester and (str(today.year) in semester or str(today.year+1) in semester)):
            table = head.find_next('table')
            start, end = None, None
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 2:
                    continue
                desc = cells[1].get_text()
                if 'Classes begin' in desc:
                    start = parse_flexible_date(cells[0].get_text(), today.year if 'Fall' in semester else today.year+1)
                if 'Undergraduate Halls close' in desc:
                    end = parse_flexible_date(cells[0].get_text(), today.year if 'Fall' in semester else today.year+1)
            if start and end:
                result[semester] = (start, end)
    for sem, (start, end) in result.items():
        if start <= today <= end:
            return sem, start, end
    return None, None, None

##################
#  Selenium: Automated Login and Data Extraction
##################

def get_flex_points_and_swipes():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://get.cbord.com/irish1card/full/login.php")
    wait = WebDriverWait(driver, 180)
    wait.until(lambda d: "Flex Points" in d.page_source)
    time.sleep(2)
    flex_points_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'Flex Points')]/following-sibling::td")
    flex_points = flex_points_elem.text.replace("$", "").strip()
    meal_swipes_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'Block 230')]/following-sibling::td")
    meal_swipes = meal_swipes_elem.text.strip()
    driver.quit()
    return float(flex_points), int(meal_swipes)

##################
#  Main Logic: Calculations and Output
##################

def main():
    today = datetime.now()
    url = "https://registrar.nd.edu/calendars/"
    semester, start_date, end_date = get_semester_dates(url, today)
    if not (start_date and end_date):
        print("Could not auto-detect semester dates. Using defaults.")
        start_date = datetime(today.year, 8, 20)
        end_date = datetime(today.year, 12, 21)
    total_days = (end_date - start_date).days
    days_since_start = (today - start_date).days
    days_till_end = (end_date - today).days

    flex_points_left, meal_swipes_left = get_flex_points_and_swipes()
    flex_point_used = 500 - flex_points_left

    meal_swipes_left_per_day = meal_swipes_left / days_till_end if days_till_end else 0
    meal_swipes_should_left = 230 - ((230 / total_days) * days_since_start)
    flex_points_per_day = 500 / total_days
    flex_points_should_used = flex_points_per_day * days_since_start
    flex_points_should_left = 500 - flex_points_should_used

    clear_console()
    print(f"Start Date: {start_date.strftime('%m-%d-%Y')}")
    print(f"End Date: {end_date.strftime('%m-%d-%Y')}\n")
    print(f"Flex Point Status:")
    print(f"Flex Points Left: {round(flex_points_left, 2)}")
    print(f"Flex Points Should Have Left: {round(flex_points_should_left, 2)}")
    print(f"Flex Point Differential: {round(flex_points_left-flex_points_should_left, 2)}")
    print(f"Flex Points Weekly Left: {round((flex_points_left/days_till_end) * 7, 2) if days_till_end else 0}")
    print(f"Flex Points Daily Left: {round(flex_points_left/days_till_end, 2) if days_till_end else 0}")
    projection = 500 - ((flex_point_used/days_since_start) * total_days) if days_since_start else flex_points_left
    print(f"Projection of Final Flex Points: {round(projection, 2)}")
    print(f"\nMeal Swipe Status:")
    print(f"Meal Swipes Left: {meal_swipes_left}")
    print(f"Meal Swipes Left Per Day: {round(meal_swipes_left_per_day, 2)}")
    print(f"Meal Swipes Differential: {round(meal_swipes_left-meal_swipes_should_left, 2)}")
    projection_swipes = 230 - ((230-meal_swipes_left)/days_since_start * total_days) if days_since_start else meal_swipes_left
    print(f"Projection of Final Meal Swipes: {round(projection_swipes, 2)}")
    input("\nPress Enter to Exit")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)