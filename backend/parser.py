import pdfplumber
import json
import re
import sys 
from pathlib import Path
import os
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv
import unicodedata
import fitz
load_dotenv()


class ResumeParser:
    def __init__(self):
        self.EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        self.linkedins = []

    def extract_text_from_pdf(self, file_path: str) -> str:
        # Extract text from a PDF file using pdfplumber and links using PyMuPDF
        # First, extract links using PyMuPDF
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            self.linkedins.append(self.extract_linkedin_from_page(page))
        doc.close()
        
        # Then extract text using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            page_texts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Clean the text to normalize Unicode characters
                    cleaned_text = self.clean_text(text.strip())
                    page_texts.append(cleaned_text)
        return page_texts
    
    def clean_text(self, text: str) -> str:
        # Clean and normalize text by replacing unicode characters
        if not text:
            return text
        
        # normalize Unicode characters to their closest ASCII equivalents
        # NFKD normalization decomposes characters and removes diacritics
        text = unicodedata.normalize('NFKD', text)
        
        # convert Unicode characters to their ASCII equivalents
        try:
            text = text.encode('ascii', 'ignore').decode('ascii')
        except UnicodeError:
            pass
            
        # Additional manual replacements for characters that normalization might miss
        # Replace various types of hyphens and dashes with regular hyphens
        text = text.replace('\u2010', '-')  # hyphen
        text = text.replace('\u2011', '-')  # non-breaking hyphen
        text = text.replace('\u2012', '-')  # figure dash
        text = text.replace('\u2013', '-')  # en dash
        text = text.replace('\u2014', '-')  # em dash
        text = text.replace('\u2015', '-')  # horizontal bar
        
        # Replace various quotation marks with regular quotes
        text = text.replace('\u2018', "'")  # left single quotation mark
        text = text.replace('\u2019', "'")  # right single quotation mark
        text = text.replace('\u201a', "'")  # single low-9 quotation mark
        text = text.replace('\u201c', '"')  # left double quotation mark
        text = text.replace('\u201d', '"')  # right double quotation mark
        text = text.replace('\u201e', '"')  # double low-9 quotation mark
        
        # Replace various spaces with regular spaces
        text = text.replace('\u00a0', ' ')  # non-breaking space
        text = text.replace('\u2000', ' ')  # en quad
        text = text.replace('\u2001', ' ')  # em quad
        text = text.replace('\u2002', ' ')  # en space
        text = text.replace('\u2003', ' ')  # em space
        text = text.replace('\u2004', ' ')  # three-per-em space
        text = text.replace('\u2005', ' ')  # four-per-em space
        text = text.replace('\u2006', ' ')  # six-per-em space
        text = text.replace('\u2007', ' ')  # figure space
        text = text.replace('\u2008', ' ')  # punctuation space
        text = text.replace('\u2009', ' ')  # thin space
        text = text.replace('\u200a', ' ')  # hair space
        
        # Replace bullet points with standard characters
        text = text.replace('\u2022', '•')  # bullet
        text = text.replace('\u2023', '•')  # triangular bullet
        text = text.replace('\u25e6', '•')  # white bullet
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def clean_json_data(self, data):
        """Recursively clean Unicode characters from JSON data"""
        if isinstance(data, dict):
            return {key: self.clean_json_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.clean_json_data(item) for item in data]
        elif isinstance(data, str):
            return self.clean_text(data)
        else:
            return data

    def extract_emails(self, page_texts: list[str]) -> list[str]:
        emails = []
        no_email_count = 1
        for page in page_texts:
            email_matches = self.EMAIL_REGEX.findall(page)
            if email_matches:
                emails.append(email_matches[0])  # Take the first email found on the page
            else:
                emails.append(f"NO_EMAIL_{no_email_count}")
                no_email_count += 1
        return emails

    def extract_linkedin_from_page(self, page) -> str:
        # Extract LinkedIn URL from PDF page using PyMuPDF
        links = page.get_links()
        for link in links:
            if 'uri' in link and link['uri'] and 'linkedin.com/in/' in link['uri']:
                return link['uri']
        return "NO_LINKEDIN"
        

    def generate_structured_data(self, resume_text: list[str], emails: list[str], target_job: str = "") -> dict:
        # Pass in resume text and return structured data to display on the FE
        api_key = os.environ.get("API_KEY_GROQ")

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        structured_data = {}

        for resume, email, linkedin in zip(resume_text, emails, self.linkedins):

            # if email == "NO_EMAIL":
            #     continue

            # Clean the resume text before processing
            cleaned_resume = self.clean_text(resume)

            # Create the prompt with job context if provided
            job_context = f"for the job role: {target_job}" if target_job else "for any general position"
            
            prompt = f"""
            Extract the following information from this resume {job_context}:
            
            Resume text:
            {cleaned_resume}
            
            Please extract and return in JSON format:
            1. Full name of the person
            2. If present, top skills relating to the job role, comma separated
            3. Education details (college/university, degree, GPA if present, graduation year or current year)
            4. Work experiences (role, company, and max 2 bullet points of key achievements)
            5. Top 2 most relevant projects {job_context} (project name, brief description, technologies used)
            
            Format the response as clean JSON only.
            """

            response = client.responses.create(
                model="openai/gpt-oss-120b",
                instructions=prompt,
                input=cleaned_resume,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "product_review",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "full_name" : {"type": "string"},
                                "skills": {"type": "string"},
                                "education": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "institution": {"type": "string"},
                                            "degree": {"type": "string"},
                                            "gpa": {"type": "string"},
                                            "graduation_year": {"type": "string"}
                                        }
                                    }
                                },
                                "work_experience": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "role": {"type": "string"},
                                            "company": {"type": "string"},
                                            "achievements": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            }
                                        }
                                    }
                                },
                                "projects": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "project_name": {"type": "string"},
                                            "description": {"type": "string"},
                                            "technologies": {"type": "string"}
                                        }
                                    }
                                }
                            },
                            "required": ["full_name", "education", "work_experience", "projects"],
                            "additional_properties": False  
                        }
                    }
                },

                temperature=0.1
            )

            try:
                # Clean the response text before parsing JSON
                cleaned_response = self.clean_text(response.output_text)

                parsed_data = json.loads(cleaned_response)
                
                # Also clean any string values in the parsed data recursively
                cleaned_parsed_data = self.clean_json_data(parsed_data)
                if "full_name" in cleaned_parsed_data:
                    cleaned_parsed_data = {
                        "full_name": cleaned_parsed_data["full_name"],
                        "linkedin": linkedin,
                        **{k: v for k, v in cleaned_parsed_data.items() if k != "full_name"}
                    }
                else:
                    cleaned_parsed_data["linkedin"] = linkedin
                structured_data[email] = cleaned_parsed_data
            except json.JSONDecodeError:
                structured_data[email] = {"error": "Failed to parse response", "raw_response": response.output_text}

        return structured_data


