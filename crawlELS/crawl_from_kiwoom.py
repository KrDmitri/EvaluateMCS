import os
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import re
import pymysql

from config import DB_CONFIG
from crawlELS.check_is_redempted import check_is_redempted
from crawlELS.download_pdf import download_pdf
from crawlELS.read_pdf import read_pdf_from_kiwoom


# 페이지 최하단으로 스크롤하는 함수
def scroll_to_bottom():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # 페이지가 로드될 시간을 줍니다

# "더보기" 버튼을 클릭하는 함수
def click_more_button():
    try:
        more_button = driver.find_element(By.XPATH, "//button[@type='button' and @class='btn-list-more']/span[text()='더보기']")
        driver.execute_script("arguments[0].click();", more_button)
        print("더보기 버튼 클릭")
        time.sleep(2)
        return True
    except NoSuchElementException:
        print("더보기 버튼 더이상 없음")
        return False


def get_tr_with_data_crncode():
    tbody = driver.find_element(By.ID, "endList")
    tr_elements = tbody.find_elements(By.TAG_NAME, "tr")

    tr_with_data_crncode = []

    for tr in tr_elements:
        attributes = driver.execute_script('''var items = {}; 
                                                  for (index = 0; index < arguments[0].attributes.length; ++index) { 
                                                      items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value 
                                                  }; 
                                                  return items;''', tr)
        # print("Attributes:", attributes)

        if attributes:
            tr_with_data_crncode.append(tr)

    return tr_with_data_crncode


# MySQL 데이터베이스 연결
conn = pymysql.connect(**DB_CONFIG)

cursor = conn.cursor()

# 데이터 삽입 쿼리
insert_query = '''
INSERT INTO ELS_kiwoom (num_equity, x_equity, y_equity, z_equity, loss_rate, x_volatility, y_volatility, z_volatility, rho_xy, rho_xz, rho_yz, coupon_rate, expiration_coupon_rate, kib, payment_conditions_1, payment_conditions_2, payment_conditions_3, payment_conditions_4, payment_conditions_5, payment_conditions_6, initial_price_evaluation_date, early_repayment_evaluation_date_1, early_repayment_evaluation_date_2, early_repayment_evaluation_date_3, early_repayment_evaluation_date_4, early_repayment_evaluation_date_5, maturity_date, is_redempted, pdf_link)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
'''


# Chrome WebDriver 생성
driver = webdriver.Chrome()

# Chrome options 설정
chrome_options = Options()
chrome_options.add_argument('--headless')  # Headless 모드 설정
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_experimental_option("detach", True)
# chrome_options.add_argument("--auto-open-devtools-for-tabs")  # 자동으로 개발자 도구를 엽니다
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)


# 웹페이지 URL
url = "https://www.kiwoom.com/wm/edl/es020/edlEndElsView"
driver.get(url)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')


# WebDriverWait을 사용하여 input 태그가 로드될 때까지 대기
wait = WebDriverWait(driver, 10)


### 전체 상품 클릭 ###
# 첫 번째 input 태그 선택
first_radio_button = driver.find_element(By.CSS_SELECTOR, '.btn-form-group .btn-check input[type="radio"]')

# JavaScript를 사용하여 클릭 이벤트 트리거
driver.execute_script("arguments[0].click();", first_radio_button)
###################


#### 날짜 입력 및 검색 버튼 클릭 ###
# 요소 찾기
from_date_element = driver.find_element(By.NAME, "searchStartDt")
to_date_element = driver.find_element(By.NAME, "searchEndDt")

# 기존 값 지우기
from_date_element.clear()
to_date_element.clear()

# 새로운 날짜 입력
from_date_str = "2021.06.20"
for elem in from_date_str:
    from_date_element.send_keys(elem)
    # time.sleep(0.5)
time.sleep(1)

to_date_str = "2021.07.01"
for elem in to_date_str:
    to_date_element.send_keys(elem)
    # time.sleep(0.5)
time.sleep(1)

search_button_element = driver.find_element(By.ID, "endSearchBtn")
search_button_element.click()
##############################


#### 상품 더보기 버튼 없어질 때까지 클릭 ####
seen_products = set()
seen_products_names = set()

