from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import datetime
import os
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw
import io
import math


class InvoiceConfig:
    """Configuration class for invoice styling and layout"""

    # Color scheme
    PRIMARY_COLOR = colors.HexColor("#0B86C8")
    SECONDARY_COLOR = colors.HexColor("#E8F4F8")
    BORDER_COLOR = colors.HexColor("#B9D3E4")
    TEXT_COLOR = colors.HexColor("#333333")
    LIGHT_GRAY = colors.HexColor("#F8F9FA")

    # Company information
    COMPANY_NAME = "F&F MARKETING"
    COMPANY_ADDRESS = [
        "No. 32/C/3",
        "Elamaldeniya,",
        "Muruthaghamula,",
        "Geliyoya"
    ]

    # Logo configuration
    LOGO_SIZE = 25 * mm  # Diameter of the round logo
    LOGO_POSITION_X = 20 * mm  # Left margin
    LOGO_POSITION_Y = 260 * mm  # From bottom

    # Layout dimensions
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 20 * mm

    # Table configuration
    TABLE_COL_WIDTHS = [15 * mm, 95 * mm, 25 * mm, 20 * mm, 30 * mm]
    ROW_HEIGHT = 8 * mm
    HEADER_HEIGHT = 10 * mm

    # Multi-page configuration
    FIRST_PAGE_TABLE_START = 90 * mm  # Where table starts on first page
    CONTINUATION_PAGE_TABLE_START = 250 * mm  # Where table starts on continuation pages
    FOOTER_SPACE = 40 * mm  # Space reserved for totals and footer
    HEADER_SPACE_CONTINUATION = 30 * mm  # Space for header on continuation pages


class InvoiceItem:
    """Represents an invoice line item"""

    def __init__(self, description: str, unit_price: float, quantity: float, tax_rate: float = 0):
        self.description = description
        self.unit_price = Decimal(str(unit_price))
        self.quantity = Decimal(str(quantity))
        self.tax_rate = Decimal(str(tax_rate))
        self.line_total = self.unit_price * self.quantity


class Customer:
    """Represents customer information"""

    def __init__(self, name: str = "", company: str = "", address: str = "",
               city: str = "", phone: str = "", email: str = ""):
        self.name = name
        self.company = company
        self.address = address
        self.city = city
        self.phone = phone
        self.email = email


