from CPACqc.report.utils import *
import pandas as pd
from fnmatch import fnmatch
from CPACqc.logging.log import logger
from CPACqc.report.utils import *
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from colorama import Fore, Style
import os
import json

class Report:
    def __init__(self, df, qc_dir, sub_ses, overlay_df=None):
        self.df = df
        self.qc_dir = qc_dir
        self.sub_ses = sub_ses
        self.overlay_df = overlay_df
        self.pdf_path = self.get_pdf_path()
        self.canvas = canvas.Canvas(self.pdf_path, pagesize=letter)
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()

    def get_pdf_path(self):
        pdf = f"{self.sub_ses}_qc_report.pdf"
        if os.path.isabs(pdf):
            return pdf
        else:
            return os.path.join(os.getcwd(), pdf)

    def add_front_page(self):
        logo_path = 'https://avatars.githubusercontent.com/u/2230402?s=200&v=4'
        logo_img = ImageReader(logo_path)
        logo_width = 150
        logo_height = 150

        self.canvas.setFont("Helvetica", 25)
        title = Paragraph(f"{self.sub_ses.replace('_', ' ')}", self.styles['Title'])
        title.wrapOn(self.canvas, self.width - 40, self.height)
        title.drawOn(self.canvas, 20, self.height - 100)

        self.canvas.drawImage(logo_img, (self.width - logo_width) / 2, (self.height - logo_height) / 2, width=logo_width, height=logo_height)
        self.canvas.setFont("Helvetica", 15)
        self.canvas.drawCentredString(self.width / 2, self.height - 120, "Quality Control Report")

        self.canvas.setFont("Helvetica", 12)
        self.canvas.drawCentredString(self.width / 2, 100, f"Created on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.canvas.drawCentredString(self.width / 2, 80, "CPAC developers")

        self.canvas.showPage()

    def add_contents_page(self):
        self.canvas.setFont("Helvetica", 20)
        self.canvas.drawCentredString(self.width / 2, self.height - 100, "Contents")
        self.canvas.setFont("Helvetica", 12)
        y_position = self.height - 150
        chapters = sorted(set(self.df['datatype'].dropna()))

        for chapter in chapters:
            if y_position < 50:
                self.canvas.showPage()
                y_position = self.height - 50
            y_position -= 20
            self.canvas.setFillColor(colors.blue)
            self.canvas.drawString(100, y_position, f"{chapter}")
            text_width = self.canvas.stringWidth(chapter, "Helvetica", 12)
            self.canvas.linkRect("", f"chapter_{chapter}", (100, y_position - 2, 100 + text_width, y_position + 10), color=colors.blue)
            y_position -= 10

            chapter_data = self.df[self.df['datatype'] == chapter]
            scans = sorted(set(chapter_data['scan'].dropna()))
            for scan in scans:
                if y_position < 50:
                    self.canvas.showPage()
                    y_position = self.height - 50
                self.canvas.setFillColor(colors.green)
                self.canvas.drawString(120, y_position, f"{scan}")
                text_width = self.canvas.stringWidth(scan, "Helvetica", 12)
                if scan.strip() == '':
                    self.canvas.linkRect("", f"subsection_{chapter}", (120, y_position - 2, 120 + text_width, y_position + 10), color=colors.green)
                else:
                    self.canvas.linkRect("", f"subsection_{chapter}_{scan}", (120, y_position - 2, 120 + text_width, y_position + 10), color=colors.green)
                y_position -= 10

                scan_data = chapter_data[chapter_data['scan'] == scan]

                if not scan_data.empty:
                    ordered_images = []
                    extra_images = []

                    if self.overlay_df is not None:
                        ordered_images = scan_data[scan_data['resource_name'].isin(self.overlay_df['output'])]
                        extra_images = scan_data[~scan_data['resource_name'].isin(self.overlay_df['output'])]
                    else:
                        ordered_images = scan_data

                    # Remove duplicates, keeping only the last occurrence
                    ordered_images = ordered_images.drop_duplicates(subset='file_name', keep='last')
                    extra_images = extra_images.drop_duplicates(subset='file_name', keep='last')

                    for _, image_data in ordered_images.iterrows():
                        if y_position < 50:
                            self.canvas.showPage()
                            y_position = self.height - 50
                        self.canvas.setFillColor(colors.black)
                        self.canvas.drawString(140, y_position, f"{image_data['resource_name']}")
                        text_width = self.canvas.stringWidth(image_data['resource_name'], "Helvetica", 12)
                        self.canvas.linkRect("", f"image_{chapter}_{scan}_{image_data['resource_name']}", (140, y_position - 2, 140 + text_width, y_position + 10), color=colors.blue)
                        y_position -= 13

                    for _, image_data in extra_images.iterrows():
                        if y_position < 50:
                            self.canvas.showPage()
                            y_position = self.height - 50
                        self.canvas.setFillColor(colors.black)
                        self.canvas.drawString(140, y_position, f"{image_data['resource_name']}")
                        text_width = self.canvas.stringWidth(image_data['resource_name'], "Helvetica", 12)
                        self.canvas.linkRect("", f"image_{chapter}_{scan}_{image_data['resource_name']}", (140, y_position - 2, 140 + text_width, y_position + 10), color=colors.blue)
                        y_position -= 13

                y_position -= 10
        self.canvas.showPage()

    def add_images(self):
        chapters = sorted(set(self.df['datatype'].dropna()))
        page_number = 1  

        for chapter in chapters:
            self.add_chapter_title_page(chapter)
            page_number += 1

            chapter_data = self.df[self.df['datatype'] == chapter]
            scans = sorted(set(chapter_data['scan'].dropna()))

            for scan in scans:

                self.add_scan_title_page(chapter, scan)
                page_number += 1

                scan_data = chapter_data[chapter_data['scan'] == scan]

                if not scan_data.empty:
                    ordered_images = []
                    extra_images = []

                    if self.overlay_df is not None:
                        ordered_images = scan_data[scan_data['resource_name'].isin(self.overlay_df['output'])]
                        extra_images = scan_data[~scan_data['resource_name'].isin(self.overlay_df['output'])]
                    else:
                        ordered_images = scan_data

                    # Remove duplicates, keeping only the last occurrence
                    ordered_images = ordered_images.drop_duplicates(subset='file_name', keep='last')
                    extra_images = extra_images.drop_duplicates(subset='file_name', keep='last')

                    y_position = self.height - 30

                    for _, image_data in ordered_images.iterrows():
                        y_position, page_number = self.add_image(image_data, chapter, scan, y_position, page_number)

                    for _, image_data in extra_images.iterrows():
                        y_position, page_number = self.add_image(image_data, chapter, scan, y_position, page_number)

    def add_chapter_title_page(self, chapter):
        self.canvas.setFont("Helvetica", 30)
        self.canvas.drawCentredString(self.width / 2, self.height / 2, chapter)
        self.canvas.bookmarkPage(f"chapter_{chapter}")
        self.canvas.showPage()

    def add_scan_title_page(self, chapter, scan):
        if scan.strip() == '':
            print(Fore.YELLOW + f"Scan name is empty for chapter {chapter}. Skipping..." + Style.RESET_ALL)
            self.canvas.bookmarkPage(f"subsection_{chapter}")
            return
        self.canvas.setFont("Helvetica", 25)
        self.canvas.drawCentredString(self.width / 2, self.height / 2, f"{chapter} - {scan}")
        self.canvas.bookmarkPage(f"subsection_{chapter}_{scan}")
        self.canvas.showPage()

    def add_image(self, image_data, chapter, scan, y_position, page_number):
        image_path = os.path.join(self.qc_dir, image_data['relative_path'])
        if os.path.exists(image_path):
            img = ImageReader(image_path)
            max_img_width = self.width - 20
            max_img_height = self.height - 100

            img_width, img_height = img.getSize()
            aspect_ratio = img_width / img_height
            if aspect_ratio > 1:
                img_width = max_img_width
                img_height = img_width / aspect_ratio
            else:
                img_height = max_img_height
                img_width = img_height * aspect_ratio

            if y_position - img_height - 140 < 0:
                self.add_footer(page_number)
                page_number += 1
                y_position = self.height - 30
                self.add_header(chapter, scan)

            self.canvas.setFont("Helvetica", 15)
            self.canvas.drawString(10, y_position - 20, f"{image_data['resource_name']}")
            self.canvas.bookmarkPage(f"image_{chapter}_{scan}_{image_data['resource_name']}")

            self.canvas.drawImage(img, (self.width - img_width) / 2, y_position - img_height - 40, width=img_width, height=img_height)

            label = f"{image_data['file_name']}"
            self.styles['Normal'].textColor = colors.whitesmoke
            wrapped_label = Paragraph(label, self.styles['Normal'])
            wrapped_label.wrapOn(self.canvas, self.width - 20, self.height)

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

            table = Table(file_info_text, colWidths=[80, self.width - 100])
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
            table.wrapOn(self.canvas, self.width - 20, self.height)
            table_height = table.wrap(self.width - 20, self.height)[1]
            table.drawOn(self.canvas, 10, y_position - img_height - table_height - 60)

            y_position -= img_height + table_height + 70
            
            self.canvas.showPage()
        return y_position, page_number

    def add_header(self, chapter, scan):
        self.canvas.setFont("Helvetica", 12)
        self.canvas.drawString(10, self.height - 30, f"Chapter : {chapter}/{scan}")

    def add_footer(self, page_number):
        self.canvas.drawRightString(self.width - 30, 20, str(page_number))

    def generate(self):
        print(Fore.YELLOW + "Generating PDF report..." + Style.RESET_ALL)
        self.add_front_page()
        self.add_contents_page()
        self.add_images()
        self.canvas.save()
        print(Fore.GREEN + "PDF report generated successfully." + Style.RESET_ALL)

def make_pdf(df, qc_dir, sub_ses, overlay_df=None):
    report = Report(df, qc_dir, sub_ses, overlay_df)
    report.generate()