while True:
    scroll_to_bottom()

    # 현재 페이지의 상품들을 가져옵니다
    current_products = get_tr_with_data_crncode()
    current_products_names = []

    for product in current_products:
        product_name = product.find_element(By.ID, "data-stkcode")
        current_products_names.append(product_name.text)


    # 새로운 상품이 있는지 확인합니다
    new_products = []

    for i in range(len(current_products)):
        if current_products_names[i] not in seen_products_names:
            new_products.append(current_products[i])
            seen_products_names.add(current_products_names[i])


    if not new_products:
        print("새로운 상품이 더 이상 없습니다.")
        break

    # 새로운 상품들의 data-crncode를 seen_products에 추가합니다
    for tr in new_products:
        seen_products.add(tr)


    if not click_more_button():
        break

print(f"총 {len(seen_products)}개의 고유한 상품을 찾았습니다.")
#####################################


#### 상품들 정보 리스트로 가져오기 ####
seen_products = list(seen_products)

product_number = 1
# 데이터 가져오기
for product in seen_products:
    product_type = product.find_elements(By.TAG_NAME, 'td')[4].text
    if product_type[:10] != "만기3년 조기상환형" or product_type[32:34] != "KI":
        continue

    a_tag = product.find_element(By.TAG_NAME, 'a')

    # 현재 탭의 핸들 저장
    current_handle = driver.current_window_handle

    tab_html = driver.page_source

    # 새 탭으로 링크 열기 (새 탭이 열릴 때까지 대기)
    a_tag.send_keys(Keys.COMMAND + Keys.RETURN)

    # 모든 창 핸들 가져오기 (현재 탭과 새 탭)
    all_window_handles = driver.window_handles

    # 새로 열린 탭 핸들 찾기
    new_tab_handle = [handle for handle in driver.window_handles if handle != current_handle][0]

    # 새 탭으로 전환
    driver.switch_to.window(new_tab_handle)

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    # 추가로 JavaScript가 실행될 시간을 주기 위해 잠시 대기
    time.sleep(5)

    new_tab_html = driver.page_source
    soup = BeautifulSoup(new_tab_html, 'html.parser')

    els_block_content = driver.find_element(By.CLASS_NAME, 'els-block-content')
    first_els_blocks = els_block_content.find_elements(By.CLASS_NAME, 'els-blocks')[0]

    #### 연 수익률 가져오기 ####
    first_els_block = first_els_blocks.find_elements(By.CLASS_NAME, 'els-block')[0]
    coupon_text = first_els_block.find_element(By.TAG_NAME, 'p').text
    # Use regular expression to find the number in the text
    match = re.search(r'\d+(\.\d+)?', coupon_text)

    if match:
        # Extract the number and convert it to a float
        number = float(match.group())
        # Convert the number to its percentage form
        percentage = number / 100
    else:
        print("No number found in the text.")
        driver.switch_to.window(current_handle)
        continue

    coupon_rate = percentage
    expiration_coupon_rate = coupon_rate * 3
    #######################


    #### 유형 가져오기 ####
    second_els_block = first_els_blocks.find_elements(By.CLASS_NAME, 'els-block')[1]
    condition_text = second_els_block.find_element(By.TAG_NAME, 'p').text
    # 괄호 안의 숫자를 추출하는 정규식 패턴
    bracket_numbers = re.findall(r'\((.*?)\)', condition_text)
    # 마지막 KI 앞의 숫자를 추출하는 정규식 패턴
    ki_number = re.search(r'(\d+)KI', condition_text)

    # 괄호 안의 숫자를 '/'로 나누어 리스트로 변환
    numbers_list = []
    if bracket_numbers:
        numbers_list = bracket_numbers[0].split('/')

    # 마지막 KI 앞의 숫자를 리스트에 추가
    if ki_number:
        numbers_list.append(ki_number.group(1))

    # 숫자들을 정수로 변환
    numbers_list = [int(num) for num in numbers_list]

    payment_conditions_1 = numbers_list[0]
    payment_conditions_2 = numbers_list[1]
    payment_conditions_3 = numbers_list[2]
    payment_conditions_4 = numbers_list[3]
    payment_conditions_5 = numbers_list[4]
    payment_conditions_6 = numbers_list[5]
    kib = numbers_list[6]
    ####################


    # #### 기초자산 이름 가져오기 #### - 키움에서 기초자산 이름은 PDF에서 가져와야 할 수도
    # equities_block_tooltip = first_els_blocks.find_element(By.CSS_SELECTOR, 'div.els-block.tooltip')
    # equities_block = equities_block_tooltip.find_element(By.CLASS_NAME, "els-block-bold")
    # equities_text = equities_block.find_element(By.TAG_NAME, 'p').text
    # equities = equities_text.split(', ')
    # print(equities)
    # ####################################################################

    #### 날짜들 가져오기 ####
    third_els_blocks = els_block_content.find_elements(By.CLASS_NAME, 'els-blocks')[2]
    second_els_block = third_els_blocks.find_elements(By.CLASS_NAME, 'els-block')[1]
    date_div = second_els_block.find_element(By.CLASS_NAME, 'els-block-bold')
    date_text = date_div.find_element(By.TAG_NAME, 'p').text

    # 정규식을 사용하여 뒤의 날짜 추출
    match = re.search(r'~ (\d{4}\.\d{2}\.\d{2})', date_text)

    if match:
        # 추출한 날짜
        end_date = match.group(1)
    else:
        print("날짜를 찾을 수 없습니다.")
        driver.switch_to.window(current_handle)
        continue

    initial_price_evaluation_date = datetime.strptime(end_date, "%Y.%m.%d").date()

    early_repayment_evaluation_date_1 = initial_price_evaluation_date + timedelta(days=6 * 30 * 1)
    early_repayment_evaluation_date_2 = initial_price_evaluation_date + timedelta(days=6 * 30 * 2)
    early_repayment_evaluation_date_3 = initial_price_evaluation_date + timedelta(days=6 * 30 * 3)
    early_repayment_evaluation_date_4 = initial_price_evaluation_date + timedelta(days=6 * 30 * 4)
    early_repayment_evaluation_date_5 = initial_price_evaluation_date + timedelta(days=6 * 30 * 5)

    maturity_date = initial_price_evaluation_date + timedelta(days=3 * 365)
    #####################

    #### PDF 링크 가져오기 ####
    pdf_list_content = driver.find_element(By.CLASS_NAME, 'pdf-list-content')
    fourth_li = pdf_list_content.find_elements(By.TAG_NAME, 'li')[3]
    a_tag = fourth_li.find_element(By.TAG_NAME, 'a')

    pdf_base_url = "https://www.kiwoom.com/wm/upload/gds/"
    file_name = a_tag.get_attribute('data-filenm')
    pdf_link = pdf_base_url + file_name
    ########################

    #### pdf 다운 받고, 변동성 + 상관계수 받아오는 로직 추가하기 ####
    download_pdf(pdf_link, product_number)
    time.sleep(2)
    equities, volatilities, correlations = read_pdf_from_kiwoom(product_number)
    x_equity = None
    y_equity = None
    z_equity = None

    x_equity = equities[0]
    if len(equities) == 3:
        y_equity = equities[1]
        z_equity = equities[2]
    elif len(equities) == 2:
        y_equity = equities[1]


    pdf_path = f'./materials/{product_number}.pdf'
    try:
        os.remove(pdf_path)
    except Exception as e:
        print(e)
    product_number += 1
    #####################################################

    #### 가져온 데이터 기반 생성해야 하는 데이터 ####
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
        driver.switch_to.window(current_handle)
        continue

    # 상환됐는지 확인하는 로직
    is_redempted, loss_rate = check_is_redempted(equities, initial_price_evaluation_date, maturity_date, kib)
    if is_redempted == None:
        driver.switch_to.window(current_handle)
        continue

    #######################################

    #### DB에 data 삽입 ####
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



    # 원래 탭으로 돌아가기
    driver.switch_to.window(current_handle)



################################

cursor.close()
conn.close()

# 웹드라이버 종료 (필요에 따라)
driver.quit()


