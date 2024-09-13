import pdfplumber
import re
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

class PDFExtractAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_pdf(self, pdf_file):
        file_parameters = {
            "Date Range": "",
            "Hotel ID": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Charge Type": "",
            "CITY TAX": [],
            "ROOM RENT": [],
            "STATE TAX": []
        }

        section = None

        # Regular expressions for extracting the top-level info
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        hotel_run_date_pattern = re.compile(r'Hotel ID\s*:\s*(\d+)\s+Run Date\s*:\s*([\w\s,]+)')
        run_time_pattern = re.compile(r'Run Time\s*:\s*(.*)')
        username_pattern = re.compile(r'Username\s*:\s*(.*)')
        charge_type_pattern = re.compile(r'Charge Type\s*:\s*(.*)')

        # Open the PDF
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()

                    # Extract top-level parameters
                    if date_range_match := date_range_pattern.search(line):
                        file_parameters["Date Range"] = date_range_match.group(1).strip()
                    elif hotel_run_date_match := hotel_run_date_pattern.search(line):
                        file_parameters["Hotel ID"] = hotel_run_date_match.group(1).strip()
                        file_parameters["Run Date"] = hotel_run_date_match.group(2).strip()
                    elif run_time_match := run_time_pattern.search(line):
                        file_parameters["Run Time"] = run_time_match.group(1).strip()
                    elif username_match := username_pattern.search(line):
                        file_parameters["Username"] = username_match.group(1).strip()
                    elif charge_type_match := charge_type_pattern.search(line):
                        file_parameters["Charge Type"] = charge_type_match.group(1).strip()

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

                    # Process lines with known section and valid date format (e.g., Sep 06, 2024)
                    if section and re.search(r'\b\w+ \d{2}, \d{4}', line):
                        # Regular expression to capture the columns
                        match = re.match(r'(\w+ \d{2}, \d{4})\s+(\w+)\s+([\w\s]+)\s+(\d+)\s+([-\$?\d.,]+)', line)
                        if match:
                            date, transaction_number, guest_name, room_number, amount = match.groups()

                            # Format amount
                            if amount.startswith("-"):
                                formatted_amount = f"-${amount[2:]}"
                            else:
                                formatted_amount = f"{amount.strip()}"

                            # Append data to the section
                            file_parameters[section].append({
                                "Date": date.strip(),
                                "Transaction Number": transaction_number.strip(),
                                "Guest Name": guest_name.strip(),
                                "Room Number": room_number.strip(),
                                "Amount": formatted_amount.strip()
                            })

        return file_parameters

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_data_from_pdf(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
