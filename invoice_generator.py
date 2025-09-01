# invoice_generator.py
# This script generates a professional, multi-page PDF invoice using ReportLab.
# It is designed to be highly customizable and automatically handles pagination
# for invoices with a large number of line items.

from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
import DB
from PIL import Image, ImageDraw
import io
import os
from datetime import datetime

class InvoiceConfig:
    """
    Configuration class for invoice styling and layout.
    
    This class centralizes all design choices, making it easy to
    customize the look and feel of the generated invoices without
    changing the core generation logic.
    """

    # Color scheme for a professional and branded look
    PRIMARY_COLOR = colors.HexColor("#0B86C8")
    SECONDARY_COLOR = colors.HexColor("#E8F4F8")
    BORDER_COLOR = colors.HexColor("#B9D3E4")
    TEXT_COLOR = colors.HexColor("#333333")
    LIGHT_GRAY = colors.HexColor("#F8F9FA")
    
    # Layout dimensions and margins
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 0.5 * inch # Set all margins to 0.5 inches

    # Proportional layout based on user request
    HEADER_PROPORTION = 0.1
    CUSTOMER_PROPORTION = 0.3
    TABLE_PROPORTION = 0.5
    SUMMARY_PROPORTION = 0.1

    # Y coordinates based on proportional layout
    # All Y coordinates are measured from the bottom of the page
    SUMMARY_START_Y = PAGE_HEIGHT * SUMMARY_PROPORTION
    TABLE_START_Y = PAGE_HEIGHT * (SUMMARY_PROPORTION + TABLE_PROPORTION) - MARGIN
    CUSTOMER_END_Y = PAGE_HEIGHT * (SUMMARY_PROPORTION + TABLE_PROPORTION)
    HEADER_START_Y = PAGE_HEIGHT - (PAGE_HEIGHT * HEADER_PROPORTION)

    # Table configuration
    TABLE_COL_WIDTHS = [15 * mm, 95 * mm, 25 * mm, 20 * mm, 30 * mm]
    ROW_HEIGHT = 8 * mm
    HEADER_HEIGHT = 10 * mm
    
    # Position of key sections on continuation pages
    CONTINUATION_PAGE_TABLE_START_Y = PAGE_HEIGHT - (PAGE_HEIGHT * HEADER_PROPORTION) - MARGIN
    
    # Logo configuration
    LOGO_SIZE = 25 * mm
    LOGO_POSITION_X = MARGIN
    LOGO_POSITION_Y = PAGE_HEIGHT - (PAGE_HEIGHT * HEADER_PROPORTION) - 5 * mm

    # Company information
    COMPANY_NAME = "F&F MARKETING"
    # From address is now a single line string as per request
    COMPANY_ADDRESS = "No. 32/C/3, Elamaldeniya, Muruthaghamula, Geliyoya"


class InvoiceItem:
    """Represents a single line item on the invoice."""
    
    def __init__(self, description: str, unit_price: float, quantity: float):
        """
        Initializes an invoice item.

        Args:
            description (str): A brief description of the item or service.
            unit_price (float): The price per unit.
            quantity (float): The number of units.
        """
        self.description = description
        self.unit_price = Decimal(str(unit_price))
        self.quantity = Decimal(str(quantity))
        self.line_total = self.unit_price * self.quantity

class Customer:
    """
    Represents customer information for the invoice.
    
    This class stores the customer's details for easy use in the PDF.
    """
    
    def __init__(self, name: str = "", company: str = "", address: str = "",
               city: str = "", phone: str = "", email: str = ""):
        """
        Initializes the Customer object.
        
        Args:
            name (str): The customer's full name.
            company (str): The company name (optional).
            address (str): The street address.
            city (str): The city and state/zip code.
            phone (str): The phone number.
            email (str): The email address.
        """ 
        self.name = name
        self.company = company
        self.address = address
        self.city = city
        self.phone = phone
        self.email = email


