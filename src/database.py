import csv
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from src.document import Document
import logging
import tempfile

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

PROJECTS_CSV = 'data/projects.csv'
DOCUMENTS_CSV = 'data/documents.csv'


def read_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        return list(csv.DictReader(file))


def write_csv(file_path, data, fieldnames):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def update_project_list(project_ids):
    from src.project import Project
    logger = logging.getLogger('MyApp')
    logger.info('Updating project list using CSV files')

    # Read existing projects from CSV
    existing_projects = read_csv(PROJECTS_CSV)
    existing_project_ids = [item['project_id'] for item in existing_projects]

    # Update logic
    for project_id in project_ids:
        if project_id not in existing_project_ids:
            current_project = Project(project_id)
            project_dict = current_project.to_dict()
            existing_projects.append(project_dict)
            logger.info(f"Added project {project_id}")

    # Remove projects that are no longer in the list
    updated_projects = [p for p in existing_projects if p['project_id'] in project_ids]

    # Write updated projects back to CSV
    write_csv(PROJECTS_CSV, updated_projects, existing_projects[0].keys() if existing_projects else ['project_id'])

    logger.info(f"{len(updated_projects)} projects now in the CSV file")


def retrieve_db_project_list():
    from src.project import Project
    logger = logging.getLogger('MyApp')
    logger.info('Retrieving project list from CSV file')

    # Read projects from CSV
    projects_data = read_csv(PROJECTS_CSV)

    if len(projects_data) > 0:
        projects = [Project(
            project_id=item['project_id'],
            website_soup=item['website_soup'],
            last_website_retrieval=datetime.fromisoformat(item['last_website_retrieval']) if item['last_website_retrieval'] else None,
            project_activities=item['project_activities'],
            baseline_scenario=item['baseline_scenario'],
            project_activities_raw_text=item['project_activities_raw_text'],
            baseline_scenario_raw_text=item['baseline_scenario_raw_text'],
            proponent=item['proponent'],
            annual_emission_red=item['annual_emission_red'],
            vcs_methodology=item['vcs_methodology'],
            hectares=item['hectares'],
            vcs_project_validator=item['vcs_project_validator'],
            registration_date=datetime.fromisoformat(item['registration_date']) if item['registration_date'] else None,
            crediting_period_term=item['crediting_period_term']
        ) for item in projects_data]
        return projects
    return []