class ProfessionalInvoiceGenerator:
    """Professional invoice PDF generator with multi-page support"""

    def __init__(self, config: InvoiceConfig = None):
        self.config = config or InvoiceConfig()
        self.canvas = None
        self.current_page = 1

    def format_currency(self, amount) -> str:
        """Format currency with proper decimal places"""
        decimal_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"${decimal_amount:,.2f}"

    def _create_round_logo_placeholder(self, size: float) -> ImageReader:
        """Create a round logo placeholder with company initials"""
        # Create a square image
        img_size = int(size * 2)  # Higher resolution for better quality
        img = Image.new('RGBA', (img_size, img_size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # Draw circle background
        primary_color_rgb = (11, 134, 200)  # RGB equivalent of #0B86C8
        draw.ellipse([0, 0, img_size - 1, img_size - 1], fill=primary_color_rgb + (255,))

        # Add company initials or icon
        try:
            # Try to use a font for the initials
            from PIL import ImageFont
            font_size = img_size // 3
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        except ImportError:
            font = None

        # Extract initials from company name
        company_initials = ''.join([word[0] for word in self.config.COMPANY_NAME.split() if word])[:3]

        # Calculate text position for centering
        if font:
            bbox = draw.textbbox((0, 0), company_initials, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(company_initials) * (img_size // 6)
            text_height = img_size // 4

        x = (img_size - text_width) // 2
        y = (img_size - text_height) // 2

        # Draw the initials
        draw.text((x, y), company_initials, fill='white', font=font)

        # Convert PIL image to ImageReader
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        return ImageReader(img_buffer)

    def _draw_round_logo(self, logo_path: str = None):
        """Draw a round company logo"""
        c = self.canvas
        logo_x = self.config.LOGO_POSITION_X
        logo_y = self.config.LOGO_POSITION_Y
        logo_size = self.config.LOGO_SIZE

        if logo_path and os.path.exists(logo_path):
            # Use provided logo image
            try:
                # Load and process the image to make it round
                original_img = Image.open(logo_path)
                # Convert to RGBA if not already
                if original_img.mode != 'RGBA':
                    original_img = original_img.convert('RGBA')

                # Resize to square
                img_size = int(logo_size * 2)  # Higher resolution
                original_img = original_img.resize((img_size, img_size), Image.Resampling.LANCZOS)

                # Create circular mask
                mask = Image.new('L', (img_size, img_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, img_size - 1, img_size - 1], fill=255)

                # Apply mask to make image circular
                original_img.putalpha(mask)

                # Convert to ImageReader
                img_buffer = io.BytesIO()
                original_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                logo_image = ImageReader(img_buffer)

            except Exception as e:
                print(f"Error loading logo image: {e}")
                logo_image = self._create_round_logo_placeholder(logo_size)
        else:
            # Use placeholder logo
            logo_image = self._create_round_logo_placeholder(logo_size)

        # Draw the logo
        c.drawImage(logo_image, logo_x, logo_y,
                    width=logo_size, height=logo_size,
                    mask='auto')

    def _start_new_page(self):
        """Start a new page and draw continuation header"""
        self.canvas.showPage()
        self.current_page += 1
        self._draw_continuation_header()

    def _draw_continuation_header(self):
        """Draw header for continuation pages"""
        c = self.canvas

        # Draw simplified header
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(self.config.MARGIN,
                     self.config.PAGE_HEIGHT - 25 * mm,
                     f"{self.config.COMPANY_NAME} - Invoice Continued")

        # Page number
        c.setFont("Helvetica", 10)
        c.drawRightString(self.config.PAGE_WIDTH - self.config.MARGIN,
                          self.config.PAGE_HEIGHT - 25 * mm,
                          f"Page {self.current_page}")

        # Decorative line
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.setLineWidth(2)
        c.line(self.config.MARGIN,
               self.config.PAGE_HEIGHT - 30 * mm,
               self.config.PAGE_WIDTH - self.config.MARGIN,
               self.config.PAGE_HEIGHT - 30 * mm)

    def _calculate_items_per_page(self, is_first_page: bool = True) -> int:
        """Calculate how many items can fit on a page"""
        if is_first_page:
            available_height = self.config.FIRST_PAGE_TABLE_START - self.config.FOOTER_SPACE
        else:
            available_height = self.config.CONTINUATION_PAGE_TABLE_START - self.config.FOOTER_SPACE

        # Account for header row
        items_height = available_height - self.config.HEADER_HEIGHT
        items_per_page = int(items_height // self.config.ROW_HEIGHT)

        return max(1, items_per_page)  # At least 1 item per page

    def _draw_table_header(self):
        """Draw table header row"""
        headers = ["#", "Description", "Unit Price", "Qty", "Total"]
        table_data = [headers]

        table = Table(table_data,
                      colWidths=self.config.TABLE_COL_WIDTHS,
                      rowHeights=self.config.HEADER_HEIGHT)

        # Header styling
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.config.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.config.BORDER_COLOR),
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.config.PRIMARY_COLOR),
            ('LEFTPADDING', (0, 0), (-1, -1), 3 * mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
        ])

        table.setStyle(table_style)
        return table

    def _draw_items_page(self, items_subset: list, start_index: int, y_position: float,
                         is_first_page: bool = True):
        """Draw a portion of items table on current page"""
        if not items_subset:
            return y_position

        # Draw table header
        header_table = self._draw_table_header()
        header_table.wrapOn(self.canvas, sum(self.config.TABLE_COL_WIDTHS), self.config.HEADER_HEIGHT)
        header_table.drawOn(self.canvas, self.config.MARGIN, y_position)

        # Prepare data rows for this page
        table_data = []
        for i, item in enumerate(items_subset):
            item_number = start_index + i + 1
            qty_str = f"{item.quantity:.0f}" if item.quantity % 1 == 0 else f"{item.quantity:.2f}"
            table_data.append([
                str(item_number),
                item.description,
                self.format_currency(item.unit_price),
                qty_str,
                self.format_currency(item.line_total)
            ])

        # Create data table
        if table_data:
            data_table = Table(table_data,
                               colWidths=self.config.TABLE_COL_WIDTHS,
                               rowHeights=self.config.ROW_HEIGHT)

            # Data rows styling
            data_style = TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.config.SECONDARY_COLOR]),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Item numbers
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Descriptions
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),  # Numbers
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.config.BORDER_COLOR),
                ('LEFTPADDING', (0, 0), (-1, -1), 3 * mm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3 * mm),
                ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
            ])

            data_table.setStyle(data_style)

            # Draw data table
            data_y = y_position - self.config.HEADER_HEIGHT
            data_table.wrapOn(self.canvas, sum(self.config.TABLE_COL_WIDTHS),
                              len(table_data) * self.config.ROW_HEIGHT)
            data_table.drawOn(self.canvas, self.config.MARGIN, data_y)

            return data_y - (len(table_data) * self.config.ROW_HEIGHT)

        return y_position - self.config.HEADER_HEIGHT

    def _draw_items_table_multipage(self, items: list):
        """Draw items table with automatic page breaks"""
        if not items:
            # Draw empty table on first page
            self._draw_items_page([], 0, self.config.FIRST_PAGE_TABLE_START, True)
            return

        # Calculate pagination
        first_page_capacity = self._calculate_items_per_page(True)
        continuation_page_capacity = self._calculate_items_per_page(False)

        items_processed = 0
        current_y = self.config.FIRST_PAGE_TABLE_START

        # Process first page
        if items_processed < len(items):
            items_on_first_page = min(first_page_capacity, len(items))
            first_page_items = items[items_processed:items_processed + items_on_first_page]

            current_y = self._draw_items_page(first_page_items, items_processed,
                                              current_y, is_first_page=True)
            items_processed += items_on_first_page

        # Process continuation pages
        while items_processed < len(items):
            self._start_new_page()

            remaining_items = len(items) - items_processed
            items_on_this_page = min(continuation_page_capacity, remaining_items)

            page_items = items[items_processed:items_processed + items_on_this_page]

            current_y = self._draw_items_page(page_items, items_processed,
                                              self.config.CONTINUATION_PAGE_TABLE_START,
                                              is_first_page=False)
            items_processed += items_on_this_page

        return current_y

    def _ensure_space_for_totals(self, current_y: float) -> float:
        """Ensure there's enough space for totals section, create new page if needed"""
        space_needed = self.config.FOOTER_SPACE + 30 * mm  # Extra space for safety

        if current_y < space_needed:
            self._start_new_page()
            return self.config.CONTINUATION_PAGE_TABLE_START - 50 * mm  # Safe position for totals

        return current_y - 20 * mm  # Some spacing above totals

    def create_invoice(self,
                       invoice_number: str,
                       invoice_date: str = None,
                       due_date: str = None,
                       customer: Customer = None,
                       items: list = None,
                       tax_rate: float = 0,
                       notes: str = "",
                       logo_path: str = None,
                       output_path: str = "invoice.pdf"):
        """
        Create a professional multi-page invoice PDF with round logo

        Args:
            invoice_number: Invoice number (e.g., "INV-001")
            invoice_date: Invoice date (defaults to today)
            due_date: Payment due date
            customer: Customer object with billing information
            items: List of InvoiceItem objects
            tax_rate: Overall tax rate percentage
            notes: Additional notes/terms
            logo_path: Path to company logo image (optional)
            output_path: Path to save the PDF
        """

        # Set defaults
        if not invoice_date:
            invoice_date = datetime.now().strftime("%Y-%m-%d")
        if not customer:
            customer = Customer()
        if not items:
            items = []

        # Reset page counter
        self.current_page = 1

        # Create PDF canvas
        self.canvas = canvas.Canvas(output_path, pagesize=A4)

        # Draw first page header sections
        self._draw_round_logo(logo_path)
        self._draw_header()
        self._draw_company_info()
        self._draw_invoice_details(invoice_number, invoice_date, due_date)
        self._draw_customer_info(customer)

        # Draw items table with multi-page support
        final_y = self._draw_items_table_multipage(items)

        # Calculate totals
        subtotal = sum(item.line_total for item in items)
        tax_amount = subtotal * Decimal(str(tax_rate)) / 100
        total = subtotal + tax_amount

        # Ensure space for totals and draw them
        totals_y = self._ensure_space_for_totals(final_y)
        self._draw_totals_section(subtotal, tax_rate, tax_amount, total, totals_y)

        if notes:
            self._draw_notes(notes)

        self._draw_footer()

        # Save the PDF
        self.canvas.save()
        print(f"Multi-page invoice created with {self.current_page} page(s)")
        return output_path

    def _draw_header(self):
        """Draw the main header with company branding (adjusted for logo)"""
        c = self.canvas

        # Adjust company name position to accommodate logo
        company_name_x = self.config.LOGO_POSITION_X + self.config.LOGO_SIZE + 10 * mm

        # Company name - large and prominent
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(company_name_x,
                     self.config.PAGE_HEIGHT - 40 * mm,
                     self.config.COMPANY_NAME)

        # Page number on first page
        c.setFont("Helvetica", 10)
        c.drawRightString(self.config.PAGE_WIDTH - self.config.MARGIN,
                          self.config.PAGE_HEIGHT - 15 * mm,
                          f"Page {self.current_page}")

        # Decorative line under company name
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.setLineWidth(3)
        c.line(company_name_x,
               self.config.PAGE_HEIGHT - 45 * mm,
               self.config.PAGE_WIDTH - self.config.MARGIN,
               self.config.PAGE_HEIGHT - 45 * mm)

    def _draw_company_info(self):
        """Draw company contact information (adjusted for logo)"""
        c = self.canvas
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 11)

        # Position company info next to logo
        company_info_x = self.config.LOGO_POSITION_X + self.config.LOGO_SIZE + 10 * mm
        y_pos = self.config.PAGE_HEIGHT - 55 * mm

        for line in self.config.COMPANY_ADDRESS:
            c.drawString(company_info_x, y_pos, line)
            y_pos -= 5 * mm

    def _draw_invoice_details(self, invoice_number: str, invoice_date: str, due_date: str = None):
        """Draw invoice metadata in styled boxes"""
        c = self.canvas

        # Position on the right side
        box_width = 60 * mm
        box_height = 12 * mm
        right_margin = self.config.PAGE_WIDTH - self.config.MARGIN

        # Invoice number box
        inv_box_y = self.config.PAGE_HEIGHT - 70 * mm
        self._draw_info_box(right_margin - box_width, inv_box_y, box_width, box_height,
                            "INVOICE #", invoice_number)

        # Date box
        date_box_y = inv_box_y - box_height - 3 * mm
        self._draw_info_box(right_margin - box_width, date_box_y, box_width, box_height,
                            "DATE", invoice_date)

        # Due date box (if provided)
        if due_date:
            due_box_y = date_box_y - box_height - 3 * mm
            self._draw_info_box(right_margin - box_width, due_box_y, box_width, box_height,
                                "DUE DATE", due_date)

    def _draw_info_box(self, x: float, y: float, width: float, height: float,
                       label: str, value: str):
        """Draw a styled information box"""
        c = self.canvas

        # Box background
        c.setFillColor(self.config.LIGHT_GRAY)
        c.setStrokeColor(self.config.BORDER_COLOR)
        c.setLineWidth(1)
        c.rect(x, y, width, height, fill=1, stroke=1)

        # Vertical divider
        divider_x = x + width * 0.35
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.line(divider_x, y, divider_x, y + height)

        # Label
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 2 * mm, y + height / 2 - 1 * mm, label)

        # Value
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 10)
        c.drawRightString(x + width - 2 * mm, y + height / 2 - 1 * mm, value)

    def _draw_customer_info(self, customer: Customer):
        """Draw customer billing information with enhanced formatting"""
        c = self.canvas

        # Bill To header
        bill_to_y = self.config.PAGE_HEIGHT - 120 * mm
        header_width = 40 * mm
        header_height = 8 * mm

        c.setFillColor(self.config.PRIMARY_COLOR)
        c.rect(self.config.MARGIN, bill_to_y, header_width, header_height, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.config.MARGIN + 3 * mm, bill_to_y + 2.5 * mm, "BILL TO")

        # Customer details with enhanced formatting
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 11)

        customer_info = []

        # Customer name (bold if provided)
        if customer.name:
            customer_info.append(("name", customer.name))
        if customer.company:
            customer_info.append(("company", customer.company))
        if customer.address:
            customer_info.append(("address", customer.address))
        if customer.city:
            customer_info.append(("city", customer.city))
        if customer.phone:
            customer_info.append(("phone", f"Phone: {customer.phone}"))
        if customer.email:
            customer_info.append(("email", f"Email: {customer.email}"))

        # Default placeholder if no customer data
        if not customer_info:
            customer_info = [
                ("name", "[Customer Name]"),
                ("company", "[Company Name]"),
                ("address", "[Street Address]"),
                ("city", "[City, State ZIP]"),
                ("phone", "Phone: [Phone Number]"),
                ("email", "Email: [Email Address]")
            ]

        y_pos = bill_to_y - 8 * mm
        for info_type, info_text in customer_info:
            if info_type == "name":
                # Make customer name bold
                c.setFont("Helvetica-Bold", 12)
                c.drawString(self.config.MARGIN, y_pos, info_text)
                c.setFont("Helvetica", 11)  # Reset to normal font
            else:
                c.drawString(self.config.MARGIN, y_pos, info_text)
            y_pos -= 6 * mm

    def _draw_totals_section(self, subtotal: Decimal, tax_rate: float,
                             tax_amount: Decimal, total: Decimal, y_start: float = None):
        """Draw the totals section with professional styling"""
        c = self.canvas

        # Use provided y position or default
        if y_start is None:
            y_start = 70 * mm

        # Position totals on the right
        totals_x = self.config.PAGE_WIDTH - self.config.MARGIN - 80 * mm
        amount_x = self.config.PAGE_WIDTH - self.config.MARGIN - 5 * mm

        c.setFont("Helvetica", 11)
        c.setFillColor(self.config.TEXT_COLOR)

        # Subtotal
        c.drawString(totals_x, y_start, "Subtotal:")
        c.drawRightString(amount_x, y_start, self.format_currency(subtotal))

        # Tax
        if tax_rate > 0:
            tax_y = y_start - 8 * mm
            c.drawString(totals_x, tax_y, f"Tax ({tax_rate:.2f}%):")
            c.drawRightString(amount_x, tax_y, self.format_currency(tax_amount))
            total_y = tax_y - 12 * mm
        else:
            total_y = y_start - 12 * mm

        # Total line
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.setLineWidth(2)
        c.line(totals_x, total_y + 4 * mm, amount_x, total_y + 4 * mm)

        # Total amount
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.drawString(totals_x, total_y, "TOTAL:")
        c.drawRightString(amount_x, total_y, self.format_currency(total))

        return total_y

    def _draw_notes(self, notes: str):
        """Draw additional notes or terms"""
        c = self.canvas

        # Notes header
        notes_y = 35 * mm
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.config.MARGIN, notes_y, "Notes/Terms:")

        # Notes content
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 9)

        # Handle multi-line notes
        lines = notes.split('\n')
        y_pos = notes_y - 6 * mm
        for line in lines:
            if y_pos > 15 * mm:  # Don't go too close to page bottom
                c.drawString(self.config.MARGIN, y_pos, line)
                y_pos -= 4 * mm

    def _draw_footer(self):
        """Draw footer message"""
        c = self.canvas

        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica-Bold", 12)
        footer_text = "Thank You For Your Business!"
        text_width = c.stringWidth(footer_text, "Helvetica-Bold", 12)
        x_center = (self.config.PAGE_WIDTH - text_width) / 2
        c.drawString(x_center, 15 * mm, footer_text)


