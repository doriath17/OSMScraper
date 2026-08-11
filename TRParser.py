from html.parser import HTMLParser

class TRParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tr = False
        self.current_row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.in_tr = True
            self.current_row = []
        elif tag == 'td' and self.in_tr:
            self.current_row.append('')

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.in_tr = False
            # Only append non-empty rows
            if self.current_row:
                self.rows.append(self.current_row)

    def handle_data(self, data):
        if self.in_tr and self.current_row:
            text = data.strip()
            if text:
                # If cell is currently empty, set text; otherwise append with space
                if not self.current_row[-1]:
                    self.current_row[-1] = text
                else:
                    self.current_row[-1] += f" {text}"

# class TRParser(HTMLParser):
#     def __init__(self):
#         super().__init__()
#         self.in_tr = False
#         self.current_row = []
#         self.rows = []

#     def handle_starttag(self, tag, attrs):
#         if tag == 'tr':
#             self.in_tr = True
#             self.current_row = []
#         elif tag == 'td' and self.in_tr:
#             self.current_row.append('')

#     def handle_endtag(self, tag):
#         if tag == 'tr':
#             self.in_tr = False
#             self.rows.append(self.current_row)
#         elif tag == 'td' and self.in_tr:
#             pass

#     def handle_data(self, data):
#         if self.in_tr and self.current_row is not None:
#             if len(self.current_row) > 0:
#                 self.current_row[-1] += data.strip()