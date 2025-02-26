import pandas as pd
import pdfplumber
import re
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.shortcuts import render
from datetime import datetime
import requests

from django.conf import settings


def index(request):
    return render(request, 'index.html')

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
            "GUEST ROOM":[],
            "EXTRA PERSON": [],
            "INTERNET ACCESS":[],
            "MISC SALES TAX": [],
            "RM CITY TAX": [],
            "RM STATE TAX": [],
            "SUITE SHOP": [],
            "TEXAS RECOVERY FEE": [],
            "GUEST ROOM HONORS":[],
            "ROOM RENT": [],
            "PAVILION PANTRY FOOD": [],
            "GARDEN GRILL BAR BEER": [],
            "GARDEN GRILL BAR BEV":[],
            "GARDEN GRILL BAR BFAST": [],
            "GARDEN GRILL BAR FOOD DISC":[],
            "GARDEN GRILL & BAR LIQUOR":[],
            "GARDEN GRILL & BAR DINNER":[],
            "GARDEN GRILL BAR TIPS":[],
            "GARDEN GRILL BAR WINE":[],
            "HHONORS WATER":[],
            "FB TAX":[],
            "FORT WORTH TOURISM PID FEE":[],
            "Hilton Honors Daily F&B Credit":[],
            "MISC REVENUE - NON-TAXABLE":[],
            "PET FEE":[],
            "PREMIUM INTERNET ACCESS":[],
            "RESTAURANT BEER":[],
            "VENUE HOTEL OCCUPANCY TAX":[],
        }

        section = None

        # Regular expressions for extracting the top-level info
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        hotel_run_date_pattern = re.compile(r'Hotel ID\s*:\s*(\w+)\s+Run Date\s*:\s*([\w\s,]+)')
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
                    if "CITY TAX" in line and "EXTRA"  not in line.split() and "FB"  not in line.split():
                        section = "RM CITY TAX"
                        continue  # Skip the header
                    elif "ROOM RENT" in line:
                        section = "ROOM RENT"
                        continue  # Skip the header
                    elif "STATE TAX" in line :
                        section = "RM STATE TAX"
                        continue  # Skip the header

                    elif "SUITE SHOP" in line:
                        section = "SUITE SHOP"
                        continue  # Skip the header

                    elif "TEXAS RECOVERY FEE" in line not in line.split() and "PET"  not in line.split() not in line.split() and "TOURISM"  not in line.split():
                        section = "TEXAS RECOVERY FEE"
                        continue  # Skip the header


                    elif "PAVILION PANTRY FOOD" in line:
                        section = "PAVILION PANTRY FOOD"
                        continue  # Skip the heade

                    elif "FB TAX" in line and "CITY"  not in line.split():
                        section = "FB TAX"
                        continue  # Skip the header

                    elif "FORT WORTH TOURISM PID FEE" in line and "RECOVERY"  not in line.split() and "PET"  not in line.split():
                        section = "FORT WORTH TOURISM PID FEE"
                        continue  # Skip the header



                    elif "GUEST ROOM" in line and "HONORS" not in line.split() and "RENT" not in line.split():
                        section = "GUEST ROOM"
                        continue  # Skip the header


                    elif "INTERNET ACCESS" in line and "PREMIUM" not in line.split():
                        section = "INTERNET ACCESS"

                        continue  # Skip the header
                    elif "HONORS" in line and "WATER" not in line.split():
                        section = "GUEST ROOM HONORS"

                        continue  # Skip the header

                    elif "MISC SALES TAX" in line or "MIS SALES TAX" in line:
                        section = "MISC SALES TAX"
                        continue  # Skip the header

                    elif "ROOM RENT" in line and "EXTRA"  not in line.split():
                        section = "ROOM RENT"
                        continue  # Skip the header

                    elif "EXTRA" in line:
                        section = "EXTRA PERSON"
                        continue  # Skip the heade


                    elif "GARDEN GRILL & BAR BEER" in line and "BEV" not in line.split() and "BFAST" not in line.split():
                        section = "GARDEN GRILL BAR BEER"
                        continue  # Skip the heade


                    elif "GARDEN GRILL & BAR BEV" in line and "BEER" not in line.split() and "BFAST" not in line.split():
                        section = "GARDEN GRILL BAR BEV"
                        continue  # Skip the heade


                    elif "GARDEN GRILL & BAR BFAST" in line and "BEER" not in line.split() and "BEV" not in line.split() and "DINNER" not in line.split():
                        section = "GARDEN GRILL BAR BFAST"
                        continue  # Skip the heade


                    elif "DINNER" in line and "BEER" not in line.split() and "BEV" not in line.split():
                        section = "GARDEN GRILL & BAR DINNER"
                        continue  # Skip the heade


                    elif "DISC" in line and "BEER" not in line.split() and "BEV" not in line.split():
                        section = "GARDEN GRILL BAR FOOD DISC"
                        continue  # Skip the heade


                    elif "LIQUOR" in line and "BEER" not in line.split() and "BEV" not in line.split():
                        section = "GARDEN GRILL & BAR LIQUOR"
                        continue  # Skip the heade


                    elif "TIPS" in line and "BEER" not in line.split() and "BEV" not in line.split():
                        section = "GARDEN GRILL BAR TIPS"
                        continue  # Skip the heade


                    elif "WINE" in line and "BEER" not in line.split() and "BEV" not in line.split():
                        section = "GARDEN GRILL BAR WINE"
                        continue  # Skip the heade

                    elif "HHONORS WATER" in line and "Credit" not in line.split():
                        section = "HHONORS WATER"
                        continue  # Skip the heade


                    elif "Hilton Honors Daily F&B Credit" in line and "WATER" not in line.split():

                        section = "Hilton Honors Daily F&B Credit"
                        continue  # Skip the heade


                    elif "MISC REVENUE - NON-TAXABLE" in line and "MIS" not in line.split() and "SALES" not in line.split():
                        section = "MISC REVENUE - NON-TAXABLE"
                        continue  # Skip the heade


                    elif "PET FEE" in line and "TOURISM" not in line.split() and "PID" not in line.split():
                        section = "PET FEE"
                        continue  # Skip the heade

                    elif "PREMIUM INTERNET ACCESS" in line:
                        section = "PREMIUM INTERNET ACCESS"
                        continue  # Skip the heade


                    elif "RESTAURANT BEER" in line and "GARDEN" not in line.split():

                        section = "RESTAURANT BEER"
                        continue  # Skip the heade

                    elif "VENUE HOTEL OCCUPANCY TAX" in line and "CITY" not in line.split() and "STATE" not in line.split():
                        section = "VENUE HOTEL OCCUPANCY TAX"
                        continue  # Skip the heade









                    # Process lines with known section and valid date format (e.g., Sep 06, 2024)
                    if section and re.search(r'\b\w+ \d{2}, \d{4}', line):
                        # Regular expression to capture the columns
                        match =re.match(r'(\w+ \d{2}, \d{4})\s+([A-Za-z0-9]+)\s+([A-Za-z\s&-()]+)\s+([A-Za-z0-9/]+)\s+([-\$?\d.,]+)', line)
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




class TaxExemptAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_pdf(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
            "Date Range": "",
            "Hotel ID": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Revenue Breakdown": [],
            "Tax Breakdown": [],
            "Exemptions": {
                "CITY TAX": [],
                "STATE TAX": []
            }
        }

        # Regular expressions for top-level fields
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        hotel_run_date_pattern = re.compile(r'Hotel ID\s*:\s*(\d+)\s+Run Date\s*:\s*([\w\s,]+)')
        run_time_pattern = re.compile(r'Run Time\s*:\s*(.*)')
        username_pattern = re.compile(r'Username\s*:\s*(.*)')

        # Patterns for Revenue Breakdown and Tax Breakdown
        revenue_pattern = re.compile(r'(CITY TAX|STATE TAX)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)')
        tax_breakdown_pattern = re.compile(r'(CITY TAX|STATE TAX)\s+\$([\d,.]+)\s+(-?\$[\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)')

        # Pattern to capture the Exemptions table (Tax Exemption Code, Guest Name, etc.)
        exemption_pattern =re.compile(r'(PERMANENT GUEST|OTHERS)\s+([A-Za-z\s]+)\s+([A-Z0-9]+)\s+(\$[\d,.]+)\s+(\$[\d,.]+)\s+(\$[\d,.]+)\s+([A-Za-z]{3}\s+\d{2},\s+\d{4})\s+([A-Za-z]{3}\s+\d{2},\s+\d{4})')
        #OLD RE STATEMENT
        #re.compile(r'(PERMANENT GUEST|OTHERS)\s+([A-Za-z\s]+)\s+([A-Z0-9]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+([A-Za-z]{3}\s+\d{2},\s+\d{4})\s+([A-Za-z]{3}\s+\d{2},\s+\d{4})')

        current_section = None  # Keep track of the current section to collect data across pages

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()

                    # Skip any lines that are "Page X of Y"
                    if re.search(r'Page\s+\d+\s+of\s+\d+', line):
                        continue

                    # Extract top-level fields
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    elif hotel_run_date_match := hotel_run_date_pattern.search(line):
                        data["Hotel ID"] = hotel_run_date_match.group(1).strip()
                        data["Run Date"] = hotel_run_date_match.group(2).strip()
                    elif run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    elif username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                    # Identify sections for Revenue Breakdown or Tax Breakdown or Exemptions
                    if "Revenue Breakdown" in line:
                        current_section = "Revenue Breakdown"
                        continue
                    elif "Tax Breakdown" in line:
                        current_section = "Tax Breakdown"
                        continue
                    elif "Exempt From : CITY TAX" in line:
                        current_section = "Exempt CITY TAX"
                        continue
                    elif "Exempt From : STATE TAX" in line:
                        current_section = "Exempt STATE TAX"
                        continue

                    # If there is no active section, skip processing
                    if current_section is None:
                        continue

                    # Extract Revenue Breakdown
                    if current_section == "Revenue Breakdown" and (revenue_match := revenue_pattern.search(line)):
                        data["Revenue Breakdown"].append({
                            "Tax Name": revenue_match.group(1),
                            "Taxable Rent": revenue_match.group(2),
                            "Exempt Rent": revenue_match.group(3),
                            "Other Taxable Revenue": revenue_match.group(4),
                            "Other Exempt Revenue": revenue_match.group(5),
                            "Total Taxable Revenue": revenue_match.group(6),
                            "Total Exempt Revenue": revenue_match.group(7),
                            "Total Revenue": revenue_match.group(8)
                        })

                    # Extract Tax Breakdown (including Exempted Tax)
                    elif current_section == "Tax Breakdown" and (tax_match := tax_breakdown_pattern.search(line)):
                        data["Tax Breakdown"].append({
                            "Tax Name": tax_match.group(1),
                            "Tax To Be Collected": tax_match.group(2),
                            "Adjusted Tax": tax_match.group(3),
                            "Exempted Tax": tax_match.group(4),
                            "Net Taxes": tax_match.group(5)
                        })

                    # Extract Exemptions for CITY TAX and STATE TAX
                    elif current_section.startswith("Exempt"):
                        if exemption_match := exemption_pattern.search(line):
                            exemption_data = {
                                "Tax Exemption Code": exemption_match.group(1).strip(),  # As shown in the screenshot
                                "Guest Name": exemption_match.group(2).strip(),
                                "ARR": exemption_match.group(4).strip(),
                                "Confirmation Number": exemption_match.group(3).strip(),
                                "Exempt Rent": exemption_match.group(5).strip(),
                                "Exempted Taxes": exemption_match.group(6).strip(),
                                "Arrival Date": exemption_match.group(7).strip(),
                                "Departure Date": exemption_match.group(8).strip()
                            }
                            if current_section == "Exempt CITY TAX":
                                data["Exemptions"]["CITY TAX"].append(exemption_data)
                            elif current_section == "Exempt STATE TAX":
                                data["Exemptions"]["STATE TAX"].append(exemption_data)

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




class ClerkActivityAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_excel(self, file):
        # Load the Excel file
        df = pd.read_excel(file, header=None)
        hotelid=df.iloc[1,0] if pd.notna(df.iloc[1, 0]) else ""
        df = df.drop(df.columns[0], axis=1)
        if hotelid ==  "":
            hotelid=df.iloc[1,1].replace("Hotel ID : ", "") if pd.notna(df.iloc[1, 1]) else ""

        if hotelid == "0535":
            date_range = df.iloc[0, 14] if pd.notna(df.iloc[0, 14]) else ""
            run_date = df.iloc[1, 14] if pd.notna(df.iloc[1, 14]) else ""
            run_time = df.iloc[2, 14] if pd.notna(df.iloc[2, 14]) else ""
            username = df.iloc[3, 14] if pd.notna(df.iloc[3, 14]) else ""

        if hotelid == "FTWCL":
            date_range = df.iloc[0, 7] if pd.notna(df.iloc[0, 7]) else ""
            run_date = df.iloc[1, 7] if pd.notna(df.iloc[1, 7]) else ""
            run_time = df.iloc[2, 7] if pd.notna(df.iloc[2, 7]) else ""
            username = df.iloc[3, 7] if pd.notna(df.iloc[3, 7]) else ""

        if hotelid == "FTWAA":
            date_range = df.iloc[0, 11].replace("Date Range: ", "") if pd.notna(df.iloc[0, 11]) else ""
            run_date = df.iloc[1, 11].replace("Report run date: ", "") if pd.notna(df.iloc[1, 11]) else ""
            run_time = df.iloc[2, 11].replace("Report run time: ", "") if pd.notna(df.iloc[2, 11]) else ""
            username = df.iloc[3, 11] if pd.notna(df.iloc[3, 11]) else ""





        # Initialize the data structure
        data = {
            "Date Range": date_range,  # Hardcoded for this example, adjust as needed
            "Run Date": run_date,  # Hardcoded for this example, adjust as needed
            "Run Time": run_time,  # Hardcoded for this example, adjust as needed
            "Username":username ,  # Hardcoded for this example, adjust as needed
            "User": "ALL",
            "Hotel id":hotelid,# Hardcoded for this example, adjust as needed
            "Payment Type": "ALL",  # Hardcoded for this example, adjust as needed
            "cash": [],
            "Master": [],
            "Visa": [],
            "Clerk Activity2":[],
            "Summary":[],
        }

        # Helper function to extract data from each section
        def extract_section_data(df, start_row,sectionname):
            transactions = []
            for i in range(start_row, df.shape[0]):
                # Stop if the Grand Total is reached or the next section is detected
                if pd.isna(df.iloc[i, 0]) or 'Grand Total' in str(df.iloc[i, 0]):
                    break

            # Extract transaction details, ensuring there are no NaN values
                if hotelid == "0535":
                    transaction = {
                "Date": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else "",
                "Time": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",
                "Confirmation No": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else "",
                "Guest Name": df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else "",
                "Company Name": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else "",
                "Room Number": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else "",
                "Username": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else "",
                "Amount": df.iloc[i, 14] if not pd.isna(df.iloc[i, 14]) else ""
                }
                if hotelid == "FTWCL" and sectionname =="Clerk Activity":

                    transaction = {
                "Date": df.iloc[i, 0].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 0], datetime) else df.iloc[i, 0],
                "Time": df.iloc[i, 1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(df.iloc[i, 1], datetime) else df.iloc[i, 1],
                "Company Name":df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",
                "Room Number": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else "",
                "Username": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else "",
                "Amount": df.iloc[i, 5] if not pd.isna(df.iloc[i, 5]) else "",
                "Payment Type": df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else "",

                }

                if hotelid == "FTWCL" and sectionname =="Summary" and sectionname !="Clerk Activity":


                    transaction = {

                "User name": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else "",
                "Payment Type": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else "",
                "Total Amount": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",

                }
                if hotelid == "FTWAA" and  sectionname =="Clerk Activity":
                      transaction = {

                "Date": df.iloc[i, 0].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 0], datetime) else df.iloc[i, 0],
                "Time": df.iloc[i, 1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(df.iloc[i, 1], datetime) else df.iloc[i, 1],
                "Transaction Number": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",
                "Name": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else "",
                "Company Name": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else "",
                "Room Number": df.iloc[i, 5] if not pd.isna(df.iloc[i, 5]) else "",
                "Username": df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else "",
                "Amount": df.iloc[i, 7] if not pd.isna(df.iloc[i, 7]) else "",
                "Department Code": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else "",
                "Department Name": df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else "",
                "GL Account Code": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else "",
                "GL Account Name": df.iloc[i, 11] if not pd.isna(df.iloc[i, 11]) else "",
                "Payment Type": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else "",
                "Payment Detail": df.iloc[i, 13] if not pd.isna(df.iloc[i, 13]) else "",

                }

                if hotelid == "FTWAA" and sectionname =="Summary" and sectionname !="Clerk Activity":


                    transaction = {

                "User name": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else "",
                "Payment Type": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else "",
                "Total Amount": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",

                }






                transactions.append(transaction)
            return transactions

    # Function to locate the start of each section
        def find_section_start(df, section_name):
            for i in range(df.shape[0]):
                # Convert the cell to a string, strip extra spaces, and handle NaN
                cell_value = str(df.iloc[i, 0]).strip() if not pd.isna(df.iloc[i, 0]) else ''
                # Debugging: Print the rows while searching for the section name
                if cell_value.lower() == section_name.lower():
                    return i + 2  # Skip the header row (Date, Time, etc.)
            return None

        # Identify where each section starts
        cash_start = find_section_start(df, 'Cash')
        master_start = find_section_start(df, 'Master')
        visa_start = find_section_start(df, 'Visa')
        clerksection=find_section_start(df, 'Clerk Activity')
        Summary=find_section_start(df, 'Summary')

        # Extract data for each section if the section exists
        if cash_start is not None:
            sectionname="cash"
            data["cash"] = extract_section_data(df, cash_start,sectionname)
        if master_start is not None:
            sectionname="Master"
            data["Master"] = extract_section_data(df, master_start,sectionname)
        if visa_start is not None:
            sectionname="Visa"
            data["Visa"] = extract_section_data(df, visa_start,sectionname)
        if clerksection is not None:
            sectionname="Clerk Activity"
            data["Clerk Activity2"] = extract_section_data(df, clerksection,sectionname)

        if Summary is not None:
            sectionname="Summary"
            data["Summary"] = extract_section_data(df, Summary,sectionname)




        # Return the extracted data as JSON
        return data

    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('file', None)

        if not excel_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_data_from_excel(excel_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class FinalAuditAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_pdf(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
            "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Night Audit Time":"",
            "Username": "",
            "Hotel ID": "",
            "Revenue Breakdown": [],
            "Charges Breakdown": [],
            "Taxes Breakdown": [],
            "Cash Breakdown": [],
            "Card Breakdown": [],
            "Other Breakdown": [],
            "Direct Bill Breakdown": [],
            "Deposit Information Breakdown": [],
            "Cash Drop Information Breakdown": [],
            "Room Statistics": [],
            "Performance Statistics": [],
            "Turn Away Information": [],
            "Guest Ledger Balance": {},
            "Direct Bill Balance": {},
            "Advanced Deposit Balance": {},
            "Hotel Balance": {}
        }

        # Regular expressions for top-level fields
        date_range_pattern = date_range_pattern = re.compile(r'(?:Hampton Inn and Suites by|LONESTAR INN|Hilton Garden Inn Fort Worth)\s+Date\s*:\s*([\w]+\s+\d{2},\s+\d{4})')


        hotel_run_date_pattern = re.compile(r'Hotel ID\s*:\s*(\w+)\s+Run Date\s*:\s*([\w\s,]+)')
        run_time_pattern = re.compile(r'Run Time\s*:\s*(.*)')
        night_time = re.compile(r'Night Audit Time\s*:\s*(.*)')
        username_pattern = re.compile(r'Username\s*:\s*(.*)')

        # Patterns for the sections like Revenue, Charges, etc.
        section_header_pattern = re.compile(r'(Revenue|Charges|Taxes|Cash|Card|Other|Direct Bill|Deposit Information|Cash Drop Information)\s+Actual Today')
        section_values_pattern = re.compile(r'([\w\s]+)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)')

        #re.compile(r'([\w\s]+)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)\s+\$?([\d,.]*)')
        Taxes_section_values_pattern =re.compile(r'(CITY TAX|STATE TAX)\s+\$?([\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)\s+(-?\$?[\d,.]+)')
        section_values_pattern2 = re.compile(r'([\w\s]+)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)\s+(-?\$[\d,.]*)')

        room_performance_pattern = re.compile(r'([\w\s]+)\s+\$?([\d,.]+[%$]*)\s+\$?([\d,.]+[%$]*)\s+\$?([\d,.]+[%$]*)\s+\$?([\d,.]+[%$]*)\s+\$?([\d,.]+[%$]*)')
        turn_away_pattern = re.compile(r'([\w\s]+)\s+\$?([\d,.]+)\s+\$?([\d,.]+)')
        guest_ledger_pattern = re.compile(r'(In House Opening Balance:|In House Net Change:|In House Closing Balance:|Group Master Starting Balance:|Group Master Net Change:|Group Master Ending Balance:|House Account Opening Balance:|House Account Net Change:|House Account Closing Balance:|Total Closed Folio Opening Balance:|Total Closed Folio Net Change:|Total Closed Folio Closing Balance:)\s*(-?\$?[\d,.]+)')
        direct_bill_balance_pattern = re.compile(r'(Direct Bill Opening Balance:|Direct Bill Net Change:|Direct Bill Closing Balance:)\s*(-?\$?[\d,.]+)')
        advanced_deposit_pattern = re.compile(r'(Advance Deposit Opening Balance:|Advance Deposit Net Change:|Advance Deposit Closing Balance:|Group Master Opening Balance:|Group Master Net Change:|Group Master Closing Balance:)\s*(-?\$?[\d,.]+)')
        hotel_balance_pattern = re.compile(r'(Beginning Balance:|Ending Balance:)\s*(-?\$?[\d,.]+)')

        # Track the current section
        current_section = None

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                for line in lines:
                    line = line.strip()

                    # Skip lines like "Page X of Y"
                    if re.search(r'Page\s+\d+\s+of\s+\d+', line):
                        continue

                    # Extract top-level fields
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    elif hotel_run_date_match := hotel_run_date_pattern.search(line):
                        data["Hotel ID"] = hotel_run_date_match.group(1).strip()
                        data["Run Date"] = hotel_run_date_match.group(2).strip()
                    elif night_time_match := night_time.search(line):
                        data["Night Audit Time"] = night_time_match.group(1).strip()
                    elif run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    elif username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                    # Identify section headers
                    if section_header_match := section_header_pattern.search(line):
                        current_section = section_header_match.group(1) + " Breakdown"
                        continue
                     # Extract values for other sections
                    if current_section and (section_values_match := section_values_pattern.search(line)):

                        try:
                            name = section_values_match.group(1).strip()
                            actual_today = section_values_match.group(2).strip()
                            adjusted = section_values_match.group(3).strip()
                            net_today = section_values_match.group(4).strip()
                            mtd = section_values_match.group(5).strip()
                            lymtd = section_values_match.group(6).strip()
                            variance = section_values_match.group(7).strip()
                            ytd = section_values_match.group(8).strip()
                            lytd = section_values_match.group(9).strip()
                            var = section_values_match.group(10).strip()

                            # Create a row-wise data entry
                            row_data = {
                                "Type": name,
                                "Actual Today": actual_today,
                                "Adjusted": adjusted,
                                "Net Today": net_today,
                                "M-T-D": mtd,
                                "LY-M-T-D": lymtd,
                                "Variance": variance,
                                "Y-T-D": ytd,
                                "LY-T-D": lytd,
                                "second_Variance":var

                            }

                            # Append the row data to the correct section
                            if current_section == "Revenue Breakdown":
                                data["Revenue Breakdown"].append(row_data)
                            elif current_section == "Charges Breakdown":
                                data["Charges Breakdown"].append(row_data)
                            elif current_section == "Cash Breakdown":
                                data["Cash Breakdown"].append(row_data)
                            elif current_section == "Card Breakdown":
                                data["Card Breakdown"].append(row_data)
                            elif current_section == "Other Breakdown":
                                data["Other Breakdown"].append(row_data)
                            elif current_section == "Direct Bill Breakdown":
                                data["Direct Bill Breakdown"].append(row_data)
                            # elif current_section == "Taxes Breakdown":
                            #     print("Testing yes")
                            #     data["Taxes Breakdown"].append(row_data)

                            #     data["Deposit Information Breakdown"].append(row_data)
                            # elif current_section == "Cash Drop Information Breakdown":
                            #     data["Cash Drop Information Breakdown"].append(row_data)
                        except IndexError:
                            print(f"Skipping line due to missing data: {line}")
                            continue


                    if current_section and (section_values_match3 := Taxes_section_values_pattern.search(line)):
                        try:
                            name = section_values_match3.group(1).strip()
                            actual_today = section_values_match3.group(2).strip()
                            adjusted = section_values_match3.group(3).strip()
                            net_today = section_values_match3.group(4).strip()
                            mtd = section_values_match3.group(5).strip()
                            lymtd = section_values_match3.group(6).strip()
                            variance = section_values_match3.group(7).strip()
                            ytd = section_values_match3.group(8).strip()
                            lytd = section_values_match3.group(9).strip()
                            var = section_values_match3.group(10).strip()

                            # Create a row-wise data entry
                            row_data = {
                                "Type": name,
                                "Actual Today": actual_today,
                                "Adjusted": adjusted,
                                "Net Today": net_today,
                                "M-T-D": mtd,
                                "LY-M-T-D": lymtd,
                                "Variance": variance,
                                "Y-T-D": ytd,
                                "LY-T-D": lytd,
                                "second_Variance":var

                            }





                            if current_section == "Taxes Breakdown":
                                data["Taxes Breakdown"].append(row_data)

                            #     data["Deposit Information Breakdown"].append(row_data)
                            # elif current_section == "Cash Drop Information Breakdown":
                            #     data["Cash Drop Information Breakdown"].append(row_data)
                        except IndexError:
                            print(f"Skipping line due to missing data: {line}")
                            continue









                    if current_section and (section_values_match2 := section_values_pattern2.search(line)):
                        try:
                            name = section_values_match2.group(1).strip()
                            actual_today = section_values_match2.group(2).strip() if section_values_match2.group(2) else ""
                            adjusted = section_values_match2.group(3).strip() if section_values_match2.group(3) else ""
                            net_today = section_values_match2.group(4).strip() if section_values_match2.group(4) else ""
                            mtd = section_values_match2.group(5).strip() if section_values_match2.group(5) else ""
                        # Create a row-wise data entry
                            row_data = {
                                "Type": name,
                                "Actual Today": actual_today,
                                "Adjusted": adjusted,
                                "Net Today": net_today,
                                "M-T-D": mtd,

                            }
                            # Append the row data to the correct section
                            if current_section == "Deposit Information Breakdown":
                                data["Deposit Information Breakdown"].append(row_data)
                            elif current_section == "Cash Drop Information Breakdown":
                                data["Cash Drop Information Breakdown"].append(row_data)
                        except IndexError:
                            print(f"Skipping line due to missing data: {line}")
                            continue



                                    # Handle Room Statistics section
                    if "Room Statistics" in line:
                        current_section = "Room Statistics"
                        continue

                    if current_section == "Room Statistics" and (room_stat_match := room_performance_pattern.search(line)):
                        try:
                            name = room_stat_match.group(1).strip()
                            today = room_stat_match.group(2).strip()
                            mtd = room_stat_match.group(3).strip()
                            ytd = room_stat_match.group(4).strip()
                            lymtd = room_stat_match.group(5).strip()
                            lytd = room_stat_match.group(6).strip()

                            room_stat_data = {
                                "Type": name,
                                "Today": today,
                                "M-T-D": mtd,
                                "Y-T-D": ytd,
                                "LY-M-T-D": lymtd,
                                "LY-T-D": lytd
                            }

                            data["Room Statistics"].append(room_stat_data)
                        except IndexError:
                            print(f"Skipping line due to missing data: {line}")
                            continue





                      # Handle Performance Statistics section
                    if "Performance Statistics" in line:
                        current_section = "Performance Statistics"
                        continue

                    if current_section == "Performance Statistics" and (perf_stat_match := room_performance_pattern.search(line)):
                        try:
                            name = perf_stat_match.group(1).strip()
                            today = perf_stat_match.group(2).strip()
                            mtd = perf_stat_match.group(3).strip()
                            ytd = perf_stat_match.group(4).strip()
                            lymtd = perf_stat_match.group(5).strip()
                            lytd = perf_stat_match.group(6).strip()

                            performance_stat_data = {
                                "Type": name,
                                "Today": today,
                                "M-T-D": mtd,
                                "Y-T-D": ytd,
                                "LY-M-T-D": lymtd,
                                "LY-T-D": lytd
                            }

                            data["Performance Statistics"].append(performance_stat_data)
                        except IndexError:
                            print(f"Skipping line due to missing data: {line}")
                            continue




                    # Handle Turn Away Information section
                    if "Turn Away Information" in line:
                        current_section = "Turn Away Information"
                        continue

                    if current_section == "Turn Away Information" and (turn_away_match := turn_away_pattern.search(line)):
                        try:
                            name = turn_away_match.group(1).strip()
                            today = turn_away_match.group(2).strip()
                            mtd = turn_away_match.group(3).strip()

                            turn_away_data = {
                                "Type": name,
                                "Today": today,
                                "M-T-D": mtd
                            }

                            data["Turn Away Information"].append(turn_away_data)
                        except IndexError:
                            print(f"Skipping line due to missing data: {line}")
                            continue



                    # Handle Guest Ledger Balance section
                    if (guest_ledger_match := guest_ledger_pattern.search(line)):
                        name = guest_ledger_match.group(1).strip()
                        balance = guest_ledger_match.group(2).strip()

                        data["Guest Ledger Balance"][name] = balance

                    # Handle Direct Bill Balance section
                    if (direct_bill_match := direct_bill_balance_pattern.search(line)):
                        name = direct_bill_match.group(1).strip()
                        balance = direct_bill_match.group(2).strip()

                        data["Direct Bill Balance"][name] = balance

                    # Handle Advanced Deposit Balance section
                    if (advanced_deposit_match := advanced_deposit_pattern.search(line)):
                        name = advanced_deposit_match.group(1).strip()
                        balance = advanced_deposit_match.group(2).strip()

                        data["Advanced Deposit Balance"][name] = balance

                    # Handle Hotel Balance section
                    if (hotel_balance_match := hotel_balance_pattern.search(line)):
                        name = hotel_balance_match.group(1).strip()
                        balance = hotel_balance_match.group(2).strip()

                        data["Hotel Balance"][name] = balance





        return data

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





class OccupancyForecastAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_occupancy_data(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
             "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Hotel id": "",
            "Occupancy Forecast and History": [],
            "Occupancy Forecast and History for FTWAA": [],
            "Occupancy Forecast and History for Hampton": []
        }

        # Regular expressions to match the file-level parameters
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        run_date_pattern = re.compile(r'Report run date\s*:\s*(.*)')
        run_time_pattern = re.compile(r'Report run time\s*:\s*(.*)')
        username_pattern = re.compile(r'User\s*:\s*(.*)')

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            kl=1
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                # Extract file-level parameters
                for line in lines:
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    if run_date_match := run_date_pattern.search(line):
                        data["Run Date"] = run_date_match.group(1).strip()
                    if run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    if username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()


                # Extract tables
                tables = page.extract_tables()

            # Iterate over tables
                for table in tables:
                # Skip if the table is empty or malformed
                    if not table or len(table) <= 1:

                        continue

                # Use the header row for checks
                #print(table)

                    header = table[kl]  # Assuming the second row contains the headers
                    print(header)


                    if header[-1] == "ADR":

                        for row in table[2:]:
                            if len(row) == 14:  # Ensure correct number of columns
                                occupancy_data = {
                                "Date": row[0],
                                "Day Of Week": row[1],
                                "Confirmed Revenue": row[2],
                                "Allocation Revenue": row[3],
                                "Total Rooms": row[4],
                                "Sold Rooms": row[5],
                                "OOO": row[6],
                                "Available Rooms": row[7],
                                "Arrivals": row[8],
                                "Guaranteed": row[9],
                                "Non Guaranteed": row[10],
                                "Stay Overs": row[11],
                                "Departures": row[12],
                                "ADR": row[13]
                            }
                                data["Hotel id"] = "0535"
                                data["Occupancy Forecast and History"].append(occupancy_data)

                    elif header[-1] == "Children":
                        for row in table[2:]:
                            if len(row) == 15:  # Ensure correct number of columns
                                occupancy_data = {
                                "Date": row[0],
                                "Day Of Week": row[1],
                                "Confirmed Revenue": row[2],
                                "Total Rooms": row[3],
                                "Sold Rooms": row[4],
                                "Rooms Sold Excluding Complimentary And House Room": row[5],
                                "OOO": row[6],
                                "Available Rooms": row[7],
                                "Arrivals": row[8],
                                "Guaranteed": row[9],
                                "Non Guaranteed": row[10],
                                "Stay Overs": row[11],
                                "Departures": row[12],
                                "Adults": row[13],
                                "Children": row[14],
                            }
                                data["Hotel id"] = "FTWCL"
                                data["Occupancy Forecast and History for Hampton"].append(occupancy_data)

                    elif header[-2] == "Guaranteed":
                        for row in table[2:]:
                            if len(row) == 15:  # Ensure correct number of columns
                                occupancy_data = {
                                "Date": row[0],
                                "Day Of Week": row[1],
                                "Confirmed Revenue": row[2],
                                "Allocation Revenue": row[3],
                                "Total Revenue": row[4],
                                "Total Rooms": row[5],
                                "Sold Rooms": row[6],
                                "Rooms Sold Excluding Complimentary And House Rooms": row[7],
                                "OOO": row[8],
                                "Available Rooms": row[9],
                                "Group Allocation": row[10],
                                "Group Rooms Picked Up": row[11],
                                "Arrivals": row[12],
                                "Guaranteed": row[13],
                                "Non Guaranteed": row[14],
                            }
                                data["Hotel id"] = "FTWAA"
                                data["Occupancy Forecast and History for FTWAA"].append(occupancy_data)

                kl=0
        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_occupancy_data(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class RateTypeTrackingAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_rate_type_data(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
            "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Hotel ID": "0535",  # Hardcoded based on your input
            "Date": [],
            "M-T-D": [],
            "Y-T-D": []
        }

        # Regular expressions to match the file-level parameters
        date_range_pattern = re.compile(r'Date\s*:\s*(.*)')
        run_date_pattern = re.compile(r'Report run date\s*:\s*(.*)')
        run_time_pattern = re.compile(r'Report run time\s*:\s*(.*)')
        username_pattern = re.compile(r'User\s*:\s*(.*)')

        current_section = None  # Variable to track the current section (Date, M-T-D, Y-T-D)

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Extract page text for file-level parameters
                text = page.extract_text()
                lines = text.split('\n')

                # Extract file-level parameters
                for line in lines:
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    if run_date_match := run_date_pattern.search(line):
                        data["Run Date"] = run_date_match.group(1).strip()
                    if run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    if username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                # Extract the tables from the page
                tables = page.extract_tables()

                # Process each table separately
                for table in tables:
                    # Skip if the table is empty or malformed
                    if not table or len(table) <= 1:
                        continue

                    # Identify which section (Date, M-T-D, Y-T-D) we are processing
                    for row in table:
                        # Check for headers that signify new sections
                        if any("Date" in cell for cell in row if cell):
                            current_section = "Date"
                            continue
                        elif any("M-T-D" in cell for cell in row if cell):
                            current_section = "M-T-D"
                            continue
                        elif any("Y-T-D" in cell for cell in row if cell):
                            current_section = "Y-T-D"
                            continue

                        # Skip header rows
                        if "Rate Type" in row[0]:
                            continue

                        # Capture the data from the table rows (ensure correct number of columns)
                        if len(row) >= 15:
                            row_data = {
                                "Rate Type": row[0],
                                "Room Nights Current Year": row[1],
                                "Room Nights Previous Year": row[2],
                                "Room Nights Variance": row[3],
                                "Adult Count Current Year": row[4],
                                "Adult Count Previous Year": row[5],
                                "Adult Count Variance": row[6],
                                "Room Revenue Current Year": row[7],
                                "Room Revenue Previous Year": row[8],
                                "Room Revenue Variance": row[9],
                                "Average Daily Rate Current Year": row[10],
                                "Average Daily Rate Previous Year": row[11],
                                "Average Daily Variance": row[12],
                                "Volume Current Year": row[13],
                                "Volume Previous Year": row[14]
                            }

                            # Append the row data to the corresponding section
                            if current_section == "Date":
                                data["Date"].append(row_data)
                            elif current_section == "M-T-D":
                                data["M-T-D"].append(row_data)
                            elif current_section == "Y-T-D":
                                data["Y-T-D"].append(row_data)

        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_rate_type_data(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class AccountActivity(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_rate_type_data(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
            "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Hotel ID": "FTWAA",  # Hardcoded based on your input
            "Reservation": [],
            "House Accounts": [],
        }

        # Regular expressions to match the file-level parameters
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        run_date_pattern = re.compile(r'Report run date\s*:\s*(.*)')
        run_time_pattern = re.compile(r'Report run time\s*:\s*(.*)')
        username_pattern = re.compile(r'User\s*:\s*(.*)')

        current_section = None  # Variable to track the current section (Date, M-T-D, Y-T-D)

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Extract page text for file-level parameters
                text = page.extract_text()
                lines = text.split('\n')

                # Extract file-level parameters
                for line in lines:
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    if run_date_match := run_date_pattern.search(line):
                        data["Run Date"] = run_date_match.group(1).strip()
                    if run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    if username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                # Extract the tables from the page
                tables = page.extract_tables()

                # Process each table separately
                for table in tables:
                    # Skip if the table is empty or malformed
                    if not table or len(table) <= 1:
                        continue

                    # Identify which section (Date, M-T-D, Y-T-D) we are processing
                    for row in table:
                        # Check for headers that signify new sections
                        if any("Reservation" in cell for cell in row if cell):
                            current_section = "Reservation"
                            continue
                        elif any("House Accounts" in cell for cell in row if cell):
                            current_section = "House Accounts"
                            continue

                    # Skip the row if it contains headers like "Date", "Time", etc.
                        if row[0] is not None and "Date" in row[0] or row[1] is not None and "Time" in row[1]:
                            continue

                        # Capture the data from the table rows (ensure correct number of columns)
                        if len(row) >= 12:
                            row_data = {
                                "Date": row[0],
                                "Time": row[1],
                                "Confirmation Number": row[2],
                                "Guest Name": row[3].replace('\n', '').strip(),
                                "Company Name": row[4].replace('\n', '').strip(),
                                "Room Number": row[5],
                                "Payment Type": row[6],
                                "Last 4 Digits": row[7],
                                "Amount": row[8],
                                "Entry Mode": row[9],
                                "Username": row[10],
                                "Remarks": row[11],
                        }

                        elif len(row) >= 11:
                            row_data = {
                                "Date": row[0],
                                "Time": row[1],
                                "House Account Name": row[2],
                                "House Account code ": row[3].replace('\n', '').strip(),
                                "Company Name": row[4].replace('\n', '').strip(),
                                "Payment Type": row[5],
                                "Last 4 Digits": row[6],
                                "Amount": row[7],
                                "Entry Mode": row[8],
                                "Username": row[9],
                                "Remarks": row[10],
                        }

                        if current_section == "Reservation":
                            data["Reservation"].append(row_data)
                        elif current_section == "House Accounts":
                            data["House Accounts"].append(row_data)

        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_rate_type_data(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class Rateplansummary(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_rate_type_data(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
             "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Hotel ID": "FTWAA",  # Hardcoded based on your input
            "Rate Plan Summary": [],
        }

        # Regular expressions to match the file-level parameters
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        run_date_pattern = re.compile(r'Report run date\s*:\s*(.*)')
        run_time_pattern = re.compile(r'Report run time\s*:\s*(.*)')
        username_pattern = re.compile(r'User\s*:\s*(.*)')

        current_section = None  # Variable to track the current section (Date, M-T-D, Y-T-D)

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Extract page text for file-level parameters
                text = page.extract_text()
                lines = text.split('\n')

                # Extract file-level parameters
                for line in lines:
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    if run_date_match := run_date_pattern.search(line):
                        data["Run Date"] = run_date_match.group(1).strip()
                    if run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    if username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                # Extract the tables from the page
                tables = page.extract_tables()

                # Process each table separately
                for table in tables:
                    # Skip if the table is empty or malformed
                    if not table or len(table) <= 1:
                        continue


                # Identify which section (Reservation, House Accounts) we are processing
                for row in table:
                    # Check for headers that signify new sections
                    if any("Rate Plan Summary" in cell for cell in row if cell):
                        current_section = "Rate Plan Summary"
                        continue


                    # Skip the row if it contains headers like "Date", "Time", etc.
                    if row[0] is not None and "Date" in row[0] or row[1] is not None and "Day Of Week" in row[1]:
                        continue

                    # Capture the data from the table rows (ensure correct number of columns)
                    if len(row) >= 10:
                        row_data = {
                            "Date": row[0],
                            "Day Of Week": row[1],
                            "Rate Plan": row[2].replace('\n', '').strip(),
                            "Rate Plan Code": row[3].replace('\n', '').strip(),
                            "Market Segment": row[4].replace('\n', '').strip(),
                            "Revenue": row[5],
                            "Stays": row[6],
                            "ADR": row[7],
                            "Occupancy Contribution": row[8],
                            "RevPAR Contribution": row[9],
                        }


                        if current_section == "Rate Plan Summary":
                            data["Rate Plan Summary"].append(row_data)


        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_rate_type_data(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class Adjustmentandrefund(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_rate_type_data(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
             "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Hotel ID": "",  # Hardcoded based on your input
            "Adjustments": [],
            "Adjustment Summary": [],
        }

        # Regular expressions to match the file-level parameters
        date_range_pattern = re.compile(r'Date Range\s*:\s*(.*)')
        run_date_pattern = re.compile(r'(\bFTW[A-Z]+\b)\s*Report run date\s*:\s*(.*)')
        run_time_pattern = re.compile(r'Report run time\s*:\s*(.*)')
        username_pattern = re.compile(r'User\s*:\s*(.*)')
        adjustment_summary_headers = ["Type", "Name", "User", "Adjusted Amount", "Adjusted Tax"]
        current_section = None  # Variable to track the current section (Date, M-T-D, Y-T-D)

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Extract page text for file-level parameters
                text = page.extract_text()
                lines = text.split('\n')

                # Extract file-level parameters
                for line in lines:
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    if run_date_match := run_date_pattern.search(line):
                        data["Hotel ID"]=run_date_match.group(1).strip()
                        data["Run Date"] = run_date_match.group(2).strip()
                    if run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    if username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                # Extract the tables from the page
                tables = page.extract_tables()

                for table in tables:
                # Skip if the table is empty or malformed
                    if not table or len(table) <= 1:
                        continue

                # Identify which section (Adjustments or Adjustment Summary) we are processing
                    for row in table:
                    # Check for headers that signify new sections
                        if any("Adjustments" in cell for cell in row if cell) and not any("Summary" in cell for cell in row if cell):
                            current_section = "Adjustments"
                            continue
                        elif any("Adjustment Summary" in cell for cell in row if cell):
                            current_section = "Adjustment Summary"
                            continue

                    # Skip the row if it matches the headers (for Adjustment Summary)
                        if current_section == "Adjustment Summary" and row[:5] == adjustment_summary_headers:
                            continue

                    # Skip the row if it contains headers like "Date", "Time", etc.
                        if row[0] is not None and "Date" in row[0] or row[1] is not None and "Time" in row[1]:
                            continue  # This is the header row, so skip it

                    # Initialize row_data and capture the data from the table rows
                        row_data = None

                        if len(row) == 12:
                            row_data = {
                                "Date": row[0],
                                "Time": row[1],
                                "Transaction Type": row[2],
                                "Charge Type": row[3].replace('\n', '').strip(),
                                "Transaction Name": row[4].replace('\n', '').strip(),
                                "Transaction Number": row[5],
                                "Room Number": row[6],
                                "Adjustment Reason Code": row[7],
                                "Adjusted Amount": row[8],
                                "Adjusted Tax": row[9],
                                "Username": row[10],
                                "Remarks": row[11],
                        }

                        elif len(row) == 5:
                            row_data = {
                                "Type": row[0],
                                "Name": row[1],
                                "User": row[2],
                                "Adjusted Amount": row[3].replace('\n', '').strip(),
                                "Adjusted Tax": row[4].replace('\n', '').strip(),
                        }

                    # Only append row_data if it's been populated
                        if row_data:
                            if current_section == "Adjustments":
                                data["Adjustments"].append(row_data)
                            elif current_section == "Adjustment Summary":
                                data["Adjustment Summary"].append(row_data)


        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_rate_type_data(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class Directbilagging(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_rate_type_data(self, pdf_file):
        # Initialize the dictionary to hold extracted data
        data = {
            "Date Range": "",
            "Run Date": "",
            "Run Time": "",
            "Username": "",
            "Hotel ID": "",  # Hardcoded based on your input
            "Accounts Receivables": [],
            "Invoices": [],
        }

        # Regular expressions to match the file-level parameters
        date_range_pattern =re.compile(r'Date\s*:\s*(.*)')
        run_date_pattern = re.compile(r'(\bFTW[A-Z]+\b)\s*Report run date\s*:\s*(.*)')
        run_time_pattern = re.compile(r'Report run time\s*:\s*(.*)')
        username_pattern = re.compile(r'User\s*:\s*(.*)')
        adjustment_summary_headers = ["Type", "Name", "User", "Adjusted Amount", "Adjusted Tax"]
        current_section = None  # Variable to track the current section (Date, M-T-D, Y-T-D)

        # Open the PDF and process it
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Extract page text for file-level parameters
                text = page.extract_text()
                lines = text.split('\n')

                # Extract file-level parameters
                for line in lines:
                    if date_range_match := date_range_pattern.search(line):
                        data["Date Range"] = date_range_match.group(1).strip()
                    if run_date_match := run_date_pattern.search(line):
                        data["Hotel ID"]=run_date_match.group(1).strip()
                        data["Run Date"] = run_date_match.group(2).strip()
                    if run_time_match := run_time_pattern.search(line):
                        data["Run Time"] = run_time_match.group(1).strip()
                    if username_match := username_pattern.search(line):
                        data["Username"] = username_match.group(1).strip()

                # Extract the tables from the page
                tables = page.extract_tables()

                for table in tables:
                # Skip if the table is empty or malformed
                    if not table or len(table) <= 1:
                        continue

                # Identify which section (Adjustments or Adjustment Summary) we are processing
                    for row in table:
                    # Check for headers that signify new sections
                        if any("Accounts Receivables" in cell for cell in row if cell) and not any("Invoices" in cell for cell in row if cell):
                            current_section = "Accounts Receivables"
                            continue
                        elif any("Invoices" in cell for cell in row if cell):
                            current_section = "Invoices"
                            continue

                    # # Skip the row if it matches the headers (for Adjustment Summary)
                    # if current_section == "Adjustment Summary" and row[:5] == adjustment_summary_headers:
                    #     continue

                    # Skip the row if it contains headers like "Date", "Time", etc.
                        if row[0] is not None and "Company Name" in row[0] or row[1] is not None and "Company Code" in row[1]:
                            continue  # This is the header row, so skip it

                    # Initialize row_data and capture the data from the table rows
                        row_data = None

                        if len(row) == 9:
                            row_data = {
                                "Company Name": row[0],
                                " Company Code": row[1],
                                "Current": row[2],
                                "Over 30": row[3].replace('\n', '').strip(),
                                "Over 60": row[4].replace('\n', '').strip(),
                                "Over 90": row[5],
                                "Over 120 Days": row[6],
                                "Over 150": row[7],
                                "Total": row[8],

                        }

                    # Only append row_data if it's been populated
                        if row_data:
                            if current_section == "Accounts Receivables":
                                data["Accounts Receivables"].append(row_data)
                            elif current_section == "Invoices":
                                data["Invoices"].append(row_data)


        return data

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get('file', None)

        if not pdf_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_rate_type_data(pdf_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# Custom JSON encoder to handle non-serializable objects
class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(o)

class Rateplansummaryhampton(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_excel(self, file):
        try:
            # Load the Excel file
            df = pd.read_excel(file, header=None)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")

        hotelid = df.iloc[1, 0] if pd.notna(df.iloc[1, 0]) else ""
        df = df.drop(df.columns[0], axis=1)  # Drop the first column

        # Dynamically extract the Date Range, Run Date, Run Time, and Username
        date_range = df.iloc[0, 7].replace("Date Range: ", "") if pd.notna(df.iloc[0, 7]) else ""
        run_date = df.iloc[1, 7].replace("Report run date: ", "") if pd.notna(df.iloc[1, 7]) else ""
        run_time = df.iloc[2, 7].replace("Report run time: ", "") if pd.notna(df.iloc[2, 7]) else ""
        username = df.iloc[3, 7] if pd.notna(df.iloc[3, 7]) else ""



        # Initialize the data structure
        data = {
            "Date Range": date_range,
            "Run Date": run_date,
            "Run Time": run_time,
            "Username": username,
            "Hotel Id": hotelid,
            "Rate Plan Summary": [],
        }

        # Helper function to extract data from each section
        def extract_section_data(df, start_row):
            transactions = []
            for i in range(start_row, df.shape[0]):
                # Stop if the Grand Total is reached or the next section is detected
                if pd.isna(df.iloc[i, 0]) or 'Grand Total' in str(df.iloc[i, 0]):
                    break

                # Extract transaction details, ensuring there are no NaN values
                transaction = {
                    "Date": df.iloc[i, 0].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 0], datetime) else df.iloc[i, 0],
                    "Day Of Week": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else "",
                    "Rate Plan": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",
                    "Rate Plan Code": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else "",
                    "Market Segment": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else "",
                    "Revenue": df.iloc[i, 5] if not pd.isna(df.iloc[i, 5]) else "",
                    "Stays": df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else "",
                    "ADR": df.iloc[i, 7] if not pd.isna(df.iloc[i, 7]) else "",
                    "Occupancy": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else "",
                    "RevPAR Contribution": df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else ""
                }
                transactions.append(transaction)
            return transactions

        # Function to locate the start of each section
        def find_section_start(df, section_name):
            for i in range(df.shape[0]):
                # Convert the cell to a string, strip extra spaces, and handle NaN
                cell_value = str(df.iloc[i, 0]).strip() if not pd.isna(df.iloc[i, 0]) else ''
                if cell_value.lower() == section_name.lower():
                    return i + 2  # Skip the header row (Date, Time, etc.)
            return None

        # Identify where the Rate Plan Summary starts
        rate_plan = find_section_start(df, 'Rate Plan Summary')

        # Extract data for each section if the section exists
        if rate_plan is not None:
            data["Rate Plan Summary"] = extract_section_data(df, rate_plan)

        # Return the extracted data as JSON
        return data

    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('file', None)

        if not excel_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_data_from_excel(excel_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class TaxReport(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def extract_data_from_excel(self, file):
        try:
            # Load the Excel file
            df = pd.read_excel(file, header=None)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")

        # Load the Excel file
        hotelid=df.iloc[1,0] if pd.notna(df.iloc[1, 0]) else None
        df = df.drop(df.columns[0], axis=1)

        date_range, run_date, run_time, username = None, None, None, None


        if hotelid == "0535":
            date_range = df.iloc[0, 14] if pd.notna(df.iloc[0, 14]) else None
            run_date = df.iloc[1, 14] if pd.notna(df.iloc[1, 14]) else None
            run_time = df.iloc[2, 14] if pd.notna(df.iloc[2, 14]) else None
            username = df.iloc[3, 14] if pd.notna(df.iloc[3, 14]) else None

        if hotelid == "FTWCL":
            date_range = df.iloc[0, 13].replace("Date Range: ", "") if pd.notna(df.iloc[0, 13]) else None
            run_date = df.iloc[1, 13].replace("Report run date: ", "") if pd.notna(df.iloc[1, 123]) else None
            run_time = df.iloc[2, 13].replace("Report run time: ", "") if pd.notna(df.iloc[2, 13]) else None
            username = df.iloc[3, 13] if pd.notna(df.iloc[3, 13]) else None

        if hotelid == "FTWAA":
            date_range = df.iloc[0, 14].replace("Date Range: ", "") if pd.notna(df.iloc[0, 14]) else None
            run_date = df.iloc[1, 14].replace("Report run date: ", "") if pd.notna(df.iloc[1, 14]) else None
            run_time = df.iloc[2, 14].replace("Report run time: ", "") if pd.notna(df.iloc[2, 14]) else None
            username = df.iloc[3, 14] if pd.notna(df.iloc[3, 14]) else None





        # Initialize the data structure
        data = {
            "Date Range": date_range,  # Hardcoded for this example, adjust as needed
            "Run Date": run_date,  # Hardcoded for this example, adjust as needed
            "Run Time": run_time,  # Hardcoded for this example, adjust as needed
            "Username":username ,  # Hardcoded for this example, adjust as needed
            "Hotel id":hotelid,# Hardcoded for this example, adjust as needed
            "Non Exempted Tax Details": [],
            "Exempted Tax Details":[],
            "Summary":[],
        }

        # Helper function to extract data from each section
        def extract_section_data(df, start_row,sectionname):
            transactions = []
            for i in range(start_row, df.shape[0]):
                # Stop if the Grand Total is reached or the next section is detected
                if pd.isna(df.iloc[i, 0]) or 'Grand Total' in str(df.iloc[i, 0]):
                    break

            # Extract transaction details, ensuring there are no NaN values

                if hotelid == "FTWCL" and sectionname =="Exempted Tax Details":

                    transaction = {
                    "Transaction Number": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else None,
                    "Folio Number": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else None,
                    "Transaction Type": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else None,
                    "Room Number": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else None,
                    "Guest Name": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else None,
                    "Company Name": df.iloc[i, 5] if not pd.isna(df.iloc[i,5]) else None,
                    "Tax Exemption Category": df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else None,
                    "Check In Date": df.iloc[i, 7].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 7], datetime) else df.iloc[i, 6],
                    "Check Out Date": df.iloc[i, 8].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 8], datetime) else df.iloc[i, 7],
                    "Exempted Revenue": df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else None,
                    "MISC SALES TAX": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else None,
                    "TEXAS RECOVERY FEE": df.iloc[i, 11] if not pd.isna(df.iloc[i, 11]) else None,
                    "RM STATE TAX": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else None,
                    "RM CITY TAX": df.iloc[i, 13] if not pd.isna(df.iloc[i, 13]) else None


                }

                if hotelid == "FTWCL" and sectionname =="Non Exempted Tax Details":

                    transaction = {
                    "Transaction Number": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else None,
                    "Folio Number": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else None,
                    "Transaction Type": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else None,
                    "Room Number": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else None,
                    "Guest Name": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else None,
                    "Company Name": df.iloc[i, 5] if not pd.isna(df.iloc[i,5]) else None,
                    # "Tax Exemption Category": df.iloc[i, 5] if not pd.isna(df.iloc[i, 5]) else "",
                    "Check In Date": df.iloc[i, 6].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 6], datetime) else df.iloc[i, 5],
                    "Check Out Date": df.iloc[i, 7].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 7], datetime) else df.iloc[i, 6],
                    "Exempted Revenue": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else None,
                    "MISC SALES TAX": df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else None,
                    "TEXAS RECOVERY FEE": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else None,
                    "RM STATE TAX": df.iloc[i, 11] if not pd.isna(df.iloc[i, 11]) else None,
                    "RM CITY TAX": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else None

                }

                if hotelid == "FTWCL" and sectionname =="Summary" :


                    transaction = {

                    "Tax Name": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else None,
                    "Taxable Revenue": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else None,
                    "Exempted Revenue": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else None,
                    "Payable Tax": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else None,
                    "Exempted Tax": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else None,

                }

                if hotelid == "FTWAA" and sectionname =="Exempted Tax Details":

                    transaction = {
                    "Transaction Number": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else None,
                    "Transaction Type": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else None,
                    "Room Number": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else None,
                    "Guest Name": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else None,
                    "Company Name": df.iloc[i, 4] if not pd.isna(df.iloc[i,4]) else None,
                    "Tax Exemption Category": df.iloc[i, 5] if not pd.isna(df.iloc[i, 5]) else None,
                    "Check In Date": df.iloc[i, 6].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 6], datetime) else df.iloc[i, 6],
                    "Check Out Date": df.iloc[i, 7].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 7], datetime) else df.iloc[i, 7],
                    "Exempted Revenue": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else None,
                    "MEETING ROOM TAX": df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else None,
                    "FOOD N BEVERAGE TAX": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else None,
                    "RM - STATE TAX": df.iloc[i, 11] if not pd.isna(df.iloc[i, 11]) else None,
                    "MRT RM - STATE TAX": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else None,
                    "FB TAX": df.iloc[i, 13] if not pd.isna(df.iloc[i, 13]) else None,
                    "MISC SALES TAX": df.iloc[i, 14] if not pd.isna(df.iloc[i, 14]) else None,
                    "VENUE HOTEL OCCUPANCY TAX": df.iloc[i, 15] if not pd.isna(df.iloc[i, 15]) else None,
                    "RM CITY TAX": df.iloc[i, 16] if not pd.isna(df.iloc[i, 16]) else None

                }

                if hotelid == "FTWAA" and sectionname =="Non Exempted Tax Details":

                    transaction = {
                    "Transaction Number": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else None,
                    "Transaction Type": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else None,
                    "Room Number": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else None,
                    "Guest Name": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else None,
                    "Company Name": df.iloc[i, 4] if not pd.isna(df.iloc[i,4]) else None,
                    "Check In Date": df.iloc[i, 5].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 5], datetime) else df.iloc[i, 5],
                    "Check Out Date": df.iloc[i, 6].strftime('%Y-%m-%d') if isinstance(df.iloc[i, 6], datetime) else df.iloc[i, 6],
                    "Exempted Revenue": df.iloc[i, 7] if not pd.isna(df.iloc[i, 7]) else None,
                    "MEETING ROOM TAX": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else None,
                    "FOOD N BEVERAGE TAX": df.iloc[i, 9] if not pd.isna(df.iloc[i, 9]) else None,
                    "RM - STATE TAX": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else None,
                    "MRT RM - STATE TAX": df.iloc[i, 11] if not pd.isna(df.iloc[i, 11]) else None,
                    "FB TAX": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else None,
                    "MISC SALES TAX": df.iloc[i, 13] if not pd.isna(df.iloc[i, 13]) else None,
                    "VENUE HOTEL OCCUPANCY TAX": df.iloc[i, 14] if not pd.isna(df.iloc[i, 14]) else None,
                    "RM CITY TAX": df.iloc[i, 15] if not pd.isna(df.iloc[i, 15]) else None

                }

                if hotelid == "FTWAA" and sectionname =="Summary" :
                    transaction = {

                    "Tax Name": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else None,
                    "Taxable Revenue": df.iloc[i, 1] if not pd.isna(df.iloc[i, 1]) else None,
                    "Exempted Revenue": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else None,
                    "Payable Tax": df.iloc[i, 3] if not pd.isna(df.iloc[i, 3]) else None,
                    "Exempted Tax": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else None,

                }

                transactions.append(transaction)
            return transactions

    # Function to locate the start of each section
        def find_section_start(df, section_name):
            for i in range(df.shape[0]):
                # Convert the cell to a string, strip extra spaces, and handle NaN
                cell_value = str(df.iloc[i, 0]).strip() if not pd.isna(df.iloc[i, 0]) else ''
                # Debugging: Print the rows while searching for the section name
                if cell_value.lower() == section_name.lower():
                    return i + 2  # Skip the header row (Date, Time, etc.)
            return None

        # Identify where each section starts

        non_exempted = find_section_start(df, 'Non Exempted Tax Details')
        Tax_exempted=find_section_start(df, 'Exempted Tax Details')
        Summary=find_section_start(df, 'Summary')

        # Extract data for each section if the section exists

        if non_exempted is not None:
            sectionname="Non Exempted Tax Details"
            data["Non Exempted Tax Details"] = extract_section_data(df, non_exempted,sectionname)
        if Tax_exempted is not None:
            sectionname="Exempted Tax Details"
            data["Exempted Tax Details"] = extract_section_data(df, Tax_exempted,sectionname)

        if Summary is not None:
            sectionname="Summary"
            data["Summary"] = extract_section_data(df, Summary,sectionname)

        for key in data.keys():
            if isinstance(data[key], list):
                data[key] = [{k: (v if pd.notna(v) else None) for k, v in item.items()} for item in data[key]]
            else:
                data[key] = None if pd.isna(data[key]) else data[key]


        # Return the extracted data as JSON
        return data

    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get('file', None)

        if not excel_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the extraction method
            extracted_data = self.extract_data_from_excel(excel_file)
            return Response(extracted_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








class SentimentAnalysisView(APIView):
    def post(self, request):
        # Extracting client_messages and user_messages from the request data
        client_messages = request.data.get("client_messages", [])
        user_messages = request.data.get("user_messages", [])

        # Validate input
        if not isinstance(client_messages, list) or not isinstance(user_messages, list):
            return Response({"error": "Both client_messages and user_messages should be lists."}, status=status.HTTP_400_BAD_REQUEST)

        # Call the sentiment analysis function
        result = analyze_sentiment(client_messages, user_messages)

        return Response(result)

def analyze_sentiment(client_messages, user_messages):
    url = "https://api.openai.com/v1/chat/completions"
    API_KEY = settings.API_KEY
    headers = {
        "Content-Type": "application/json",
        "Authorization":API_KEY
    }
    # Prepare the conversation context by combining client and user messages
    combined_chat = "\n".join([f"Client: {msg}" for msg in client_messages] +
                               [f"You: {msg}" for msg in user_messages])

    # We explicitly ask for the classification label to always be provided
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that analyzes sentiment in chat conversations."},
            {"role": "user", "content": f"Analyze the sentiment of the following chat history and provide the following structured output:\n\n1. Classification Label (positive, negative, neutral, aggressive, or not satisfied).\n2. Next Action (if any, like 'continue work', 'terminate project', 'refund project cost'; leave blank if not applicable).\n3. Area of Improvement (suggestions if any, otherwise say 'No improvement needed').\n\nChat History:\n{combined_chat}"}
        ],
        "max_tokens": 200
    }

    # Make the POST request to the OpenAI API
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        raw_response = response_data['choices'][0]['message']['content']

        # Initialize variables
        classification_label = ""
        next_action = ""
        area_of_improvement = ""

        # Parsing the raw response for classification, next action, and improvement
        for line in raw_response.split("\n"):
            if "Classification Label:" in line:
                classification_label = line.split(":")[-1].strip()
            elif "Next Action:" in line:
                next_action = line.split(":")[-1].strip() or ""
            elif "Area of Improvement:" in line:
                area_of_improvement = line.split(":")[-1].strip()

        # Ensure the classification label is filled in, otherwise raise an error or handle appropriately
        if not classification_label:
            classification_label = "Not Provided"

        # Prepare the final JSON response
        final_response = {
            "Classification Label": classification_label,
            "Next Action": next_action,
            "Area of Improvement": area_of_improvement
        }

        return final_response
    else:
        return {"Error": f"{response.status_code}, {response.text}"}
        
