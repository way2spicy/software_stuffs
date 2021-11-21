import pandas as pd
import requests
from bs4 import BeautifulSoup
from uszipcode import SearchEngine


class Compass:
    def __init__(self, zipcode):
        """
        __init__ function creates the main URL needed to parse by zipcode
        :param zipcode:
            param type = text
            details = zipcode of state / area
        """

        self.error_flag = 0
        self.zipcode = zipcode
        # Zipcode, City, State acquisition for home url
        self.search = SearchEngine(simple_zipcode=True)  # set simple_zipcode=False to use rich info database
        self.zipcode_s = self.search.by_zipcode(zipcode)  # acquires information from user-entered zipcode.
        dict_zip = self.zipcode_s.to_dict()

        if dict_zip.get('zipcode') != zipcode:
            print('Entered zipcode does not exist, please check input')
            self.error_flag = 1
            return
        else:
            print(dict_zip.get('zipcode'))
            self.html_raw = 'https://www.compass.com/homes-for-sale/' + dict_zip.get('major_city') + '-' + dict_zip.get(
                'state') + '-' + dict_zip.get('zipcode')
            self.html = self.html_raw.replace(" ", "-")
        print(f'Zipcode URL: {self.html}')

        # Use home html url to parse home page containing all apartments in that zip code

        self.source = requests.get(self.html).text
        self.soup = BeautifulSoup(self.source, 'lxml')

        try:
            bad = self.soup.find_all('div', class_='error-caption')
            for error in bad:
                error = error.text.strip()
                if error == 'Let us point you in a better direction.':
                    self.error_flag = 1
                    print('Homepage error, please check if zip code is searchable in compass.com')
        except:
            print('Home page checks out! Moving on')

    @staticmethod
    def compass_table(table):
        '''
        Grab online information and append it into a table (not a db). Returns two lists, 'data' (information
        grabbed online) and 'data_title' (the header for each of these lists).
        :param table:
        :return:
        '''

        # initialize two lists for table data / headers
        data_title = []
        data = []
        # # summary_title = []
        # summary = []

        data_title_list = table.find_all('th')
        data_list = table.find_all('td')

        for title in data_title_list:
            data_title.append(title.text)

        for data_tag in data_list:
            data.append(data_tag.text)

        results = dict(zip(data_title, data))
        return data_title, data

    def compass_table_db(self, link=None):
        '''
        Create a db table of all the information we're scraping from beautiful soup. Literally just makes the information
        easier to manipulate being in a db (for me at least).
        :param link:
        :return:
        '''

        dbData = pd.DataFrame()
        # Parse table from self.soup. Acquire all th (header) and td (data) information
        if link == 'list':
            table = self.soup.find('table')
            data_title, data = self.compass_table(table)
            dbData = dbData.append([data_title, data])
        else:
            url_list = self.compass_urls()
            gap = []
            for htmls in url_list:  # loop through HTML list provided
                source = requests.get(htmls).text
                soup = BeautifulSoup(source, 'lxml')
                table = soup.find('table')
                data_title, data = self.compass_table(table)
                # list values appended to go into pandas DB for excel export
                data_title.extend(['Link:', ''])
                data.extend([htmls, ''])
                dbData = dbData.append([data_title, data, gap])

        return dbData

    def excel_list(self, output_name=None):
        """
        generate and parse through a list of URLs for houses in a specific zip code (defined by our main URL in
        __init__)
         :param output_name: (str) .xlsx output file name definition. If not provided, '{zip}.xlsx' will be used.
        """

        if self.error_flag == 1:
            return

        dbData = self.compass_table_db()
        if output_name is None:
            output_name = self.zipcode + '.xlsx'
        else:
            pass

        print('Outputting information to excel')
        writer = pd.ExcelWriter(output_name, engine='xlsxwriter')  # excel output file, defining engine xlsxwriter
        # dbData = dbData.transpose()  # transpose db so it's vertical on excel
        dbData.to_excel(writer, sheet_name='Data')  # actual output to Excel
        writer.save()  # save file
        print(f'File created and outputted as {output_name}')

    def compass_urls(self):
        '''
        method used to acquire a list of excel sheets from the home page
        of compass.com after selecting a zone/ZIP code.
        :return: url_list <-- a list of URL's from the page selected.
        '''

        print('Acquiring URLs, please hold...')
        url_list = []  # define empty list to fill all URL's in
        main = self.soup.find('main')
        # print(main.prettify())
        ref = main.find_all('a', class_='uc-listingPhotoCard uc-listingCard uc-listingCard-has-photo', href=True)
        for a in ref:
            lim = a['href']
            url = 'https://www.compass.com' + lim
            url_list.append(url)
            # print(url)

        print(f'{len(url_list)} URLs acquired! Parsing each one, stand by...')
        return url_list


# Run main functions below
Lakeview = Compass('90250')
California = Compass('90278')
Lakeview.excel_list()
