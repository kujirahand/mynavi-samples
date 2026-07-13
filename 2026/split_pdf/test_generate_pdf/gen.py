from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

def create_pdf(filename="pages_350.pdf"):
    # A4 dimensions: 595.27 x 841.89 points
    width, height = A4
    c = canvas.Canvas(filename, pagesize=A4)
    
    cx = width / 2.0
    cy = height / 2.0
    radius = 100  # Radius of the circle (diameter 200)
    
    for page_num in range(1, 351):
        # Draw the circle in the center of the page
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(4)
        c.circle(cx, cy, radius, stroke=1, fill=0)
        
        # Draw the page number in the center of the circle
        # Use larger font sizes fitting the larger circle
        font_size = 90 if page_num < 10 else (80 if page_num < 100 else 70)
        c.setFont("Helvetica-Bold", font_size)
        
        # drawCentredString places the text centered horizontally at cx.
        # To center it vertically, we offset the baseline by approximately 
        # 1/3 of the font size since the text baseline is at the bottom of the characters.
        c.drawCentredString(cx, cy - font_size / 3.0, str(page_num))
        
        c.showPage()
        
    c.save()
    print(f"Successfully created: {filename}")

if __name__ == "__main__":
    create_pdf()
