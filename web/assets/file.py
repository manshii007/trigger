"""Define Different File Formats"""
import tabula
import PyPDF2
import xlrd
import xlsxwriter
import re, sys, collections
import os, errno
import datetime
import calendar


def check_or_create_file(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


A_UPPERCASE = ord('A')
ALPHABET_SIZE = 26


def _decompose(number):
    """Generate digits from `number` in base alphabet, most significants
    bits first.
    """

    number -= 1  # Account for A in base alphabet being 1 in decimal rather than 0
    if number < ALPHABET_SIZE:
        yield number
    else:
        number, remainder = divmod(number, ALPHABET_SIZE)
        yield from _decompose(number)
        yield remainder


def base_10_to_alphabet(number):
    """Convert a decimal number to its base alphabet representation"""

    return ''.join(
            chr(A_UPPERCASE + part)
            for part in _decompose(number)
    )


def base_alphabet_to_10(letters):
    """Convert an alphabet number to its decimal representation"""

    return sum(
            (ord(letter) - A_UPPERCASE + 1) * ALPHABET_SIZE**i
            for i, letter in enumerate(reversed(letters.upper()))
    )


class GroupM(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.advertiser = None
        self.agency = None
        self.brand = None
        self.ronumber = None
        self.channel = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                if page == 0:
                    split_text =text.split("\n")
                    self.agency = split_text[0]
                    h = split_text.index("Channel :")
                    self.channel = split_text[h+1]
                    print(self.channel)
                    h = split_text.index("Client Name :")
                    self.advertiser = split_text[h + 1]
                    print(self.advertiser)
                    if "Advertiser:" in split_text :
                        h = split_text.index("Advertiser:")
                        self.advertiser = split_text[h + 1]
                    print(self.advertiser)
                    h = split_text.index("Brand Name :")
                    self.brand = split_text[h + 1]
                    print(self.brand)
                    h = split_text.index("RO Number :")
                    self.ronumber = split_text[h + 1]
                    print(self.ronumber)
                    h = split_text.index("Activity Year :")
                    self.year = split_text[h + 1]
                    h = split_text.index("Activity Month :")
                    self.month = split_text[h + 1]
                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        self.parse_table()

        return df

    def parse_table(self):
        tab = self.table
        num_pages = 1 if len(tab)==1 else len(tab)

        headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                   "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]
        table_data = []
        max_days = 0
        for page in range(num_pages):
            page_data = tab[page]
            shape = page_data.shape
            num_rows = shape[0]
            num_cols = shape[1]
            if num_cols < 30:
                continue
            for i in range(1,num_rows):
                tmp_row = {}
                day = 1
                for col in range(num_cols):
                    text = " ".join(str(page_data[col][i]).split("\r"))
                    if col < len(headers)-1:
                        tmp_row[headers[col]] = text
                    else:
                        tmp_row[headers[-1]] = {} if day==1 else tmp_row[headers[-1]]
                        tmp_row[headers[-1]][day] = text if text!="nan" else ""
                        day += 1
                        max_days = max_days if max_days > day-1 else day-1
                table_data.append(tmp_row)
        self.days = max_days
        self.table_data = table_data

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        if self.brand:
            worksheet = workbook.add_worksheet(self.brand[0:30])
        else:
            worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        row = 0
        col = 0

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(self.days):
                    worksheet.write(row, col, str(i+1))
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, dest):
        # print(self.table_data)
        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                            "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]
        # Iterate over the data and write it out row by row.
        if dest=="broadview":
            for table_row_data in table_data:
                # if "Day wise Slots" in table_row_data:
                if table_row_data['Tape ID']=='Total':
                    worksheet.write(row, 0, "")
                    row+=1
                    continue
                col = 0
                try:
                    for item in headers:
                        if item == "Caption":
                            val = table_row_data['Title']
                            if val != "nan":
                                worksheet.write(row, col, val)
                            else:
                                worksheet.write(row, col, "Total")
                            col += 1
                        elif item == "Programme":
                            val = table_row_data['Program/Time']
                            if "(" in val:
                                val = val.split("(")[0]
                            else:
                                val = val.split("-")[0]

                            if val != "nan":
                                worksheet.write(row, col, val)
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Day":
                            worksheet.write(row, col, "")
                            col += 1
                        elif item == "Timeband":
                            val = table_row_data['Program/Time']
                            try:
                                if "(" in val:
                                    val = val.replace("(", "|").replace(")", "|")
                                    val = re.split('\|', val)
                                    val = val[1]
                                    val = val.replace(".",":").replace(" ","")
                                    worksheet.write(row, col, val)
                                else:
                                    val = val.split("-")
                                    val = val[-2] + "-" + val[-1]
                                    val = val.replace(".", ":").replace(" ", "")
                                    worksheet.write(row, col, val)
                            except IndexError:
                                # print(val)
                                pass
                            col += 1
                        elif item == "Requested Timeband":
                            val = table_row_data['Program/Time']
                            # print(val)
                            try:
                                if "(" in val:
                                    val = val.replace("(", "|").replace(")", "|")
                                    val = re.split('\|', val)
                                    val = val[1]
                                    val = val.replace(".",":").replace(" ","")
                                    worksheet.write(row, col, val)
                                else:
                                    val = val.split("-")
                                    val = val[-2] + "-" + val[-1]
                                    val = val.replace(".",":").replace(" ","")
                                    worksheet.write(row, col, val)
                            except IndexError:
                                # print(val)
                                pass
                            col += 1
                        elif item == "Value":
                            val = table_row_data['Net Spot Rate Per 10sec']

                            if val != "nan":
                                rate = val
                                rate = float("".join(rate.split(",")))
                                p = "Y" if rate>0 else "N"
                                worksheet.write(row, col, p)
                            else:
                                worksheet.write(row, col, "N")
                            col += 1
                        elif item == "Dur":
                            val = table_row_data['Spot Dur']
                            if val != "nan":
                                worksheet.write(row, col, val)
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Day wise Slots":
                            val = table_row_data["Day wise Slots"]
                            for i in range(self.days):
                                worksheet.write(row, col, int(val[i+1]) if val[i+1] else '')
                                col += 1
                        elif item == "Rate":
                            val = table_row_data['Net Spot Rate Per 10sec']
                            if val != "nan":
                                rate = "".join(val.split(","))
                                worksheet.write(row, col, (float(rate)))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Rate as per duration":
                            val = table_row_data['Spot Dur']

                            if val != "nan":
                                rate = table_row_data['Net Spot Rate Per 10sec']
                                rate = "".join(rate.split(","))

                                worksheet.write(row, col, int(int(val) * float(rate) / 10))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Total Spots":
                            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                             base_10_to_alphabet(col), row + 1))
                            col += 1
                        elif item == "FCT":
                            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                    '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                        base_10_to_alphabet(7), row + 1))
                            col += 1
                        elif item == "Total Cost":
                            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                    '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                           base_10_to_alphabet(col - 2), row + 1))
                            col += 1
                except KeyError:
                    pass
                row += 1
            # total spot
            print(col)
            for cl in range(8,col-4):
                worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row ),
                                        '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                                 base_10_to_alphabet(cl), row-1))
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                             base_10_to_alphabet(col - 4), row-1))
            # total fct
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row ),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                             base_10_to_alphabet(col - 3), row-1))
            # total cost
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                             base_10_to_alphabet(col), row-1))
            row += 1
            worksheet.write(row, 0, "Summary")
            row += 1
            worksheet.write(row, 0, "Channel")
            worksheet.write(row, 1, self.channel)
            row += 1
            worksheet.write(row, 0, "Advertiser")
            worksheet.write(row, 1, self.advertiser)
            row += 1
            worksheet.write(row, 0, "Agency")
            worksheet.write(row, 1, self.agency)
            row += 1
            worksheet.write(row, 0, "Brand")
            worksheet.write(row, 1, self.brand)
            row += 1
            worksheet.write(row, 0, "RO Number")
            worksheet.write(row, 1, self.ronumber)
            row += 1
            worksheet.write(row, 0, "Activity Month")
            worksheet.write(row, 1, self.ronumber.split("/")[0])

        elif dest=="champ":
            for table_row_data in table_data:
                # if "Day wise Slots" in table_row_data:
                col = 0
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Title']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Program/Time']
                        if "(" in val:
                            val = val.split("(")[0]
                        else:
                            val = val.split("-")[0]

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Program/Time']
                        try:
                            if "(" in val:
                                val = val.replace("(", "|").replace(")", "|")
                                val = re.split('\|', val)
                                val = val[1]
                                worksheet.write(row, col, val)
                            else:
                                val = val.split("-")
                                val = val[-2] + "-" + val[-1]
                                worksheet.write(row, col, val)
                        except IndexError:
                            # print(val)
                            pass
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Program/Time']
                        # print(val)
                        try:
                            if "(" in val:
                                val = val.replace("(", "|").replace(")", "|")
                                val = re.split('\|', val)
                                val = val[1]
                                worksheet.write(row, col, val)
                            else:
                                val = val.split("-")
                                val = val[-2] + "-" + val[-1]
                                worksheet.write(row, col, val)
                        except IndexError:
                            # print(val)
                            pass
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Spot Dur']

                        if val != "nan":
                            rate = table_row_data['Net Spot Rate Per 10sec']
                            rate = "".join(rate.split(","))

                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Spot Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        for i in range(self.days):
                            if i+1 in val:
                                worksheet.write(row, col, val[i + 1])
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Net Spot Rate Per 10sec']
                        if val != "nan":
                            rate = "".join(val.split(","))
                            worksheet.write(row, col, (float(rate)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, self.month)
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        print(item)
                        raise KeyError
                row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            print(self.month)
            output_path = '/tmp/{}/{}-{}-{}-{}-{}.xlsx'.format(filename, self.channel, self.month, " ".join(self.advertiser.split(" ")[0:2]), self.brand, self.ronumber.replace("/","-"))
            check_or_create_file(output_path)

            wb, ws = self.create_sheet(output_path)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return [output_path]


class Madison(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                # print(text)
                if page == 0:
                    # print("length : {}".format(len(text)))
                    t = re.compile(r'([A-Z]\w+/[0-9]+)Cost')
                    m = t.search(text)

                    if m:
                        t_month = m.group(1)
                        self.month = t_month.split('/')[0]
                        self.year = t_month.split('/')[1]
                    self.text = text

                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        return df

    def parse_table(self):
        tab = self.table
        num_tables = len(tab) - 2
        original_headers = ["Programme", "Week wise Slots", "Rate per 10sec duration", "Cost/Spot", "Cost/Row"]
        headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                   "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        table_data = []
        for page in range(num_tables):
            page_data = tab[page]
            shape = page_data.shape
            num_rows = shape[0]
            num_cols = shape[1]
            caption = None
            slot_time = None
            for i in range(2,num_rows):
                tmp_row = {}
                day = 1
                for col in range(num_cols):
                    text = " ".join(str(page_data[col][i]).split("\r"))
                    if "total" in text and col==0:
                        break
                    if "Caption" in text and col==0:
                        _caption = text.split(":")[1]
                        _time_change = _caption.replace("(", "|").replace(")","|")
                        slot_time = _time_change.split("|")[1][0:-1].strip()
                        caption = _time_change.split("|")[0].strip()
                    elif col==0:
                        tmp_row['Caption'] = caption
                        tmp_row['Dur'] = slot_time
                        day_slot_filter = re.compile(r'([A-Z]\w+-+[A-Z]\w+)')
                        t = day_slot_filter.search(text)
                        day_part = False
                        if t:
                            tmp_row['Day'] = t.group(1)
                            day_part = True
                            tmp_row['Programme'] = text[0:t.start(1)].strip()
                        else:
                            tmp_row['Day'] = ""

                        time_slot_filter = re.compile(r'([0-9:]+ to +[0-9:]+)')
                        t = time_slot_filter.search(text)
                        if t:

                            tmp_row['Timeband'] = t.group(1).replace(" to ",'-')
                            if not day_part:
                                tmp_row['Programme'] = text[0:t.start(1)-1].strip()

                    elif col>0 and col<5:
                        # this is the date wise slots
                        if col==1:
                            tmp_row['Day wise Slots']={}
                        if text!="nan":
                            day_wise = text.split(", ")
                            for d in day_wise:
                                d = d.replace("(","|").replace(")", "|")
                                day = d.split("|")[0]
                                day_wise_num_slots = d.split("|")[1]
                                tmp_row['Day wise Slots'][day] = day_wise_num_slots
                                # print(day, day_wise_num_slots)
                    elif col==5:
                        tmp_row['Total Spots'] = text
                    elif col==6:
                        tmp_row['Rate'] = text
                    elif col==7:
                        tmp_row['Rate as per duration'] = text
                        tmp_row['Value'] = text
                    elif col==8:
                        tmp_row['Total Cost'] = text
                if "Caption" in tmp_row:
                    table_data.append(tmp_row)
        self.days = 31
        self.table_data = table_data

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(days):
                    worksheet.write(row, col, str(i+1))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                            "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            pass
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Value']

                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        print(val)
                        for i in range(self.days):
                            if str(i+1) in val:
                                worksheet.write(row, col, val[str(i+1)])
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "Total Spots":
                        val = table_row_data['Total Spots']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "FCT":
                        spots = table_row_data['Total Spots']
                        val = table_row_data['Dur']
                        worksheet.write(row, col, int(spots)*int(val))
                        col += 1
                    elif item == "Rate":
                        val = table_row_data['Rate']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Rate as per duration']
                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Cost":
                        val = table_row_data['Total Cost']
                        worksheet.write(row, col, val)
                        col += 1
                    else:
                        raise KeyError
            elif dest=="champ":
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            pass
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Value']

                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        for i in range(self.days):
                            if str(i + 1) in val:
                                worksheet.write(row, col, val[str(i + 1)])
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Rate']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, self.month)
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        raise KeyError
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            wb, ws = self.create_sheet(filename)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        else:
            raise FileNotFoundError


class MadisonViacom(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.month = None
        self.year=None
        self.advertiser = None
        self.channel = None
        self.agency = "Madison"
        self.ronumber = None
        self.brand = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                # print(text.split("/n"))
                if page == 0:
                    # print("length : {}".format(len(text)))
                    t = re.compile(r'([A-Z]\w+/[0-9]+)Cost')
                    m = t.search(text)

                    if m:
                        t_month = m.group(1)
                        self.month = t_month.split('/')[0]
                        self.year = t_month.split('/')[1]
                    self.text = text

                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        # print(df)
        self.parse_table()
        return df

    def parse_table(self):
        tab = self.table
        num_tables = len(tab) - 2
        original_headers = ["Programme", "Week wise Slots", "Rate per 10sec duration", "Cost/Spot", "Cost/Row"]
        headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                   "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        table_data = []
        for page in range(num_tables):
            page_data = tab[page]
            shape = page_data.shape
            num_rows = shape[0]
            num_cols = shape[1]
            caption = None
            slot_time = None
            for i in range(2,num_rows):
                tmp_row = {}
                day = 1
                brk = False
                for col in range(num_cols):
                    text = " ".join(str(page_data[col][i]).split("\r"))
                    if ("total" in text or "Totals" in text) and col==0:
                        brk = True
                        break
                    else:
                        if "Caption" in text and col==0:
                            print(text)
                            _caption = text.split(":")[1]
                            _time_change = _caption.replace("(", "|").replace(")","|")
                            slot_time = _time_change.split("|")[1][0:-1].strip()
                            caption = _time_change.split("|")[0].strip()
                            tmp_row['Caption'] = caption
                            tmp_row['Dur'] = slot_time
                            # day part
                            tmp_row['Day'] = ''
                            time_slot_filter = re.compile(r'([0-9:]+ to +[0-9:]+)')
                            t = time_slot_filter.search(text)
                            if t:
                                tmp_row['Timeband'] = t.group(1).replace(" to ", '-')
                                tmp_row['Programme'] = text[0:t.start(1) - 1].split(")")[1].replace("Sat","").replace("Sun","").strip()
                                # day part
                                if 'Sat' in tmp_row['Programme']:
                                    tmp_row['Day'] += 'Sat-'
                                if 'Sun' in tmp_row['Programme'] :
                                    tmp_row['Day'] += 'Sun'
                        elif col==0:
                            tmp_row['Caption'] = caption
                            tmp_row['Dur'] = slot_time
                            day_slot_filter = re.compile(r'([A-Z]\w+-+[A-Z]\w+)')
                            t = day_slot_filter.search(text)
                            day_part = False
                            if t:
                                tmp_row['Day'] = t.group(1)
                                day_part = True
                                tmp_row['Programme'] = text[0:t.start(1)].strip()
                            else:
                                tmp_row['Day'] = ""

                            time_slot_filter = re.compile(r'([0-9:]+ to +[0-9:]+)')
                            t = time_slot_filter.search(text)
                            if t:

                                tmp_row['Timeband'] = t.group(1).replace(" to ",'-')
                                if not day_part:
                                    tmp_row['Programme'] = text[0:t.start(1) - 1].replace("Sat","").replace("Sun", "").strip()
                                    # day part
                                    if 'Sat' in text[0:t.start(1) - 1]:
                                        tmp_row['Day'] += 'Sat-'
                                    if 'Sun' in text[0:t.start(1) - 1]:
                                        tmp_row['Day'] += 'Sun'
                        elif col>0 and col<32:
                            # this is the date wise slots
                            if col==1:
                                tmp_row['Day wise Slots']={}
                            if text!="nan":
                                tmp_row['Day wise Slots'][col] = text

                        elif col==32:
                            tmp_row['Total Spots'] = text
                        elif col==33:
                            tmp_row['Rate'] = text
                            tmp_row['Rate as per duration'] = text
                        elif col==34:
                            tmp_row['Value'] = text
                            tmp_row['Total Cost'] = text
                if not brk:
                    table_data.append(tmp_row)
                if brk and num_rows-i<=2:
                    # print(i, num_rows)
                    caption = None
                    slot_time = None
                    break
        self.days = 31
        self.table_data = table_data
        # print(table_data)

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        # print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(days):
                    worksheet.write(row, col, str(i+1))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                            "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            pass
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Value']

                        if val != "nan":
                            val = val.replace(",", "")
                            rate = float(val)
                            p = "Y" if rate > 0 else "N"
                            worksheet.write(row, col, p)
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        # print(self.days)
                        for i in range(self.days):
                            if (i+1) in val:
                                worksheet.write(row, col, int(val[(i+1)]))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "Rate":
                        val = table_row_data['Rate']
                        val = val.replace(",","")
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Rate as per duration']
                        val = val.replace(",","")
                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
            row += 1
        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row+1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row ))
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row+1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row ))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row+1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row ))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row+1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row ))
        # row += 1
        # worksheet.write(row, 0, "Summary")
        # row += 1
        # worksheet.write(row, 0, "Channel")
        # worksheet.write(row, 1, self.channel)
        # row += 1
        # worksheet.write(row, 0, "Advertiser")
        # worksheet.write(row, 1, self.advertiser)
        # row += 1
        # worksheet.write(row, 0, "Agency")
        # worksheet.write(row, 1, self.agency)
        # row += 1
        # worksheet.write(row, 0, "Brand")
        # worksheet.write(row, 1, self.brand)
        # row += 1
        # worksheet.write(row, 0, "RO Number")
        # worksheet.write(row, 1, self.ronumber)
        # row += 1
        # worksheet.write(row, 0, "Activity Month")
        # worksheet.write(row, 1, self.month)
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            # print(self.month)
            output_path = '/tmp/{}/{}-CONV.xlsx'.format(filename, filename)
            check_or_create_file(output_path)
            wb, ws = self.create_sheet(output_path)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return [output_path]
        else:
            raise FileNotFoundError


