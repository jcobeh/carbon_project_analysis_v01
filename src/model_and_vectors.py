import json
import logging
import pandas as pd
from dotenv import load_dotenv
import os
import openai
from sklearn.cluster import KMeans
from sklearn import preprocessing
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
import time


def create_model_and_vectors(project_activities):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(message)s')
    logger = logging.getLogger('MyApp')

    def get_embeddings(sentences):
        logger.info("Starting to create embeddings")
        load_dotenv()
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        embeddings = []
        batch_size = 10
        for i in range(0, len(sentences), batch_size):
            try:
                # Slice the list to get the current batch
                logger.info("embedding at activity number: " + str(i))
                if sentences[i] == "":
                    sentences[i] = "no activity"
                batch = sentences[i:i + batch_size]
                # Call the OpenAI API
                # response = openai.Embedding.create(input=batch, engine="text-similarity-davinci-001")
                response = openai.Embedding.create(input=batch, engine="text-embedding-ada-002")
                batch_embeddings = [item['embedding'] for item in response['data']]
                # Extract embeddings from the response and append to your list
                embeddings.extend(batch_embeddings)
            except openai.error.OpenAIError as e:
                logger.info(f"An error occurred: {e}")
                logger.info(sentences[i:i + batch_size])
                time.sleep(2)  # simple backoff strategy
            except Exception as e:
                logger.info(f"An unexpected error occurred: {e}")
                time.sleep(2)  # simple backoff strategy
        return embeddings

    vectors = get_embeddings(list(project_activities.values()))
    vectors = pd.DataFrame(vectors)
    print(vectors.head)
    vectors_norm = preprocessing.normalize(vectors)
    vec = pd.DataFrame(vectors_norm)
    print(vec.head)

    # Clustering of selected points
    distortions = []
    km_silhouette = []

    # range of cluster numbers to validate
    clusters = range(4, 25)
    for i in clusters:
        logger.info(i)
        km = KMeans(
            init='k-means++', n_clusters=i,
            n_init=10, max_iter=300,
            tol=1e-04, random_state=80
        )
        km.fit(vec)
        preds = km.predict(vec)
        # for kmeans ellbow diagram
        distortions.append(km.inertia_)

        # for silhouette diagramme
        silhouette = silhouette_score(vec, preds)
        km_silhouette.append(silhouette)

    def plotting(y_data, x_values, name_y, name_plot, number):
        f = plt.figure(number)
        plt.plot(x_values, y_data, marker='o')
        plt.xlabel('Number of clusters')
        plt.ylabel(name_y)
        f.savefig(name_plot, format='png', bbox_inches='tight')

    # plot kmeans distortion
    plotting(distortions, clusters, name_y='Distortion', name_plot='elbow.png', number=1)

    # plotting silhouette
    plotting(km_silhouette, clusters, name_y='Silhouette_score', name_plot='silhouette.png', number=2)

    def apply_clustering(cluster_number):
        km = KMeans(
            init='k-means++', n_clusters=cluster_number,
            n_init=100, max_iter=1000,
            tol=1e-07, random_state=80
        )
        km.fit(vec)

        activity_list = [{'ID': k, 'Activity': v} for k, v in project_activities.items()]
        df_activities = pd.DataFrame(activity_list)
        df_activities['Cluster'] = km.predict(vec)

        logger.info(df_activities.head())

        for i in range(cluster_number):
            logger.info("cluster " + str(i) + ":")
            for index, row in df_activities.iterrows():
                if row['Cluster'] == i:
                    logger.info(row['Activity'])

        csv_filename = "data/clustered_activities.csv"
        df_activities.to_csv(csv_filename, index=False)

    number_as_string = input("Please review the elbow diagram and enter the number of clusters as integer: ")
    number_as_integer = int(number_as_string)
    apply_clustering(number_as_integer)


