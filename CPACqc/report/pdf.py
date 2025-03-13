from CPACqc.report.utils import *

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from colorama import Fore, Style
import pandas as pd
import os
import json
# ...existing code...

def make_pdf(df, qc_dir, sub_ses):
    print(Fore.YELLOW + "Generating PDF report..." + Style.RESET_ALL)

    # Handle .pdf in pdf_name
    pdf = f"{sub_ses}_qc_report.pdf"

    # Determine if pdf is a full path or just a file name
    if os.path.isabs(pdf):
        pdf_path = pdf
    else:
        pdf_path = os.path.join(os.getcwd(), pdf)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Add CPAC logo and description to the front page
    logo_path = 'https://avatars.githubusercontent.com/u/2230402?s=200&v=4'  # Adjust the path as needed
    logo_img = ImageReader(logo_path)
    logo_width = 150  # Adjust the logo width
    logo_height = 150  # Adjust the logo height

    # Title at the top
    c.setFont("Helvetica", 30)
    c.drawCentredString(width / 2, height - 100, f"{sub_ses}")

    # Logo in the middle
    c.drawImage(logo_img, (width - logo_width) / 2, (height - logo_height) / 2, width=logo_width, height=logo_height)
    c.setFont("Helvetica", 15)
    c.drawCentredString(width / 2, height - 120, "Quality Control Report")

    # Footer information
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, 100, f"Created on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawCentredString(width / 2, 80, "CPAC developers")

    # Add an initial page to skip the first page
    c.showPage()

    # Contents page
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, height - 100, "Contents")
    c.setFont("Helvetica", 12)
    y_position = height - 150
    contents = []

    # Get unique chapters and sort them in ascending order
    chapters = sorted(set(df['datatype'].dropna()))

    for chapter in chapters:
        contents.append(f"{chapter}")
        y_position -= 20
        c.setFillColor(colors.blue)
        c.drawString(100, y_position, f"{chapter}")
        c.linkRect("", f"chapter_{chapter}", (100, y_position - 2, 200, y_position + 10), color=colors.blue)
        y_position -= 10

        # List subsections under each chapter if they exist
        chapter_data = df[df['datatype'] == chapter]
        scans = sorted(set(chapter_data['scan'].dropna()))
        for scan in scans:
            c.setFillColor(colors.green)
            c.drawString(120, y_position, f"{scan}")
            c.linkRect("", f"subsection_{chapter}_{scan}", (120, y_position - 2, 220, y_position + 10), color=colors.green)
            y_position -= 20

    y_position = height - 30  # Start at the top of the new page
    page_number = 1  # Initialize page number

    # Add all images to the PDF, grouped by chapter and scan
    for chapter in chapters:
        # Add a new page for each chapter
        c.showPage()
        page_number += 1  # Increment page number
        y_position = height - 30  # Reset y_position for the new page

        # Add chapter name to the blank page
        c.setFont("Helvetica", 30)
        c.drawCentredString(width / 2, height / 2, chapter)
        c.bookmarkPage(f"chapter_{chapter}")

        chapter_data = df[df['datatype'] == chapter]
        scans = sorted(set(chapter_data['scan'].dropna()))

        for scan in scans:
            # Add a new page for each scan
            c.showPage()
            page_number += 1  # Increment page number
            y_position = height - 30  # Reset y_position for the new page

            # Add chapter name and subsection string at the top of each page
            c.setFont("Helvetica", 12)
            c.drawString(10, height - 30, f"Chapter: {chapter}/{scan}")
            c.bookmarkPage(f"subsection_{chapter}_{scan}")

            scan_data = chapter_data[chapter_data['scan'] == scan]

            if not scan_data.empty:
                for _, image_data in scan_data.iterrows():
                    image_path = os.path.join(qc_dir, image_data['relative_path'])
                    if os.path.exists(image_path):
                        img = ImageReader(image_path)
                        max_img_width = width - 20  # Adjust the max width to fit the page
                        max_img_height = height - 100  # Adjust the max height to fit the page

                        # Preserve aspect ratio
                        img_width, img_height = img.getSize()
                        aspect_ratio = img_width / img_height
                        if aspect_ratio > 1:
                            img_width = max_img_width
                            img_height = img_width / aspect_ratio
                        else:
                            img_height = max_img_height
                            img_width = img_height * aspect_ratio

                        # Check if the image fits on the current page, otherwise add a new page
                        if y_position - img_height - 140 < 0:  # Adjusted to account for additional text and white space
                            c.drawRightString(width - 30, 20, str(page_number))  # Add page number
                            c.showPage()
                            page_number += 1  # Increment page number
                            y_position = height - 30  # Reset y_position for the new page

                            # Add chapter name and subsection string at the top of each page
                            c.setFont("Helvetica", 12)
                            c.drawString(10, height - 30, f"Chapter : {chapter}/{scan}")
                            c.bookmarkPage(f"subsection_{chapter}_{scan}")

                        # Print the image name above each image
                        c.setFont("Helvetica", 15)
                        c.drawString(10, y_position - 20, f"{image_data['resource_name']}")

                        # Add the image to the PDF
                        c.drawImage(img, (width - img_width) / 2, y_position - img_height - 40, width=img_width, height=img_height)
                        
                        # Use Paragraph to wrap the label text
                        label = f"{image_data['file_name']}"
                        styles = getSampleStyleSheet()
                        styles['Normal'].textColor = colors.whitesmoke
                        wrapped_label = Paragraph(label, styles['Normal'])
                        wrapped_label.wrapOn(c, width - 20, height)

                        # Add file information under the image label
                        file_info = json.loads(image_data['file_info'])
                        file_info_text = [
                            ["Image:", wrapped_label],
                            ["Orientation:", file_info['orientation']],
                            ["Dimensions:", " x ".join(map(str, file_info['dimension']))],
                            ["Resolution:", " x ".join(map(lambda x: str(round(x, 2)), file_info['resolution']))]
                        ]

                        if file_info['tr'] is not None:
                            file_info_text.append(["TR:", str(round(file_info['tr'], 2))])

                        if file_info['nos_tr'] is not None:
                            file_info_text.append(["No of TRs:", str(file_info['nos_tr'])])

                        table = Table(file_info_text, colWidths=[80, width - 100])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))
                        table.wrapOn(c, width - 20, height)
                        table_height = table.wrap(width - 20, height)[1]
                        table.drawOn(c, 10, y_position - img_height - table_height - 60)

                        # Move to the next row after each image
                        y_position -= img_height  + table_height + 70  # Adjusted to account for additional text and white space

    # Add the final page number
    c.drawRightString(width - 30, 20, str(page_number))

    # Save the PDF
    c.save()
    print(Fore.GREEN + "PDF report generated successfully." + Style.RESET_ALL)