from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys, getopt, time, io, string, re, random, os
import urllib.request, bs4
import multiprocessing
import pickle


def check_proxy(proxy_a):
    page_url = "http://trendstop.knack.be/nl/sector.aspx"
    proxy_support = urllib.request.ProxyHandler({'http' : proxy_a})
    opener = urllib.request.build_opener(proxy_support)
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0')]
    try:
        page_html = opener.open(page_url, timeout=5).read()
        page_soup = bs4.BeautifulSoup(page_html)
        if len(page_soup.find_all('ul', {'class':'sector-list hidden'})) == 22:
            return proxy_a
    except:
        pass


def filter_proxy(proxy_list):
    selected_proxy_list = []

    pool = multiprocessing.Pool(processes=in_cpu_num)
    results = pool.map(check_proxy, proxy_list)
    pool.close()
    pool.join()

    for result in results:
        if result is not None:
            selected_proxy_list.append(result)

    return selected_proxy_list


def retrieve_new_proxy_list():
    global Proxy_List

    print("\nAcquiring proxy list!")

    proxy_list = []

    for page_count in range(1, 4):
        page_url = "http://www.getproxy.jp/en/fastest/" + str(page_count)
        page_html = urllib.request.urlopen(page_url, timeout=15).read()
        page_soup = bs4.BeautifulSoup(page_html)

        proxy_elements = page_soup.find('table', {'id' : 'mytable'}).find_all('td', style=re.compile('left'))

        for element in proxy_elements:
            proxy_list.append(element.get_text().strip())

    print("\nFiltering proxy list!")

    Proxy_List = filter_proxy(proxy_list)
    print(Proxy_List)


def write_to_csv_file(input_list, output_file, opt):
    delimiter = ','
    quote = '"'
    antiquote = "'"
    string = ""
    for count in range(0, len(input_list)):
        if count == 0:
            string += quote
        string += str(input_list[count]).replace(quote, antiquote)
        if count != len(input_list)-1:
            string += quote + delimiter + quote
        else:
            string += quote
    print(string)
    with io.open(output_file, opt, encoding='utf8') as f:
        f.write(string + "\n")


