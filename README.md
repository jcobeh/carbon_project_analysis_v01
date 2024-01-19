This repository contains the underlying code for the Masterthesis “Utilising Language Models for Enhanced Understanding and Analysis of REDD Carbon Projects: A Clustering Framework and the role of Co-Benefits” by Jakob Ehlert.

# Code
The following outlines the steps performed by the code:
1. The project list is downloaded from the Verra registry and the project ids of REDD projects are extracted and saved
2. For each project, the respective page in the registry is opened, relevant information is scraped and all documents are iteratively downloaded, the text is extracted and stored and the document is classified
3. For each project, the relevant text section in the right document is identified, which is used for extracting a list of project activities
4. The project activities are embedded and the k-means clustering provides an elbow diagram to identify the best number of clusters. Based on user input, the clustering is performed for that number of clusters
5. Each project activity is classified with the use of the OpenAI API
6. The results are re-combined into csv documents containing the overview of the most relevant information
7. The file __analysis_file.xslx contains the work product from the manual analyses performed on top

Disclaimer: due to the size of the Documents.csv file (>300 MB), this file is not included in the repository.

# Data
The data for the analysis is automatically extracted from the Verra registry: https://registry.verra.org/app/search/VCS/All%20Projects