class Purnima(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                # print(text)
                if page == 0:
                    # print("length : {}".format(len(text)))
                    t = re.compile(r'([A-Z]\w+/[0-9]+)Cost')
                    m = t.search(text)

                    if m:
                        t_month = m.group(1)
                        self.month = t_month.split('/')[0]
                        self.year = t_month.split('/')[1]
                    self.text = text

                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, pages='all')
        self.table = df
        raise ValueError("Not Implemented Yet...")

    def parse_table(self):
        tab = self.table
        num_tables = len(tab) - 2
        original_headers = ["Programme", "Week wise Slots", "Rate per 10sec duration", "Cost/Spot", "Cost/Row"]
        headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                   "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        table_data = []
        for page in range(num_tables):
            page_data = tab[page]
            shape = page_data.shape
            num_rows = shape[0]
            num_cols = shape[1]
            caption = None
            slot_time = None
            for i in range(2,num_rows):
                tmp_row = {}
                day = 1
                for col in range(num_cols):
                    text = " ".join(str(page_data[col][i]).split("\r"))
                    if "total" in text and col==0:
                        break
                    if "Caption" in text and col==0:
                        _caption = text.split(":")[1]
                        _time_change = _caption.replace("(", "|").replace(")","|")
                        slot_time = _time_change.split("|")[1][0:-1].strip()
                        caption = _time_change.split("|")[0].strip()
                    elif col==0:
                        tmp_row['Caption'] = caption
                        tmp_row['Dur'] = slot_time
                        day_slot_filter = re.compile(r'([A-Z]\w+-+[A-Z]\w+)')
                        t = day_slot_filter.search(text)
                        day_part = False
                        if t:
                            tmp_row['Day'] = t.group(1)
                            day_part = True
                            tmp_row['Programme'] = text[0:t.start(1)].strip()
                        else:
                            tmp_row['Day'] = ""

                        time_slot_filter = re.compile(r'([0-9:]+ to +[0-9:]+)')
                        t = time_slot_filter.search(text)
                        if t:

                            tmp_row['Timeband'] = t.group(1).replace(" to ",'-')
                            if not day_part:
                                tmp_row['Programme'] = text[0:t.start(1)-1].strip()

                    elif col>0 and col<5:
                        # this is the date wise slots
                        if col==1:
                            tmp_row['Day wise Slots']={}
                        if text!="nan":
                            day_wise = text.split(", ")
                            for d in day_wise:
                                d = d.replace("(","|").replace(")", "|")
                                day = d.split("|")[0]
                                day_wise_num_slots = d.split("|")[1]
                                tmp_row['Day wise Slots'][day] = day_wise_num_slots
                                # print(day, day_wise_num_slots)
                    elif col==5:
                        tmp_row['Total Spots'] = text
                    elif col==6:
                        tmp_row['Rate'] = text
                    elif col==7:
                        tmp_row['Rate as per duration'] = text
                        tmp_row['Value'] = text
                    elif col==8:
                        tmp_row['Total Cost'] = text
                if "Caption" in tmp_row:
                    table_data.append(tmp_row)
        self.days = 31
        self.table_data = table_data

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(days):
                    worksheet.write(row, col, str(i+1))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                            "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            pass
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Value']

                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        print(val)
                        for i in range(self.days):
                            if str(i+1) in val:
                                worksheet.write(row, col, val[str(i+1)])
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "Total Spots":
                        val = table_row_data['Total Spots']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "FCT":
                        spots = table_row_data['Total Spots']
                        val = table_row_data['Dur']
                        worksheet.write(row, col, int(spots)*int(val))
                        col += 1
                    elif item == "Rate":
                        val = table_row_data['Rate']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Rate as per duration']
                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Cost":
                        val = table_row_data['Total Cost']
                        worksheet.write(row, col, val)
                        col += 1
                    else:
                        raise KeyError
            elif dest=="champ":
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Timeband']
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            pass
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Value']

                        if val != "nan":
                            val = val.replace(",", "")
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        for i in range(self.days):
                            if str(i + 1) in val:
                                worksheet.write(row, col, val[str(i + 1)])
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Rate']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, self.month)
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        raise KeyError
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            wb, ws = self.create_sheet(filename)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        else:
            raise FileNotFoundError