def extract_info_from_profile_page(arg):
    profile_page_url, output_file, out_pck = arg

    attempt = 0
    flag = 0
    while attempt < 3:
        try:
            if in_http_proxy != '':
                if in_http_proxy == '0':
                    service_args = [ '--proxy=' + random.choice(Proxy_List), '--proxy-type=http' ]
                else:
                    service_args = [ '--proxy=' + in_http_proxy, '--proxy-type=http' ]
                driver = webdriver.PhantomJS(service_args=service_args)
            else:
                driver = webdriver.PhantomJS()
            driver.set_page_load_timeout(60)
            driver.get(profile_page_url)
            flag = 0
            break
        except:
            try:
                driver.quit()
            except:
                pass
            time.sleep(1)
            attempt += 1
            flag = 1

    if flag == 1:
        print("Opening PhantomJS with proxy failed!")
        driver.quit()
        return 0

    if in_http_proxy != '':
        if in_http_proxy == '0':
            proxy_support = urllib.request.ProxyHandler({'http' : random.choice(Proxy_List)})
        else:
            proxy_support = urllib.request.ProxyHandler({'http' : in_http_proxy})
        opener = urllib.request.build_opener(proxy_support)
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0')]

    attempt = 1
    flag = 0
    while attempt < 10:
        try:
            print("\n>> Attempt " + str(attempt) + ": " + profile_page_url)
            driver.get(profile_page_url)
            
            str_xpath = "//nav//a[contains(text(), 'Info')][contains(@href, 'detail')]"
            if driver.find_element_by_xpath(str_xpath).get_attribute('class') != 'active':
                driver.find_element_by_xpath(str_xpath).click()
            
            str_xpath = "//div[@id='general-details']//th[contains(text(), 'Sector')]/../td/a"
            WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, str_xpath)))
            flag = 0
            break
        except:
            time.sleep(1)
            attempt += 1
            flag = 1

    if flag == 1:
        driver.quit()
        return 0

    Adres = Website = Email = Statutaire_Naam = Juridische_Toestand = Ondernemingsnr = Oprichtingsdatum = Telefoon = Fax = Sector = Nacebel = B2B_gericht = B2C_gericht = ""

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Adres')]/../td"
    Adres = driver.find_element_by_xpath(str_xpath).text.strip()
    Adres_Straat = ', '.join(Adres.splitlines()[0:len(Adres.splitlines())-1]).strip()
    Adres_Postcode = Adres.splitlines()[len(Adres.splitlines())-1].split()[0].strip()
    Adres_Stad = ' '.join(Adres.splitlines()[len(Adres.splitlines())-1].split()[1:]).strip()

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Website')]/../td"
    try:
        Website = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'E-mail')]/../td"
    try:
        Email = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Statutaire naam')]/../td"
    try:
        Statutaire_Naam = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Juridische toestan')]/../td"
    try:
        Juridische_Toestand = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Ondernemingsnr')]/../td"
    try:
        Ondernemingsnr = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Oprichtingsdatum')]/../td"
    try:
        Oprichtingsdatum = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Telefoon')]/../td"
    try:
        Telefoon = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Fax')]/../td"
    try:
        Fax = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Sector')]/../td/a"
    try:
        Sector = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'Nacebel')]/../td"
    try:
        Nacebel = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'B2B-gericht')]/../td"
    try:
        B2B_gericht = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    str_xpath = "//div[@id='general-details']//th[contains(text(), 'B2C-gericht')]/../td"
    try:
        B2C_gericht = driver.find_element_by_xpath(str_xpath).text.replace('Mijn gegevens aanpassen', '').strip()
    except:
        pass

    ###

    Plaats_Top_omzet = Plaats_Top_toeg = Plaats_sector_omzet = Plaats_sector_toeg = ""

    str_xpath = "//div[@id='company-ranking']//span[@id='RankList1txt']"
    try:
        Plaats_Top_omzet = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass
    str_xpath = "//div[@id='company-ranking']//span[@id='RankList2txt']"
    try:
        Plaats_Top_toeg = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass
    str_xpath = "//div[@id='company-ranking']//span[@id='RankList3txt']"
    try:
        Plaats_sector_omzet = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass
    str_xpath = "//div[@id='company-ranking']//span[@id='RankList4txt']"
    try:
        Plaats_sector_toeg = driver.find_element_by_xpath(str_xpath).text.strip()
    except:
        pass

    driver.quit()

    ###

    Email_List = []

    if Website != "":
        if 'http://' not in Website:
            page_url = "http://" + Website
        else:
            page_url = Website

        flag = 1
        try:
            page_html = opener.open(page_url, timeout=30).read()
        except:
            flag = 0

        if flag == 1:
            Email_List.extend(re.findall('[\w\-][\w\-\.]+@[\w\-][\w\-\.]+\.[a-zA-Z]{2,4}', str(page_html)))

            page_soup = bs4.BeautifulSoup(page_html)
            contact_page_list = []
            try:
                contact_page_list.extend(page_soup.find_all('a', href=re.compile('[Cc]ontact')))
            except:
                pass
            try:
                contact_page_list.extend(page_soup.find_all('a', href=re.compile('[Kk]ontakt')))
            except:
                pass
            try:
                contact_page_list.extend(page_soup.find_all('a', text=re.compile('[Cc]ontact')))
            except:
                pass
            try:
                contact_page_list.extend(page_soup.find_all('a', text=re.compile('[Kk]ontakt')))
            except:
                pass
            contact_page_list = list(set(contact_page_list))

            for a in contact_page_list:
                flag = 1
                try:
                    url = a['href']
                    if page_url not in url:
                        url = page_url + url
                    if 'http://' not in url:
                        url = 'http://' + url
                except:
                    flag = 0

                if flag == 1:
                    try:
                        page_html = opener.open(url, timeout=30).read()
                        Email_List.extend(re.findall('[\w\-][\w\-\.]+@[\w\-][\w\-\.]+\.[a-zA-Z]{2,4}', str(page_html)))
                    except:
                        continue

            Clean_Email_List = []
            for email in Email_List:
                if email.lower() != Email.lower() and email.lower() not in Clean_Email_List and '.jpg' not in email.lower() and '.png' not in email.lower() and '.gif' not in email.lower() and 'johndoe' not in email.lower() and 'john.doe' not in email.lower() and 'example' not in email.lower():
                    Clean_Email_List.append(email.lower())
            Clean_Email_List.sort()
            Email_List = Clean_Email_List

    ###

    print_list = [ Adres_Straat, Adres_Postcode, Adres_Stad, Website, Email, Statutaire_Naam, Juridische_Toestand, Ondernemingsnr, Oprichtingsdatum, Telefoon, Fax, Sector, Nacebel, B2B_gericht, B2C_gericht, Plaats_Top_omzet, Plaats_Top_toeg, Plaats_sector_omzet, Plaats_sector_toeg, ' | '.join(Email_List) ]

    print()
    write_to_csv_file(print_list, output_file, 'a')

    with open(out_pck, 'ab') as f:
        pickle.dump(profile_page_url, f)
        print(out_pck + ' rewritten!')

    return 1


