#IMPORTS
import os 
import requests 
import json 
from typing import List 
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import ollama
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import markdown
import re


#CONSTANTS
MODEL = "llama3.2"
headers = {
   "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


#ENVIORNMENT
load_dotenv(override=True)

class Website:
  """
   utility class of website object that we will parse with links 
  """

  def __init__(self, url):
    print(f"Generating website object for {url}... \n \n")

    self.url = url
    try:
      response = requests.get(url, headers=headers, timeout=10)
      response.raise_for_status()  # Raise an exception for bad status codes
      self.body = response.content

      soup = BeautifulSoup(self.body, 'html.parser')
      self.title = soup.title.string if soup.title else "No title found"

      if soup.body:
          for irrelevant in soup.body(["script", "style", "img", "input"]):
              irrelevant.decompose()
          self.text = soup.body.get_text(separator="\n", strip=True)
      else:
          self.text = ""

      links = [link.get('href') for link in soup.find_all('a')]
      self.links = [link for link in links if link]
    except Exception as e:
      print(f"Error fetching {url}: {str(e)}")
      self.body = ""
      self.title = "Error fetching page"
      self.text = f"Could not fetch content from {url}"
      self.links = []

    print("Generated website object!! \n \n")
  
  def get_contents(self):
    return f"Webpage title:\n {self.title} \n webpage contents:\n {self.text}\n \n"




link_system_prompt = "You are provided with a list of links found on a webpage. \
You are able to decide which of the links would be most relevant to include in a brochure about the company, \
such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
link_system_prompt += "You should respond in JSON as in this example:"
link_system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page": "url": "https://another.full.url/careers"}
    ]
}
"""


def get_links_user_prompt(website):
  print("Generating user prompt to get additional links... \n \n")


  user_prompt = f"Here is the list of links on the website of {website.url} - "
  user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. \
Do not include Terms of Service, Privacy, email links.\n"
  user_prompt += "Links (some might be relative links):\n"
  user_prompt += "\n".join(website.links)

  print("Generated user prompt to get additional links!! \n \n")
  return user_prompt


def get_links(url):
  print("Fetching user prompt to get additional links... \n \n")
  website = Website(url)
  response = ollama.chat(
    model=MODEL,
    messages=[
      {"role": "system", "content": link_system_prompt},
      {"role": "user", "content": get_links_user_prompt(website)}
    ],
    format="json"
  )

  result = response['message']['content']
  print("Fetched user prompt to get additional links!! \n \n")

  return json.loads(result)


def get_all_details(url):
  print("Fetching all the details using all the links... \n \n")

  result = "Landing page: \n"
  result += Website(url).get_contents()
  
  try:
    links = get_links(url)
    
    for link in links.get("links", []):
      try:
        result += f"\n \n {link['type']} \n"
        # Ensure the URL is absolute
        link_url = link["url"]
        if not link_url.startswith(('http://', 'https://')):
          # If it's a relative URL, make it absolute
          if link_url.startswith('/'):
            base_url = '/'.join(url.split('/')[:3])  # Get domain part
            link_url = base_url + link_url
          else:
            link_url = url.rstrip('/') + '/' + link_url

        result += Website(link_url).get_contents()
      except Exception as e:
        print(f"Error processing link {link.get('url')}: {str(e)}")
        continue

  except Exception as e:
    print(f"Error getting links: {str(e)}")
    # Return just the landing page content if we can't get additional links
    pass

  print("Fetched all the details using all the links!! \n \n")
  return result


system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
Include details of company culture, customers and careers/jobs if you have the information."

# Or uncomment the lines below for a more humorous brochure - this demonstrates how easy it is to incorporate 'tone':

# system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
# and creates a short humorous, entertaining, jokey brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
# Include details of company culture, customers and careers/jobs if you have the information."

def get_brochure_user_prompt(company_name, url):
  print("Generating user prompt to create a brochure... \n \n")

  user_prompt = f"You are looking at a company called: {company_name}\n"
  user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company.\n"
  user_prompt += get_all_details(url)
  user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters


  print("Generated user prompt to create a brochure!! \n \n")
  return user_prompt


pdf_system_prompt = """You are a professional document designer that structures content for PDF brochures.
Format the content into clear sections with appropriate headings and styling.
Each section should be clearly marked with '###' for headers.
Use bullet points where appropriate.
Keep the formatting clean and professional.
Also if you use any images just use any random images present on google, make sure the images work.
"""

def convert_to_pdf_content(markdown_content):
    print("Structuring content for PDF... \n \n")
    
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": pdf_system_prompt},
            {"role": "user", "content": f"Structure this content for a PDF brochure: \n\n{markdown_content}"}
        ]
    )
    
    structured_content = response['message']['content']
    print("Content structured for PDF!! \n \n")
    return structured_content

def create_pdf_brochure(content, company_name):
    filename = f"{company_name.lower().replace(' ', '_')}_brochure.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='BrochureTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a237e')
    ))
    styles.add(ParagraphStyle(
        name='BrochureHeader',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#303f9f')
    ))
    styles.add(ParagraphStyle(
        name='BrochureBodyText',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        leading=14
    ))

    # Build PDF content
    elements = []
    
    # Add title
    elements.append(Paragraph(company_name + " Brochure", styles['BrochureTitle']))
    elements.append(Spacer(1, 12))

    # Process content sections
    sections = content.split('###')
    for section in sections:
        if not section.strip():
            continue
            
        # Split into lines
        lines = section.strip().split('\n')
        if lines:
            # First line is header
            header = lines[0].strip()
            elements.append(Paragraph(header, styles['BrochureHeader']))
            
            # Rest is content
            content = '\n'.join(lines[1:]).strip()
            
            # Process bullet points
            for paragraph in content.split('\n\n'):
                if paragraph.strip():
                    if paragraph.startswith('*'):
                        # Handle bullet points
                        for bullet in paragraph.split('\n'):
                            if bullet.strip():
                                elements.append(Paragraph(
                                    bullet.replace('*', '•'),
                                    styles['BrochureBodyText']
                                ))
                    else:
                        elements.append(Paragraph(paragraph, styles['BrochureBodyText']))
                        
                elements.append(Spacer(1, 12))

    # Generate PDF
    doc.build(elements)
    print(f"Saved brochure as {filename}!! \n \n")
    return filename

def create_brochure(company_name, url):
    print(f"Creating the brochure {company_name} ... \n \n")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    markdown_result = response['message']['content']
    print(f"Created the markdown brochure for {company_name} !! \n \n")
    
    # Convert to PDF-friendly content and save
    pdf_content = convert_to_pdf_content(markdown_result)
    filename = create_pdf_brochure(pdf_content, company_name)
    
    print(f"Brochure has been created and saved as {filename}")
    return filename

def stream_brochure(company_name, url):
    print(f"Creating the brochure {company_name} ... \n \n")
    
    markdown_content = ""
    stream = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
        stream=True
    )
    
    for chunk in stream:
        if 'message' in chunk:
            content = chunk['message']['content']
            markdown_content += content
            print(content, end='')
    
    print(f"\nCreated the markdown brochure {company_name}!! \n \n")
    
    # Convert to PDF-friendly content and save
    pdf_content = convert_to_pdf_content(markdown_content)
    filename = create_pdf_brochure(pdf_content, company_name)
    
    print(f"Brochure has been created and saved as {filename}")
    return filename

# Example usage:
stream_brochure("HuggingFace", "https://huggingface.co")
# or
# create_brochure("HuggingFace", "https://huggingface.co")