class ProfessionalInvoiceGenerator:
    """
    Generates a professional, multi-page invoice PDF.
    
    This class orchestrates the drawing of all invoice elements,
    including headers, customer details, a paginated table of items,
    and a totals section.
    """

    def __init__(self, config: InvoiceConfig = None):
        """
        Initializes the generator with an optional configuration.
        
        Args:
            config (InvoiceConfig): The configuration object. Defaults to a new instance.
        """
        self.config = config or InvoiceConfig()
        self.canvas = None
        self.current_page = 1

    def format_currency(self, amount) -> str:
        """
        Formats a numeric amount as a currency string.
        
        Args:
            amount (Decimal): The amount to format.
        
        Returns:
            str: The formatted currency string (e.g., "LKR 1,234.56").
        """
        decimal_amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"LKR {decimal_amount:,.2f}"

    def _create_round_logo_placeholder(self) -> ImageReader:
        """
        Creates a round logo placeholder with the company's initials.
        
        Returns:
            ImageReader: A ReportLab-compatible image reader object.
        """
        img_size = int(self.config.LOGO_SIZE * 2)
        img = Image.new('RGBA', (img_size, img_size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a primary-colored circle
        primary_color_rgb = (11, 134, 200) # RGB equivalent of #0B86C8
        draw.ellipse([0, 0, img_size - 1, img_size - 1], fill=primary_color_rgb + (255,))
        
        # Add company initials
        initials = ''.join([word[0] for word in self.config.COMPANY_NAME.split() if word])[:3]
        
        try:
            from PIL import ImageFont
            font_size = img_size // 3
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
        except ImportError:
            font = ImageFont.load_default()

        # Calculate text position for centering
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_size - text_width) // 2
        y = (img_size - text_height) // 2
        
        draw.text((x, y), initials, fill='white', font=font)
        
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return ImageReader(img_buffer)

    def _draw_first_page_header(self):
        """Draws the main header for the first page of the invoice."""
        c = self.canvas
        
        # Draw the round logo
        logo = self._create_round_logo_placeholder()
        c.drawImage(logo, self.config.LOGO_POSITION_X, self.config.LOGO_POSITION_Y,
                    width=self.config.LOGO_SIZE, height=self.config.LOGO_SIZE, mask='auto')

        # Company name next to the logo
        company_name_x = self.config.LOGO_POSITION_X + self.config.LOGO_SIZE + 10 * mm
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 32)
        c.drawString(company_name_x, self.config.LOGO_POSITION_Y + 10 * mm, self.config.COMPANY_NAME)

        # Company address below the name
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 13)
        c.drawString(company_name_x, self.config.LOGO_POSITION_Y + 3 * mm, self.config.COMPANY_ADDRESS)

        # Decorative line under the company name and address
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.setLineWidth(3)
        c.line(company_name_x, self.config.LOGO_POSITION_Y - 2 * mm,
               self.config.PAGE_WIDTH - self.config.MARGIN, self.config.LOGO_POSITION_Y - 2 * mm)

        # Page number on the first page
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 10)
        c.drawRightString(self.config.PAGE_WIDTH - self.config.MARGIN,
                          self.config.PAGE_HEIGHT - self.config.MARGIN,
                          f"Page {self.current_page}")

    def _draw_continuation_header(self):
        """Draws a simplified header for continuation pages."""
        c = self.canvas
        
        # Simplified header text
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(self.config.MARGIN, self.config.PAGE_HEIGHT - self.config.MARGIN - 10 * mm,
                     f"{self.config.COMPANY_NAME} - Invoice Continued")
        
        # Page number
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 10)
        c.drawRightString(self.config.PAGE_WIDTH - self.config.MARGIN,
                          self.config.PAGE_HEIGHT - self.config.MARGIN,
                          f"Page {self.current_page}")

        # Decorative line
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.setLineWidth(2)
        c.line(self.config.MARGIN, self.config.PAGE_HEIGHT - self.config.MARGIN - 15 * mm,
               self.config.PAGE_WIDTH - self.config.MARGIN, self.config.PAGE_HEIGHT - self.config.MARGIN - 15 * mm)

    def _draw_invoice_details(self, invoice_number: str, invoice_date: str, due_date: str = None):
        """Draws key invoice metadata in styled boxes."""
        c = self.canvas
        
        box_width = 60 * mm
        box_height = 12 * mm
        right_margin_x = self.config.PAGE_WIDTH - self.config.MARGIN
        
        # Draw Invoice Number box
        inv_box_y = self.config.HEADER_START_Y - 40 * mm
        self._draw_info_box(right_margin_x - box_width, inv_box_y, box_width, box_height,
                            "INVOICE #", invoice_number)
        
        # Draw Date box
        date_box_y = inv_box_y - box_height - 3 * mm
        self._draw_info_box(right_margin_x - box_width, date_box_y, box_width, box_height,
                            "DATE", invoice_date)
        
        # Draw Due Date box if provided
        if due_date:
            due_box_y = date_box_y - box_height - 3 * mm
            self._draw_info_box(right_margin_x - box_width, due_box_y, box_width, box_height,
                                "DUE DATE", due_date)

    def _draw_info_box(self, x: float, y: float, width: float, height: float,
                       label: str, value: str):
        """Helper to draw a single styled information box."""
        c = self.canvas
        
        # Box background
        c.setFillColor(self.config.LIGHT_GRAY)
        c.setStrokeColor(self.config.BORDER_COLOR)
        c.setLineWidth(1)
        c.rect(x, y, width, height, fill=1, stroke=1)
        
        # Vertical divider line
        divider_x = x + width * 0.35
        c.setStrokeColor(self.config.PRIMARY_COLOR)
        c.line(divider_x, y, divider_x, y + height)
        
        # Label text
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 2 * mm, y + height / 2 - 1 * mm, label)
        
        # Value text
        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 10)
        c.drawRightString(x + width - 2 * mm, y + height / 2 - 1 * mm, value)

    def _draw_customer_info(self, customer: Customer):
        """Draws the customer billing information with a 'Bill To' header."""
        c = self.canvas
        
        # 'Bill To' header box
        bill_to_y = self.config.HEADER_START_Y - 40 * mm
        header_width = 40 * mm
        header_height = 8 * mm
        
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.rect(self.config.MARGIN, bill_to_y, header_width, header_height, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.config.MARGIN + 3 * mm, bill_to_y + 2.5 * mm, "BILL TO")
        
        # Customer details list
        c.setFillColor(self.config.TEXT_COLOR)
        y_pos = bill_to_y - 8 * mm
        
        customer_details = [customer.name, customer.company, customer.address,
                            customer.city, f"Phone: {customer.phone}",
                            f"Email: {customer.email}"]
        
        for detail in customer_details:
            if detail and "[None]" not in detail: # Avoid printing empty placeholders
                c.setFont("Helvetica-Bold" if customer_details.index(detail) == 0 else "Helvetica", 11)
                c.drawString(self.config.MARGIN, y_pos, detail)
                y_pos -= 6 * mm

    def _calculate_items_per_page(self, y_start: float) -> int:
        """
        Calculates how many invoice items can fit on a given page.
        
        Args:
            y_start (float): The starting Y position for the item table.
        
        Returns:
            int: The number of items that can be displayed on the page.
        """
        table_height = y_start - self.config.SUMMARY_START_Y - 20 * mm
        # Subtract header row height
        items_height = table_height - self.config.HEADER_HEIGHT
        items_per_page = int(items_height // self.config.ROW_HEIGHT)
        return max(1, items_per_page)

    def _draw_items_table_on_page(self, items_subset: list, start_index: int, y_position: float):
        """
        Draws a portion of the items table on the current page.
        
        Args:
            items_subset (list): The list of InvoiceItem objects for this page.
            start_index (int): The starting global index of the items on this page.
            y_position (float): The Y coordinate to start drawing the table header.
        
        Returns:
            float: The Y coordinate of the last drawn row, for continuation.
        """
        # Table Header
        headers = ["#", "Description", "Unit Price", "Qty", "Total"]
        header_table = Table([headers], colWidths=self.config.TABLE_COL_WIDTHS, rowHeights=self.config.HEADER_HEIGHT)
        
        header_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.config.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.config.BORDER_COLOR),
        ])
        header_table.setStyle(header_style)
        header_table.wrapOn(self.canvas, sum(self.config.TABLE_COL_WIDTHS), self.config.HEADER_HEIGHT)
        header_table.drawOn(self.canvas, self.config.MARGIN, y_position)
        
        # Table Data
        table_data = []
        for i, item in enumerate(items_subset):
            item_number = start_index + i + 1
            qty_str = f"{item.quantity:.0f}" if item.quantity.is_zero() else f"{item.quantity:.2f}"
            table_data.append([
                str(item_number),
                item.description,
                self.format_currency(item.unit_price),
                qty_str,
                self.format_currency(item.line_total)
            ])
            
        data_table = Table(table_data, colWidths=self.config.TABLE_COL_WIDTHS, rowHeights=self.config.ROW_HEIGHT)
        
        data_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, self.config.SECONDARY_COLOR]),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.config.BORDER_COLOR),
        ])
        data_table.setStyle(data_style)
        
        data_y_position = y_position - self.config.HEADER_HEIGHT
        data_table.wrapOn(self.canvas, sum(self.config.TABLE_COL_WIDTHS), len(table_data) * self.config.ROW_HEIGHT)
        data_table.drawOn(self.canvas, self.config.MARGIN, data_y_position)
        
        return data_y_position - (len(table_data) * self.config.ROW_HEIGHT)

    def _draw_items_table_multipage(self, items: list) -> float:
        """
        Draws the items table with automatic page breaks.
        
        Args:
            items (list): A list of InvoiceItem objects.
        
        Returns:
            float: The final Y coordinate after drawing the last item row.
        """
        items_processed = 0
        current_y = self.config.TABLE_START_Y
        
        # Process the first page
        first_page_capacity = self._calculate_items_per_page(self.config.TABLE_START_Y)
        items_on_first_page = min(first_page_capacity, len(items))
        
        current_y = self._draw_items_table_on_page(
            items[items_processed:items_processed + items_on_first_page],
            items_processed,
            current_y
        )
        items_processed += items_on_first_page
        
        # Process continuation pages
        while items_processed < len(items):
            self.canvas.showPage()
            self.current_page += 1
            self._draw_continuation_header()
            
            continuation_page_capacity = self._calculate_items_per_page(self.config.CONTINUATION_PAGE_TABLE_START_Y)
            remaining_items = len(items) - items_processed
            items_on_this_page = min(continuation_page_capacity, remaining_items)
            
            current_y = self._draw_items_table_on_page(
                items[items_processed:items_processed + items_on_this_page],
                items_processed,
                self.config.CONTINUATION_PAGE_TABLE_START_Y
            )
            items_processed += items_on_this_page
            
        return current_y

    def _draw_totals_section(self, subtotal: Decimal, tax_rate: float, tax_amount: Decimal, total: Decimal, y_start: float):
        """
        Draws the subtotal, tax, and total amount.
        
        Args:
            subtotal (Decimal): The sum of all line item totals.
            tax_rate (float): The tax percentage.
            tax_amount (Decimal): The calculated tax amount.
            total (Decimal): The grand total.
            y_start (float): The starting Y position to draw the section.
        """
        c = self.canvas
        
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

    def _draw_notes(self, notes: str):
        """Draws additional notes or terms at the bottom of the invoice."""
        c = self.canvas
        c.setFillColor(self.config.PRIMARY_COLOR)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.config.MARGIN, self.config.SUMMARY_START_Y - 10 * mm, "Notes/Terms:")

        c.setFillColor(self.config.TEXT_COLOR)
        c.setFont("Helvetica", 9)
        lines = notes.split('\n')
        y_pos = self.config.SUMMARY_START_Y - 16 * mm
        for line in lines:
            if y_pos > self.config.MARGIN:
                c.drawString(self.config.MARGIN, y_pos, line)
                y_pos -= 4 * mm

    def create_invoice(self,
                       invoice_number: str,
                       invoice_date: str = None,
                       due_date: str = None,
                       customer: Customer = None,
                       items: list = None,
                       tax_rate: float = 0,
                       notes: str = "",
                       output_path: str = "invoice.pdf"):
        """
        Creates the complete multi-page invoice PDF.
        
        Args:
            invoice_number (str): The unique invoice number.
            invoice_date (str): The date the invoice was issued.
            due_date (str): The payment due date.
            customer (Customer): A Customer object with billing info.
            items (list): A list of InvoiceItem objects.
            tax_rate (float): The tax percentage to apply.
            notes (str): Additional notes or terms and conditions.
            output_path (str): The path to save the generated PDF.
        """
        if not invoice_date:
            invoice_date = datetime.now().strftime("%Y-%m-%d")
        if not customer:
            customer = Customer()
        if not items:
            items = []
        
        self.current_page = 1
        self.canvas = canvas.Canvas(output_path, pagesize=A4)
        
        # Draw all sections of the first page
        self._draw_first_page_header()
        self._draw_invoice_details(invoice_number, invoice_date, due_date)
        self._draw_customer_info(customer)
        
        # Draw items table with multi-page support
        final_y = self._draw_items_table_multipage(items)
        
        # Calculate totals
        subtotal = sum(item.line_total for item in items)
        tax_amount = subtotal * Decimal(str(tax_rate)) / 100
        total = subtotal + tax_amount
        
        # Check if notes and totals fit on the last page.
        # Summary starts at a fixed position, so we don't need a complex check.
        if notes:
            self._draw_notes(notes)

        self._draw_totals_section(subtotal, tax_rate, tax_amount, total, self.config.SUMMARY_START_Y + 20 * mm)

        self.canvas.save()
        print(f"Multi-page invoice created with {self.current_page} page(s) at {output_path}")