def extract_sector_url_list(out_pck):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0')]

    url_list = []

    if os.path.isfile(out_pck):
        with open(out_pck, 'rb') as f:
            url_list = pickle.load(f)
    else:
        pass

    if len(url_list) != 307:
        page_url = "http://trendstop.knack.be/nl/sector.aspx"
        page_html = opener.open(page_url).read()
        page_soup = bs4.BeautifulSoup(page_html)

        url_list = []
        ul_list = page_soup.find_all('ul', {'class':'sector-list hidden'})
        for ul in ul_list:
            a_list = ul.find_all('a', {'id':'hl'})
            for a in a_list:
                url_list.append("http://trendstop.knack.be" + a['href'])
        # print(url_list)

        with open(out_pck, 'wb') as f:
            pickle.dump(url_list, f)

    return url_list


def extract_company_profile_url_list(sector_url_list, sector_url_count, out_pck):
    if in_http_proxy != '':
        if in_http_proxy == '0':
            proxy_support = urllib.request.ProxyHandler({'http' : random.choice(Proxy_List)})
        else:
            proxy_support = urllib.request.ProxyHandler({'http' : in_http_proxy})
        opener = urllib.request.build_opener(proxy_support)
    else:
        opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0')]

    attempt = 0
    flag = 0
    while attempt < 3:
        try:
            if in_http_proxy != '':
                if in_http_proxy == '0':
                    service_args = [ '--proxy=' + random.choice(Proxy_List), '--proxy-type=http' ]
                else:
                    service_args = [ '--proxy=' + in_http_proxy, '--proxy-type=http' ]
                driver = webdriver.PhantomJS(service_args=service_args)
            else:
                driver = webdriver.PhantomJS()
            driver.set_page_load_timeout(60)
            page_url = Sector_URL_List[sector_count] + "?page=1"
            driver.get(page_url)
            flag = 0
            break
        except:
            try:
                driver.quit()
            except:
                pass
            time.sleep(1)
            attempt += 1
            flag = 1

    if flag == 1:
        print("Opening PhantomJS with proxy failed!")
        print("Using no proxy instead!")
        driver = webdriver.PhantomJS()
        driver.set_page_load_timeout(60)

    url_list = []
    if os.path.isfile(out_pck):
        with open(out_pck, 'rb') as f:
            url_list = pickle.load(f)
            print("\nContinuing company profile URLs extraction!")
    else:
        print("\nStarting company profile URLs extraction!")

    page_count = int(len(url_list)/10 + 1)
    while 1:
        page_url = Sector_URL_List[sector_count] + "?page=" + str(page_count)
        print("\n>> " + page_url)
        while 1:
            try:
                response = opener.open(page_url, timeout=120)
                break
            except:
                time.sleep(1)
        if response.geturl() != page_url:
            while 1:
                try:
                    driver.get(page_url)
                    if 'sector-ad' in driver.current_url:
                        while 1:
                            try:
                                driver.get(page_url)
                                break
                            except:
                                time.sleep(1)
                    page_html = driver.page_source
                    break
                except:
                    time.sleep(1)
        else:
            page_html = response.read()
        page_soup = bs4.BeautifulSoup(page_html)

        try:
            tr_list = page_soup.find('div', {'id':'companies'}).find_all('tr')
            for tr in tr_list:
                a = tr.find('a', href=re.compile('detail'))
                if a != None and a['href'] not in url_list:
                    url_list.append("http://trendstop.knack.be" + a['href'])
        except:
            continue

        with open(out_pck, 'wb') as f:
            pickle.dump(url_list, f)
            print(out_pck + ' rewritten!')

        try:
            if page_soup.find('td', {'class':'pager'}).find('a', {'id':'PageNext'}) != None:
                page_count += 1
            else:
                break
        except:
            break

    url_list = list(set(url_list))
    with open(out_pck, 'wb') as f:
        pickle.dump(url_list, f)
        print(out_pck + ' DONE!')

    # print(url_list)

    driver.quit()

    return url_list


