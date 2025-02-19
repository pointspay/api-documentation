import os
import fitz  # PyMuPDF
import re  # Regular expression module
from pathlib import Path

def extract_text_with_headings(pdf_path, md_path, image_folder):
    doc = fitz.open(pdf_path)
    text_content = ""

    # Extract the base name of the PDF file to use in image filenames
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]

    # Regular expressions to remove unwanted lines like "Page x" and "Table x"
    page_pattern = re.compile(r"Page \d+")  # Matches lines like "Page 1", "Page 2", etc.
    table_pattern = re.compile(r"Table \d+")  # Matches lines like "Table 1", "Table 2", etc.

    # Extract text and headings
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]  # Extract structured text

        for block in blocks:
            for line in block.get("lines", []):
                line_text = ""
                is_bold = False  # Flag for bold text
                font_size = 0  # Track font size

                # Check if the line is composed only of dots
                raw_line = "".join([span["text"] for span in line["spans"]]).strip()

                # Skip lines like "Page x" or "Table x"
                if page_pattern.match(raw_line) or table_pattern.match(raw_line):
                    continue  # Skip this line (remove it)

                if raw_line == "." * len(raw_line):  # Line is full of dots
                    continue  # Skip this line (remove it)

                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    # Remove sequences of dots if they are more than 3 dots in a row
                    text = re.sub(r'\.{4,}', '', text)  # Remove sequences of 4 or more dots

                    font_size = span["size"]  # Extract font size
                    font_name = span["font"].lower()

                    # Determine if the text is bold
                    is_bold = "bold" in font_name

                    # Assign heading levels based on font size
                    if font_size >= 18:  # Large size for H1
                        text = f"# {text}"
                    elif font_size >= 16:  # Medium size for H2
                        text = f"## {text}"
                    elif font_size >= 14:  # Smaller heading for H3
                        text = f"### {text}"
                    elif is_bold:  # Bold but not large enough for a heading
                        text = f"**{text}**"

                    line_text += text + " "

                text_content += line_text.strip() + "\n\n"

        text_content += "---\n\n"  # Page separator

    # Save text content to Markdown file
    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(text_content)

    print(f"Extracted text saved to {md_path}")

    # Extract images from the PDF and save them
    image_count = 0
    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # Include PDF filename in the image filename
            image_filename = os.path.join(image_folder, f"{pdf_filename}_image_{page_num + 1}_{img_index + 1}.png")

            # Save the image
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            image_count += 1

    print(f"Extracted {image_count} images saved to {image_folder}")


def extract_from_folder(pdf_folder, md_folder, image_folder):
    # Ensure output folders exist
    os.makedirs(md_folder, exist_ok=True)
    os.makedirs(image_folder, exist_ok=True)

    # Process all PDF files in the folder
    for filename in os.listdir(pdf_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            md_filename = os.path.splitext(filename)[0] + ".md"
            md_path = os.path.join(md_folder, md_filename)

            # Extract text and images
            extract_text_with_headings(pdf_path, md_path, image_folder)

# Input and Output folder paths
root_dir = Path(__file__).resolve().parent
pdf_folder = root_dir / "input_pdfs"
md_folder = root_dir / "output_markdown"
image_folder = root_dir / "output_images"

# Run the extraction
extract_from_folder(pdf_folder, md_folder, image_folder)
