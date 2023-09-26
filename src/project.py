from bs4 import BeautifulSoup
import requests
import os
from src.document import Document
from typing import List
import globals
import logging
from datetime import datetime
from pyppeteer import launch
import asyncio
import src.db_ops as database
import src.llm as llm


class Project:

    def __init__(self, project_id, website_soup=None, last_website_retrieval=None):
        self.project_id = project_id
        self.documents: List[Document] = []
        self.website_soup = website_soup
        self.last_website_retrieval = last_website_retrieval

    def scrape_and_analyse_documents(self):
        logger = logging.getLogger('MyApp')
        logger.info(f"Starting to scrape documents for project {self.project_id}.")

        soup = asyncio.get_event_loop().run_until_complete(self.get_soup())
        self.documents = database.retrieve_existing_project_documents(self)

        for group in soup.find_all('apx-document-group'):
            section = group.find('div', {'class': 'card-header'}).text.strip()
            logger.info(f'Iterating through website sections, current section Name: {section}.')
            for row in group.find_all('tr'):
                # select the correct index for the document
                doc_id = max(doc.doc_id for doc in self.documents) + 1 if self.documents else 1
                # find document data
                cells = row.find_all('td')
                if len(cells) > 1:  # (otherwise, this row is not a document)
                    link = cells[0].find('a')
                    file_url = link['href']
                    filename = link.text.strip()
                    date_updated = datetime.strptime(cells[1].text.strip(), "%d/%m/%Y")
                    if any(file.filename == filename for file in self.documents):
                        document = [doc for doc in self.documents if doc.filename == filename][0]
                        if document.last_updated < date_updated:
                            logger.info(f"File {filename} was updated, analysing again!")
                            self.download_analyse_save_delete_file(document.doc_id, filename, file_url, section,
                                                                   date_updated)
                        else:
                            logger.info(f"File {filename} already in database, skipping download")
                    else:
                        self.download_analyse_save_delete_file(doc_id, filename, file_url, section, date_updated)
                        logger.info(f"File {filename} not in database, downloading and analysing")
        logger.info("Finished downloading documents for this project, see details:")
        logger.info(self.project_details())
        # llm.project_documents_llm_processor(self)

    def download_analyse_save_delete_file(self, doc_id, filename, file_url, section, date_updated):
        logger = logging.getLogger('MyApp')
        logger.info(f"Downloading file {filename} from {file_url}")
        response = requests.get(file_url)
        with open(os.path.join(globals.TEMP_DOC_STORAGE, filename), 'wb') as file:
            file.write(response.content)
        document = Document(doc_id, self.project_id, filename, section, date_updated, file_url)
        document.analyse_doc()
        self.documents = [doc for doc in self.documents if doc.filename != filename]
        self.documents.append(document)
        database.store_document(document)
        logger.info(f"Deleting file {filename}")
        os.remove(os.path.join(globals.TEMP_DOC_STORAGE, filename))

    async def get_soup(self):
        logging.getLogger('MyApp').info(f"Getting soup for project {self.project_id} with managed browser.")
        url = globals.PROJECT_URL_BASE + str(self.project_id)
        browser = await launch()
        page = await browser.newPage()
        await page.goto(url)
        await page.waitForSelector('apx-document-group')
        content = await page.content()
        database.store_website_content(self, content)
        soup = BeautifulSoup(content, 'html.parser')
        await browser.close()
        return soup

    def project_details(self):
        general_info = (
            f"project id: {self.project_id}\n"
            f"the project contains {len(self.documents)} documents\n"
            "the following documents are part of the project:"
        )
        documents_info = [
            f"type: {doc.doc_type}; language: {doc.language}; filename: {doc.filename}"
            for doc in self.documents
        ]
        info = general_info + "\n" + '\n'.join(documents_info)
        return info

    def to_dict(self):
        return {
            "project_id": int(self.project_id),
            "website_soup": self.website_soup,
            "last_website_retrieval": self.last_website_retrieval.strftime('%Y-%m-%d %H:%M:%S') if
            self.last_website_retrieval else None
        }
