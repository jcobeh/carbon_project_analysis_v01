import json
import re
import src.database as database
from dotenv import load_dotenv
import os
import openai
import logging


load_dotenv()
openai_api_key: str = os.environ.get("OPENAI_API_KEY")


def analyse_project_activities(project_id):
    logger = logging.getLogger('MyApp')
    logger.info('analysing project activities')
    system_prompt = "You are tasked to analyze a section from a carbon removal project's documentation focusing " \
                    "exclusively on the project’s activities. Your task is to extract the key project activities. " \
                    "Provide a list of avtivities, where each activity is summarised in a few sentences." \
                    "If the snippet is fragmented or lacks meaningful content, respond with 'No meaningful data \n" \
                    "found.'\n\n"
    function = [{
        "name": "list_project_activities",
        "description": "logs the project activities in the database",
        "parameters": {
            "type": "object",
            "properties": {
                "project_activities": {
                    "type": "array",
                    "description": "the list of project activities",
                    "items": {
                        "type": "object",
                        "properties": {
                            "activity_name": {
                                "type": "string",
                                "description": "description of a project activity",
                            },
                            "activity_summary": {
                                "type": "string",
                                "description": "few sentences summarising the project activity",
                            }
                        }
                    }
                }
            },
            "required": ["project_activities"],
        },
    }]
    relevant_document_types = [11, 13]
    file = extract_project_and_document(project_id, relevant_document_types)
    if not file:
        database.store_project_attribute(project_id, "project_activities", "No file found to analyse")
        return ["No file found to analyse"]
    if file.text.count("VCS Version 3") > 10 and file.text.count("CCB Version 3") > 10:
        headings = ["2.1.11"]
    elif file.text.count("VCS Version 3") > 10:
        headings = ["1.8"]
    elif file.text.count("VCS Version 4") > 10:
        headings = ["1.11"]
    else:
        return ["Invalid document version. Expected a document using the VCS template Version of 3 or 4."]
    extracted_text = call_relevant_text_extraction(headings, file.text)
    if len(extracted_text) > 30000:
        logger.info("extracted text was shortened, as original character length was " + str(len(extracted_text)))
        extracted_text = extracted_text[:30000]
    database.store_project_attribute(project_id, "project_activities_raw_text", extracted_text)
    try:
        result = call_llm(system_prompt, extracted_text, function)
    except Exception as e:
        logger.info("call to llm failed due to exception " + str(e))
        return ["call to llm failed due to exception " + str(e)]
    logger.info("llm result: " + str(result))
    database.store_project_attribute(project_id, "project_activities", result)
    return result


def extract_project_and_document(project_id, relevant_document_types):
    logger = logging.getLogger('MyApp')
    analysed_project = database.get_project_by_id(project_id)
    filtered_documents = [doc for doc in analysed_project.documents if int(doc.doc_type) in relevant_document_types]
    if not filtered_documents:
        return None
    if len(filtered_documents) > 1:
        filtered_documents = [doc for doc in filtered_documents if not ("draft" in doc.filename.lower())]
    if len(filtered_documents) > 1:
        filtered_documents = [doc for doc in filtered_documents if not ("summary" in doc.filename.lower())]
    if len(filtered_documents) > 1:
        filtered_documents = [doc for doc in filtered_documents if doc.language == "en"]
    logger.info("there is / are " + str(len(filtered_documents)) + " document(s) that could be considered")
    analysed_document = sorted(filtered_documents, key=lambda x: x.last_updated, reverse=True)[0]
    logger.info("filename of analysed document: " + analysed_document.filename)
    return analysed_document


def call_relevant_text_extraction(target_headings, document_text):
    target_text = ""
    for target_heading in target_headings:
        extracted_text = relevant_text_extraction(document_text, target_heading)
        if extracted_text == "" and len(target_heading.split(".")) == 3:
            print(f"This heading: {target_heading} is not in the document, trying again with heading above")
            shortened_target_heading = re.sub(re.compile(r'(\d+\.\d+)\.\d+'), r'\1', target_heading)
            extracted_text = relevant_text_extraction(document_text, shortened_target_heading)
        target_text += extracted_text
    return target_text