class Initiative(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        for rx in range(sh.nrows):

            row_data = sh.row(rx)

            row_value = []
            ind = 0
            for r in row_data:
                ind+=1
                v = r.value
                row_value.append(v)
                if v == "Channel" or v == "channel":
                    table_start = True
                if v == "Total" or v == "total" or (type(v)==str and len(v)>20 and ind==1):
                    table_start = False
            if table_start:
                table_data.append(row_value)

        headers = []
        t_data = []
        self.days = 0
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                last_date = 0

                for d in data:
                    hit = False
                    if d:
                        start = True
                    if self.days and not d:
                        d = str(last_date+1)
                        hit = True
                    if bool(re.search(r'\d', d)):
                        print(d)
                        last_date = int(d) if hit else int(d.strip()[0:-2])
                        d = str(last_date)
                        self.days += 1
                    if start:
                        headers.append(d)

            if r > 1:
                data = table_data[r]
                start = False
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if d:
                        start = True
                    if start and headers[r_ind]:
                        if type(headers[r_ind]) is float or type(headers[r_ind]) is int or bool(re.search(r'\d', headers[r_ind])):
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind]: d})
                            else:
                                row_d['Day wise Slots'][headers[r_ind]] = d
                            day_count += 1
                        else:
                            row_d[headers[r_ind]]= d
                        r_ind += 1
                if len(row_d)>1:
                    t_data.append(row_d)
        print("rows : {}".format(len(t_data)))
        self.headers = headers
        self.table_data = t_data
        self.month = ""
        self.year = ""

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                d = self.table_data[0]['Day wise Slots']
                for i in d:
                    worksheet.write(row, col, ''.join(c for c in i if c.isdigit()))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                            "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            # print(table_row_data)
            if dest=="broadview":
                for item in headers:

                    if item == "Caption":
                        val = ""
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day(s)']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":

                        start_time = str((table_row_data['Start Time']))
                        start_time = start_time[0:2]+":"+start_time[2:4]
                        end_time = str((table_row_data['End Time']))
                        end_time = end_time[0:2]+":"+end_time[2:4]
                        val = start_time+"-"+end_time
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        start_time = str((table_row_data['Start Time']))
                        start_time = start_time[0:2] + ":" + start_time[2:4]
                        end_time = str((table_row_data['End Time']))
                        end_time = end_time[0:2] + ":" + end_time[2:4]
                        val = start_time + "-" + end_time
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Nett Cost']

                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['ACD']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, int(val[i]) if val[i] else '')
                            col += 1

                    elif item == "Rate":
                        val = table_row_data['Net Rate']

                        if val != "nan" and (type(val)==float or val.isdigit()) :
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Net Rate']
                        if val != "nan"  and (type(val)==float or val.isdigit()):
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
            row += 1
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-CONV-{}.xlsx'.format(filename,filename,m)
                check_or_create_file(output_path)
                wb, ws = self.create_sheet(output_path)
                ws = self.write_header(ws,m, dest)
                ws = self.write_table_data(ws,m, dest)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError


class FCBULKA(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None
        self.months = []
        self.advertiser = None
        self.agency = None
        self.brand = None
        self.ronumber = None
        self.channel = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        prev_row = []
        month_row = []
        clicked =False
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            ind = 0
            for r in row_data:
                ind += 1
                v = r.value
                row_value.append(v)
                if type(v)is str and (v.strip() == "Channel / Program" or v.strip() == "channel / program"):
                    table_start = True
                    last_f = ""
                    for f in prev_row:
                        if f:
                            last_f = datetime.datetime(*xlrd.xldate_as_tuple(f, book.datemode))
                            if last_f and last_f.month not in self.months:
                                    self.months.append(last_f.month)
                        month_row.append(last_f.month if last_f else "")
                if type(v)is str and ("total" in v.lower()):
                    table_start = False
                    clicked = True
                if type(v)is str and v.strip().lower()[0:6]=="client":
                    self.advertiser = v.split(":")[1].strip().title() if ":" in v else row_data[ind].value.strip().title()
                if type(v)is str and v.strip().lower()[0:7]=="product":
                    self.brand = v.split(":")[1].strip().title() if ":" in v else row_data[ind].value.strip().title()
                if type(v)is str and v.strip().lower()[0:6]=="number":
                    self.ronumber = v.split(":")[1].strip().title() if ":" in v else row_data[ind].value.strip().title()
            prev_row = row_value
            if table_start:
                table_data.append(row_value)
            if clicked:
                clicked=False
        print(self.months)
        headers = []
        t_data = []

        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                for d in data:
                    if d:
                        start = True
                    if start:
                        headers.append(d.strip())
                    if type(d) is float or type(d) is int:
                        self.days += 1
            if r == 1:
                data = table_data[r]
                start = False
                ind = 0
                for d in data:
                    if type(d) is float or type(d) is int:
                        headers[ind] = datetime.datetime(month=month_row[ind],day=int(d), year=2018)
                    ind += 1
            if r == 2:
                # channel name
                data = table_data[r]
                self.channel = data[0].strip()

            if r > 2:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if headers[r_ind]:
                        if type(headers[r_ind]) is datetime.datetime:
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind]: d.strip() if type(d) is str else d})
                            else:
                                row_d['Day wise Slots'][headers[r_ind]] = d.strip() if type(d) is str else d
                            day_count += 1
                        elif headers[r_ind] == "Channel / Program" and not d:
                            row_d[headers[r_ind]] = table_data[r][0]
                        else:
                            row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                        r_ind += 1
                if len(row_d)>1:
                    t_data.append(row_d)
        print("rows : {}".format(len(t_data)))
        # print(headers)

        self.headers = headers
        self.table_data = t_data
        self.month = month_row
        self.year = ""

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        if self.brand:
            worksheet = workbook.add_worksheet(self.brand[0:30])
        else:
            worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(2018, month)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i+1)
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, month, dest):
        print("writing table data for {} month".format(month))
        row = 1
        table_data = self.table_data
        (s, l) = calendar.monthrange(2018, month)

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Channel / Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Days']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Cost/Spot']

                        if val != "nan" and float(val):
                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        base_col = col
                        for i in val:
                            if i.month==month:
                                day = i.day
                                worksheet.write(row, base_col+day-1, int(val[i]) if val[i] else '')
                        col += l
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col+1),row+1), '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8),row+1,base_10_to_alphabet(col),row+1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Rate":
                        val = table_row_data['Rate 10/Sec']

                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Cost/Spot']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col-1), row + 1,
                                                                    base_10_to_alphabet(col-2), row + 1))
                        col += 1
                    else:
                        raise KeyError
            row += 1
        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row))
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        worksheet.write(row, 0, "Summary")
        row += 1
        worksheet.write(row, 0, "Channel")
        worksheet.write(row, 1, self.channel)
        row += 1
        worksheet.write(row, 0, "Advertiser")
        worksheet.write(row, 1, self.advertiser)
        row += 1
        worksheet.write(row, 0, "Agency")
        worksheet.write(row, 1, self.agency)
        row += 1
        worksheet.write(row, 0, "Brand")
        worksheet.write(row, 1, self.brand)
        row += 1
        worksheet.write(row, 0, "RO Number")
        worksheet.write(row, 1, self.ronumber)
        row += 1
        worksheet.write(row, 0, "Activity Month")
        worksheet.write(row, 1, calendar.month_abbr[month].upper())
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-{}-{}-{}-{}.xlsx'.format(filename,self.channel, calendar.month_abbr[m].upper(), " ".join(self.advertiser.split(" ")[0:2]), " ".join(self.brand.split(" ")[0:2]), self.ronumber.replace("/","-"))
                check_or_create_file(output_path)
                wb, ws = self.create_sheet(output_path)
                ws = self.write_header(ws,m, dest)
                ws = self.write_table_data(ws,m, dest)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError


class SkyStar(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        start_rx = None
        end_rx = None
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            # print(row_data)
            for r in row_data:
                v = r.value
                v = v.strip() if type(v) is str else v
                row_value.append(v)
                if type(v)is str and v.lower().strip() == "net rate":
                    table_start = True
                    print("table start")
                    start_rx = rx
                    print(row_data)
                if type(v)is str and ("total" in v.lower()) and rx != start_rx:
                    table_start = False
                    print("table end")
                    print(row_data)
            if table_start and any(row_value):
                table_data.append(row_value)
        headers = []
        t_data = []
        self.days = 0
        prev_netrate = 0
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                for d in data:
                    d = d.replace(":","")
                    if d:
                        start = True
                    if start:
                        headers.append(d.strip())
                    if type(d) is float or type(d) is int:
                        self.days += 1
            if r == 1:
                data = table_data[r]
                start = False
                ind = 0
                for d in data:
                    if type(d) is float or type(d) is int:
                        headers[ind] = int(d)
                    ind += 1

            if r > 2:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if headers[r_ind]:
                        if type(headers[r_ind]) is float or type(headers[r_ind]) is int:
                            d = d.replace("-", "") if type(d) is str else d
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({"{}".format(headers[r_ind]): d.strip() if type(d) is str else d})
                            else:
                                row_d['Day wise Slots']["{}".format(headers[r_ind])] = d.strip() if type(d) is str else d
                            day_count += 1
                        elif headers[r_ind] == "Programme":
                            d = d.split("(")[0].strip()
                            d = d.lower().replace("hrs","")
                            row_d[headers[r_ind]] = d
                        elif headers[r_ind] == "Net Rate":
                            if d:
                                row_d[headers[r_ind]] = d.replace("/","").replace("-","").replace(",","").strip()
                                prev_netrate = row_d[headers[r_ind]]
                            else:
                                row_d[headers[r_ind]] = prev_netrate
                        elif headers[r_ind] == "Duration":
                            if type(d) is str:
                                d = d.lower()
                                if "mins" in d:
                                    d = int(d.replace("mins","").strip())*60
                                elif "min" in d:
                                    d = int(d.replace("min","").strip())*60
                                elif "secs" in d:
                                    d = int(d.replace("secs","").strip())
                                elif "sec" in d:
                                    d = int(d.replace("sec","").strip())
                                elif "s" in d:
                                    d = int(d.replace("s","").strip())
                                else:
                                    raise ValueError("Unknown Duration Format")

                                row_d[headers[r_ind]] = d
                        else:
                            row_d[headers[r_ind]] = d.strip() if type(d) is str else d
                        r_ind += 1
                if len(row_d)>1:
                    t_data.append(row_d)
        print("rows : {}".format(len(t_data)))
        # print(headers)
        # print(t_data)
        self.headers = headers
        self.table_data = t_data
        self.year = ""

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):

        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                d = self.table_data[0]['Day wise Slots']
                for i in d:
                    worksheet.write(row, col, i)
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", "Program/Time", "Title", "Spot Dur", "Pmt Type", "Position",
                            "Total FCT", "Net Spot Rate Per 10sec", "No of Spots", "Net Cost", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":

                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Programme'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Programme'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Net Rate']

                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "Total Spots":
                        val = table_row_data['Total']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "FCT":

                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate":
                        val = table_row_data['Net Rate']
                        dur = table_row_data['Duration']

                        if val != "nan":
                            worksheet.write(row, col, float(val)*10/dur)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Net Rate']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Cost":
                        val = table_row_data['Net Rate']
                        worksheet.write(row, col, val)
                        col += 1
                    else:
                        raise KeyError
            elif dest=="champ":
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Tape Id']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Caption']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Programme'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Programme'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Net Rate']

                        if val != "nan":
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Net Rate']
                        dur = table_row_data['Duration']

                        if val != "nan":
                            worksheet.write(row, col, float(val) * 10 / dur)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        raise KeyError
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            wb, ws = self.create_sheet(filename)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        else:
            raise FileNotFoundError


