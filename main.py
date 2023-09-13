import json

from src.project import Project
from src.scraper import *
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import src.db_ops as database
from src.document import Document


def script():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(message)s')
    logger = logging.getLogger('MyApp')
    logger.info('Starting the application')
    start_time = time.time()
    # check the list of projects (if new projects were added)
    # download_and_update_project_list()

    print(database.check_text().data)

    # for each project run the scrape / analysis
    '''
    projects = database.retrieve_db_project_list()
    runner = 0
    for project in projects:
        if runner < 10:
            project.scrape_and_analyse_documents()
            runner += 1
    '''

    end_time = time.time()
    logger.info(f"Finished the application in {end_time - start_time} seconds")


if __name__ == '__main__':
    script()