def call_llm(system_prompt, extracted_text, functions):
    if len(extracted_text) < 10:
        return ["No meaningful data found."]
    messages = [{
        "role": "system",
        "content": system_prompt
    }, {
        "role": "user",
        "content": extracted_text
    }]
    try:
        # if False:
        if functions:
            print(2)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                temperature=0.7,
                functions=functions,
            )
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                temperature=0.7,
            )
        if response["choices"][0]["message"]['content']:
            activities = response["choices"][0]["message"]['content']
            activities = cleanup_activities(activities)
        else:
            activities = response["choices"][0]["message"]['function_call']['arguments']
            activities = json.loads(activities)
            print("x")
            activities = [f"{activity['activity_name']}: {activity['activity_summary']}"
                          for activity in activities['project_activities']]
        print(activities)
        return activities
    except Exception as e:
        return ["call to LLM failed"]


def cleanup_activities(activities):
    system_prompt = "You extract project activities. In case there are no project activities described, answer with " \
                    "'no project activities'."
    function = [{
        "name": "list_project_activities",
        "description": "logs the project activities in the database",
        "parameters": {
            "type": "object",
            "properties": {
                "project_activities": {
                    "type": "array",
                    "description": "the list of project activities",
                    "items": {
                        "type": "string",
                        "description": "description of a project activity in the format "
                                       "'activity name: activity summary'"
                    }
                }
            },
            "required": ["project_activities"],
        },
    }]
    messages = [{
        "role": "system",
        "content": system_prompt
    }, {
        "role": "user",
        "content": activities
    }]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        temperature=0.7,
        functions=function,
    )
    if response["choices"][0]["message"]['content']:
        activities = [response["choices"][0]["message"]['content']]
        print(activities)
    else:
        x = json.loads(response["choices"][0]["message"]['function_call']['arguments'])
        activities = x['project_activities']
        print(activities)
    return activities


def text_structuring(text, heading_depth):
    if heading_depth == 2:
        pattern = re.compile(r'(?<![\d\.])(\d+\.[1-9]\d*)(\s+.+?)(?=\d+\.[1-9]\d*|$)', re.DOTALL)
    elif heading_depth == 3:
        pattern = re.compile(r'(\d+\.[1-9]\d*\.\d+)(\s+.+?)(?=\d+\.[1-9]\d*\.\d+|$)', re.DOTALL)
    else:
        raise ValueError("Invalid heading depth. Expected a heading depth of 2 or 3.")
    matches = re.findall(pattern, text)
    return matches


def relevant_text_extraction(text, target_heading):
    target_text = ""
    match_count = 0
    heading_depth = len(target_heading.split("."))
    print("current target heading: " + str(target_heading))
    print("heading depth:" + str(heading_depth))
    matches = text_structuring(text, heading_depth)
    index = 0
    tracked_heading = ""
    for current_heading, text in matches:
        if heading_depth == 2:
            current_heading_integer, current_heading_decimal = map(int, current_heading.split('.'))
            target_heading_integer, target_heading_decimal = map(int, target_heading.split('.'))
            append_if_no_match = current_heading != target_heading and \
                                 (current_heading_integer > (target_heading_integer + 1) or
                                  current_heading_decimal > (target_heading_decimal + 1))
        elif heading_depth == 3:
            current_heading_integer, current_heading_decimal, current_heading_cent = map(int, current_heading.split('.'))
            target_heading_integer, target_heading_decimal, target_heading_cent = map(int, target_heading.split('.'))
            append_if_no_match = current_heading != target_heading and \
                                 (current_heading_integer > (target_heading_integer + 1) or
                                  current_heading_decimal > (target_heading_decimal + 1) or
                                  current_heading_cent > (target_heading_cent + 1))
        else:
            raise ValueError("Invalid heading depth. Expected a heading depth of 2 or 3.")

        heading_match = current_heading == target_heading
        if heading_match:
            match_count += 1
            tracked_heading = current_heading
            target_text += ";\nPosition " + str(index) + ": "

        if tracked_heading and (heading_match or append_if_no_match):
            target_text += current_heading + text
            index += 1
            continue
        index += 1
        tracked_heading = ""
    print("# of matches: " + str(match_count))
    return target_text