class StarCom(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.date_offset = None
        self.min_date = None
        self.max_date = None
        self.months = []
        self.advertiser = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        self.parse_table()
        return df

    def parse_table(self):
        tab = self.table

        headers = ["Programme", "Start Time", "End Time", "Caption", "Ad Date", "Rate/10s",
                   "Dur sec", "Rate / Spot", "# of Spots", "Total Amount (Rs.)"]
        table_data = []
        max_day = 1

        min_date = None
        max_date = None
        for page in range(len(tab)):
            page_data = tab[page]

            shape = page_data.shape

            num_rows = shape[0]
            num_cols = shape[1]

            if num_cols == 10:
                for i in range(0, num_rows):
                    if i:
                        tmp_row = {}
                        for col in range(num_cols):
                            text = " ".join(str(page_data[col][i]).split("\r"))
                            tmp_row[headers[col]] = text
                        if tmp_row['# of Spots']!='nan':
                            table_data.append(tmp_row)
                            date = tmp_row['Ad Date']
                            py_date = datetime.datetime.strptime(date, '%d/%m/%Y').date()
                            if py_date.month not in self.months:
                                self.months.append(py_date.month)
                            if not min_date:
                                min_date = py_date
                            if not max_date:
                                max_date = py_date

                            if min_date > py_date:
                                min_date = py_date
                            if max_date < py_date:
                                max_date = py_date
                            day = int(date.split('/')[0])
                            if day>max_day:
                                max_day=day

        first_day = min_date.replace(day=1)
        self.min_date = min_date
        self.max_date = max_date
        self.date_offset = (min_date - first_day).days
        self.days = (max_date-first_day).days+1
        self.table_data = table_data
        print(self.months)

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(2018, month)
        row = 0
        col = 0
        if dest == "broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest == "champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i + 1)
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, month, dest):
        print("writing table data for {} month".format(month))
        (s, l) = calendar.monthrange(2018, month)
        row = 1
        table_data = self.table_data

        original_headers = ["Programme", "Start Time", "End Time", "Caption", "Ad Date", "Rate/10s",
                            "Dur sec", "Rate / Spot", "# of Spots", "Total Amount (Rs.)"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]
        # Iterate over the data and write it out row by row.
        if dest=="broadview":
            for table_row_data in table_data:
                airdate = table_row_data["Ad Date"]
                slots = table_row_data['# of Spots']
                date = datetime.datetime.strptime(airdate, '%d/%m/%Y').date()
                if date.month != month:
                    continue
                col = 0
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']
                        if "(" in val:
                            val = val.split("(")[0]
                        else:
                            val = val.split("-")[0]

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        worksheet.write(row, col, '')
                        col += 1
                    elif item == "Timeband":
                        start = table_row_data['Start Time']
                        end = table_row_data['End Time']
                        try:
                            val = start + "-" + end
                            worksheet.write(row, col, val)
                        except IndexError:
                            # print(val)
                            pass
                        col += 1
                    elif item == "Requested Timeband":
                        start = table_row_data['Start Time']
                        end = table_row_data['End Time']
                        try:
                            val = start + "-" + end
                            worksheet.write(row, col, val)
                        except IndexError:
                            # print(val)
                            pass
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Rate / Spot']
                        val = val.replace(",", "")
                        if val != "nan" and float(val):

                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur sec']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Ad Date"]
                        slots = table_row_data['# of Spots']
                        date = datetime.datetime.strptime(val, '%d/%m/%Y').date()
                        if date.month==month:
                            worksheet.write(row, col+date.day-1, int(slots))
                        col+=l
                    elif item == "Rate":
                        val = table_row_data['Rate/10s']
                        if val != "nan":
                            rate = "".join(val.split(","))
                            worksheet.write(row, col, (float(rate)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        rate = table_row_data['Rate / Spot']

                        if val != "nan":
                            rate = "".join(rate.split(","))
                            worksheet.write(row, col, float(float(rate) / 10))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
                row += 1
            for cl in range(8, col - 4):
                worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                        '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                                 base_10_to_alphabet(cl), row))
            # total spot
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                             base_10_to_alphabet(col - 4), row))
            # total fct
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                             base_10_to_alphabet(col - 3), row))
            # total cost
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                             base_10_to_alphabet(col), row))
            row += 1

        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-CONV-{}.xlsx'.format(filename, filename, m)
                check_or_create_file(output_path)
                wb, ws = self.create_sheet(output_path)
                ws = self.write_header(ws,m, dest)
                ws = self.write_table_data(ws,m, dest)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError


class Zenith(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        self.parse_table()
        return df

    def parse_table(self):
        tab = self.table

        headers = ["Programme", "Rate/10s", "Caption\Dur", "# of Spots", "Total Amount (Rs.)", "U", "Day wise Slots"]
        table_data = []

        for page in range(len(tab)):
            page_data = tab[page]

            shape = page_data.shape
            num_rows = shape[0]
            num_cols = shape[1]
            slots = 0
            if num_cols > 35:
                for i in range(0, num_rows):
                    if i:
                        tmp_row = {}

                        for col in range(num_cols):
                            text = " ".join(str(page_data[col][i]).split("\r"))
                            if col < 6 and headers[col] != 'Day wise Slots' :
                                tmp_row[headers[col]] = text
                            else:
                                val = text
                                if val.isdigit():
                                    val = int(text)
                                    slots += 1
                                else:
                                    val = None
                                if col == 6:
                                    tmp_row['Day wise Slots'] = [val]
                                else:
                                    tmp_row['Day wise Slots'].append(val)
                        if tmp_row['# of Spots'].lower() != 'nan' and slots:
                            table_data.append(tmp_row)

        self.days = 31
        self.table_data = table_data

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        row = 0
        col = 0

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(days):
                    worksheet.write(row, col, str(i+1))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Programme", "Rate/10s", "Caption\Dur", "# of Spots", "Total Amount (Rs.)", "U", "Day wise Slots"]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]
        # Iterate over the data and write it out row by row.
        if dest=="broadview":
            for table_row_data in table_data:
                # if "Day wise Slots" in table_row_data:
                # print(table_row_data)
                col = 0
                try:
                    for item in headers:
                        if item == "Caption":
                            val = table_row_data['Caption\Dur']
                            cap = val.split("(")[0].replace('\r',' ')
                            if val != "nan":
                                worksheet.write(row, col, cap)
                            col += 1
                        elif item == "Programme":
                            val = table_row_data['Programme']
                            prog = val.split('\r')[0]
                            if prog != "nan":
                                worksheet.write(row, col, prog)
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Day":
                            val = table_row_data['Programme']
                            days = val.split('\r')[-1]
                            worksheet.write(row, col, days)
                            col += 1
                        elif item == "Timeband":
                            val = table_row_data['Programme']
                            time = val.split('\r')[1]
                            time = time.replace("(","").replace(")","")
                            try:
                                worksheet.write(row, col, time)
                            except IndexError:
                                # print(val)
                                pass
                            col += 1
                        elif item == "Requested Timeband":
                            val = table_row_data['Programme']
                            time = val.split('\r')[1]
                            time = time.replace("(", "").replace(")", "")
                            try:
                                worksheet.write(row, col, time)
                            except IndexError:
                                # print(val)
                                pass
                            col += 1
                        elif item == "Value":
                            val = table_row_data['Rate/10s']

                            if val != "nan" and float(val) != 0:

                                worksheet.write(row, col, 'Y')
                            else:
                                worksheet.write(row, col, "N")
                            col += 1
                        elif item == "Dur":
                            val = table_row_data['Caption\Dur']
                            dur = val.replace('(',"|").replcae(")","|").split('|')[1]
                            if val != "nan":
                                worksheet.write(row, col, float(dur))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Day wise Slots":
                            val = table_row_data["Day wise Slots"]
                            for i in range(self.days):
                                if val[i+1]:
                                    worksheet.write(row, col, int(val[i+1]))
                                else:
                                    worksheet.write(row, col, '')
                                col += 1
                        elif item == "Total Spots":
                            val = table_row_data['# of Spots']
                            worksheet.write(row, col, val)
                            col += 1
                        elif item == "FCT":
                            spots = table_row_data['# of Spots']
                            val = table_row_data['Caption\Dur']
                            dur = val.replace('(', "|").replcae(")", "|").split('|')[1]
                            worksheet.write(row, col, float(spots)*float(dur))
                            col += 1
                        elif item == "Rate":
                            val = table_row_data['Rate/10s']
                            if val.lower() != "nan":
                                rate = "".join(val.split(","))
                                worksheet.write(row, col, (float(rate)))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Rate as per duration":
                            amount = table_row_data['Total Amount (Rs.)']
                            val = table_row_data['# of Spots']
                            if val.lower() != "nan" and amount.lower()!='nan':
                                amount = "".join(amount.split(","))
                                worksheet.write(row, col, float(amount)/float(val))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Total Cost":
                            val = table_row_data['Total Amount (Rs.)']
                            worksheet.write(row, col, val)
                            col += 1
                        else:
                            raise KeyError
                    row += 1
                except IndexError:
                    print(table_data)
        elif dest=="champ":
            for table_row_data in table_data:
                # if "Day wise Slots" in table_row_data:
                col = 0
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Title']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Program/Time']
                        if "(" in val:
                            val = val.split("(")[0]
                        else:
                            val = val.split("-")[0]

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Program/Time']
                        try:
                            if "(" in val:
                                val = val.replace("(", "|").replace(")", "|")
                                val = re.split('\|', val)
                                val = val[1]
                                worksheet.write(row, col, val)
                            else:
                                val = val.split("-")
                                val = val[-2] + "-" + val[-1]
                                worksheet.write(row, col, val)
                        except IndexError:
                            # print(val)
                            pass
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Program/Time']
                        # print(val)
                        try:
                            if "(" in val:
                                val = val.replace("(", "|").replace(")", "|")
                                val = re.split('\|', val)
                                val = val[1]
                                worksheet.write(row, col, val)
                            else:
                                val = val.split("-")
                                val = val[-2] + "-" + val[-1]
                                worksheet.write(row, col, val)
                        except IndexError:
                            # print(val)
                            pass
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Spot Dur']

                        if val != "nan":
                            rate = table_row_data['Net Spot Rate Per 10sec']
                            rate = "".join(rate.split(","))

                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Spot Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        for i in range(self.days):
                            if i+1 in val:
                                worksheet.write(row, col, val[i + 1])
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Net Spot Rate Per 10sec']
                        if val != "nan":
                            rate = "".join(val.split(","))
                            worksheet.write(row, col, (float(rate)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, self.month)
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        print(item)
                        raise KeyError
                row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            wb, ws = self.create_sheet(filename)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        # else:
        #     raise FileNotFoundError


class Vizeum(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.date_offset = None
        self.min_date = None
        self.max_date = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        self.parse_table()
        return df

    def parse_table(self):
        tab = self.table

        headers = ['Channel', 'Program', 'Day', 'Time', 'Caption', 'Dur', 'Spots', 'FCT', 'Rate/10s', 'Net Total', 'Day wise Slots']
        table_data = []
        max_day = 1

        min_date = None
        max_date = None
        for page in range(len(tab)):
            page_data = tab[page]

            shape = page_data.shape
            print(page_data)
            num_rows = shape[0]
            num_cols = shape[1]
            max_days = 0
            if num_cols >20:
                for i in range(2, num_rows):
                    days = 0
                    if i:
                        tmp_row = {}
                        for col in range(num_cols):
                            text = " ".join(str(page_data[col][i]).split("\r"))
                            if col< 10 and headers[col]!='Day wise Slots':
                                tmp_row[headers[col]] = text
                            else:
                                if col==10:
                                    tmp_row['Day wise Slots'] = [text.lower()]
                                else:
                                    tmp_row['Day wise Slots'].append(text.lower())
                                days+=1
                                max_days = days if days> max_days else max_days
                        if tmp_row['Spots']!='nan':
                            table_data.append(tmp_row)

        self.days = max_days
        self.table_data = table_data

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        row = 0
        col = 0

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(days):
                    worksheet.write(row, col, str(i+1))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ['Channel', 'Program', 'Day', 'Time', 'Caption', 'Dur', 'Spots', 'FCT', 'Rate/10s', 'Net Total', 'Day wise Slots']

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]
        # Iterate over the data and write it out row by row.
        if dest=="broadview":
            for table_row_data in table_data:
                # if "Day wise Slots" in table_row_data:
                # print(table_row_data)
                if table_row_data['Caption'] == 'Total' or table_row_data['Caption']=='nan':
                    continue
                else:
                    col = 0
                    for item in headers:
                        if item == "Caption":
                            val = table_row_data['Caption']

                            if val != "nan":
                                worksheet.write(row, col, val)
                            else:
                                worksheet.write(row, col, "Total")
                            col += 1
                        elif item == "Programme":
                            val = table_row_data['Program']
                            if "(" in val:
                                val = val.split("(")[0]
                            else:
                                val = val.split("-")[0]

                            if val != "nan":
                                worksheet.write(row, col, val)
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Day":
                            val=table_row_data['Day']
                            if val != "nan":
                                worksheet.write(row, col, val)
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Timeband":
                            val = table_row_data['Time']
                            try:
                                worksheet.write(row, col, val)
                            except IndexError:
                                # print(val)
                                pass
                            col += 1
                        elif item == "Requested Timeband":
                            val = table_row_data['Time']
                            try:
                                worksheet.write(row, col, val)
                            except IndexError:
                                # print(val)
                                pass
                            col += 1
                        elif item == "Value":
                            val = table_row_data['Rate/10s']

                            if val != "nan" and float(val):

                                worksheet.write(row, col, 'Y')
                            else:
                                worksheet.write(row, col, "N")
                            col += 1
                        elif item == "Dur":
                            val = table_row_data['Dur']
                            if val != "nan":
                                worksheet.write(row, col, float(val))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Day wise Slots":

                            for i in range(self.days):
                                val = table_row_data['Day wise Slots'][i]
                                if val.lower()!='nan' and val.isdigit():
                                    worksheet.write(row, col, int(val))
                                else:
                                    worksheet.write(row, col, '')
                                col += 1
                        elif item == "Rate":
                            val = table_row_data['Rate/10s']
                            if val != "nan":
                                rate = "".join(val.split(","))
                                worksheet.write(row, col, (float(rate)))
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Rate as per duration":
                            rate = table_row_data['Rate/10s']
                            dur = table_row_data['Dur']

                            if rate != "nan" and dur!="nan":
                                worksheet.write(row, col, float(dur)*float(rate) / 10)
                            else:
                                worksheet.write(row, col, "")
                            col += 1
                        elif item == "Total Spots":
                            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                             base_10_to_alphabet(col), row + 1))
                            col += 1
                        elif item == "FCT":
                            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                    '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                        base_10_to_alphabet(7), row + 1))
                            col += 1
                        elif item == "Total Cost":
                            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                    '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                           base_10_to_alphabet(col - 2), row + 1))
                            col += 1
                        else:
                            raise KeyError
                row += 1
            # total spot
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                             base_10_to_alphabet(col - 4), row))
            # total fct
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                             base_10_to_alphabet(col - 3), row))
            # total cost
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                             base_10_to_alphabet(col), row))
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            output_path = '/tmp/{}/{}-CONV.xlsx'.format(filename, filename)
            check_or_create_file(output_path)
            wb, ws = self.create_sheet(output_path)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return [output_path]
        # else:
        #     raise FileNotFoundError


