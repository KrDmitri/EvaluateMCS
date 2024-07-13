import PyPDF2
import re
import os

def read_pdf_from_hantoo(product_number):
    # PDF 파일의 정확한 경로를 지정하세요
    pdf_path = f'./materials/{product_number}.pdf'

    # 파일 존재 여부 확인
    if not os.path.exists(pdf_path):
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
    else:
        # PDF 파일 열기
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # 페이지 수 확인
            if len(reader.pages) < 4:
                print("PDF 파일에 4페이지가 없습니다.")
            else:
                # 여러 페이지에서 텍스트 추출
                # pages = reader.pages[1:4]
                # text = ''
                # for page in pages:
                #     text += page.extract_text() + '\n'

                # 한 페이지
                page = reader.pages[3]
                text = page.extract_text()


                # 전체 텍스트 출력 (디버깅 용도)
                # print("\n4페이지 전체 텍스트:")
                # print(text)

                # 변동성 추출
                volatilities = re.findall(r'(\b(?!100)\d+\.?\d*)%', text)
                volatilities = [float(v) for v in volatilities]

                # 상관계수 추출
                correlation_matrix = []
                for line in text.split('\n'):
                    numbers = re.findall(r'0\.\d+\b(?!%)', line)

                    if len(numbers) == 1:
                        correlation_matrix = []
                        correlation_matrix.append(float(numbers[0]))
                        continue

                    if len(numbers) > 0:  # 상관계수 행으로 간주
                        for number in numbers:
                            correlation_matrix.append(float(number))

                # print("변동성:", volatilities)
                # print(correlation_matrix)

                correlations = []
                for elem in correlation_matrix:
                    correlations.append(elem)
                # print("상관계수 행렬:", correlations)
                # print(volatilities, correlations)


                return volatilities, correlations
    return None, None



def read_pdf_from_kiwoom(product_number):
    # PDF 파일의 정확한 경로를 지정하세요
    pdf_path = f'./materials/{product_number}.pdf'

    # 파일 존재 여부 확인
    if not os.path.exists(pdf_path):
        print(f"파일을 찾을 수 없습니다: {pdf_path}")
    else:
        # PDF 파일 열기
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # 페이지 수 확인
            if len(reader.pages) < 4:
                print("PDF 파일에 4페이지가 없습니다.")
            else:
                # 여러 페이지에서 텍스트 추출
                # pages = reader.pages[1:4]
                # text = ''
                # for page in pages:
                #     text += page.extract_text() + '\n'

                # 한 페이지
                page = reader.pages[3]
                text = page.extract_text()


                # 전체 텍스트 출력 (디버깅 용도)
                # print("\n4페이지 전체 텍스트:")
                # print(text)

                # 변동성 추출
                volatilities = re.findall(r'(\b(?!100)\d+\.?\d*)%', text)
                volatilities = [float(v) for v in volatilities]

                # 상관계수 추출
                correlation_matrix = []
                for line in text.split('\n'):
                    numbers = re.findall(r'0\.\d+\b(?!%)', line)

                    if len(numbers) == 1:
                        correlation_matrix.append(float(numbers[0]))
                        continue

                    # if len(numbers) > 0:  # 상관계수 행으로 간주
                    #     for number in numbers:
                    #         correlation_matrix.append(float(number))

                # print("변동성:", volatilities)
                # print(correlation_matrix)

                correlations = []
                for elem in correlation_matrix:
                    correlations.append(elem)
                # print("상관계수 행렬:", correlations)
                # print(volatilities, correlations)

                # 회사 이름 추출
                # 정규식을 사용하여 주식 종목이나 주가지수 이름 추출
                pattern = r'- ([A-Za-z0-9가-힣& ]+(지수|보통주)) : \d+\.\d+%'

                matches = re.findall(pattern, text)
                equities = []

                # 결과 출력
                for match in matches:
                    equities.append(match[0].split()[0])


                return equities, volatilities, correlations
    return None, None, None



read_pdf_from_kiwoom(1)