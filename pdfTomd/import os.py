import os
import fitz  # PyMuPDF
from pathlib import Path

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()  # Extract text from each page
    return text

# Function to extract images from PDF and save them as files
def extract_images_from_pdf(pdf_path, image_folder):
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    doc = fitz.open(pdf_path)
    image_list = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        img_list = page.get_images(full=True)
        
        for img in img_list:
            xref = img[0]  # Image reference number
            base_image = doc.extract_image(xref)  # Extract image using xref
            image_bytes = base_image["image"]  # Get the image bytes
            image_filename = os.path.join(image_folder, f"image_{page_num+1}_{xref}.png")
            
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)  # Write image data to file
            
            image_list.append(image_filename)  # Add image file path to list
    
    return image_list

# Function to generate Markdown from text and images
def generate_markdown(text, image_list):
    md_content = "# API Documentation\n\n"
    md_content += "## Extracted Text\n\n" + text + "\n\n"

    if image_list:
        md_content += "## Extracted Images\n\n"
        for img in image_list:
            md_content += f"![Image]({img})\n\n"
    
    return md_content

# Main function to convert PDF to Markdown
def convert_pdf_to_markdown(pdf_path, output_md_path, image_folder="images"):
    # Extract text and images
    text = extract_text_from_pdf(pdf_path)
    images = extract_images_from_pdf(pdf_path, image_folder)
    
    # Generate Markdown content
    markdown_content = generate_markdown(text, images)
    
    # Save the Markdown content to a file
    with open(output_md_path, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_content)
    
    print(f"Markdown file saved to {output_md_path}")

# Function to process multiple PDF files
def process_multiple_pdfs(pdf_folder, output_folder, image_folder="images"):
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # List all PDF files in the folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    
    # Loop through each PDF and convert it to markdown
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        output_md_path = os.path.join(output_folder, f"{os.path.splitext(pdf_file)[0]}.md")
        
        print(f"Processing {pdf_file}...")
        convert_pdf_to_markdown(pdf_path, output_md_path, image_folder)
        print(f"Converted {pdf_file} to {output_md_path}\n")

# Define the folder paths
root_dir = Path(__file__).resolve().parent.parent
print(root_dir)
pdf_folder = root_dir /"inputFiles"  # Folder containing PDFs
output_folder = root_dir / "mdFilesDoc"  # Folder to save the markdown files
image_folder = root_dir /"img"  # Folder to save images

# Example Usage: Process all PDFs in the specified folder
process_multiple_pdfs(pdf_folder, output_folder, image_folder)