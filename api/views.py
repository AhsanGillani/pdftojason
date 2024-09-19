import pandas as pd
import pdfplumber
import re
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.shortcuts import render


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
        exemption_pattern = re.compile(
            r'PERMANENT GUEST\s+([A-Za-z\s]+)\s+([A-Z0-9]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)\s+([A-Za-z]{3}\s+\d{2},\s+\d{4})\s+([A-Za-z]{3}\s+\d{2},\s+\d{4})'
        )

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
                                "Tax Exemption Code": "PERMANENT GUEST",  # As shown in the screenshot
                                "Guest Name": exemption_match.group(1).strip(),
                                "ARR": exemption_match.group(3).strip(),
                                "Confirmation Number": exemption_match.group(2).strip(),
                                "Exempt Rent": exemption_match.group(4).strip(),
                                "Exempted Taxes": exemption_match.group(5).strip(),
                                "Arrival Date": exemption_match.group(6).strip(),
                                "Departure Date": exemption_match.group(7).strip()
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
        df = pd.read_excel(file, sheet_name='Sheet1', header=None)
        df = df.drop(df.columns[0], axis=1)
        
        # Initialize the data structure
        data = {
            "Date Range": "Sep 06, 2024 - Sep 06, 2024",  # Hardcoded for this example, adjust as needed
            "Run Date": "Sep 07, 2024",  # Hardcoded for this example, adjust as needed
            "Run Time": "3:32:59 PM",  # Hardcoded for this example, adjust as needed
            "Username": "Sagar Patel",  # Hardcoded for this example, adjust as needed
            "User": "ALL",  # Hardcoded for this example, adjust as needed
            "Payment Type": "ALL",  # Hardcoded for this example, adjust as needed
            "cash": [],
            "Master": [],
            "Visa": []
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
                    "Date": df.iloc[i, 0] if not pd.isna(df.iloc[i, 0]) else "",
                    "Time": df.iloc[i, 2] if not pd.isna(df.iloc[i, 2]) else "",
                    "Confirmation No": df.iloc[i, 4] if not pd.isna(df.iloc[i, 4]) else "",
                    "Guest Name": df.iloc[i, 6] if not pd.isna(df.iloc[i, 6]) else "",
                    "Company Name": df.iloc[i, 8] if not pd.isna(df.iloc[i, 8]) else "",
                    "Room Number": df.iloc[i, 10] if not pd.isna(df.iloc[i, 10]) else "",
                    "Username": df.iloc[i, 12] if not pd.isna(df.iloc[i, 12]) else "",
                    "Amount": df.iloc[i, 14] if not pd.isna(df.iloc[i, 14]) else ""
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

        # Identify where each section starts
        cash_start = find_section_start(df, 'Cash')
        master_start = find_section_start(df, 'Master')
        visa_start = find_section_start(df, 'Visa')

        # Extract data for each section if the section exists
        if cash_start is not None:
            data["cash"] = extract_section_data(df, cash_start)
        if master_start is not None:
            data["Master"] = extract_section_data(df, master_start)
        if visa_start is not None:
            data["Visa"] = extract_section_data(df, visa_start)

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
        date_range_pattern = re.compile(r'LONESTAR INN\s+Date\s*:\s*([\w]+\s+\d{2},\s+\d{4})')
        hotel_run_date_pattern = re.compile(r'Hotel ID\s*:\s*(\d+)\s+Run Date\s*:\s*([\w\s,]+)')
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