class HRI(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.read()

    def convert(self, output_format="broadview"):
        self.output_format = output_format

    def read(self):
        if self.file:
            pdfFileObj = open(self.file, 'rb')

            # creating a pdf reader object
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_text = []
            for page in range(pdfReader.numPages):
                # creating a page object
                pageObj = pdfReader.getPage(page)

                # extracting text from page
                text = pageObj.extractText()
                file_text.append(text)

            # closing the pdf file object
            pdfFileObj.close()
            return file_text
        else:
            raise FileNotFoundError

    def get_table(self, format='csv'):
        df = tabula.read_pdf(self.file, output_format=format, lattice=True, multiple_tables=True, pages='all')
        self.table = df
        self.parse_table()
        return df

    def parse_table(self):
        tab = self.table

        headers = ["Tape ID", 'Dur', 'Title', 'Program', 'Time', 'Category', 'Type', 'FCT', 'Net Rate', 'Spots',
                   'Total Cost', "Day wise Slots"]
        table_data = []

        for page in range(len(tab)):
            page_data = tab[page]
            print(page_data)
            shape = page_data.shape
            num_rows = shape[0]
            num_cols = shape[1]
            slots = 0
            days = 0
            if num_cols > 7:

                for i in range(0, num_rows):
                    max_days = 0
                    if i>1:
                        tmp_row = {}

                        for col in range(num_cols):
                            text = " ".join(str(page_data[col][i]).split("\r"))
                            if col < 11 and headers[col] != 'Day wise Slots' :
                                tmp_row[headers[col]] = text
                            else:
                                val = text
                                max_days +=1
                                if val.isdigit():
                                    val = int(text)
                                    slots += 1
                                else:
                                    val = None
                                if col == 11:
                                    tmp_row['Day wise Slots'] = [val]
                                else:
                                    tmp_row['Day wise Slots'].append(val)
                        if tmp_row['Spots'].lower() != 'nan' and slots and ('total' not in tmp_row['Tape ID'].lower()):
                            table_data.append(tmp_row)
                days = days if days>max_days else max_days
        self.days = days
        self.table_data = table_data

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        row = 0
        col = 0

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(days):
                    worksheet.write(row, col, str(i+1))
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        original_headers = ["Tape ID", 'Dur', 'Title', 'Program', 'Time', 'Category', 'Type', 'FCT', 'Net Rate', 'Spots',
                            'Total Cost', "Day wise Slots"]
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        if dest=="broadview":
            for table_row_data in table_data:
                # if "Day wise Slots" in table_row_data:
                # print(table_row_data)
                col = 0
                # try:
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Title']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Program']
                        if val.lower() != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time']
                        val =val.replace(" ","")

                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                            pass
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time']
                        val =val.replace(" ","")

                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                            pass
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Type']
                        val =val.replace(" ","")

                        if val != "nan":

                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        val =val.replace(" ","")

                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        print(self.days)
                        for i in range(self.days):
                            if val[i]:
                                worksheet.write(row, col, int(val[i]))
                            else:
                                worksheet.write(row, col, '')
                            col += 1
                    elif item == "Rate":
                        val = table_row_data['Net Rate']
                        val =val.replace(" ","")

                        if val.lower() != "nan":
                            rate = "".join(val.split(","))
                            worksheet.write(row, col, (float(rate)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        amount = table_row_data['Net Rate']
                        amount =amount.replace(" ","")

                        if amount.lower()!='nan':
                            amount = "".join(amount.split(","))
                            worksheet.write(row, col, float(amount))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
                row += 1
                # except IndexError:
                #     print(table_row_data)
            # total spot
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                             base_10_to_alphabet(col - 4), row))
            # total fct
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                             base_10_to_alphabet(col - 3), row))
            # total cost
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                             base_10_to_alphabet(col), row))
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            output_path = '/tmp/{}/{}-CONV.xlsx'.format(filename, filename)
            check_or_create_file(output_path)
            wb, ws = self.create_sheet(output_path)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        # else:
        #     raise FileNotFoundError


class RKSWAMY(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None
        self.months = []
        self.advertiser = None
        self.agency = None
        self.brand = None
        self.ronumber = None
        self.channel = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        month_row = []
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            prev_row_value = None
            for ind, r in enumerate(row_data):
                v = r.value
                row_value.append(v)

                # activity month
                if prev_row_value and type(prev_row_value) is str and  prev_row_value.strip().lower() == "activity month":
                    print(v)
                    month_num = datetime.datetime.strptime(v[0:3].title(), '%b').month
                    if month_num is not self.months:
                        self.months.append(month_num)

                if type(v)is str and (v.lower().strip() == "tape id"):
                    table_start = True
                if type(v)is str and (v.lower().strip()=='total'):
                    table_start = False
                    break
                if type(v)is str and v.strip().lower()[0:6]=="client":
                    self.advertiser = row_data[ind+1].value.strip().title()
                if type(v)is str and v.strip().lower()=="station":
                    self.channel = row_data[ind+1].value.strip().title()
                if type(v)is str and v.strip().lower()=="brand":
                    self.brand = row_data[ind+1].value.strip().title()
                if type(v)is str and v.strip().lower()=="ro number":
                    self.ronumber = row_data[ind+3].value.strip().title()
                prev_row_value = v
            if table_start:
                table_data.append(row_value)
        headers = []
        t_data = []
        self.days = 0
        max_days = 0
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                for d in data:
                    if d:
                        start = True
                    if start:
                        try:
                            headers.append(d.strip())
                        except AttributeError:
                            headers.append(d)
                    if type(d) is float or type(d) is int:
                        self.days += 1
            if r  == 1:
                data = table_data[r]

            if r > 1:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if headers[r_ind]:
                        if type(headers[r_ind]) is float or type(headers[r_ind]) is int:
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind]: d.strip() if type(d) is str else d})
                            else:
                                row_d['Day wise Slots'][headers[r_ind]] = d.strip() if type(d) is str else d

                            day_count += 1
                        elif headers[r_ind] == "Channel / Program" and not d:
                            row_d[headers[r_ind]] = table_data[r][0]
                        else:
                            row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                        r_ind += 1

                if len(row_d)>1:
                    t_data.append(row_d)
                    max_date = max(row_d['Day wise Slots'].keys())
                    max_days = max_date if max_date>max_days else max_days
        print("rows : {}".format(len(t_data)))
        print(self.months)
        self.headers = headers
        self.table_data = t_data
        self.month = month_row
        self.year = ""
        self.days = max_days

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(2018, month)
        row = 0
        col = 0
        if dest == "broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest == "champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i + 1)
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, month, dest):

        print("writing table data for {} month".format(month))
        row = 1
        table_data = self.table_data
        (s, l) = calendar.monthrange(2018, month)

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Title']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        if ":" not in val:
                            val = val[0:2]+":"+val[2:7]+":"+val[7:]
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        if ":" not in val:
                            val = val[0:2] + ":" + val[2:7] + ":" + val[7:]
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Aggmt#/Rate in INR']

                        if val != "nan" and val.isdigit() and float(val):
                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Spot Dur']
                        if type(val)==float or type(val)==int or ( val != "nan" and val.isdigit()):
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        base_col = col
                        total_spot = 0
                        for i in val:
                            spot = int(val[i]) if val[i] else ''
                            total_spot += int(val[i]) if val[i] else 0
                            worksheet.write(row, base_col + i - 1, spot)
                        col += l
                    elif item == "Rate":
                        val = table_row_data['Aggmt#/Rate in INR']
                        spots = table_row_data['Spot Dur']

                        if val != "nan" and val.isdigit():
                            worksheet.write(row, col, float(val)*10/float(spots))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Aggmt#/Rate in INR']
                        if val != "nan" and val.isdigit():
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError

                val = table_row_data["Day wise Slots"]
                base_col = col
                total_spot = 0
                for i in val:
                    spot = int(val[i]) if val[i] else ''
                    total_spot += int(val[i]) if val[i] else 0

                if not total_spot:
                    for i in range(col):
                        worksheet.write(row, i, '')
                    row = row-1

            row += 1
        # cleanup
        for i in range(col):
            worksheet.write(row, i, ' ')
        print(col)
        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row - 1))
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        worksheet.write(row, 0, "Summary")
        row += 1
        worksheet.write(row, 0, "Channel")
        worksheet.write(row, 1, self.channel)
        row += 1
        worksheet.write(row, 0, "Advertiser")
        worksheet.write(row, 1, self.advertiser)
        row += 1
        worksheet.write(row, 0, "Agency")
        worksheet.write(row, 1, self.agency)
        row += 1
        worksheet.write(row, 0, "Brand")
        worksheet.write(row, 1, self.brand)
        row += 1
        worksheet.write(row, 0, "RO Number")
        worksheet.write(row, 1, self.ronumber)
        row += 1
        worksheet.write(row, 0, "Activity Month")
        worksheet.write(row, 1, self.ronumber.split("/")[0])
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-{}-{}-{}-{}.xlsx'.format(filename,self.channel, calendar.month_abbr[m].upper(), " ".join(self.advertiser.split(" ")[0:2]), " ".join(self.brand.split(" ")[0:2]), self.ronumber.replace("/","-"))
                check_or_create_file(output_path)
                wb, ws = self.create_sheet(output_path)
                ws = self.write_header(ws,m, dest)
                ws = self.write_table_data(ws,m, dest)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError


