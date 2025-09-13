# Not ATS
A full-stack application that parses candidates and lets recruiters pick the best one by putting candidates head to head.

## Resume Parser (backend script)

A Python script that extracts key information from bulk PDF resumes using AI-powered parsing. Handles multi-page PDFs containing multiple resumes and extracts structured data including experiences, projects, skills, and education.

## Features

- **Bulk PDF Processing**: Process PDFs containing up to 200 pages with multiple resumes
- **Automatic Resume Detection**: Uses email addresses to identify and split individual resumes
- **Multi-page Resume Support**: Automatically merges two-page resumes based on matching email addresses
- **AI-Powered Extraction**: Uses Groq's LLM for intelligent data extraction
- **Job-Role Filtering**: Extracts skills and projects relevant to specific job roles
- **Unicode Normalization**: Cleans PDF text artifacts and special characters
- **Structured JSON Output**: Saves parsed data in clean, structured JSON format
- **Error Handling**: Gracefully handles parsing errors and resumes without email addresses

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Groq API key:
```bash
# Create a .env file in the project directory
echo "API_KEY_GROQ=your_groq_api_key_here" > .env
```

## Usage

### Basic Usage
```python
from parser import ResumeParser

# Initialize the parser
parser = ResumeParser()

# Extract text from PDF
resumes = parser.extract_text_from_pdf('bulk_resumes.pdf')

# Extract emails to identify individual resumes
emails = parser.extract_emails(resumes)

# Generate structured data with AI
structured_data = parser.generate_structured_data(resumes, emails, target_job="Data Scientist")
```

### Command Line Usage
Update the file paths in the script and run:
```bash
python parser.py
```

## Configuration

Edit the main section in `parser.py`:

```python
if __name__ == "__main__":
    # Update the file path to your PDF
    file_name = '/path/to/your/bulk_resumes.pdf'
    
    # Specify target job role (leave empty for general parsing)
    target_job = "Data Scientist"  # Change to your target role
    
    # Run the parser
    parser = ResumeParser()
    # ... rest of the code
```

## Output

The script generates a `parsed_resumes_structured.json` file with structured data for each resume, using email addresses as keys:

```json
{
  "john.doe@email.com": {
    "full_name": "John Doe",
    "skills": "Python, TensorFlow, AWS, Docker, Machine Learning, Data Science",
    "education": [
      {
        "institution": "University of Technology",
        "degree": "Bachelor of Science in Computer Science",
        "gpa": "3.8",
        "graduation_year": "2020"
      }
    ],
    "work_experience": [
      {
        "role": "Data Scientist",
        "company": "Tech Corp",
        "achievements": [
          "Built ML models that improved prediction accuracy by 25%",
          "Led cross-functional team of 5 engineers on data pipeline project"
        ]
      }
    ],
    "projects": [
      {
        "project_name": "Stock Price Predictor",
        "description": "LSTM model for predicting stock prices using historical data",
        "technologies": "Python, TensorFlow, Keras, pandas, NumPy"
      }
    ]
  },
  "NO_EMAIL": {
    "full_name": "Jane Smith",
    "skills": "React, Node.js, JavaScript, MongoDB",
    "education": [...],
    "work_experience": [...],
    "projects": [...]
  }
}
```

## Key Components

### Email-Based Resume Identification
The parser uses email addresses found in resumes to:
- Identify individual resumes within bulk PDFs
- Merge multi-page resumes (when the same email appears on consecutive pages)
- Handle resumes without emails (labeled as "NO_EMAIL", "NO_EMAIL_1", etc.)

### AI-Powered Data Extraction
- Uses Groq's `gpt-oss-120b` model for intelligent parsing
- Extracts job-role-specific skills and projects when target job is specified
- Provides structured JSON output with consistent schema
- Handles parsing errors gracefully

### Unicode Text Cleaning
- Normalizes Unicode characters from PDF extraction
- Converts special characters (em dashes, smart quotes, etc.) to ASCII equivalents
- Cleans both input text and AI response to ensure clean output

## Customization

### Changing Target Job Role
Modify the target job role to extract relevant skills and projects:

```python
# For Data Science roles
target_job = "Data Scientist"

# For Software Engineering roles  
target_job = "Software Engineer"

# For general parsing (no job-specific filtering)
target_job = ""
```

### Modifying API Settings
Update the API configuration in `generate_structured_data()`:

```python
# Change the model (available models: llama-3.1-70b-versatile, etc.)
model="openai/gpt-oss-120b"

# Adjust temperature for creativity vs consistency
temperature=0.1  # Lower = more consistent, Higher = more creative
```

### Adding Custom Text Cleaning
Extend the `clean_text()` method to handle additional Unicode characters:

```python
def clean_text(self, text: str) -> str:
    # Add custom character replacements
    text = text.replace('\u2026', '...')  # ellipsis
    text = text.replace('\u00ae', '(R)')  # registered trademark
    # ... existing cleaning code
```

## File Structure

```
not_ats/
├── parser.py                          # Main parser script with AI integration
├── requirements.txt                   # Python dependencies  
├── .env                              # API keys (create this file)
├── .gitignore                        # Git ignore file
├── README.md                         # This file
└── parsed_resumes_structured.json   # Output file (generated)
```

## Dependencies

- `pdfplumber`: PDF text extraction
- `openai`: OpenAI-compatible client for Groq API
- `groq`: Groq API integration  
- `python-dotenv`: Environment variable management
- `unicodedata`: Unicode normalization (built-in)
- `json`, `re`, `os`: Standard library modules

## Environment Setup

Create a `.env` file in the project directory with your Groq API key:

```env
API_KEY_GROQ=your_groq_api_key_here
```

Get your API key from [Groq Console](https://console.groq.com/).

## Notes

- **PDF Quality**: Works best with text-based PDFs; image-based PDFs may need OCR preprocessing
- **Email Detection**: Resumes are identified by email addresses; resumes without emails are labeled as "NO_EMAIL"
- **API Costs**: Each resume processed makes one API call to Groq (check pricing)
- **Processing Time**: Bulk processing time depends on number of resumes and API response times
- **Unicode Handling**: Automatically cleans PDF artifacts like smart quotes and special hyphens

## Troubleshooting

1. **API Errors**: 
   - Check your Groq API key in `.env` file
   - Verify API quota and billing status
   - Ensure internet connectivity

2. **No Text Extracted**: 
   - PDF might be image-based (use OCR tools first)
   - Check if PDF is password-protected or corrupted

3. **Missing Email Detection**: 
   - Resumes without emails will be labeled "NO_EMAIL"
   - Check email regex pattern if detection seems inaccurate

4. **Unicode Issues**: 
   - The parser includes comprehensive Unicode cleaning
   - Add custom character mappings in `clean_text()` if needed

5. **Poor Extraction Quality**:
   - Adjust the target job role for better relevance
   - Modify the prompt in `generate_structured_data()` for different extraction requirements

## Future Enhancements

- **Multiple File Formats**: Support for Word documents (.docx) and other formats
- **Advanced Resume Splitting**: Improve detection algorithms for complex layouts
- **Batch Job Processing**: Process multiple job roles in one run
- **Data Validation**: Add schema validation for extracted data
- **Export Options**: Support for CSV, Excel, and database exports
- **Resume Scoring**: Add relevance scoring based on job requirements
- **Language Support**: Multi-language resume parsing capabilities