# Usage example and convenience function
def create_sample_invoice():
    """Create a sample invoice for demonstration"""

    # Create invoice generator
    generator = ProfessionalInvoiceGenerator()

    # Sample customer with complete information
    customer = Customer(
        name="John Doe",
        company="ABC Corporation",
        address="123 Business Street, Suite 100",
        city="Cityville, ST 12345",
        phone="(555) 123-4567",
        email="john.doe@abc-corp.com"
    )

    # Sample items (many items to test multi-page functionality)
    items = [
        InvoiceItem("Tool box", 150.00, 3),
        InvoiceItem("Screws (assorted)", 10.00, 30),
        InvoiceItem("Carbon sheet", 200.00, 1),
        InvoiceItem("Professional consultation", 75.00, 2),
        InvoiceItem("Installation service", 125.00, 4),
        InvoiceItem("Premium warranty", 50.00, 1),
        InvoiceItem("Training materials", 35.00, 5),
        InvoiceItem("Technical support", 80.00, 3),
        InvoiceItem("Additional hardware", 95.00, 2),
        InvoiceItem("Software licensing", 250.00, 1),
        InvoiceItem("Maintenance contract", 150.00, 6),
        InvoiceItem("Shipping and handling", 25.00, 1),
        InvoiceItem("Rush delivery", 75.00, 1),
        InvoiceItem("Extended support", 100.00, 2),
        InvoiceItem("Documentation", 40.00, 3),
        InvoiceItem("Quality assurance", 60.00, 4),
        InvoiceItem("Project management", 120.00, 5),
        InvoiceItem("Final inspection", 85.00, 1),
        InvoiceItem("Client training", 90.00, 2),
        InvoiceItem("Performance optimization", 110.00, 1),
    ]

    # Create invoice with logo (logo_path is optional)
    return generator.create_invoice(
        invoice_number="INV-234567",
        invoice_date="2024/03/15",
        due_date="2024/04/15",
        customer=customer,
        items=items,
        tax_rate=6.25,
        notes="Payment due within 30 days.\nLate payments subject to 1.5% monthly service charge.\nAll work performed according to industry standards.",
        logo_path=None,  # Set to your logo file path if you have one
        output_path="multi_page_invoice_with_logo.pdf"
    )