class SPAN(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None
        self.months = []
        self.year = None
        self.caption = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        prev_row = []
        month_row = []
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            ind = 0
            for r in row_data:
                ind+=1
                v = r.value
                row_value.append(v)
                if type(v)is str and (v.lower().strip() == "channel / station"):
                    table_start = True
                    last_f = ""
                    for f in prev_row:
                        if f.value:
                            last_f = datetime.datetime(*xlrd.xldate_as_tuple(f.value, book.datemode))
                            print(last_f)
                            if last_f and not self.year :
                                self.year= last_f.year
                            if last_f and last_f.month not in self.months:
                                self.months.append(last_f.month)
                        month_row.append(last_f.month if last_f else "")
                if type(v)is str and ('total' in v.lower().strip()) and ind==1:
                    table_start = False
                    break
                if type(v)is str and (v.lower().strip() == "caption:"):
                    self.caption = sh.row(rx)[ind].value
            if table_start:
                table_data.append(row_value)
            prev_row = row_data
        headers = []
        t_data = []
        self.days = 0
        print(self.months)
        print(month_row)
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                ind = 0
                for d in data:
                    if d:
                        start = True
                    if start:

                        if type(d) is float or type(d) is int:
                            date = datetime.datetime(year = self.year, month=month_row[ind], day=int(d))
                            headers.append(date)
                        else:
                            try:
                                headers.append(d.strip())
                            except AttributeError:
                                headers.append(d)
                    ind+=1
            if r  == 1:
                data = table_data[r]

            if r > 1:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if headers[r_ind]:
                        if type(headers[r_ind]) is datetime.datetime:
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind]: d.strip() if type(d) is str else d})
                            else:
                                row_d['Day wise Slots'][headers[r_ind]] = d.strip() if type(d) is str else d

                            day_count += 1
                        elif headers[r_ind] == "Channel / Program" and not d:
                            row_d[headers[r_ind]] = table_data[r][0]
                        else:
                            row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                        r_ind += 1

                if len(row_d)>1:
                    t_data.append(row_d)
                    max_date = max(row_d['Day wise Slots'].keys())
        print("rows : {}".format(len(t_data)))

        self.headers = headers
        self.table_data = t_data
        self.month = month_row
        self.year = ""
        self.days = 31

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(2018, month)
        row = 0
        col = 0
        if dest == "broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest == "champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i + 1)
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, month, dest):

        print("writing table data for {} month".format(month))
        row = 1
        table_data = self.table_data
        (s, l) = calendar.monthrange(2018, month)

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        # val = table_row_data['Channel / Station']
                        if self.caption:
                            worksheet.write(row, col, self.caption)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Requested Time Band'].replace(' ', "")
                        if ":" not in val:
                            val = val[0:2]+":"+val[2:7]+":"+val[7:]
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Requested Time Band'].replace(' ', "")
                        if ":" not in val:
                            val = val[0:2] + ":" + val[2:7] + ":" + val[7:]
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Net Rate (Per 10sec)']

                        if val != "nan" and val.isdigit():
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Spot Duration']
                        if type(val)==float or type(val)==int or ( val != "nan" and val.isdigit()):
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        base_col = col
                        total_spot = 0
                        for i in val:
                            if i.month == month:
                                day = i.day
                                spot = int(val[i]) if val[i] else ''
                                total_spot += int(val[i]) if val[i] else 0
                                worksheet.write(row, base_col + day - 1, spot)
                        col += l

                    elif item == "Rate":
                        val = table_row_data['Net Rate (Per 10sec)']

                        if val != "nan" and val.isdigit():
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Net Rate (Per 10sec)']
                        if val != "nan" and val.isdigit():
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError

                val = table_row_data["Day wise Slots"]
                total_spot = 0
                for i in val:
                    if i.month == month:
                        total_spot += int(val[i]) if val[i] else 0
                if not total_spot:
                    for i in range(col):
                        worksheet.write(row, i, '')
                    row = row-1

            row += 1

        # cleanup
        for i in range(col):
            worksheet.write(row, i, ' ')

        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row))

        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-CONV-{}.xlsx'.format(filename,filename,m)
                check_or_create_file(output_path)
                wb, ws = self.create_sheet(output_path)
                ws = self.write_header(ws,m, dest)
                ws = self.write_table_data(ws,m, dest)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError


class PENTAGON(object):
    def __init__(self, file):
        self.file = file
        self.table_data = []
        self.output_format = None
        self.table = []
        self.days = []
        self.headers = []
        self.month = []
        self.year = []
        self.advertiser = []
        self.brand =[]
        self.ronumber = []
        self.nsheets = 0
        self.sheetnames = []

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        self.nsheets = book.nsheets
        self.sheetnames = book.sheet_names()
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        for i in range(book.nsheets):
            sh = book.sheet_by_index(i)
            table_start = None
            table_data = []
            prev_row = []
            month_row = []
            for rx in range(sh.nrows):
                row_data = sh.row(rx)
                row_value = []
                ind = 0
                for r in row_data:
                    ind += 1
                    v = r.value
                    row_value.append(v)
                    if type(v)is str and (v.lower().strip() == "channel"):
                        table_start = True
                    if type(v)is str and (v.lower().strip()=='total') and ind==1:
                        table_start = False
                        break
                    if type(v) is str and v.strip().lower()[0:6] == "client":
                        self.advertiser.append(v.split(":")[1].strip().title() if ":" in v else row_data[ind].value.strip().title())
                    if type(v) is str and v.strip().lower()[0:7] == "product":
                        self.brand.append(v.split(":")[1].strip().title() if ":" in v else row_data[ind].value.strip().title())
                    if type(v) is str and v.strip().lower()[0:5] == "ro no":
                        self.ronumber.append(v.split(":")[1].strip().title() if ":" in v else row_data[ind].value.strip().title())

                if table_start:
                    table_data.append(row_value)
            headers = []
            t_data = []
            max_days = 0
            for r in range(len(table_data)):
                if r == 0:
                    data = table_data[r]
                    start = False
                    for d in data:
                        if d:
                            start = True
                        if start:
                            try:
                                headers.append(d.strip())
                            except AttributeError:
                                date = last_f = datetime.datetime(*xlrd.xldate_as_tuple(d, book.datemode))
                                headers.append(date)
                if r  == 1:
                    data = table_data[r]

                if r > 1:
                    data = table_data[r]
                    row_d = collections.OrderedDict()
                    r_ind = 0
                    day_count = 0
                    for d in data:
                        if headers[r_ind]:
                            if isinstance(headers[r_ind], datetime.datetime):
                                if not day_count:
                                    row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind].day: d.strip() if type(d) is str else d})
                                else:
                                    row_d['Day wise Slots'][headers[r_ind].day] = d.strip() if type(d) is str else d

                                day_count += 1
                            elif headers[r_ind] == "Channel / Program" and not d:
                                row_d[headers[r_ind]] = table_data[r][0]
                            else:
                                row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                            r_ind += 1

                    if len(row_d)>1:
                        t_data.append(row_d)
                        max_date = max(row_d['Day wise Slots'].keys())
                        max_days = max_date if max_date>max_days else max_days
            # print("rows : {}".format(len(t_data)))
            # print(headers)
            print(len(t_data))
            self.headers.append(headers)
            self.table_data.append(t_data)
            self.month.append(month_row)
            self.year.append("")
            self.days.append(max_days)

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        # print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(int(days)):
                    worksheet.write(row, col, i+1)
                    col+=1
        return worksheet

    def write_table_data(self, worksheet, dest, r):

        row = 1
        table_data = self.table_data[r]

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Spot']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "Total")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        if ":" not in val:
                            val = val[0:2]+":"+val[2:7]+":"+val[7:]
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        if ":" not in val:
                            val = val[0:2] + ":" + val[2:7] + ":" + val[7:]
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Net Rate/']

                        if val != "nan" and float(val)>0:
                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if type(val)==float or type(val)==int or ( val != "nan" and val.isdigit()):
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        for i in range(int(self.days[r])):
                            if i+1 in val:
                                worksheet.write(row, col, val[i+1])
                            else:
                                worksheet.write(row, col, '')
                            col += 1
                    elif item == "Rate":
                        val = table_row_data['Net Rate/']
                        spots = table_row_data['Dur']

                        if type(val) is float or (val != "nan" and val.isdigit()):
                            worksheet.write(row, col, float(val)*10/float(spots))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Net Rate/']
                        if type(val) is float or ( val != "nan" and val.isdigit()):
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
            elif dest=="champ":
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Channel / Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        val = table_row_data['Days']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Amount']

                        if val != "nan":
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Rate 10/Sec']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        raise KeyError
            row += 1
        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row))
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        worksheet.write(row, 0, "Summary")
        row += 1
        worksheet.write(row, 0, "Channel")
        worksheet.write(row, 1, self.sheetnames[r])
        row += 1
        worksheet.write(row, 0, "Advertiser")
        worksheet.write(row, 1, self.advertiser[r])
        row += 1
        worksheet.write(row, 0, "Agency")
        worksheet.write(row, 1, "Pentagon")
        row += 1
        worksheet.write(row, 0, "Brand")
        worksheet.write(row, 1, self.brand[r])
        row += 1
        worksheet.write(row, 0, "RO Number")
        worksheet.write(row, 1, self.ronumber[r])
        row += 1
        worksheet.write(row, 0, "Activity Month")
        worksheet.write(row, 1, "")
        return worksheet

    def generate_output(self, filename, dest):
        files = []
        for r in range(self.nsheets):
            print("sheet {}".format(r))
            if self.table_data[r]:
                output_path = '/tmp/{}/{}-CONV.xlsx'.format(filename, self.sheetnames[r])
                check_or_create_file(output_path)

                wb, ws = self.create_sheet(output_path)
                ws = self.write_header(ws,self.days[r], dest)
                ws = self.write_table_data(ws, dest, r)
                wb.close()
                files.append(output_path)
            else:
                raise FileNotFoundError
        return files


class HAVAS(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        prev_row = []
        month_row = []
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            for r in row_data:
                v = r.value
                row_value.append(v)
                if type(v)is str and (v.strip() == "Channels" or v.strip() == "channels"):
                    table_start = True
                if type(v)is str and ("total" in v.lower()):
                    table_start = False
            prev_row = row_value
            if table_start:
                table_data.append(row_value)
        print(table_data)
        headers = []
        t_data = []
        self.days = 0
        channel = ''
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                for d in data:
                    if d:
                        start = True
                    if start:
                        headers.append(d)
                    if type(d) is float or type(d) is int:
                        self.days += 1
            if r == 1:
                # channel name
                data = table_data[r]
                channel = data[0]

            if r > 1:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if headers[r_ind]:
                        if type(headers[r_ind]) is float or type(headers[r_ind]) is int:
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind]: d.strip() if type(d) is str else d})
                            else:
                                row_d['Day wise Slots'][headers[r_ind]] = d.strip() if type(d) is str else d
                            day_count += 1
                        elif headers[r_ind] == "Channels" and not d:
                            row_d[headers[r_ind]] = channel
                        else:
                            row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                        r_ind += 1
                if len(row_d)>1:
                    t_data.append(row_d)
        print("rows : {}".format(len(t_data)))
        print(headers)
        print(t_data)
        self.headers = headers
        self.table_data = t_data
        self.month = month_row
        self.year = ""

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                d = self.table_data[0]['Day wise Slots']
                for i in d:
                    worksheet.write(row, col, i)
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        worksheet.write(row, col, '')
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Days']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time Band'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['NPTS']

                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "Total Spots":
                        val = table_row_data['# Spots']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "FCT":
                        spots = table_row_data['FCT']
                        worksheet.write(row, col, spots)
                        col += 1
                    elif item == "Rate":
                        val = table_row_data['NPTS']

                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['NPTS']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Cost":
                        val = table_row_data['COST']
                        worksheet.write(row, col, val)
                        col += 1
                    else:
                        raise KeyError
            elif dest=="champ":
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Channel / Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        val = table_row_data['Days']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Amount']

                        if val != "nan":
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Rate 10/Sec']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        raise KeyError
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            wb, ws = self.create_sheet(filename)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        else:
            raise FileNotFoundError


