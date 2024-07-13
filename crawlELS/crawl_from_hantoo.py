## 해당 디렉토리 프로그램 활용법 ###
# 1. 아래의 from_date와 to_date 값을 변경해서 가져오고 싶은 날짜의 ELS 상품 데이터를 가져올 수 있음
# 2. 현재까지의 코드로는 2017-04-04 이후의 ELS 상품 정보만 정상적으로 가져옴, 그 이전거는 코드 추가 필요(PDF data 관련)


import os
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pymysql
from config import DB_CONFIG


from crawlELS.download_pdf import download_pdf
from crawlELS.read_pdf import read_pdf_from_hantoo
from crawlELS.check_is_redempted import check_is_redempted


# MySQL 데이터베이스 연결
conn = pymysql.connect(**DB_CONFIG)

cursor = conn.cursor()

# 데이터 삽입 쿼리
insert_query = '''
INSERT INTO ELS_hantoo_v2 (num_equity, x_equity, y_equity, z_equity, loss_rate, x_volatility, y_volatility, z_volatility, rho_xy, rho_xz, rho_yz, coupon_rate, expiration_coupon_rate, kib, payment_conditions_1, payment_conditions_2, payment_conditions_3, payment_conditions_4, payment_conditions_5, payment_conditions_6, initial_price_evaluation_date, early_repayment_evaluation_date_1, early_repayment_evaluation_date_2, early_repayment_evaluation_date_3, early_repayment_evaluation_date_4, early_repayment_evaluation_date_5, maturity_date, is_redempted, pdf_link)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
'''

# Chrome options 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=chrome_options)

# 웹페이지 URL
url = "https://www.truefriend.com/main/mall/openels/EdlsInfo.jsp?cmd=TF02cc000000_Main"
driver.get(url)

# WebDriverWait을 사용하여 input 태그가 로드될 때까지 대기
wait = WebDriverWait(driver, 10)
from_date_element = wait.until(EC.presence_of_element_located((By.ID, "fromDate")))
to_date_element = wait.until(EC.presence_of_element_located((By.ID, "toDate")))

# input 태그의 현재 값을 가져오기
current_value = from_date_element.get_attribute('value')

# 한 글자씩 백스페이스를 입력하여 값 지우기
for _ in range(len(current_value)):
    from_date_element.send_keys(Keys.BACK_SPACE)
from_date_element.send_keys("20160115")

for _ in range(len(current_value)):
    to_date_element.send_keys(Keys.BACK_SPACE)
to_date_element.send_keys("20180426")

# 120개로 옵션 바꾸기
# JavaScript를 사용하여 값을 변경하고 change 이벤트를 발생시킵니다
script = """
    var select = document.getElementById('selRowsPerPage');
    select.value = '120';
    var event = new Event('change');
    select.dispatchEvent(event);
"""
driver.execute_script(script)

# 검색 버튼 클릭
search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='button' and @class='mtl_button btnWhite']")))
search_button.click()

time.sleep(2)

# 테이블 데이터 저장을 위한 리스트 초기화
all_table_data = []

# 페이지 네비게이션 루프
page_number = 1
product_number = 1

