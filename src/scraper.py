import asyncio
import os
import time
import shutil
import pandas as pd
from pyppeteer import launch
import globals
import logging


def download_project_list(retries=3):
    logger = logging.getLogger('MyApp')
    if not file_download_required():
        return True
    for i in range(retries):
        logger.info(f'Trial number {i} to retrieve the project list starting.')
        try:
            asyncio.get_event_loop().run_until_complete(access_project_list())
        except Exception as e:
            print(f"Try {i}: that didn't work due to the following error: {e}")
        filename = recently_created_file_exists()
        if filename != "False":
            check_and_move_or_replace(filename)
            return True
    return False


def find_redd_ids():
    logger = logging.getLogger('MyApp')
    logger.info('Finding REDD AFOLU project IDs.')
    file_path = os.path.join(os.getcwd(), 'files', 'allprojects.xlsx')
    df = pd.read_excel(file_path)
    filtered_df = df[(df['AFOLU Activities'] == 'REDD') & (df['Status'] == 'Registered')]
    project_ids = filtered_df['ID'].values
    logger.info('There are ' + str(len(project_ids)) + ' registered REDD AFOLU projects.')
    return project_ids


async def access_project_list():
    logger = logging.getLogger('MyApp')
    logger.info('Launching managed browser to retrieve project list.')
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto(globals.URL)
    await page.waitForXPath('//button[@type="submit"]')
    buttons = await page.xpath('//button[@type="submit"]')
    await buttons[0].click()
    await page.waitForSelector('.alert-text.mx-4')
    await page.waitForXPath('//button[@title="Download Excel"]')
    button = await page.xpath('//button[@title="Download Excel"]')
    await button[0].click()
    logger.info('Clicked "Download Excel". Waiting and checking if file was successfully downloaded.')
    for i in range(6):
        await asyncio.sleep(3)
        if recently_created_file_exists():
            logger.info('File was successfully downloaded.')
            break
    logger.info('Closing managed browser.')
    await browser.close()


def recently_created_file_exists():
    current_time = time.time()
    two_minutes_ago = current_time - 120  # 120 seconds is 2 minutes
    dl_path = os.path.expanduser('~/Downloads')
    for filename in os.listdir(dl_path):
        if filename.startswith("allprojects"):
            creation_time = os.path.getctime(os.path.join(dl_path, filename))
            if creation_time >= two_minutes_ago:
                return filename
    return None


def check_and_move_or_replace(filename):
    logger = logging.getLogger('MyApp')
    source_file = os.path.expanduser(f'~/Downloads/{filename}')
    destination_path = os.path.join(os.getcwd(), 'files', 'allprojects.xlsx')
    if os.path.exists(destination_path):
        logger.info('FYI: A file with that name already existed, it will be replaced.')
    shutil.move(source_file, destination_path)
    logger.info('File successfully downloaded and moved into project directory.')


def file_download_required():
    current_time = time.time()
    one_day_ago = current_time - (60*60*24)
    path = os.path.join(os.getcwd(), 'files', 'allprojects.xlsx')
    if os.path.exists(path):
        creation_time = os.path.getctime(path)
        if creation_time >= one_day_ago:
            logging.getLogger('MyApp').info('Download not required as a file exists that is younger than 24h.')
            return False
    return True