class BEI(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        prev_row = []
        month_row = []
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            ind = 0
            for r in row_data:
                v = r.value
                row_value.append(v)
                if type(v)is str and (v.strip() == "CHANNEL" or v.strip() == "CHANNEL"):
                    table_start = True
                    # print(row_data)
                if type(v)is str and ("total" in v.lower()) and ind==0:
                    table_start = False
                ind += 1
            prev_row = row_value
            if table_start:
                table_data.append(row_value)
        print(table_data)
        headers = []
        t_data = []
        self.days = 0
        channel = ''
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                for d in data:
                    if d:
                        start = True
                    if start:
                        headers.append(d)
                    if type(d) is float or type(d) is int:
                        self.days += 1
            if r == 1:
                data = table_data[r]
                start = False
                ind = 0
                for d in data:
                    if d:
                        start = True
                    if start:
                        headers.append(d)
                    if type(d) is float or type(d) is int:
                        self.days += 1
                        headers[ind] = d
                    ind += 1

            if r > 2:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                day_count = 0
                for d in data:
                    if headers[r_ind]:
                        if type(headers[r_ind]) is float or type(headers[r_ind]) is int:
                            if not day_count:
                                row_d['Day wise Slots'] = collections.OrderedDict({headers[r_ind]: d.strip() if type(d) is str else d})
                            else:
                                row_d['Day wise Slots'][headers[r_ind]] = d.strip() if type(d) is str else d
                            day_count += 1
                        elif headers[r_ind] == "Channels" and not d:
                            row_d[headers[r_ind]] = channel
                        else:
                            row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                        r_ind += 1
                if len(row_d)>1:
                    t_data.append(row_d)
        print(headers)
        print(t_data)
        self.headers = headers
        self.table_data = t_data
        self.month = month_row
        self.year = ""

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                d = self.table_data[0]['Day wise Slots']
                for i in d:
                    worksheet.write(row, col, i)
                    col += 1

        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['CAPTION/']
                        worksheet.write(row, col, val.strip())
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['CATEGORY']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['DAYS']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['TIME-BAND'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['TIME-BAND'].replace(' ', "")
                        try:
                            worksheet.write(row, col, '')
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['RATE (NET)/']

                        if val != "nan" or float(val) > 0:
                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['DUR./EDIT']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "Total Spots":
                        val = table_row_data['# SPOTS']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "FCT":
                        spots = table_row_data['FCT (SEC)']
                        worksheet.write(row, col, spots)
                        col += 1
                    elif item == "Rate":
                        val = table_row_data['RATE (NET)/']

                        if val != "nan":
                            print(val)
                            worksheet.write(row, col, float(val))

                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['RATE (NET)/']
                        dur = table_row_data['DUR./EDIT']

                        if val != "nan":
                            worksheet.write(row, col, float(val*dur/10))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Cost":
                        val = table_row_data['TOTAL COST (NET)/']
                        worksheet.write(row, col, val)
                        col += 1
                    else:
                        raise KeyError
            elif dest=="champ":
                for item in headers:
                    if item == "Ad Copy Id":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Program/Time Band":
                        val = table_row_data['Channel / Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Days":
                        val = table_row_data['Days']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Isolation Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Paid/ Bonus":
                        val = table_row_data['Amount']

                        if val != "nan":
                            worksheet.write(row, col, "Y")
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Length":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        for i in val:
                            worksheet.write(row, col, val[i])
                            col += 1
                    elif item == "LINE RATE":
                        val = table_row_data['Rate 10/Sec']
                        if val != "nan":
                            worksheet.write(row, col, (float(val)))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Month":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Act Year":
                        worksheet.write(row, col, self.year)
                        col += 1
                    else:
                        raise KeyError
            row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:
            wb, ws = self.create_sheet(filename)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        else:
            raise FileNotFoundError


class DDB(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(0)
        table_start = None
        table_data = []
        prev_row = []
        month_row = []
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            ind = 0
            valid = False
            for r in row_data:
                v = r.value

                row_value.append(v)
                if type(v)is str and (v.strip() == "Program" or v.strip() == "Program"):
                    table_start = True
                    # print(row_data)
                if type(v)is str and ("total" in v.lower()) and ind==0:
                    table_start = False
                ind += 1
                if type(v)is float or type(v)is int or v.strip():
                    valid = True
            if table_start and valid:
                table_data.append(row_value)
        print(table_data)
        headers = []
        t_data = []
        self.days = 0
        channel = ''
        for r in range(len(table_data)):
            if r == 0:
                data = table_data[r]
                start = False
                for d in data:
                    if d:
                        start = True
                    if start:
                        headers.append(d)
                    if type(d) is float or type(d) is int:
                        self.days += 1
            if r == 1:
                data = table_data[r]
                start = False
                ind = 0
                for d in data:
                    if d:
                        start = True
                    if start:
                        headers[ind] += ' {}'.format(d)

                    ind += 1

            if r >= 3:
                data = table_data[r]
                row_d = collections.OrderedDict()
                r_ind = 0
                for d in data:
                    if headers[r_ind].strip():
                        if headers[r_ind].strip()=='Schedule':
                            if d != "nan":
                                day_wise = d.split(", ")
                                row_d['Day wise Slots'] = collections.OrderedDict()
                                for d in day_wise:
                                    d = d.replace("(", "|").replace(")", "|")
                                    day = d.split("|")[0]
                                    day_wise_num_slots = d.split("|")[1]
                                    row_d['Day wise Slots'][day] = day_wise_num_slots
                                    print(day, day_wise_num_slots)
                        elif headers[r_ind] == "Channels" and not d:
                            row_d[headers[r_ind]] = channel
                        else:
                            row_d[headers[r_ind]]= d.strip() if type(d) is str else d
                    r_ind += 1
                if len(row_d)>1:
                    t_data.append(row_d)

        headers = [h for h in headers if h.strip()]

        print(headers)
        print(t_data)

        self.headers = headers
        self.table_data = t_data
        self.month = month_row
        self.year = ""

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        return workbook ,worksheet

    def write_header(self, worksheet, days, dest):
        print(days)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(31):
                    worksheet.write(row, col, i+1)
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, dest):

        row = 1
        table_data = self.table_data

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            col = 0
            if dest=="broadview":
                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        worksheet.write(row, col, val.strip())
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Program']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":
                        val = table_row_data['Day']
                        worksheet.write(row, col, val)
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time'].replace(' ', "")
                        try:
                            worksheet.write(row, col, '')
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        val = table_row_data['Gross Rate/10']

                        if val != "nan" or float(val) > 0:
                            worksheet.write(row, col, 'Y')
                        else:
                            worksheet.write(row, col, "N")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, int(val))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Day wise Slots"]
                        # print(val)
                        base_col = col
                        for i in val:
                            col = base_col + int(i) - 1
                            worksheet.write(row, col, val[i])
                        col = base_col+31
                    elif item == "Rate":
                        val = table_row_data['Net Rate/10']

                        if val != "nan":
                            print(val)
                            worksheet.write(row, col, float(val))

                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Rate as per duration":
                        val = table_row_data['Net Rate/10']
                        dur = table_row_data['Dur']

                        if val != "nan":
                            worksheet.write(row, col, float(val*dur/10))
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
            row += 1
            # total spot
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col-5), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col-5), 2,
                                                             base_10_to_alphabet(col-5), row))
            # total fct
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                             base_10_to_alphabet(col - 4), row))
            # total cost
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 1), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 1), 2,
                                                             base_10_to_alphabet(col - 1), row))
            row+=1

        # cleanup
        for i in range(col):
            worksheet.write(row, i, ' ')

        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        return worksheet

    def generate_output(self, filename, dest):
        if self.table_data:

            output_path = '/tmp/{}/{}-CONV.xlsx'.format(filename, filename)
            check_or_create_file(output_path)

            wb, ws = self.create_sheet(output_path)
            ws = self.write_header(ws,self.days, dest)
            ws = self.write_table_data(ws, dest)
            wb.close()
            return True
        else:
            raise FileNotFoundError