def store_website_content(project, website_content):
    logger = logging.getLogger('MyApp')
    logger.info(f'Storing website content for project {project.project_id} in CSV file')

    # Read existing projects from CSV
    projects = read_csv(PROJECTS_CSV)

    # Update the project
    for p in projects:
        if p['project_id'] == project.project_id:
            p['website_soup'] = website_content
            p['last_website_retrieval'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    # Write updated projects back to CSV
    write_csv(PROJECTS_CSV, projects, projects[0].keys())


def store_project_attribute(project_id, attribute, value):
    logger = logging.getLogger('MyApp')
    logger.info(f'Storing {attribute} for project {project_id} in CSV file')


    # Read existing projects from CSV
    projects = read_csv(PROJECTS_CSV)

    # Update the project's attribute
    for p in projects:
        if p['project_id'] == project_id:
            p[attribute] = value
            break

    # Write updated projects back to CSV
    write_csv(PROJECTS_CSV, projects, projects[0].keys())


def retrieve_existing_project_documents(project):
    csv.field_size_limit(2000000)
    logger = logging.getLogger('MyApp')
    logger.info(f'Retrieving existing documents for project {project.project_id} from CSV file')

    documents = []

    with open(DOCUMENTS_CSV, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if int(row['project_id']) == int(project.project_id):
                doc_to_append = Document(
                    doc_id=int(row['doc_id']),
                    project_id=int(row['project_id']),
                    filename=row['filename'],
                    website_category=row['website_category'],
                    last_updated=datetime.fromisoformat(row['last_updated']) if row['last_updated'] else None,
                    url=row['url'],
                    text=row['text'],
                    language=row['language'],
                    doc_type=row['doc_type']
                )
                documents.append(doc_to_append)
    return documents


def store_document(document):
    csv.field_size_limit(2000000)
    logger = logging.getLogger('MyApp')
    logger.info(f'Storing document {document.filename} in CSV file')
    try:
        document_dict = document.to_dict()

        with open(DOCUMENTS_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            original_fieldnames = reader.fieldnames
            all_fieldnames = set(original_fieldnames).union(document_dict.keys())

            with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8') as temp_file:
                writer = csv.DictWriter(temp_file, fieldnames=all_fieldnames)
                writer.writeheader()

                found = False
                for row in reader:
                    if row['doc_id'] == document.doc_id and row['project_id'] == document.project_id:
                        writer.writerow(document_dict)
                        found = True
                    else:
                        # Fill missing keys with empty values for existing rows
                        for key in all_fieldnames:
                            row.setdefault(key, '')
                        writer.writerow(row)

                if not found:
                    print(len(document_dict['text']))
                    if len(document_dict['text']) > 2000000:
                        document_dict['text'] = document_dict['text'][:2000000]
                    writer.writerow(document_dict)

        os.replace(temp_file.name, DOCUMENTS_CSV)

    except Exception as e:
        logger.info(f"Storing document {document.filename} in CSV file failed due to the following error: {e}")
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def doc_type_metrics():
    logger = logging.getLogger('MyApp')
    logger.info('Calculating document type metrics from CSV file')

    # Read documents from CSV
    documents = read_csv(DOCUMENTS_CSV)

    # Process data
    result_dict = {}
    for d in documents:
        project_id = d['project_id']
        doc_type = d['doc_type']

        if project_id not in result_dict:
            result_dict[project_id] = {doc_type: 1}
        else:
            result_dict[project_id][doc_type] = result_dict[project_id].get(doc_type, 0) + 1

    print(result_dict)

    # Calculate frequencies for specific document types
    calc_freq_for_doc_type(result_dict, '11')
    calc_freq_for_doc_type(result_dict, '12')
    calc_freq_for_doc_type(result_dict, '13')
    calc_freq_for_doc_type(result_dict, '61')


def calc_freq_for_doc_type(result_dict, doc_type):
    zero = 0
    one = 0
    two = 0
    three = 0
    four = 0
    more = 0
    for project_id, doc_types in result_dict.items():
        if doc_type in doc_types:
            if doc_types[doc_type] == 0:
                zero += 1
            elif doc_types[doc_type] == 1:
                one += 1
            elif doc_types[doc_type] == 2:
                two += 1
            elif doc_types[doc_type] == 3:
                three += 1
            elif doc_types[doc_type] == 4:
                four += 1
            else:
                more += 1
    print(f"document of type {doc_type} is distributed across projects as follows: 0x: {zero}, 1x: {one}, 2x: {two}, "
          f"3x: {three}, 4x: {four}, more: {more}")


def get_project_by_id(project_id):
    from src.project import Project
    logger = logging.getLogger('MyApp')
    logger.info(f'Getting project with ID {project_id} from CSV file')

    projects = read_csv(PROJECTS_CSV)

    for project_data in projects:
        if project_data['project_id'] == project_id:
            project = Project(
                project_id=int(project_data['project_id']),
                website_soup=project_data['website_soup'],
                last_website_retrieval=datetime.fromisoformat(project_data['last_website_retrieval']) if project_data['last_website_retrieval'] else None,
                project_activities=project_data['project_activities'],
                baseline_scenario=project_data['baseline_scenario'],
                project_activities_raw_text=project_data['project_activities_raw_text'],
                baseline_scenario_raw_text=project_data['baseline_scenario_raw_text'],
                proponent=project_data['proponent'],
                annual_emission_red=project_data['annual_emission_red'],
                vcs_methodology=project_data['vcs_methodology'],
                hectares=project_data['hectares'],
                vcs_project_validator=project_data['vcs_project_validator'],
                registration_date=datetime.fromisoformat(project_data['registration_date']) if project_data['registration_date'] else None,
                crediting_period_term=project_data['crediting_period_term']
            )
            project.documents = retrieve_existing_project_documents(project)
            return project
    print("did not find targeted project in CSV file")
    return None


def get_all_project_activities():
    # Retrieve the list of projects
    projects = retrieve_db_project_list()  # or old_retrieve_db_project_list() for database

    # Initialize an empty list to store all activities
    all_activities = []
    all_projects = []
    print(len(projects))
    # Loop through each project and extract its activities
    for project in projects:
        # Check if project_activities attribute is present and not empty
        if project.project_activities:
            all_projects.append(project.project_id)
            all_activities.append(project.project_activities)

    return [all_projects, all_activities]