def process_resume_file(file_path: str, target_job: str = "Data Scientist") -> dict:
    """
    Wrapper function to process a resume file and return structured data
    This provides a simpler interface for API usage
    """
    parser = ResumeParser()
    
    # Extract text and process
    page_texts = parser.extract_text_from_pdf(file_path)
    emails = parser.extract_emails(page_texts)
    structured_data = parser.generate_structured_data(page_texts, emails, target_job)
    
    return {
        "success": True,
        "pages_processed": len(page_texts),
        "resumes_found": len(emails),
        "data": structured_data
    }



if __name__ == "__main__":

    # Fill in the file name here
    file_name = '/Users/aviralgupta/Downloads/resume_test_copy.pdf'
    
    # Specify the target job role (leave empty for general parsing)
    target_job = "Data Scientist"

    parser = ResumeParser()

    resumes = parser.extract_text_from_pdf(file_name)
    print(f"Extracted {len(resumes)} pages from PDF")

    emails = parser.extract_emails(resumes)
    print(f"Found emails: {emails}")

    print(f"\nExtracting structured data for job role: {target_job}")
    structured_data = parser.generate_structured_data(resumes, emails, target_job)
    
    # Print results
    for email, data in structured_data.items():
        print(f"\n{'='*60}")
        print(f"RESUME FOR: {email}")
        print(f"{'='*60}")
        print(json.dumps(data, indent=2))
    
    # Save to file
    with open('parsed_resumes_structured.json', 'w') as f:
        json.dump(structured_data, f, indent=2)
    
    print(f"\n✅ Structured data saved to 'parsed_resumes_structured.json'")