def create_large_invoice_test():
    """Create a test invoice with many items to demonstrate multi-page functionality"""

    generator = ProfessionalInvoiceGenerator()

    customer = Customer(
        name="Sarah Johnson",
        company="Tech Solutions Inc.",
        address="456 Innovation Drive, Building B",
        city="San Francisco, CA 94105",
        phone="(415) 555-0123",
        email="sarah.johnson@techsolutions.com"
    )

    # Create many items to force multiple pages
    items = []
    for i in range(1, 51):  # 50 items to definitely trigger multi-page
        items.append(InvoiceItem(f"Service Item #{i:02d}", 25.00 + (i * 2), 1))

    return generator.create_invoice(
        invoice_number="INV-999999",
        invoice_date="2024/03/20",
        due_date="2024/04/20",
        customer=customer,
        items=items,
        tax_rate=8.25,
        notes="This is a test invoice with many items to demonstrate multi-page functionality.\nEach page maintains professional formatting and proper pagination.",
        logo_path=None,
        output_path="large_multi_page_invoice.pdf"
    )


# For database integration (matching your original function signature)
def export_invoice_pdf_png_jpg(session, invoice_id: int, tax_percent=0, output_dir: str = "invoices",
                                  logo_path: str = None):
    """
    Generate multi-page invoice from database (compatible with your existing code)

    Args:
        session: SQLAlchemy session
        invoice_id: Invoice ID from database
        tax_percent: Tax percentage
        output_dir: Output directory
        logo_path: Path to company logo image (optional)
    """
    import DB  # Your database models

    os.makedirs(output_dir, exist_ok=True)

    # Load data from database
    invoice = session.get(DB.Invoice, invoice_id)
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    customer_data = session.get(DB.Customer, invoice.customer_id) if invoice.customer_id else None

    # Convert database customer to our Customer object with complete info
    customer = Customer()
    if customer_data:
        customer.name = getattr(customer_data, 'name', '')
        customer.company = getattr(customer_data, 'company', '')
        customer.address = getattr(customer_data, 'street_address', '')
        customer.city = getattr(customer_data, 'city', '')
        customer.phone = getattr(customer_data, 'mobile', '') or getattr(customer_data, 'phone', '')
        customer.email = getattr(customer_data, 'email', '')

    # Load invoice items from database
    query = (session.query(DB.InvoiceHasStock, DB.Stock, DB.Product)
             .join(DB.Stock, DB.InvoiceHasStock.stock_id == DB.Stock.id)
             .join(DB.Product, DB.Stock.product_id == DB.Product.id)
             .filter(DB.InvoiceHasStock.invoice_id == invoice_id)
             .order_by(DB.InvoiceHasStock.id.asc()))

    item_rows = query.all()

    # Convert database items to InvoiceItem objects
    items = []
    for invoice_stock, stock, product in item_rows:
        item = InvoiceItem(
            description=product.title or "Item",
            unit_price=float(invoice_stock.unit_price),
            quantity=float(invoice_stock.quantity)
        )
        items.append(item)

    # Generate multi-page invoice
    generator = ProfessionalInvoiceGenerator()

    output_path = os.path.join(output_dir, f"invoice_{invoice_id}.pdf")
    invoice_date = invoice.created_on.strftime("%Y-%m-%d")

    return generator.create_invoice(
        invoice_number=f"INV-{invoice_id}",
        invoice_date=invoice_date,
        customer=customer,
        items=items,
        tax_rate=tax_percent,
        logo_path=logo_path,
        output_path=output_path
    )


# if _name_ == "_main_":
#     # Create sample invoice
#     print("Creating sample multi-page invoice...")
#     pdf_path = create_sample_invoice()
#     print(f"Sample invoice created: {pdf_path}")
#
#     # Create large test invoice
#     print("\nCreating large test invoice with 50 items...")
#     large_pdf_path = create_large_invoice_test()
#     print(f"Large test invoice created: {large_pdf_path}")
#
#     print("\n✅ Features included:")
#     print("• Round company logo (placeholder with F&F initials)")
#     print("• Customer name, phone, and address properly displayed")
#     print("• Automatic page breaks when items exceed page limit")
#     print("• Professional multi-page formatting")
#     print("• Page numbering on each page")
#     print("• Proper table headers on continuation pages")