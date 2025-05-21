import pandas as pd
from fnmatch import fnmatch
from CPACqc.core.logger import logger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from colorama import Fore, Style
import os
import json
from dataclasses import dataclass, field
from CPACqc.services.report_generator_service import ReportGeneratorService

@dataclass
class Report(ReportGeneratorService):
    _instance: "Report" = field(default=None, init=False, repr=False)
    df: pd.DataFrame = None
    qc_dir: str = None
    sub_ses: str = None
    overlay_df: pd.DataFrame = None
    pdf_path: str = field(init=False)
    pdf_canvas: canvas.Canvas = field(init=False)
    page_size: tuple = field(default=letter)
    width: int = field(init=False)
    height: int = field(init=False)
    styles: object = field(init=False, default_factory=getSampleStyleSheet)
    missing_files: list = field(default_factory=list)
    page_number: int = field(init=False, default=1)
    page_log: list = field(default_factory=list)

    # Margins (in points)
    margin_top: int = 60
    margin_bottom: int = 60
    margin_left: int = 30
    margin_right: int = 30

    # Content width will be set in __post_init__
    CONTENT_WIDTH: int = field(init=False)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Report, cls).__new__(cls)
        return cls._instance

    def __post_init__(self):
        self.width, self.height = self.page_size
        # Make content width fill the page between margins
        self.CONTENT_WIDTH = self.width - self.margin_left - self.margin_right
        if self.qc_dir and self.sub_ses:
            self.pdf_path = self.get_pdf_path()
            self.pdf_canvas = canvas.Canvas(self.pdf_path, pagesize=self.page_size)
            self.page_number = 1
            self.page_log = []
        else:
            self.pdf_path = None
            self.pdf_canvas = None

    @classmethod
    def destroy_instance(cls):
        if cls._instance:
            cls._instance = None

    def get_pdf_path(self):
        pdf = f"{self.sub_ses}_qc_report.pdf"
        base_dir = self.qc_dir if self.qc_dir and ".temp" not in self.qc_dir else os.getcwd()
        return os.path.join(base_dir, pdf)

    def new_page(self, reason=None, chapter=None, scan=None, content_type=None):
        self.pdf_canvas.showPage()
        self.page_number += 1
        entry = {
            "page_number": self.page_number,
            "reason": reason,
            "chapter": chapter,
            "scan": scan
        }
        self.page_log.append(entry)
        logger.info(f"New page: {entry}")
        # Only add header/footer for image or json_details pages
        if content_type in ("image", "json_details"):
            self.add_header(chapter, scan)
            self.add_footer(self.page_number)

    def add_header(self, chapter=None, scan=None):
        self.pdf_canvas.setFont("Helvetica", 10)
        header_text = f"CPAC QC Report"
        if chapter and scan:
            header_text += f" | {chapter}/{scan}"
        elif chapter:
            header_text += f" | {chapter}"
        self.pdf_canvas.drawString(self.margin_left, self.height - self.margin_top + 20, header_text)

    def add_footer(self, page_number):
        self.pdf_canvas.setFont("Helvetica", 10)
        self.pdf_canvas.drawRightString(self.width - self.margin_right, self.margin_bottom / 2, f"Page {page_number}")

    def add_front_page(self):
        logo_path = 'https://avatars.githubusercontent.com/u/2230402?s=200&v=4'
        logo_img = ImageReader(logo_path)
        logo_width = 150
        logo_height = 150

        self.pdf_canvas.setFont("Helvetica", 25)
        title = Paragraph(f"{self.sub_ses.replace('_', ' ')}", self.styles['Title'])
        title.wrapOn(self.pdf_canvas, self.width - 2 * self.margin_left, self.height)
        title.drawOn(self.pdf_canvas, self.margin_left, self.height - self.margin_top - 60)

        self.pdf_canvas.drawImage(
            logo_img,
            (self.width - logo_width) / 2,
            (self.height - logo_height) / 2,
            width=logo_width,
            height=logo_height
        )
        self.pdf_canvas.setFont("Helvetica", 15)
        self.pdf_canvas.drawCentredString(self.width / 2, self.height - self.margin_top - 120, "Quality Control Report")

        self.pdf_canvas.setFont("Helvetica", 12)
        self.pdf_canvas.drawCentredString(self.width / 2, self.margin_bottom + 40, f"Created on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.pdf_canvas.drawCentredString(self.width / 2, self.margin_bottom + 20, "CPAC Team")
        self.pdf_canvas.showPage()
        self.page_number = 1  # Reset so contents is page 1

    def add_contents_page(self):
        self.pdf_canvas.setFont("Helvetica", 20)
        self.pdf_canvas.drawCentredString(self.width / 2, self.height - self.margin_top, "Contents")
        self.pdf_canvas.setFont("Helvetica", 12)
        y_position = self.height - self.margin_top - 50
        chapters = sorted(set(self.df['datatype'].dropna()))

        for chapter in chapters:
            if y_position < self.margin_bottom + 60:
                self.new_page(reason="contents")
                y_position = self.height - self.margin_top
            y_position -= 20
            self.pdf_canvas.setFillColor(colors.blue)
            self.pdf_canvas.drawString(self.margin_left, y_position, f"{chapter}")
            text_width = self.pdf_canvas.stringWidth(chapter, "Helvetica", 12)
            self.pdf_canvas.linkRect("", f"chapter_{chapter}", (self.margin_left, y_position - 2, self.margin_left + text_width, y_position + 10), color=colors.blue)
            self.pdf_canvas.bookmarkPage(f"chapter_{chapter}")
            self.pdf_canvas.addOutlineEntry(f"{chapter}", f"chapter_{chapter}", level=0)
            y_position -= 10

            chapter_data = self.df[self.df['datatype'] == chapter]
            scans = sorted(set(chapter_data['scan'].dropna()))
            for scan in scans:
                if y_position < self.margin_bottom + 40:
                    self.new_page(reason="contents")
                    y_position = self.height - self.margin_top
                self.pdf_canvas.setFillColor(colors.green)
                self.pdf_canvas.drawString(self.margin_left + 20, y_position, f"{scan}")
                text_width = self.pdf_canvas.stringWidth(scan, "Helvetica", 12)
                if scan.strip() == '':
                    self.pdf_canvas.linkRect("", f"subsection_{chapter}", (self.margin_left + 20, y_position - 2, self.margin_left + 20 + text_width, y_position + 10), color=colors.green)
                    self.pdf_canvas.bookmarkPage(f"subsection_{chapter}")
                    self.pdf_canvas.addOutlineEntry(f"{chapter}", f"subsection_{chapter}", level=1)
                else:
                    self.pdf_canvas.linkRect("", f"subsection_{chapter}_{scan}", (self.margin_left + 20, y_position - 2, self.margin_left + 20 + text_width, y_position + 10), color=colors.green)
                    self.pdf_canvas.bookmarkPage(f"subsection_{chapter}_{scan}")
                    self.pdf_canvas.addOutlineEntry(f"{chapter} - {scan}", f"subsection_{chapter}_{scan}", level=1)
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
                    ordered_images = ordered_images.drop_duplicates(subset='file_name', keep='last')
                    extra_images = extra_images.drop_duplicates(subset='file_name', keep='last')
                    for _, image_data in ordered_images.iterrows():
                        if y_position < self.margin_bottom + 20:
                            self.new_page(reason="contents")
                            y_position = self.height - self.margin_top
                        self.pdf_canvas.setFillColor(colors.black)
                        self.pdf_canvas.drawString(self.margin_left + 40, y_position, f"{image_data['resource_name']}")
                        text_width = self.pdf_canvas.stringWidth(image_data['resource_name'], "Helvetica", 12)
                        self.pdf_canvas.linkRect("", f"image_{chapter}_{scan}_{image_data['resource_name']}", (self.margin_left + 40, y_position - 2, self.margin_left + 40 + text_width, y_position + 10), color=colors.blue)
                        self.pdf_canvas.bookmarkPage(f"image_{chapter}_{scan}_{image_data['resource_name']}")
                        self.pdf_canvas.addOutlineEntry(f"{image_data['resource_name']}", f"image_{chapter}_{scan}_{image_data['resource_name']}", level=2)
                        y_position -= 13
                    for _, image_data in extra_images.iterrows():
                        if y_position < self.margin_bottom + 20:
                            self.new_page(reason="contents")
                            y_position = self.height - self.margin_top
                        self.pdf_canvas.setFillColor(colors.black)
                        self.pdf_canvas.drawString(self.margin_left + 40, y_position, f"{image_data['resource_name']}")
                        text_width = self.pdf_canvas.stringWidth(image_data['resource_name'], "Helvetica", 12)
                        self.pdf_canvas.linkRect("", f"image_{chapter}_{scan}_{image_data['resource_name']}", (self.margin_left + 40, y_position - 2, self.margin_left + 40 + text_width, y_position + 10), color=colors.blue)
                        self.pdf_canvas.bookmarkPage(f"image_{chapter}_{scan}_{image_data['resource_name']}")
                        self.pdf_canvas.addOutlineEntry(f"{image_data['resource_name']}", f"image_{chapter}_{scan}_{image_data['resource_name']}", level=2)
                        y_position -= 13
                y_position -= 10

        # Add "Missing Files" to contents if there are any missing files
        if self.missing_files:
            if y_position < self.margin_bottom + 60:
                self.new_page(reason="contents")
                y_position = self.height - self.margin_top
            y_position -= 20
            self.pdf_canvas.setFillColor(colors.red)
            self.pdf_canvas.drawString(self.margin_left, y_position, "Missing Files")
            text_width = self.pdf_canvas.stringWidth("Missing Files", "Helvetica", 12)
            self.pdf_canvas.linkRect("", "missing_files", (self.margin_left, y_position - 2, self.margin_left + text_width, y_position + 10), color=colors.red)
            self.pdf_canvas.bookmarkPage("missing_files")
            self.pdf_canvas.addOutlineEntry("Missing Files", "missing_files", level=0)
            y_position -= 10

    def add_chapter_title_page(self, chapter):
        self.new_page(reason="chapter_title", chapter=chapter, content_type="title")
        self.pdf_canvas.setFont("Helvetica-Bold", 30)
        self.pdf_canvas.drawCentredString(self.width / 2, self.height / 2, chapter)
        self.pdf_canvas.bookmarkPage(f"chapter_{chapter}")

    def add_scan_title_page(self, chapter, scan):
        self.new_page(reason="scan_title", chapter=chapter, scan=scan, content_type="title")
        self.pdf_canvas.setFont("Helvetica-Bold", 25)
        if scan.strip() == '':
            self.pdf_canvas.drawCentredString(self.width / 2, self.height / 2, f"{chapter} - (No scan name)")
            self.pdf_canvas.bookmarkPage(f"subsection_{chapter}")
        else:
            self.pdf_canvas.drawCentredString(self.width / 2, self.height / 2, f"{chapter} - {scan}")
            self.pdf_canvas.bookmarkPage(f"subsection_{chapter}_{scan}")
        self.pdf_canvas.bookmarkPage(f"subsection_{chapter}_{scan}")
        # Always start a new page after scan title page for images
        self.new_page(reason="scan_images_start", chapter=chapter, scan=scan, content_type="image")
        self.add_header(chapter, scan)
        self.add_footer(self.page_number)

    def add_images(self):
        chapters = sorted(set(self.df['datatype'].dropna()))
        for chapter in chapters:
            self.add_chapter_title_page(chapter)
            chapter_data = self.df[self.df['datatype'] == chapter]
            scans = sorted(set(chapter_data['scan'].dropna()))
            for scan in scans:
                self.add_scan_title_page(chapter, scan)
                scan_data = chapter_data[chapter_data['scan'] == scan]
                if not scan_data.empty:
                    ordered_images = []
                    extra_images = []
                    if self.overlay_df is not None:
                        ordered_images = scan_data[scan_data['resource_name'].isin(self.overlay_df['output'])]
                        extra_images = scan_data[~scan_data['resource_name'].isin(self.overlay_df['output'])]
                    else:
                        ordered_images = scan_data
                    ordered_images = ordered_images.drop_duplicates(subset='file_name', keep='last')
                    extra_images = extra_images.drop_duplicates(subset='file_name', keep='last')

                    cursor_y = self.height - self.margin_top
                    for _, image_data in pd.concat([ordered_images, extra_images]).iterrows():
                        cursor_y = self.add_image_with_cursor(image_data, chapter, scan, cursor_y)

    def add_image_with_cursor(self, image_data, chapter, scan, cursor_y):
        image_path = os.path.join(self.qc_dir, image_data['relative_path'])
        if not os.path.exists(image_path):
            return cursor_y

        img = ImageReader(image_path)
        max_img_width = self.CONTENT_WIDTH
        max_img_height = self.height - self.margin_top - self.margin_bottom - 200
        img_width, img_height = img.getSize()
        aspect_ratio = img_width / img_height
        if aspect_ratio > 1:
            img_width = min(max_img_width, img_width)
            img_height = img_width / aspect_ratio
        else:
            img_height = min(max_img_height, img_height)
            img_width = img_height * aspect_ratio

        image_block_height = img_height + 40
        details_height = self.estimate_image_details_height(image_data)
        json_height = self.estimate_json_details_height(image_data)
        total_needed = image_block_height + details_height + json_height + 60

        if cursor_y - total_needed < self.margin_bottom:
            self.new_page(reason="image", chapter=chapter, scan=scan, content_type="image")
            self.add_footer(self.page_number)
            self.add_header(chapter, scan)
            cursor_y = self.height - self.margin_top

        self.pdf_canvas.setFont("Helvetica", 15)
        self.pdf_canvas.drawString(self.margin_left, cursor_y - 20, f"{image_data['resource_name']}")
        self.pdf_canvas.bookmarkPage(f"image_{chapter}_{scan}_{image_data['resource_name']}")
        cursor_y -= 40

        self.pdf_canvas.drawImage(img, self.margin_left, cursor_y - img_height, width=self.CONTENT_WIDTH, height=img_height)
        cursor_y -= img_height + 20

        details_drawn = self.add_image_details(image_data, cursor_y, 0)
        cursor_y -= details_drawn + 20

        json_drawn = self.add_json_details(image_data, cursor_y, chapter, scan)
        cursor_y -= json_drawn + 20

        return cursor_y

    def estimate_image_details_height(self, image_data):
        label = f"{image_data['file_name']}"
        wrapped_label = Paragraph(label, self.styles['Normal'])
        wrapped_label.wrapOn(self.pdf_canvas, self.CONTENT_WIDTH, self.height)
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
        table = Table(file_info_text, colWidths=[80, self.CONTENT_WIDTH - 80])
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
        return table.wrap(self.CONTENT_WIDTH, self.height)[1]

    def estimate_json_details_height(self, image_data):
        flat_json = image_data.get('json', None)
        if flat_json is None or flat_json == '' or flat_json == {}:
            return 0
        if isinstance(flat_json, str):
            try:
                flat_json = json.loads(flat_json)
            except Exception:
                return 0
        if not flat_json or flat_json == {}:
            return 0
        json_text = [["Json Field", "Value"]]
        for key, value in flat_json.items():
            if not key or (isinstance(value, float) and pd.isna(value)):
                continue
            para_key = Paragraph(str(key), self.styles['Normal'])
            para_value = Paragraph(str(value), self.styles['Normal'])
            json_text.append([para_key, para_value])
        col1_width = min(180, self.CONTENT_WIDTH * 0.3)
        col2_width = self.CONTENT_WIDTH - col1_width
        table = Table(json_text, colWidths=[col1_width, col2_width], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        return table.wrap(self.CONTENT_WIDTH, self.height)[1]

    def add_image_details(self, image_data, y_position, img_height):
        label = f"{image_data['file_name']}"
        self.styles['Normal'].textColor = colors.whitesmoke
        wrapped_label = Paragraph(label, self.styles['Normal'])
        wrapped_label.wrapOn(self.pdf_canvas, self.CONTENT_WIDTH, self.height)
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
        table = Table(file_info_text, colWidths=[80, self.CONTENT_WIDTH - 80])
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
        table.wrapOn(self.pdf_canvas, self.CONTENT_WIDTH, self.height)
        table_height = table.wrap(self.CONTENT_WIDTH, self.height)[1]
        table.drawOn(self.pdf_canvas, self.margin_left, y_position - table_height)
        return table_height

    def add_json_details(self, image_data, y_position, chapter=None, scan=None):
        flat_json = image_data.get('json', None)
        if flat_json is None or flat_json == '' or flat_json == {}:
            print(Fore.YELLOW + f"JSON data is empty for {image_data.get('file_name', '')}. Skipping..." + Style.RESET_ALL)
            return 0
        if isinstance(flat_json, str):
            try:
                flat_json = json.loads(flat_json)
            except Exception as e:
                print(Fore.YELLOW + f"Could not parse JSON for {image_data.get('file_name', '')}: {e}" + Style.RESET_ALL)
                return 0
        if not flat_json or flat_json == {}:
            print(Fore.YELLOW + f"JSON data is empty for {image_data.get('file_name', '')}. Skipping..." + Style.RESET_ALL)
            return 0
        json_text = [["Json Field", "Value"]]
        for key, value in flat_json.items():
            if not key or (isinstance(value, float) and pd.isna(value)):
                continue
            self.styles['Normal'].textColor = colors.black
            para_key = Paragraph(str(key), self.styles['Normal'])
            para_value = Paragraph(str(value), self.styles['Normal'])
            json_text.append([para_key, para_value])
        if len(json_text) == 1:
            print(Fore.YELLOW + f"JSON data is empty for {image_data.get('file_name', '')}. Skipping..." + Style.RESET_ALL)
            return 0

        col1_width = min(180, self.CONTENT_WIDTH * 0.3)
        col2_width = self.CONTENT_WIDTH - col1_width

        table = Table(json_text, colWidths=[col1_width, col2_width], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        table.wrapOn(self.pdf_canvas, self.CONTENT_WIDTH, self.height)
        table_height = table.wrap(self.CONTENT_WIDTH, self.height)[1]
        table.drawOn(self.pdf_canvas, self.margin_left, y_position - table_height)
        return table_height

    def add_missing_files_page(self):
        if not self.missing_files:
            print(Fore.YELLOW + "No missing files to report." + Style.RESET_ALL)
            return
        self.new_page(reason="missing_files", content_type="end")
        self.pdf_canvas.bookmarkPage("missing_files")
        self.pdf_canvas.setFont("Helvetica", 20)
        self.pdf_canvas.drawCentredString(self.width / 2, self.height - 120, "Missing Files")
        self.pdf_canvas.setFont("Helvetica", 12)
        y_position = self.height - 150
        for file in self.missing_files:
            print(Fore.YELLOW + f"Missing file: {file}" + Style.RESET_ALL)
            if y_position < 70:
                self.new_page(reason="missing_files", content_type="end")
                y_position = self.height - 50
            self.pdf_canvas.setFont("Helvetica", 12)
            self.pdf_canvas.drawString(70, y_position - 20, file)
            y_position -= 13
        # Always end with a new page for "End of Report"
        self.new_page(reason="end_of_report", content_type="end")
        self.pdf_canvas.setFont("Helvetica", 25)
        self.pdf_canvas.drawCentredString(self.width / 2, self.height / 2, "End of Report")

    def add_missing_files(self, missing_files):
        """Add missing files to the report's missing_files list."""
        if isinstance(missing_files, list):
            self.missing_files.extend(missing_files)
        else:
            self.missing_files.append(missing_files)

    def generate_report(self):
        print(Fore.YELLOW + "Generating PDF report..." + Style.RESET_ALL)
        self.add_front_page()
        self.add_contents_page()
        self.page_number = 1
        self.page_log = []
        self.add_images()
        self.add_missing_files_page()
        print(Fore.GREEN + "PDF report generated successfully." + Style.RESET_ALL)

    def save_report(self):
        if self.pdf_canvas:
            self.pdf_canvas.save()
            print(Fore.GREEN + f"PDF report saved at {self.pdf_path}" + Style.RESET_ALL)
        else:
            print(Fore.RED + "PDF canvas is not initialized." + Style.RESET_ALL)