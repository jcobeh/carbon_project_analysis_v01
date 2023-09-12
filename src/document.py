from pdfminer.high_level import extract_text
from langdetect import detect
import globals
import logging


class Document:

    def __init__(self, doc_id, project_id, filename, website_category, last_updated, url, text="", doc_type=0,
                 language="not detected"):
        self.doc_id = doc_id
        self.project_id = project_id
        self.filename: str = filename
        self.website_category = website_category
        self.last_updated = last_updated
        self.url = url
        self.text = text
        self.doc_type = doc_type
        self.language = language

    def analyse_doc(self):
        self.extract_text()
        self.classify_doc()
        self.analyse_language()

    def extract_text(self):
        logger = logging.getLogger('MyApp')
        logger.info(f"extracting text from {self.filename}")
        if self.filename.lower().endswith(".pdf"):
            try:
                self.text = extract_text(globals.TEMP_DOC_STORAGE + "/" + self.filename)
            except Exception as e:
                logger.info("text extraction failed!")
        if len(self.text) < 10:
            self.text = "not pdf or could not be classified"
            self.doc_type = globals.OTHER

    def classify_doc(self):
        self.is_legal_doc()
        self.is_pd()
        self.is_mr()
        self.is_j_pd_mr()
        self.is_val_r()
        self.is_ver_r()
        self.is_j_vr_vr()
        self.is_other_doc()

    def analyse_language(self):
        if self.filename.lower().endswith(".pdf"):
            try:
                self.language = detect(self.text)
            except Exception as e:
                logging.getLogger('MyApp').info(f"language in the file: "
                                                f"{self.filename} could not be detected due to the error: {e}")
                self.language = "not detected"

    def is_legal_doc(self):
        if self.filename.lower().endswith(".pdf"):
            a = self.text.count("VCS LISTING REPRESENTATION")
            b = self.text.count("VCS REGISTRATION DEED OF REPRESENTATION")
            c = self.text.count("VCS ISSUANCE DEED OF REPRESENTATION")
            d = self.text.count("VCS VALIDATION DEED OF REPRESENTATION")
            e = self.text.count("VCS VERIFICATION DEED OF REPRESENTATION")
            f = self.text.count("VERRA REGISTRY COMMUNICATIONS AGREEMENT")
            g = self.text.count("DECLARATION OF AGENCY AND COMMUNICATIONS AGREEMENT")
            if a > 0:
                self.doc_type = globals.VCS_LISTING_REPRESENTATION
            elif b > 0:
                self.doc_type = globals.VCS_REGISTRATION_DEED_OF_REPRESENTATION
            elif c > 0:
                self.doc_type = globals.VCS_ISSUANCE_DEED_OF_REPRESENTATION
            elif d > 0:
                self.doc_type = globals.VCS_VALIDATION_DEED_OF_REPRESENTATION
            elif e > 0:
                self.doc_type = globals.VCS_VERIFICATION_DEED_OF_REPRESENTATION
            elif f > 0:
                self.doc_type = globals.VERRA_REGISTRY_COMMUNICATIONS_AGREEMENT
            elif g > 0:
                self.doc_type = globals.VERRA_REGISTRY_COMMUNICATIONS_AGREEMENT

    def is_pd(self):
        score = 0
        if self.doc_type == 0:
            # A: filename based scoring
            if self.filename.lower().count("proj") > 0 and self.filename.lower().count("desc") > 0:
                score += 1
            elif self.filename.count("PD") > 0:
                score += 1
            # B: content based scoring
            if self.text.count("CCB & VCS PROJECT DESCRIPTION") > 0:
                score += 1
            elif self.text.count("Project Description: VCS Version ") > 0:
                score += 1
            elif self.text.count("PROJECT DESCRIPTION: VCS Version ") > 0:
                score += 1
            # assign document type
            if score > 0:
                self.doc_type = globals.PROJECT_DESCRIPTION

    def is_mr(self):
        score = 0
        if self.doc_type == 0:
            # A: filename based scoring
            if self.filename.lower().count("monitoring") > 0:
                score += 1
            elif self.filename.count("MR") > 0:
                score += 1
            # B: content based scoring
            if self.text.count("MONITORING REPORT:") > 0:
                score += 1
            # assign document type
            if score > 0:
                self.doc_type = globals.MONITORING_REPORT

    def is_j_pd_mr(self):
        score = 0
        if self.doc_type == 0 or self.doc_type == 11 or self.doc_type == 12:
            # A: filename based scoring
            if self.filename.lower().count("joint") > 0 and self.filename.lower().count("description"):
                score += 1
            elif self.filename.lower().count("joint") > 0 and self.filename.lower().count("monitoring"):
                score += 1
            # B: content based scoring
            if self.text.count("Joint Project Description & Monitoring Report: VCS Version ") > 0:
                score += 1
            # assign document type
            if score > 0:
                self.doc_type = globals.JOINT_PD_AND_MR

    def is_val_r(self):
        score = 0
        if self.doc_type == 0:
            # A: filename based scoring
            if self.filename.lower().count("val") > 0 and self.filename.lower().count("report") > 0:
                score += 1
            # B: content based scoring
            if self.text.lower().count("validation report: vcs version ") > 0:
                score += 1
            elif self.text.count("CCB & VCS VALIDATION REPORT:") > 0:
                score += 1
            # assign document type
            if score > 0:
                self.doc_type = globals.VALIDATION_REPORT

    def is_ver_r(self):
        score = 0
        if self.doc_type == 0:
            # A: filename based scoring
            if self.filename.lower().count("ver") > 0 and self.filename.lower().count("report") > 0:
                score += 1
            # B: content based scoring
            if self.text.lower().count("verification report: vcs version ") > 0:
                score += 1
            elif self.text.count("CCB & VCS VERIFICATION REPORT:") > 0:
                score += 1
            # assign document type
            if score > 0:
                self.doc_type = globals.VERIFICATION_REPORT

    def is_j_vr_vr(self):
        score = 0
        if self.doc_type == 0:
            # A: filename based scoring
            name = self.filename.lower()
            if name.count("joint") > 0 and name.count("val") > 0 and name.count("ver") > 0:
                score += 1
            # B: content based scoring
            if self.text.lower().count("joint validation & verification report: vcs version ") > 0:
                score += 1
            # assign document type
            if score > 0:
                self.doc_type = globals.JOINT_VR_VR

    def is_other_doc(self):
        if self.doc_type == 0:
            self.doc_type = globals.OTHER

    def to_dict(self):
        return {
            "doc_id": int(self.doc_id),
            "project_id": int(self.project_id),
            "filename": self.filename,
            "website_category": self.website_category,
            "last_updated": self.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
            "url": self.url,
            "text": self.text,
            "language": self.language,
            "doc_type": int(self.doc_type)
        }
