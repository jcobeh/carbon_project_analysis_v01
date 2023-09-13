import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from src.document import Document
import logging


load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)


def update_project_list(project_ids):
    logger = logging.getLogger('MyApp')
    logger.info('updating project list in the database')
    from src.project import Project
    existing_project_ids_dicts = supabase.table('Projects').select('project_id').execute()
    existing_project_ids = [item['project_id'] for item in existing_project_ids_dicts.data]

    for project_id in project_ids:
        # check if project exists in database
        if project_id not in existing_project_ids:
            current_project = Project(project_id)
            project_dict = current_project.to_dict()
            project_data = supabase.table('Projects').insert(project_dict).execute()
            assert (len(project_data.data) > 0)
    for project_id in existing_project_ids:
        # check if project exists in project_ids
        if project_id not in project_ids:
            project_data = supabase.table('Projects').delete().eq('project_id', project_id).execute()
            assert (len(project_data.data) > 0)
            logger.info(f"deleted project {project_id} from database as it is not in the list of projects anymore")
    logger.info(str(len(supabase.table('Projects').select('*').execute().data)) + " projects now in the database")


def retrieve_db_project_list():
    logging.getLogger('MyApp').info('retrieving project list from the database')
    from src.project import Project
    projects = supabase.table('Projects').select('*').execute()
    data = projects.data
    if len(data) > 0:
        projects = [Project(project_id=item['project_id'],
                            website_soup=item['website_soup'],
                            last_website_retrieval=item['last_website_retrieval'])
                    for item in data]
        return projects
    return []


def store_website_content(project, website_content):
    logging.getLogger('MyApp').info(f'storing website content for project {project.project_id} in the database')
    project.website_soup = website_content
    project.last_website_retrieval = datetime.now()
    data = supabase.table("Projects")\
        .update({"website_soup": website_content,
                 "last_website_retrieval": project.last_website_retrieval.strftime('%Y-%m-%d %H:%M:%S')})\
        .eq("project_id", project.project_id).execute()
    assert(len(data.data) > 0)


def retrieve_existing_project_documents(project):
    logging.getLogger('MyApp').info(f'retrieving existing documents for project {project.project_id} from the database')
    documents = supabase.table('Documents').select('*').eq('project_id', project.project_id).execute()
    data = documents.data
    if len(data) > 0:
        documents = [Document(doc_id=item['doc_id'],
                              project_id=item['project_id'],
                              filename=item['filename'],
                              website_category=item['website_category'],
                              last_updated=datetime.fromisoformat(item['last_updated']),
                              url=item['url'],
                              text=item['text'],
                              language=item['language'],
                              doc_type=item['doc_type'])
                     for item in data]
        return documents
    return []


def store_document(document):
    logging.getLogger('MyApp').info(f'storing document {document.filename} in the database')
    document_dict = document.to_dict()
    existing_document = supabase.table('Documents').select('doc_id', 'project_id').eq('doc_id', document.doc_id)\
        .eq('project_id', document.project_id).execute()
    if not existing_document.data:
        document_data = supabase.table('Documents').insert(document_dict).execute()
        assert (len(document_data.data) > 0)
    else:
        document_data = supabase.table('Documents').update(document_dict).eq('doc_id', document.doc_id)\
            .eq('project_id', document.project_id).execute()
        assert (len(document_data.data) > 0)


def check_text():
    return supabase.table('Documents').select('text').eq('doc_type', 11).eq('project_id', 2502).execute()
