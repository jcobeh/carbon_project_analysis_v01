from pdfminer.high_level import extract_text
from langdetect import detect
import globals
import logging
import re


class Document:

    def __init__(self, doc_id, project_id, filename, website_category, last_updated, url, text="", doc_type=0,
                 language="not detected"):
        self.doc_id: int = doc_id
        self.project_id: int = project_id
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
                self.preprocess_text()
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
        self.is_prr()
        self.is_mapping()
        self.is_other_doc()

    def analyse_language(self):
        if self.filename.lower().endswith(".pdf"):
            try:
                self.language = detect(self.text)
            except Exception as e:
                logging.getLogger('MyApp').info(f"language in the file: "
                                                f"{self.filename} could not be detected due to the error: {e}")
                self.language = "not detected"

    def preprocess_text(self):
        x = self.text
        if x:
            x1 = re.sub(r'\n+', '\n', x)
            x2 = re.sub(r'\S+@\S+', '[personal e-mail]', x1)
            x3 = re.sub(r'\d{6,}', '[personal phone number]', x2)
            x4 = re.sub(r'\.{5,}', '....', x3)
            self.text = x4

    def is_legal_doc(self):
        if self.filename.lower().endswith(".pdf"):
            a = self.text.count("VCS LISTING REPRESENTATION")
            if self.filename.lower().count("listing") > 0 and self.filename.lower().count("representation") > 0:
                a += 1
            b = self.text.count("VCS REGISTRATION DEED OF REPRESENTATION")
            if self.filename.lower().count("registration") > 0 and self.filename.lower().count("representation") > 0:
                b += 1
            c = self.text.count("VCS ISSUANCE DEED OF REPRESENTATION")
            if self.filename.lower().count("issuance") > 0 and self.filename.lower().count("representation") > 0:
                c += 1
            d = self.text.count("VCS VALIDATION DEED OF REPRESENTATION")
            if self.filename.lower().count("validation") > 0 and self.filename.lower().count("representation") > 0:
                d += 1
            e = self.text.count("VCS VERIFICATION DEED OF REPRESENTATION")
            if self.filename.lower().count("verification") > 0 and self.filename.lower().count("representation") > 0:
                e += 1
            f = self.text.count("VERRA REGISTRY COMMUNICATIONS AGREEMENT")
            f += self.text.count("DECLARATION OF AGENCY AND COMMUNICATIONS AGREEMENT")
            if self.filename.lower().count("communications") > 0 and self.filename.lower().count("agreement") > 0:
                f += 1
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

    def is_pd(self):
        score = 0
        if self.doc_type == 0:
            # A: filename based scoring
            if self.filename.lower().count("proj") > 0 and self.filename.lower().count("desc") > 0:
                score += 1
            elif re.findall(r'(?<![a-zA-Z])PD(?![a-zA-Z])', self.filename):
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
            elif re.findall(r'(?<![a-zA-Z])MR(?![a-zA-Z])', self.filename):
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

    def is_prr(self):
        a = 0
        if self.filename.lower().count("project") > 0 & self.filename.count("review") > 0:
            a += 1
        if self.filename.lower().count("review") > 0 & self.filename.count("report") > 0:
            a += 1
        if re.findall(r'(?<![a-zA-Z])PRR(?![a-zA-Z])', self.filename):
            a += 1
        if a > 0:
            self.doc_type = globals.PROJECT_REVIEW_REPORT

    def is_mapping(self):
        if self.filename.endswith(".kml"):
            self.doc_type = globals.MAPPING_OF_AREA

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
