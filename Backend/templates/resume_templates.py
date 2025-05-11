# resume_templates.py - Template configurations for resume PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle

def get_template_styles(template_name):
    """Return style configuration for the specified template"""
    # Base styles shared across templates
    base_styles = {
        'Header': ParagraphStyle(
            name='Header',
            fontSize=16,
            leading=20,
            spaceAfter=12,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        ),
        'Contact': ParagraphStyle(
            name='Contact',
            fontSize=10,
            leading=12,
            spaceAfter=12,
            alignment=1,
            fontName='Helvetica'
        ),
        'SubHeader': ParagraphStyle(
            name='SubHeader',
            fontSize=12,
            leading=14,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ),
        'NormalBold': ParagraphStyle(
            name='NormalBold',
            fontSize=10,
            leading=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ),
        'NormalItalic': ParagraphStyle(
            name='NormalItalic',
            fontSize=10,
            leading=12,
            spaceAfter=6,
            fontName='Helvetica-Oblique'
        ),
        'Normal': ParagraphStyle(
            name='Normal',
            fontSize=10,
            leading=12,
            spaceAfter=6,
            fontName='Helvetica'
        )
    }

    # Template-specific configurations
    templates = {
        'professional': {
            'page_size': letter,
            'margins': {'left': 1 * inch, 'right': 1 * inch, 'top': 1 * inch, 'bottom': 0.5 * inch},
            'colors': {
                'subheader': colors.HexColor('#000000'),  # Black subheaders
                'text': colors.black
            },
            'styles': base_styles,
            'layout': {
                'header_border': True,  # Horizontal line under contact info
                'section_spacing': 0.2 * inch
            }
        },
        'modern': {
            'page_size': letter,
            'margins': {'left': 0.75 * inch, 'right': 0.75 * inch, 'top': 0.75 * inch, 'bottom': 0.5 * inch},
            'colors': {
                'subheader': colors.HexColor('#3498db'),  # Blue subheaders
                'text': colors.black
            },
            'styles': {
                **base_styles,
                'Sidebar': ParagraphStyle(
                    name='Sidebar',
                    fontSize=10,
                    leading=12,
                    textColor=colors.white,
                    backColor=colors.HexColor('#2c3e50'),
                    spaceAfter=6,
                    spaceBefore=6,
                    fontName='Helvetica'
                )
            },
            'layout': {
                'sidebar': True,  # Left sidebar for skills
                'sidebar_width': 1.5 * inch,  # Reduced width to prevent overflow
                'section_spacing': 0.15 * inch
            }
        },
        'minimalist': {
            'page_size': letter,
            'margins': {'left': 1.5 * inch, 'right': 1.5 * inch, 'top': 1.5 * inch, 'bottom': 0.5 * inch},
            'colors': {
                'subheader': colors.HexColor('#3498db'),  # Blue header bar
                'text': colors.black
            },
            'styles': {
                **base_styles,
                'HeaderBar': ParagraphStyle(
                    name='HeaderBar',
                    fontSize=12,
                    leading=14,
                    textColor=colors.white,
                    backColor=colors.HexColor('#3498db'),
                    spaceAfter=12,
                    spaceBefore=12,
                    fontName='Helvetica-Bold'
                )
            },
            'layout': {
                'header_bar': True,  # Blue header bar for name
                'section_spacing': 0.25 * inch
            }
        }
    }

    return templates.get(template_name, templates['professional'])