def usage():
    print("Usage:\n   %s -i sector_index_start[:sector_index_end] [-c concurrent_processes_num] [-p http_proxy:port]" % sys.argv[0])
    print("Note:\n   The sector index ranges from 0 to 306.")
    print("Example:")
    print("   Extracting company profiles from the sector with index 0:\n      %s -i 0" % sys.argv[0])
    print("   Extracting company profiles from the sector with index 20 until 22:\n      %s -i 20:22" % sys.argv[0])
    print("   Extracting company profiles from the sector with index 7 until 10 using 2 concurrent processes:\n      %s -i 7:10 -c 2" % sys.argv[0])
    sys.exit()


if __name__ == "__main__":
    try:
        myopts, args = getopt.getopt(sys.argv[1:],"i:c:p:h")
    except getopt.GetoptError as err:
        print("Error:\n   " + str(err))
        usage()

    in_sector_index_start = ''
    in_sector_index_end   = ''
    try:
        in_cpu_num = multiprocessing.cpu_count()
    except:
        in_cpu_num = 2
    in_http_proxy = ''

    for o, a in myopts:
        if o == '-i':
            list_a = a.split(':')
            if len(list_a) == 2:
                in_sector_index_start = list_a[0]
                in_sector_index_end = str(int(list_a[1])+1)
                if in_sector_index_end <= in_sector_index_start:
                    usage()
            elif len(list_a) == 1:
                in_sector_index_start = list_a[0]
                in_sector_index_end = str(int(in_sector_index_start)+1)
            else:
                usage()
        elif o == '-c':
            in_cpu_num = int(a)
        elif o == '-p':
            in_http_proxy = a
        elif o == '-h':
            usage()
        else:
            usage()

    if in_sector_index_start == '':
        usage()

    if not os.path.isdir('out'):
        os.makedirs('out')

    if not os.path.isdir('pck'):
        os.makedirs('pck')

    if in_http_proxy == '0':
        Proxy_List = []
        retrieve_new_proxy_list()

    print("\nConcurrent processes number: " + str(in_cpu_num) + "!")

    print("\nStarting sector page URLs extraction!")

    pck_Sector_URL_List_filename = 'pck/Sector_URL_List.pck'
    Sector_URL_List = extract_sector_url_list(pck_Sector_URL_List_filename)
    print()
    # print(Sector_URL_List)
    print('## ' + pck_Sector_URL_List_filename + ': ' + str(len(Sector_URL_List)))

    sector_count_start = int(in_sector_index_start)
    sector_count_end   = int(in_sector_index_end)

    for sector_count in range(sector_count_start, sector_count_end):
        csv_output_filename = "out/output_" + str(sector_count) + ".csv"
        pck_Bedrijf_URL_List_filename = 'pck/Bedrijf_URL_List_' + str(sector_count) + '.pck'
        pck_Processed_Bedrijf_URL_List_filename = 'pck/Processed_Bedrijf_URL_List_' + str(sector_count) + '.pck'

        Bedrijf_URL_List = extract_company_profile_url_list(Sector_URL_List, sector_count, pck_Bedrijf_URL_List_filename)
        print()
        # print(Bedrijf_URL_List)
        print('## ' + pck_Bedrijf_URL_List_filename + ': ' + str(len(Bedrijf_URL_List)))

        Processed_Bedrijf_URL_List = []
        if os.path.isfile(pck_Processed_Bedrijf_URL_List_filename):
            with open(pck_Processed_Bedrijf_URL_List_filename, 'rb') as f:
                while 1:
                    try:
                        Processed_Bedrijf_URL_List.append(pickle.load(f))
                    except EOFError:
                        break
                print("\nContinuing company profiles extraction!")
        else:
            print("\nStarting company profiles extraction!")
            print_list = [ 
                "Adres [straat]", "Adres [Postcode]", "Adres [Stad]", "Website", "E-mail", 
                "Statutaire naam", "Juridische toestand", "Ondernemingsnr", "Oprichtingsdatum", 
                "Telefoon", "Fax", "Sector", "Nacebel", "B2B-gericht", "B2C-gericht", 
                "Plaats Top (omzet/brutomarge*)", "Plaats Top (toeg. waarde)", 
                "Plaats sector (omzet/brutomarge*)", "Plaats sector (toeg. waarde)", "E-mail extractor"
            ]
            print()
            write_to_csv_file(print_list, csv_output_filename, 'w')

        print()
        # print(Processed_Bedrijf_URL_List)
        print('## ' + pck_Processed_Bedrijf_URL_List_filename + ': ' + str(len(Processed_Bedrijf_URL_List)))

        if Processed_Bedrijf_URL_List != []:
            Filtered_Bedrijf_URL_List = []
            for url in Bedrijf_URL_List:
                if url not in Processed_Bedrijf_URL_List:
                    Filtered_Bedrijf_URL_List.append(url)
        else:
            Filtered_Bedrijf_URL_List = Bedrijf_URL_List

        # print(len(Bedrijf_URL_List), len(Filtered_Bedrijf_URL_List))

        if len(Filtered_Bedrijf_URL_List) != 0:
            chunks = [ Filtered_Bedrijf_URL_List[x:x+100] for x in range(0, len(Filtered_Bedrijf_URL_List), 100) ]

            for chunk_count in range(0, len(chunks)):
                pool = multiprocessing.Pool(processes=in_cpu_num)
                args = ((Bedrijf_URL, csv_output_filename, pck_Processed_Bedrijf_URL_List_filename) for Bedrijf_URL in chunks[chunk_count])
                results = pool.map(extract_info_from_profile_page, args)
                pool.close()
                pool.join()

            Processed_Bedrijf_URL_List = []
            if os.path.isfile(pck_Processed_Bedrijf_URL_List_filename):
                with open(pck_Processed_Bedrijf_URL_List_filename, 'rb') as f:
                    while 1:
                        try:
                            Processed_Bedrijf_URL_List.append(pickle.load(f))
                        except EOFError:
                            break
            else:
                print('\n' + pck_Processed_Bedrijf_URL_List_filename + " can't be found!")

            if len(Processed_Bedrijf_URL_List) == len(Bedrijf_URL_List):
                print('\n' + pck_Processed_Bedrijf_URL_List_filename + ' COMPLETE!')
            else:
                print('\n' + pck_Processed_Bedrijf_URL_List_filename + ' NOT COMPLETE!')
                print('Maybe there was connection problems. Try to run the script again.')
