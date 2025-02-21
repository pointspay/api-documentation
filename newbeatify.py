import fitz  # PyMuPDF
import re
from pathlib import Path

def extract_text_with_headings(pdf_path, md_path, image_folder):
    doc = fitz.open(pdf_path)
    text_content = []

    pdf_filename = pdf_path.stem  # Get filename without extension
    page_pattern = re.compile(r"^Page \d+\s*$")  # Matches "Page X"
    table_pattern = re.compile(r"^Table \d+\s*$")  # Matches "Table X"
    toc_pattern = re.compile(r"^[A-Za-z\s]+(\d+)$")  # Matches "Some heading 3"

    for page in doc:
        page_text = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            for line in block.get("lines", []):
                line_text = []
                is_bold = False
                font_size = 0

                raw_line = "".join([span["text"] for span in line["spans"]]).strip()

                # Skip unwanted entries
                if page_pattern.match(raw_line) or table_pattern.match(raw_line):
                    continue  # Remove "Page X" and "Table X"
                if toc_pattern.match(raw_line):
                    continue  # Remove TOC-like entries
                if raw_line == "." * len(raw_line):  
                    continue  # Remove lines made entirely of dots

                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    # Remove misplaced numbers (e.g., TOC numbers)
                    text = re.sub(r"\s*\d+\s*$", "", text)  # Remove trailing numbers
                    
                    # Remove sequences of dots
                    text = re.sub(r'\.{4,}', '', text)

                    font_size = span["size"]
                    font_name = span["font"].lower()
                    is_bold = "bold" in font_name

                    # Assign heading levels based on font size
                    if font_size >= 18:
                        text = f"# {text}"  # H1
                    elif font_size >= 16:
                        text = f"## {text}"  # H2
                    elif font_size >= 14:
                        text = f"### {text}"  # H3
                    elif is_bold:
                        text = f"**{text}**"

                    line_text.append(text)

                page_text.append(" ".join(line_text))

        text_content.append("\n".join(page_text))
        text_content.append("---")  # Page separator

    # Save to Markdown
    md_path.write_text("\n\n".join(text_content).strip(), encoding="utf-8")
    print(f"✅ Extracted text saved to {md_path}")

    # Extract images
    extract_images(doc, pdf_filename, image_folder)

def extract_images(doc, pdf_filename, image_folder):
    image_folder.mkdir(parents=True, exist_ok=True)
    image_count = 0

    for page_num, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_filename = image_folder / f"{pdf_filename}_page{page_num + 1}_{img_index + 1}.png"

            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)

            image_count += 1

    print(f"✅ Extracted {image_count} images saved to {image_folder}")

def process_pdfs(pdf_folder, md_folder, image_folder):
    md_folder.mkdir(parents=True, exist_ok=True)
    image_folder.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdf_folder.glob("*.pdf"):
        md_path = md_folder / f"{pdf_path.stem}.md"
        extract_text_with_headings(pdf_path, md_path, image_folder)

# Paths
root_dir = Path(__file__).resolve().parent
pdf_folder = root_dir / "input_pdfs"
md_folder = root_dir / "output_markdown"
image_folder = root_dir / "output_images"

# Run script
process_pdfs(pdf_folder, md_folder, image_folder)