def classify_all_project_activities():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(message)s')
    logger = logging.getLogger('MyApp')
    # get all project activities
    df = pd.read_csv("data/clustered_activities.csv")
    # loop through all project activities and call classify_project_activity
    for index, row in df.iterrows():
        classification = classify_project_activity(row['Activity'])
        df.at[index, 'Classification'] = classification
        logger.info("classified activity " + str(index) + ": " + row['Activity'] + " as " + classification)
    # save dataframe to csv
    csv_filename = "data/clustered_activities_classified.csv"
    df.to_csv(csv_filename, index=False)
    return df


def result_processing():
    project_cluster_matching()
    add_project_details()
    cluster_summary_classification()
    cluster_processing()


def project_cluster_matching():
    df = pd.read_csv("data/clustered_activities_classified.csv")
    # group by project id (stored as the first 4 letters of the column "ID") and count the number of activities
    # per project, total, per cluster and per classification. I want one column per cluster and one column per
    # classification.

    # Step 1: Extract Project ID
    df['Project_ID'] = df['ID'].apply(lambda x: x.split('_')[0])

    # Step 2: Group by Project ID, Cluster, and Classification, and count activities
    grouped_df = df.groupby(['Project_ID', 'Cluster', 'Classification']).count().reset_index()
    grouped_df = grouped_df.rename(columns={'Activity': 'Activity_Count'})

    # Step 3: Pivot the DataFrame
    # For Cluster
    pivot_cluster = grouped_df.pivot_table(index='Project_ID', columns='Cluster', values='Activity_Count', fill_value=0,
                                           aggfunc='sum')
    pivot_cluster.columns = ['Cluster_' + str(col) for col in pivot_cluster.columns]

    # For Classification
    pivot_classification = grouped_df.pivot_table(index='Project_ID', columns='Classification', values='Activity_Count',
                                                  fill_value=0, aggfunc='sum')
    pivot_classification.columns = ['Classification_' + str(col) for col in pivot_classification.columns]

    # Convert all counts to integers
    pivot_cluster = pivot_cluster.astype(int)
    pivot_classification = pivot_classification.astype(int)

    # Step 4: Merge Pivot Tables and Calculate Total Activities
    final_df = pd.concat([pivot_cluster, pivot_classification], axis=1)
    final_df['Total_Activities'] = df.groupby('Project_ID')['Activity'].count()

    # Resetting index for final DataFrame
    final_df = final_df.reset_index()

    cols = [c for c in final_df.columns if c != 'Total_Activities']
    cols.insert(1, 'Total_Activities')
    final_df = final_df[cols]

    # Output the resulting DataFrame
    print(final_df.head())

    csv_filename = "data/project_summary.csv"
    final_df.to_csv(csv_filename, index=False)


def add_project_details():
    columns_to_add = ['proponent', 'annual_emission_red', 'vcs_methodology', 'hectares',
                      'vcs_project_validator', 'registration_date', 'crediting_period_term']
    df1 = pd.read_csv("data/projects.csv")
    df1.rename(columns={'project_id': 'Project_ID'}, inplace=True)
    df2 = pd.read_csv("data/project_summary.csv")
    merged_df = pd.merge(df1[['Project_ID'] + columns_to_add], df2, on='Project_ID', how='left')

    df2_int_columns = df2.select_dtypes(include=['int']).columns
    for column in df2_int_columns:
        # Check if the column is in the merged DataFrame and is of float type
        if column in merged_df and merged_df[column].dtype == float:
            # Convert back to int, handling NaNs
            merged_df[column] = merged_df[column].fillna(0).astype(int)

    csv_filename = "data/project_summary_details.csv"
    merged_df.to_csv(csv_filename, index=False)


def cluster_summary_classification():
    classified_activities = pd.read_csv("data/clustered_activities_classified.csv")
    cluster_summary = pd.read_csv("data/cluster_summary.csv")
    cluster_summary = cluster_summary.sort_values(by='Cluster')
    cluster_summary = cluster_summary.reset_index(drop=True)
    cluster_summary['carbon'] = 0
    cluster_summary['community'] = 0
    cluster_summary['biodiversity'] = 0
    cluster_summary['project management'] = 0
    cluster_summary['no classification'] = 0
    for index, row in classified_activities.iterrows():
        cluster_label = row['Cluster']
        classification = row['Classification']
        cluster_index = cluster_summary[cluster_summary['Cluster'] == cluster_label].index[0]
        cluster_summary.at[cluster_index, classification] += 1
    print(cluster_summary.head())
    csv_filename = "data/cluster_summary_classified.csv"
    cluster_summary.to_csv(csv_filename, index=False)


