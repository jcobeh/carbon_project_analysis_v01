from src.scraper import *
import src.database as database
from src.analysis import analyse_project_activities
from src.model_and_vectors import *


load_dotenv()
openai_api_key: str = os.environ.get("OPENAI_API_KEY")


def script():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(message)s')
    logger = logging.getLogger('MyApp')
    logger.info('Starting the application')
    start_time = time.time()
    ##############################
    # download project list and save project IDs in database
    download_and_update_project_list()
    ##############################
    # scrape documents for projects and extract project activities
    scrape_all_projects()
    analyse_all_projects()
    ##############################
    # cluster project activities and classify them.
    cluster_project_activities()
    classify_all_project_activities()
    ##############################
    result_processing()
    ##############################
    end_time = time.time()
    logger.info(f"Finished the application in {end_time - start_time} seconds")


def cluster_project_activities():
    project_activities = get_activity_list()
    transformed_activities = {}
    no_project_activities = ["No meaningful data found.",
                             "No meaningful data found",
                             "No file found to analyse",
                             "Invalid document version. Expected a document using the VCS template Version of 3 or 4.",
                             "call to llm failed due to exception",
                             "call to LLM failed",
                             "no project activities",
                             "no project activities."]
    for project_id, activities in project_activities.items():
        for index, activity in enumerate(activities, start=1):
            if activity not in no_project_activities:
                new_key = f"{project_id}_{index}"
                transformed_activities[new_key] = activity
    create_model_and_vectors(transformed_activities)


def get_activity_list():
    projects = {}
    current_project = None
    with open('data/project_activities.txt', 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith("::: Project "):
                current_project = line[12:]
                projects[current_project] = []
            else:
                projects[current_project].append(line)
    return projects


def scrape_all_projects():
    projects = database.retrieve_db_project_list()
    for project in projects:
        project.scrape_and_analyse_documents()


def analyse_all_projects():
    projects = database.retrieve_db_project_list()
    with open('data/project_activities.txt', 'w') as file:
        for project in projects:
            # analyse_baseline_scenario(project.project_id)
            activities = analyse_project_activities(project.project_id)
            file.write("::: Project " + project.project_id + '\n')
            for activity in activities:
                file.write(activity + '\n')


if __name__ == '__main__':
    script()