class FULCRUM(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None
        self.months = []
        self.advertiser = None
        self.agency = None
        self.brand = None
        self.ronumber = None
        self.channel = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        # read the first sheet data
        sh = book.sheet_by_index(0)
        table_start = False
        table_data = []
        top_table = []
        prev_row = []
        month_row = []
        i_hit_a_table = False
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            ind = 0
            for r in row_data:
                v = r.value
                row_value.append(v)
                if type(v)is str and (v.lower().strip() == "date") and row_data[ind+1].value.lower().strip()=="programname":
                    table_start = True
                    i_hit_a_table = True
                if type(v)is str and (v.lower().strip()=='') and ind==0 and table_start:
                    table_start = False
                    break
                ind+=1
            if table_start:
                table_data.append(row_value)

            if not table_start and not i_hit_a_table:
                top_table.append(row_value)
        headers = table_data[0]
        top_table_headers = []
        for r in range(len(top_table)):
            top_table_headers.append(top_table[r][10])
        print(top_table_headers, headers[0:11])
        t_data = []
        self.days = 0
        max_days = 0
        for r in range(len(table_data)):
            if r > 0:
                data = table_data[r]
                row_d = []
                r_ind = 0
                day_count = 0
                for dind in range(len(data)):
                    d = data[dind]
                    if dind>10 and d:
                        # print(d)
                        tmp_row = {}
                        for i in range(11):
                            if headers[i].lower() not in ["start time", "end time"]:
                                tmp_row[headers[i]] = data[i].strip() if type(data[i]) is str else data[i]
                            else:
                                tmp_row[headers[i]] = data[i]*24 if type(data[i]) is float else data[i]

                        for i in range(len(top_table)):
                            # print(top_table[i][dind])
                            if top_table_headers[i]:
                                tmp_row[top_table_headers[i]] = top_table[i][dind]
                        tmp_row['Spots'] = d
                        t_data.append(tmp_row)
                        if tmp_row['Date'] not in row_d:
                            row_d.append(tmp_row['Date'])
                        last_f = datetime.datetime(*xlrd.xldate_as_tuple(tmp_row['Date'], book.datemode))
                        tmp_row['Date'] = last_f
                        if last_f and last_f.month:
                            if last_f.month not in self.months:
                                self.months.append(last_f.month)
                                self.year=last_f.year

                    r_ind += 1

                if len(row_d)>1:
                    t_data.append(row_d)
                    max_date = max(row_d)
                    max_days = max_date if max_date>max_days else max_days
        print("rows : {}".format(len(t_data)))
        print(self.months)

        self.headers = headers
        self.table_data = t_data
        # self.year = ""
        self.days = max_days

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        ws1 = workbook.add_worksheet("Sheet 1")
        ws2 = workbook.add_worksheet("Sheet 2")
        return workbook, [ws1,ws2]

    def write_header(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(2019, month)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband",
                       "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i+1)
                    col+=1
        return worksheet

    def write_header2(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(self.year, month)
        row = 0
        col = 0
        if dest=="broadview":
            headers = ["Brand", "Caption", "IB No", 'Start Date', "End Date", "Programme", "Day", "Timeband",
                       "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i+1)
                    day = calendar.day_name[datetime.date(year=self.year, month=month, day=i + 1).weekday()]
                    worksheet.write(row + 1, col, day[0:3])
                    col+=1
        return worksheet

    def write_table_data(self, worksheet, month, dest):
        (s, l) = calendar.monthrange(2019, month)
        row = 1
        table_data = self.table_data
        col_data_map = []

        if dest=="broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            airdate = table_row_data["Date"]
            slots = table_row_data['Spots']
            start_time = "{0:02d}:00".format(int(table_row_data['Start Time']))
            end_time = "{0:02d}:00".format(int(table_row_data['End Time']))
            if (table_row_data['Start Time']*2)%2==1:
                start_time = "{0:02d}:30".format(int(table_row_data['Start Time']))
            if (table_row_data['End Time']*2)%2==1:
                end_time = "{0:02d}:30".format(int(table_row_data['End Time']))
            key = [table_row_data['Commercial Name'], table_row_data['ProgramName'],
                   "{}-{}".format(start_time, end_time),
                   table_row_data['Dur']]
            if key not in col_data_map:
                col_data_map.append(key)
                row = len(col_data_map)
            else:
                row = col_data_map.index(key)+1
            date = airdate.date()
            if date.month != month:
                continue
            col = 0
            if dest=="broadview":

                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Commercial Name']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['ProgramName']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":

                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = "{}-{}".format(start_time, end_time)
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = "{}-{}".format(start_time, end_time)
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Date"]
                        slots = table_row_data["Spots"]
                        date = val.date()
                        if date.month == month:
                            worksheet.write(row, col + date.day - 1, int(slots))
                        col += l
                    elif item == "Rate":

                        worksheet.write(row, col, 0.0)
                        col += 1
                    elif item == "Rate as per duration":

                        worksheet.write(row, col, 0.0)

                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
        row = len(col_data_map) + 1
        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row))
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        return worksheet

    def write_table_data2(self, worksheet, month, dest, book):
        (s, l) = calendar.monthrange(2019, month)
        row = 1
        table_data = self.table_data
        col_data_map = []

        if dest=="broadview":
            headers = ["Brand", "Caption", "IB No", 'Start Date', "End Date", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest=="champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            airdate = table_row_data["Date"]
            slots = table_row_data['Spots']
            start_time = "{0:02d}:00".format(int(table_row_data['Start Time']))
            end_time = "{0:02d}:00".format(int(table_row_data['End Time']))
            if (table_row_data['Start Time']*2)%2==1:
                start_time = "{0:02d}:30".format(int(table_row_data['Start Time']))
            if (table_row_data['End Time']*2)%2==1:
                end_time = "{0:02d}:30".format(int(table_row_data['End Time']))
            key = [table_row_data['Commercial Name'], table_row_data['ProgramName'],
                   "{}-{}".format(start_time, end_time),
                   table_row_data['Dur']]
            if key not in col_data_map:
                col_data_map.append(key)
                row = len(col_data_map)+1
            else:
                row = col_data_map.index(key)+2
            date = airdate.date()
            if date.month != month:
                continue
            col = 0
            if dest=="broadview":

                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Commercial Name']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Brand":
                        val = table_row_data['Brand Name']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "IB No":
                        val = table_row_data['IB No']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Start Date":
                        val = table_row_data['Start Date']
                        cell_format1 = book.add_format()
                        cell_format1.set_num_format('dd/mm/yyyy')  # Format string.
                        if val != "nan":
                            worksheet.write(row, col, val, cell_format1)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "End Date":
                        val = table_row_data['End Date']
                        cell_format1 = book.add_format()
                        cell_format1.set_num_format('dd/mm/yyyy')  # Format string.
                        if val != "nan":
                            worksheet.write(row, col, val, cell_format1)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['ProgramName']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":

                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = "{}-{}".format(start_time, end_time)
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Requested Timeband":
                        val = "{}-{}".format(start_time, end_time)
                        try:
                            worksheet.write(row, col, val)
                        except IndexError:
                            print(val)
                        col += 1
                    elif item == "Value":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Dur']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Date"]
                        slots = table_row_data["Spots"]
                        date = val.date()
                        if date.month == month:
                            worksheet.write(row, col + date.day - 1, int(slots))
                        col += l
                    elif item == "Rate":

                        worksheet.write(row, col, 0.0)
                        col += 1
                    elif item == "Rate as per duration":

                        worksheet.write(row, col, 0.0)

                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
        row = len(col_data_map) + 2
        for cl in range(12, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row))
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        return worksheet

    def generate_output(self, filename, dest):
        print(self.months)
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-CONV-{}.xlsx'.format(filename, filename, m)
                check_or_create_file(output_path)
                wb, [ws1, ws2] = self.create_sheet(output_path)
                ws1 = self.write_header(ws1, m, dest)
                ws1 = self.write_table_data(ws1, m, dest)
                ws2 = self.write_header2(ws2, m, dest)
                ws2 = self.write_table_data2(ws2, m, dest, wb)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError


class VINI(object):
    def __init__(self, file):
        self.file = file
        self.table_data = None
        self.output_format = None
        self.table = None
        self.days = None
        self.headers = None
        self.months = []
        self.advertiser = None
        self.agency = None
        self.brand = None
        self.ronumber = None
        self.channel = None

    def get_table(self, format='csv'):
        book = xlrd.open_workbook(self.file)
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        # read the first sheet data
        sh = book.sheet_by_index(0)
        table_start = False
        table_data = []
        top_table = []
        prev_row = []
        month_row = []
        for rx in range(sh.nrows):
            row_data = sh.row(rx)
            row_value = []
            ind = 0
            i_hit_a_table = False
            for r in row_data:
                v = r.value
                row_value.append(v)
                # print(v)
                if type(v) is str and (v.lower().strip() == "programme") and row_data[ind + 1].value.lower().strip() == "day":
                    table_start = True
                    i_hit_a_table = True
                if type(v) is str and (v.lower().strip() == '') and ind == 0 and table_start:
                    table_start = False
                    ind += 1
                    break
                ind += 1

            if table_start and not i_hit_a_table:
                table_data.append(row_value)
            elif i_hit_a_table:
                headers = row_value


            # if not table_start and not i_hit_a_table:
            #     top_table.append(row_value)
        top_table_headers = []
        for r in range(len(top_table)):
            top_table_headers.append(top_table[r][10])
        # print(table_data)
        t_data = []
        self.days = 0
        max_days = 0
        row_d = []
        for r in range(len(table_data)):
            if r >= 0:
                data = table_data[r]
                # print(data)
                tmp_row = {}
                for i in range(12):
                    # print(headers[i].lower(), data[i])
                    if headers[i].lower() not in ["time", "date"]:
                        tmp_row[headers[i]] = data[i].strip() if type(data[i]) is str else data[i]
                    elif headers[i].lower() == "date":
                        print(data[i])
                        last_f = datetime.datetime.strptime(tmp_row['Month'].replace(" ",""),"%B'%Y")
                        # print(last_f)
                        last_f = last_f.replace(day=int(data[i]))
                        tmp_row[headers[i]] = last_f
                        if last_f.month not in self.months:
                            self.months.append(last_f.month)
                            self.year = last_f.year
                    else:
                        tmp_row[headers[i]] = data[i].strip().replace(" ", "")
                if tmp_row['Date'] not in row_d:
                    row_d.append(tmp_row['Date'])
                t_data.append(tmp_row)

        # if len(row_d) > 1:
        #     max_date = max(row_d)
        #     max_days = max_date if max_date > max_days else max_days
        print("rows : {}".format(len(t_data)))
        print(self.months)

        self.headers = headers
        self.table_data = t_data
        # self.year = ""
        # self.days = max_days

    def create_sheet(self, filename):
        workbook = xlsxwriter.Workbook(filename)
        ws1 = workbook.add_worksheet("Sheet 1")
        ws2 = workbook.add_worksheet("Sheet 2")
        return workbook, [ws1, ws2]

    def write_header(self, worksheet, month, dest):
        print("writing header for {} month".format(month))
        (s, l) = calendar.monthrange(2019, month)
        row = 0
        col = 0
        if dest == "broadview":
            headers = ["Caption", "Programme", "Day", "Timeband",
                       "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest == "champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for item in headers:
            if item != "Day wise Slots":
                worksheet.write(row, col, item)
                col += 1
            else:
                for i in range(l):
                    worksheet.write(row, col, i + 1)
                    col += 1
        return worksheet

    def write_table_data(self, worksheet, month, dest):
        (s, l) = calendar.monthrange(2019, month)
        row = 1
        table_data = self.table_data
        col_data_map = []

        if dest == "broadview":
            headers = ["Caption", "Programme", "Day", "Timeband", "Requested Timeband", "Value",
                       "Dur", "Day wise Slots", "Total Spots", "FCT", "Rate", "Rate as per duration", "Total Cost"]
        elif dest == "champ":
            headers = ["Ad Copy Id", "Program/Time Band", "Days", "Timeband", "Isolation Timeband", "Paid/ Bonus",
                       "Length", "Day wise Slots", "LINE RATE", "Act Month", "Act Year"]

        # Iterate over the data and write it out row by row.
        for table_row_data in table_data:
            airdate = table_row_data["Date"]
            key = [table_row_data['Caption'], table_row_data['Programme'],
                   table_row_data['Time'],
                   table_row_data['Duration'], table_row_data['Net Rate / secs']]
            # if key not in col_data_map:
            #     col_data_map.append(key)
            #     row = len(col_data_map)
            # else:
            #     row = col_data_map.index(key) + 1
            # date = airdate.date()
            # if date.month != month:
            #     continue
            col = 0
            if dest == "broadview":

                for item in headers:
                    if item == "Caption":
                        val = table_row_data['Caption']
                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Programme":
                        val = table_row_data['Programme']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Day":

                        val = table_row_data['Day']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Timeband":
                        val = table_row_data['Time']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Requested Timeband":
                        val = table_row_data['Time']

                        if val != "nan":
                            worksheet.write(row, col, val)
                        else:
                            worksheet.write(row, col, "")
                        col += 1
                    elif item == "Value":
                        worksheet.write(row, col, "")
                        col += 1
                    elif item == "Dur":
                        val = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        col += 1
                    elif item == "Day wise Slots":
                        val = table_row_data["Date"]
                        slots = table_row_data["No. Spots"]
                        date = val.date()
                        if date.month == month:
                            worksheet.write(row, col + date.day - 1, int(slots))
                        col += l
                    elif item == "Rate":

                        val = table_row_data['Net Rate / secs']
                        if val != "nan":
                            worksheet.write(row, col, float(val))
                        col += 1
                    elif item == "Rate as per duration":

                        val = table_row_data['Net Rate / secs']
                        dur = table_row_data['Duration']
                        if val != "nan":
                            worksheet.write(row, col, float(val)*float(dur)/10)
                        col += 1
                    elif item == "Total Spots":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(8), row + 1,
                                                                         base_10_to_alphabet(col), row + 1))
                        col += 1
                    elif item == "FCT":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}'.format(base_10_to_alphabet(col), row + 1,
                                                                    base_10_to_alphabet(7), row + 1))
                        col += 1
                    elif item == "Total Cost":
                        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col + 1), row + 1),
                                                '={}{}*{}{}/10'.format(base_10_to_alphabet(col - 1), row + 1,
                                                                       base_10_to_alphabet(col - 2), row + 1))
                        col += 1
                    else:
                        raise KeyError
            row+=1
        for cl in range(8, col - 4):
            worksheet.write_formula('{}{}'.format(base_10_to_alphabet(cl), row + 1),
                                    '=SUM({}{}:{}{})'.format(base_10_to_alphabet(cl), 2,
                                                             base_10_to_alphabet(cl), row))
        # total spot
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 4), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 4), 2,
                                                         base_10_to_alphabet(col - 4), row))
        # total fct
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col - 3), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col - 3), 2,
                                                         base_10_to_alphabet(col - 3), row))
        # total cost
        worksheet.write_formula('{}{}'.format(base_10_to_alphabet(col), row + 1),
                                '=SUM({}{}:{}{})'.format(base_10_to_alphabet(col), 2,
                                                         base_10_to_alphabet(col), row))
        row += 1
        return worksheet

    def generate_output(self, filename, dest):
        print(self.months)
        if self.table_data and self.months:
            files = []
            for m in self.months:
                output_path = '/tmp/{}/{}-CONV-{}.xlsx'.format(filename, filename, m)
                check_or_create_file(output_path)
                wb, [ws1, ws2] = self.create_sheet(output_path)
                ws1 = self.write_header(ws1, m, dest)
                ws1 = self.write_table_data(ws1, m, dest)
                wb.close()
                files.append(output_path)
            return files
        else:
            raise FileNotFoundError
