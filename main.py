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
    # download_project_list()
    # project_ids = find_redd_ids()
    # database.update_project_list(project_ids)

    # for each project run the scrape / analysis
    # projects = database.retrieve_project_list()

    # test code:
    # Project(2558).scrape_and_analyse_documents()
    docs = database.retrieve_existing_project_documents(Project(2558))
    print(docs[0].filename)
    print(docs[0].text)
    print(docs[0].text.count(" "))
    end_time = time.time()
    logger.info(f"Finished the application in {end_time - start_time} seconds")


if __name__ == '__main__':
    script()
