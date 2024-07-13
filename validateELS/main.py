import pymysql

from config import DB_CONFIG
from eval_functions import eval_prod_with_one_prop, eval_prod_with_two_prop, eval_prod_with_three_prop


# 데이터 삽입 쿼리
insert_query = '''
INSERT INTO ELS_hantoo_temp (loss_probability, early_redemption_probability_1, early_redemption_probability_2, early_redemption_probability_3, early_redemption_probability_4, early_redemption_probability_5)
VALUES (%s, %s, %s, %s, %s, %s)
WHERE
'''

def change_data_format(row):
    data = {}
    data["interest_rate"] = float(row[7]) / 100
    data["x_volatility"] = float(row[8])
    if row[9] != None:
        data["y_volatility"] = float(row[9])
    if row[10] != None:
        data["z_volatility"] = float(row[10])
    if row[11] != None:
        data["rho_xy"] = float(row[11])
    if row[12] != None:
        data["rho_xz"] = float(row[12])
    if row[13] != None:
        data["rho_yz"] = float(row[13])
    data["kib"] = float(row[14])
    data["coupon_rate"] = float(row[15])
    data["expiration_coupon_rate"] = float(row[22])


    temp = []
    for i in range(23, 29):
        temp.append(float(row[i]) / 100)
    data["payment_conditions"] = temp

    data["initial_price_evaluation_date"] = row[29].strftime("%Y-%m-%d")

    temp = []
    for i in range(30, 35):
        temp.append(row[i].strftime("%Y-%m-%d"))
    data["early_repayment_evaluation_dates"] = temp

    data["maturity_date"] = row[35].strftime("%Y-%m-%d")

    return data


# MySQL 데이터베이스 연결
connection = pymysql.connect(**DB_CONFIG)


try:
    with connection.cursor() as cursor:
        # SQL 쿼리
        sql = "SELECT * FROM ELS_hantoo_temp"

        # 쿼리 실행
        cursor.execute(sql)

        # 결과 가져오기
        result = cursor.fetchall()

        update_query = "UPDATE ELS_hantoo_temp SET loss_probability = %s, early_redemption_probability_1 = %s, early_redemption_probability_2 = %s, early_redemption_probability_3 = %s, early_redemption_probability_4 = %s, early_redemption_probability_5 = %s WHERE id = %s"


        # 결과 출력
        for row in result:
            data = change_data_format(row)
            id = row[0]

            if row[16] != None:
                continue

            if row[1] == 3:
                price, early_redemption_probabilities, final_gain_prob, loss_prob = eval_prod_with_three_prop(data)
            elif row[1] == 2:
                price, early_redemption_probabilities, final_gain_prob, loss_prob = eval_prod_with_two_prop(data)
            else:
                price, early_redemption_probabilities, final_gain_prob, loss_prob = eval_prod_with_one_prop(data)

            print(loss_prob, row[2])
            cursor.execute(update_query, (loss_prob, early_redemption_probabilities[0], early_redemption_probabilities[1], early_redemption_probabilities[2], early_redemption_probabilities[3], early_redemption_probabilities[4], id))
            connection.commit()

finally:
    connection.close()