while True:
    # if page_number == 2:
    #     break

    # 페이지 소스 가져오기
    html = driver.page_source
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(html, 'html.parser')

    # id가 list인 div 찾기
    div_list = soup.find('div', id='list')
    if not div_list:
        print("No div with id 'list' found.")
        break


    # div 안의 table 태그 찾기
    table = div_list.find('table')
    if not table:
        print("No table found within the div.")
        break

    # table 안의 모든 tr 태그 찾기
    rows = table.find_all('tr')

    # 각 tr 태그의 텍스트 값을 리스트에 저장
    for row in rows:
        els_data_to_db = []
        cells = row.find_all('td')
        cell_values = [cell.get_text(strip=True) for cell in cells]  # 각 td 태그의 텍스트 값 추출
        if len(cell_values) != 11:
            continue

        if cell_values[10] == '상환':
            is_redempted = True
        else:
            is_redempted = False

        # 각 행에서 <a> 태그 찾기
        link = row.find('a', class_='product_listTitle name', onclick=lambda value: value and 'doView' in value)
        if link:
            # 링크 클릭
            driver.execute_script(link['onclick'])
            time.sleep(2)  # 페이지가 로드될 시간을 기다림

            # 페이지 소스 가져오기
            new_html = driver.page_source
            # BeautifulSoup을 사용하여 HTML 파싱
            new_soup = BeautifulSoup(new_html, 'html.parser')

            # 회사 이름들 가져오기
            equities_div = new_soup.find('div', class_='cover_txt')
            if equities_div:
                spans = equities_div.find_all('span')
                companies = []

                for span in spans:
                    a_tag = span.find('a')
                    if not a_tag:
                        text_value = span.get_text()
                    else:
                        text_value = a_tag.get_text()
                    companies.append(text_value)
                y_equity = None
                z_equity = None
                if len(companies) == 3:
                    x_equity = companies[0]
                    y_equity = companies[1]
                    z_equity = companies[2]
                    companies = [x_equity, y_equity, z_equity]
                elif len(companies) == 2:
                    x_equity = companies[0]
                    y_equity = companies[1]
                    companies = [x_equity, y_equity]
                else:
                    x_equity = companies[0]
                    companies = [x_equity]
            else:
                print("회사 이름 div 찾을 수 없음")
                # 이전 페이지로 돌아가기
                driver.back()
                time.sleep(2)  # 페이지가 로드될 시간을 기다림
                continue

            # coupon_rate 가져오기
            coupon_rate_str = new_soup.find('strong', class_='impact')
            if coupon_rate_str:
                text = coupon_rate_str.get_text(strip=True)

                # 숫자 부분만 추출
                number_part = ''.join(filter(str.isdigit, text))
                if number_part:
                    # 소수점과 숫자만 추출
                    coupon_rate = number_value = float(number_part) / 1000
                    expiration_coupon_rate = coupon_rate * 3
                else:
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue
            else:
                # 이전 페이지로 돌아가기
                driver.back()
                time.sleep(2)  # 페이지가 로드될 시간을 기다림
                continue

            # 낙인, 상환조건 가져오기
            p_tag = new_soup.find('p', class_='sup')
            if p_tag:
                # p 태그의 텍스트 내용 추출
                text = p_tag.get_text(strip=True)
                text = text[5:]
                kib_str = text[18:20]
                if kib_str.isdigit():
                    kib = int(kib_str)
                else:
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue

                # <br> 태그를 기준으로 문자열 분할 후 두 번째 부분 추출
                second_part = text.split('<br>')[-1]

                # 숫자 부분 추출
                numbers_str = second_part.split('/')[0]

                # 숫자들을 '-'를 기준으로 분할하여 리스트에 저장
                try:
                    numbers_list = [int(num) for num in numbers_str.split('-')]
                except ValueError:
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue
                if len(numbers_list) != 6:
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue

                payment_conditions_1 = numbers_list[0]
                payment_conditions_2 = numbers_list[1]
                payment_conditions_3 = numbers_list[2]
                payment_conditions_4 = numbers_list[3]
                payment_conditions_5 = numbers_list[4]
                payment_conditions_6 = numbers_list[5]

                kib = kib
            else:
                print("No p tag found.")
                # 이전 페이지로 돌아가기
                driver.back()
                time.sleep(2)  # 페이지가 로드될 시간을 기다림
                continue

            # 각 날짜들 가져오기
            div_cover_ader = new_soup.find('div', class_='cover_ader')

            if div_cover_ader:
                # div 태그 아래의 첫 번째 dl 태그 찾기
                first_dl = div_cover_ader.find('dl')

                if first_dl:
                    # dl 태그의 첫 번째 dd 태그 내의 텍스트 추출
                    first_dd_text = first_dl.find('dd').get_text(strip=True)
                    # 뒤에서부터 첫 번째 등장하는 날짜 추출
                    end_date = first_dd_text[11:21]

                    # 문자열을 date 형식으로 변환
                    try:
                        initial_price_evaluation_date = datetime.strptime(end_date, "%Y.%m.%d").date()
                    except Exception:
                        driver.back()
                        time.sleep(2)  # 페이지가 로드될 시간을 기다림
                        continue
                else:
                    print("No dl tag found inside div.")
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue

                initial_price_evaluation_date = initial_price_evaluation_date

                early_repayment_evaluation_date_1 = initial_price_evaluation_date + timedelta(days=6 * 30 * 1)
                early_repayment_evaluation_date_2 = initial_price_evaluation_date + timedelta(days=6 * 30 * 2)
                early_repayment_evaluation_date_3 = initial_price_evaluation_date + timedelta(days=6 * 30 * 3)
                early_repayment_evaluation_date_4 = initial_price_evaluation_date + timedelta(days=6 * 30 * 4)
                early_repayment_evaluation_date_5 = initial_price_evaluation_date + timedelta(days=6 * 30 * 5)

                maturity_date = initial_price_evaluation_date + timedelta(days=3 * 365)
            else:
                print("Div with class 'cover_ader' not found.")
                # 이전 페이지로 돌아가기
                driver.back()
                time.sleep(2)  # 페이지가 로드될 시간을 기다림
                continue

            # 간이투자설명서 pdf link 가져오기
            div_processStep_download_btn = new_soup.find('div', class_='processStep_download_btn')

            if div_processStep_download_btn:
                # div 태그 아래의 첫 번째 a 태그 찾기
                first_a_tag = div_processStep_download_btn.find('a')

                if first_a_tag:
                    # a 태그의 href 속성 값 추출
                    pdf_link = first_a_tag.get('href')
                    # print("pdf link of ELS explainer:", pdf_link)
                else:
                    print("No a tag found inside div.")
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue
            else:
                print("Div with class 'processStep_download_btn' not found.")
                # 이전 페이지로 돌아가기
                driver.back()
                time.sleep(2)  # 페이지가 로드될 시간을 기다림
                continue

            # 발행취소 상품인지 아닌지 확인하기
            notice_ul = new_soup.find('ul', class_='tabType1')

            # <a> 태그 찾기
            notice_a_tag = None
            for a_tag in notice_ul.find_all('a'):
                if '공지사항' in a_tag.text:
                    notice_a_tag = a_tag
                    break

            # 공지사항 <a> 태그가 존재하면
            if notice_a_tag:
                print("공지사항으로 이동")
                driver.execute_script(notice_a_tag['onclick'])
                time.sleep(2)  # 페이지가 로드될 시간을 기다림

                # 페이지 소스 가져오기
                notice_html = driver.page_source
                # BeautifulSoup을 사용하여 HTML 파싱
                notice_soup = BeautifulSoup(notice_html, 'html.parser')
                # "발행취소" 텍스트가 있는지 확인
                if notice_soup.find(string="발행취소"):
                    print("발행취소 상품")
                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림

                    # 이전 페이지로 돌아가기
                    driver.back()
                    time.sleep(2)  # 페이지가 로드될 시간을 기다림
                    continue
            else:
                # 이전 페이지로 돌아가기
                driver.back()
                time.sleep(2)  # 페이지가 로드될 시간을 기다림
                continue

            # 이전 페이지로 돌아가기(상품 상세 페이지로)
            driver.back()
            time.sleep(2)  # 페이지가 로드될 시간을 기다림


            # 이전 페이지로 돌아가기(상품 리스트로)
            driver.back()
            time.sleep(2)  # 페이지가 로드될 시간을 기다림

        # 상환됐는지 확인하는 로직
        is_redempted, loss_rate = check_is_redempted(companies, initial_price_evaluation_date, maturity_date, kib)
        if is_redempted == None:
            # driver.back()
            # time.sleep(2)  # 페이지가 로드될 시간을 기다림
            continue

        # pdf 다운 받고, 변동성 + 상관계수 받아오는 로직 추가하기
        download_pdf(pdf_link, product_number)
        time.sleep(2)
        volatilities, correlations = read_pdf_from_hantoo(product_number)
        print(volatilities, correlations)


        pdf_path = f'./materials/{product_number}.pdf'
        try:
            os.remove(pdf_path)
        except Exception as e:
            print(e)


        if volatilities == None:
            driver.back()
            time.sleep(2)  # 페이지가 로드될 시간을 기다림
            continue
        if len(volatilities) > 3 or len(correlations) > 3:
            print("변동성, 상관계수 갯수 이상 발생")
            driver.back()
            time.sleep(2)  # 페이지가 로드될 시간을 기다림
            continue

        for i in range(len(volatilities)):
            volatilities[i] = float(volatilities[i]) / 100

        for i in range(len(correlations)):
            correlations[i] = float(correlations[i])

        y_volatility = None
        z_volatility = None
        rho_xy = None
        rho_xz = None
        rho_yz = None

        if len(volatilities) == 3:
            num_equity = 3
            x_volatility = volatilities[0]
            y_volatility = volatilities[1]
            z_volatility = volatilities[2]
            rho_xy = correlations[0]
            rho_xz = correlations[1]
            rho_yz = correlations[2]
        elif len(volatilities) == 2:
            num_equity = 2
            x_volatility = volatilities[0]
            y_volatility = volatilities[1]
            rho_xy = correlations[0]
        elif len(volatilities) == 1:
            num_equity = 1
            x_volatility = volatilities[0]
        else:
            print("error with equities number")
            driver.back()
            time.sleep(2)  # 페이지가 로드될 시간을 기다림
            continue




        ### 여기 레벨에 DB에 새로운 row 저장 로직 ###
        try:
            cursor.execute(insert_query, (
                num_equity,
                x_equity,
                y_equity,
                z_equity,
                loss_rate,
                x_volatility,
                y_volatility,
                z_volatility,
                rho_xy,
                rho_xz,
                rho_yz,
                coupon_rate,
                expiration_coupon_rate,
                kib,
                payment_conditions_1,
                payment_conditions_2,
                payment_conditions_3,
                payment_conditions_4,
                payment_conditions_5,
                payment_conditions_6,
                initial_price_evaluation_date,
                early_repayment_evaluation_date_1,
                early_repayment_evaluation_date_2,
                early_repayment_evaluation_date_3,
                early_repayment_evaluation_date_4,
                early_repayment_evaluation_date_5,
                maturity_date,
                is_redempted,
                pdf_link
            ))
            # 변경사항 저장
            conn.commit()
            print("Data inserted successfully.")
            product_number += 1
        except pymysql.MySQLError as e:
            print(f"Error occurred while inserting data: {e}")
            conn.rollback()


    # 다음 페이지로 이동
    page_number += 1
    time.sleep(2)
    try:
        # 페이지 소스 가져오기
        html_source = driver.page_source
        cur_soup = BeautifulSoup(html_source, 'html.parser')

        # 다음 페이지로 이동
        page_number += 1
        next_button = driver.find_element(By.XPATH, f"//a[@onclick=\"goPage('{page_number}');return false;\"]")

        if next_button:
            next_button.click()
            time.sleep(2)  # 페이지가 로드될 시간을 기다림
        else:
            break  # 더 이상 다음 페이지가 없으면 종료
    except Exception as e:
        print(f"No more pages or next button for page {page_number} not found.")
        print(e)
        break


cursor.close()
conn.close()

# 웹드라이버 종료 (필요에 따라)
driver.quit()

