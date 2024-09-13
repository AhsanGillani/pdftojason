import pdfplumber
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

class PDFExtractAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_pdf(self, pdf_file):
        data = {"CITY TAX": [], "ROOM RENT": [], "STATE TAX": []}
        section = None

        # Open the PDF
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()

                    # Identify sections
                    if "CITY TAX" in line:
                        section = "CITY TAX"
                        continue  # Skip the header
                    elif "ROOM RENT" in line:
                        section = "ROOM RENT"
                        continue  # Skip the header
                    elif "STATE TAX" in line:
                        section = "STATE TAX"
                        continue  # Skip the header

                    # Process lines that contain data
                    if section and re.search(r'\bSep \d{2}, \d{4}', line):  # Detect a valid line with a date pattern
                        # Regular expression to capture date, transaction number, guest name, room number, amount, and remarks
                        match = re.match(r'(\w+ \d{2}, \d{4})\s+(\w+)\s+([\w\s]+)\s+(\d+)\s+([-\$?\d.]+)', line)
                        if match:
                            date, transaction_number, guest_name, room_number, amount = match.groups()

                            # Format the amount with a dollar sign
                            if amount.startswith("-"):
                                formatted_amount = f"-${amount[2:]}"  # Ensure the negative amount is formatted as "-$X.XX"
                            else:
                                formatted_amount = f"{amount}"  # Format positive values with "$X.XX"

                            # Append the data, including negative amounts
                            data[section].append({
                                "Date": date.strip(),
                                "Transaction Number": transaction_number.strip(),
                                "Guest Name": guest_name.strip(),
                                "Room Number": room_number.strip(),
                                "Amount": formatted_amount.strip(),  # Both positive and negative values are captured
                            })

        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            extracted_data = self.extract_data_from_pdf(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
