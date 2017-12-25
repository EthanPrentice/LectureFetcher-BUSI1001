from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re
import requests
import os
import sys
from getpass import getpass

COURSE_URL = 'https://culearn.carleton.ca/moodle/course/view.php?id=92224'
CATEGORIES_XPATH = '//*[@id="yui_3_17_2_1_1509315930278_248"]'
INVALID_CHARS = ['.', '~', '#', '%', '&', '*', '{', '}', '\\', ':', '<', '>', '?', '/', '+', '|', '"']

log_path = os.path.dirname(os.path.realpath(sys.argv[0]))+'/err.log'

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('disable-gpu')
options.add_argument('disable-logging')
options.add_argument('silent')
driver = webdriver.Chrome(executable_path=r'chromedriver.exe',
                          service_args=["--verbose", "--log-path="+log_path, '--silent'],
                          chrome_options=options)


def sign_in():
    while driver.current_url != COURSE_URL:
        username = input("Username: ")
        password = getpass("Password: ")

        driver.get(COURSE_URL)

        driver.find_element_by_xpath('//*[@id="user"]').send_keys(username)
        driver.find_element_by_xpath('//*[@id="pass"]').send_keys(password + Keys.ENTER)

        if driver.current_url == COURSE_URL:
            break
        else:
            print("\nWrong credentials. Please Try Again.\n")


def download_mp4(name, week, url, save_dir):
    valid_name = name
    for char in INVALID_CHARS:
        valid_name = valid_name.replace(char, '')
    try:
        driver.get(url)
        video_url = re.findall('https://content\.screencast\.com/.*?\.mp4', driver.page_source)[0]
        file_name = f"{save_dir}/Week {week}/{valid_name}.mp4"

        r = requests.get(video_url, stream=True)
        if r.status_code == 200:
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

        print(f"Downloaded Week {week} - {name} successfully.")

    except requests.exceptions.ConnectionError as e:
        print("Error connecting to CULearn.  Please check your connection.")
        quit(code=-1)
    except requests.exceptions.Timeout:
        print("Connection timed out.  Please check your connection.")
        quit(code=-1)
    except requests.exceptions.RequestException as e:
        print("An unknown error occurred while attempting to connect to the API service.")
        print(f"Error: {e}")
        quit(code=-1)


def main():
    sign_in()

    while True:
        save_dir = input("Save directory: ")

        if os.path.isdir(save_dir):
            break
        else:
            print("Directory does not exist.  Please enter a valid directory.\n")

    while True:
        week_input = input("What week(s) would you like to download? ")
        try:
            weeks = week_input.strip().split(',')
            weeks = [int(x) for x in weeks]
            break
        except ValueError:
            pass

    for week_number in weeks:
        week = driver.find_element_by_xpath(f'//*[@id="section-{week_number+4}"]')

        innerHTML = week.get_attribute("innerHTML")

        video_links = re.findall('https://culearn\.carleton\.ca/moodle/mod/url/view\.php\?id=\d{7}', innerHTML)
        video_names = re.findall('Video \d - .*?\(', innerHTML)
        video_names = [s[:-2] for s in video_names]

        video_dict = {}
        for name, url in zip(video_names, video_links):
            video_dict[name] = url
        del video_links, video_names

        if not os.path.isdir(f"{save_dir}/Week {week_number}"):
            os.makedirs(f"{save_dir}/Week {week_number}")

        print(f"\nDownloading videos from week {week_number}")

        for name in video_dict.keys():
            download_mp4(name, week=week_number, url=video_dict[name], save_dir=save_dir)

        driver.get(COURSE_URL)


main()
