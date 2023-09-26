from src.scraper import *
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import src.db_ops as database
from src.document import Document
from src.llm import *


def script():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(message)s')
    logger = logging.getLogger('MyApp')
    logger.info('Starting the application')
    start_time = time.time()
    # check the list of projects (if new projects were added)
    # download_and_update_project_list()
    # for each project run the scrape / analysis

    sample_project = database.get_project_by_id(1882)
    project_documents_llm_processor(sample_project, "You are an answering machine which answers in very short, precise and concise words, not sentences. Which company is the project proponent of this project? Be aware, that there are many different companies involved in executing and documenting this project.")

    """projects = database.retrieve_db_project_list()
    runner = 0
    for project in projects:
        if runner < 10:
            project.scrape_and_analyse_documents()
            runner += 1"""

    sample_text_bionics = "The Future of Bionics Bionics, the confluence of biology and electronics, holds the promise of revolutionizing the way we perceive human potential and medical intervention. From advanced prosthetics to enhanced sensory capabilities, the future of bionics is teeming with possibilities. Advanced Prosthetics: Today's prosthetics have made significant strides, but the future might behold limbs that seamlessly integrate with the human body. These would not just mimic the biological function but could potentially surpass human capabilities in terms of strength, speed, and endurance. Imagine a world where a prosthetic leg can detect surface texture and adjust its grip, or an arm that can lift weights far beyond human limits. Sensory Augmentation: Beyond just restoring lost senses, bionics might offer the potential to augment our existing sensory capabilities. Infrared vision, ultrasonic hearing, or even the ability to detect minute changes in atmospheric pressure could become a reality. Brain-Computer Interfaces (BCI): While still in nascent stages, BCIs could pave the way for direct communication between the brain and machines. This would enable not just thought-controlled devices but could also lead to enhanced cognitive capabilities, improved memory retention, and even the potential for direct brain-to-brain communication. Regenerative Medicine: In the realm of bionics, there's also the tantalizing possibility of integrating electronics with cellular structures to stimulate regeneration. Damaged organs or tissues could be repaired not by transplant but by stimulating the body's innate ability to heal, using bionic interventions. Enhanced Mobility: Exoskeletons, wearable suits equipped with bionic technology, might become common tools for people with mobility issues or for those engaged in tasks requiring augmented strength or endurance. Ethical and Societal Implications: As with all advancements, the growth of bionics will also usher in discussions about ethics and societal impact. The demarcation between restoration and enhancement, accessibility of bionic technologies, and the implications of 'superhuman' abilities will become vital discourse points. The future of bionics is not just about technological advancements but a reshaping of the boundaries of human potential. As we stand on the cusp of these innovations, we're not just looking at better solutions for medical challenges but possibly a new chapter in human evolution."
    sample_text_aviation = "The Future of Aviation As we soar into the new era, the realm of aviation stands poised for transformative changes, driven by technological advancements, environmental concerns, and evolving consumer demands. Here's a glimpse into what the skies might behold for the future of aviation: Sustainability and Eco-friendly Solutions: With growing environmental concerns, the focus is on developing more sustainable aviation solutions. Research into biofuels, electric planes, and hybrid solutions is in full swing. The goal? Aircraft that emit significantly fewer greenhouse gases and have a reduced carbon footprint. Urban Air Mobility: Imagine hopping onto a drone-like taxi to cross the city! Urban air mobility aims to decongest road traffic and provide quick intra-city transportation using vertical takeoff and landing (VTOL) vehicles. Companies are already testing prototypes, indicating that the age of flying taxis might be closer than we think. Supersonic and Hypersonic Travel: While the Concorde's supersonic era ended years ago, there's renewed interest in ultra-fast air travel. Companies are exploring quieter, more efficient supersonic jets, and even hypersonic travel, aiming to drastically reduce intercontinental flight times. Pilotless Aircraft: Automation and AI have made significant inroads into aviation. While autopilot systems are common, the industry is researching completely pilotless aircraft. With advancements in AI, sensor technology, and data processing, fully autonomous commercial flights could become a reality. Enhanced Passenger Experience: The in-flight experience is set to undergo a makeover. Larger windows, quieter cabins, more spacious seating, and augmented reality (AR) entertainment systems might become the norm. Moreover, biometric systems, like facial recognition, could make airport check-ins faster and more secure. Advanced Air Traffic Management: As skies become busier, advanced air traffic management solutions will be crucial. Technologies like AI-driven predictive analytics could optimize flight paths in real-time, ensuring efficient use of airspace, reducing delays, and enhancing safety. Space Travel: While not traditional aviation, the boundaries between aviation and space travel are blurring. With companies like SpaceX and Blue Origin aiming for commercial space travel, soon, taking a trip to space might become as commonplace as a transatlantic flight. Safety Innovations: Despite being one of the safest modes of transport, continuous efforts are made to make aviation safer. From advanced collision avoidance systems to enhanced weather prediction tools, future aircraft will be equipped with even more safety features. As challenges like climate change and urbanization intensify, the aviation sector's role becomes even more crucial. By embracing innovation and prioritizing sustainability, the future of aviation not only promises faster and more efficient travel but also a journey towards a more connected and sustainable world."
    # project_documents_llm_processor([sample_text_bionics, sample_text_aviation], "What type of fuel might power airplanes in the future?")

    end_time = time.time()
    logger.info(f"Finished the application in {end_time - start_time} seconds")
    # database.doc_type_metrics()


if __name__ == '__main__':
    script()