def cluster_processing():
    df = pd.read_csv("data/clustered_activities.csv")
    unique_clusters = df['Cluster'].unique()

    cluster_info = []

    for cluster in unique_clusters:
        loop = True
        iterations = 0
        cluster_name = ""
        cluster_summary = ""
        cluster_activities = []
        while loop and iterations < 3:
            loop = False
            iterations += 1
            cluster_data = df[df['Cluster'] == cluster]
            print(f"Processing activities in Cluster {cluster}:")
            for index, row in cluster_data.iterrows():
                cluster_activities.append(row['Activity'])

            system_prompt = "You analyse clusters of project activities in the context of 'Agriculture, Forestry, and " \
                            "Other Land Use' projects and come up with representative names for clusters. Only respond " \
                            "with the function."
            function = [{
                "name": "name_cluster",
                "description": "gives a representative name to a cluster of project activities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cluster_name": {
                            "type": "string",
                            "description": "brief name of the cluster"
                        },
                        "cluster_summary": {
                            "type": "string",
                            "description": "summary of the cluster"
                        }
                    },
                    "required": ["cluster_name", "cluster_summary"],
                },
            }]
            messages = [{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": ";;; ".join(cluster_activities)
            }]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                temperature=0.7,
                functions=function,
            )

            if response["choices"][0]["message"]['content']:
                print(response["choices"][0]["message"]['content'])
                loop = True
            else:
                try:
                    print(cluster)
                    print(cluster_activities[1:5])
                    x = json.loads(response["choices"][0]["message"]['function_call']['arguments'])
                    print(x['cluster_name'])
                    cluster_name = x['cluster_name']
                    cluster_summary = x['cluster_summary']
                except:
                    print("accessing project activities property failed")
                    loop = True
        cluster_info.append({'Cluster': int(cluster),
                             'Cluster_Name': str(cluster_name),
                             'Cluster_Summary': str(cluster_summary),
                             'Number_of_Activities': len(cluster_activities)})
    cluster_info_df = pd.DataFrame(cluster_info)
    csv_filename = "data/cluster_summary.csv"
    cluster_info_df.to_csv(csv_filename, index=False)


def classify_project_activity(project_activity):
    system_prompt = "You analyse a project activity in the context of 'Agriculture, Forestry, and Other Land Use' " \
                    "projects and come up with a classification. " \
                    "Either the project activity A) focuses exclusively on carbon benefits (i.e., healthy forests, " \
                    "avoiding deforestation, ...), B) promotes economic or social benefits for the community " \
                    "(i.e., livelihoods, food security, ...), C) explicitly seeks to improve biodiversity " \
                    "(i.e., species monitoring and conservation, provision of sanctuaries, ...), or D) revolves " \
                    "around project management, overhead and communication. " \
                    "If the activity does not fit into any of these categories, please select the option " \
                    "'no classification'. " \
                    "Only respond with the function."
    function = [{
        "name": "classify_activity",
        "description": "gives a classification to a project activity",
        "parameters": {
            "type": "object",
            "properties": {
                "classification": {
                    "type": "string",
                    "enum": ["carbon", "community", "biodiversity", "project management", "no classification"],
                    "description": "Classification of the project activity with regards to their focus.",
                }
            },
            "required": ["classification"],
        },
    }]
    messages = [{
        "role": "system",
        "content": system_prompt
    }, {
        "role": "user",
        "content": project_activity
    }]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        temperature=0.7,
        functions=function,
    )

    try:
        x = json.loads(response["choices"][0]["message"]['function_call']['arguments'])
        classification = x['classification']
    except:
        print("accessing classification property failed")
        classification = "no classification"
    return classification