def export_invoice_from_db(session, invoice_id: int, tax_percent: float, output_dir: str = "invoices", logo_path: str = None):
    """
    Generates a multi-page invoice PDF from a database session.
    
    This function is designed to be compatible with a SQLAlchemy-based
    database structure similar to the one in the original printer.py file.

    Args:
        session: The SQLAlchemy session object for database queries.
        invoice_id (int): The ID of the invoice to generate.
        tax_percent (float): The tax percentage to apply to the invoice.
        output_dir (str): The directory to save the generated PDF.
        logo_path (str): Path to the company logo image (optional).
    """
    # NOTE: You will need to import your database models (e.g., DB) here.
    # import DB
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load invoice and customer data from the database
        # Replace `DB.Invoice` and `DB.Customer` with your actual models
        invoice = session.get(DB.Invoice, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found in the database.")
            
        customer_data = session.get(DB.Customer, invoice.customer_id) if invoice.customer_id else None
        
        # Convert database customer data to the local Customer object
        customer = Customer()
        if customer_data:
            customer.name = getattr(customer_data, 'name', '')
            customer.company = getattr(customer_data, 'company', '')
            customer.address = getattr(customer_data, 'street_address', '')
            customer.city = getattr(customer_data, 'city', '')
            customer.phone = getattr(customer_data, 'mobile', '') or getattr(customer_data, 'phone', '')
            customer.email = getattr(customer_data, 'email', '')
            
        # Load invoice items from the database
        # Replace `DB.InvoiceHasStock`, `DB.Stock`, and `DB.Product` with your actual models
        query = (session.query(DB.InvoiceHasStock, DB.Stock, DB.Product)
                 .join(DB.Stock, DB.InvoiceHasStock.stock_id == DB.Stock.id)
                 .join(DB.Product, DB.Stock.product_id == DB.Product.id)
                 .filter(DB.InvoiceHasStock.invoice_id == invoice_id)
                 .order_by(DB.InvoiceHasStock.id.asc()))
        
        item_rows = query.all()
        
        # Convert database items to a list of InvoiceItem objects
        items = []
        for invoice_stock, stock, product in item_rows:
            item = InvoiceItem(
                description=product.title or "Item",
                unit_price=float(invoice_stock.unit_price),
                quantity=float(invoice_stock.quantity)
            )
            items.append(item)
            
        # Generate the multi-page invoice PDF
        generator = ProfessionalInvoiceGenerator()
        output_path = os.path.join(output_dir, f"invoice_{invoice_id}.pdf")
        
        invoice_date = invoice.created_on.strftime("%Y-%m-%d")
        
        generator.create_invoice(
            invoice_number=f"INV-{invoice_id}",
            invoice_date=invoice_date,
            customer=customer,
            items=items,
            tax_rate=tax_percent,
            notes="", # Add notes from your database if they exist
            output_path=output_path
        )
        return output_path
        
    except Exception as e:
        print(f"Error generating invoice from database: {e}")
        return None

if __name__ == "__main__":
    pass