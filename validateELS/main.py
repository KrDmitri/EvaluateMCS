import pymysql

from config import DB_CONFIG
from validateELS.eval_functions import eval_prod_with_one_prop, eval_prod_with_two_prop, eval_prod_with_three_prop
def change_data_format(row):
    data = {}
    data["interest_rate"] = float(row[3]) / 100
    data["x_volatility"] = float(row[4])
    if row[5] != None:
        data["y_volatility"] = float(row[5])
    if row[6] != None:
        data["z_volatility"] = float(row[6])
    if row[7] != None:
        data["rho_xy"] = float(row[7])
    if row[8] != None:
        data["rho_xz"] = float(row[8])
    if row[9] != None:
        data["rho_yz"] = float(row[9])
    data["coupon_rate"] = float(row[10])
    data["expiration_coupon_rate"] = float(row[11])
    data["kib"] = float(row[12])

    temp = []
    for i in range(13, 19):
        temp.append(float(row[i]) / 100)
    data["payment_conditions"] = temp

    data["initial_price_evaluation_date"] = row[19].strftime("%Y-%m-%d")

    temp = []
    for i in range(20, 25):
        temp.append(row[i].strftime("%Y-%m-%d"))
    data["early_repayment_evaluation_dates"] = temp

    data["maturity_date"] = row[25].strftime("%Y-%m-%d")

    return data

# MySQL 데이터베이스 연결
connection = pymysql.connect(**DB_CONFIG)


try:
    with connection.cursor() as cursor:
        # SQL 쿼리
        sql = "SELECT * FROM ELS_hantoo where num_equity = 1 limit 20"

        # 쿼리 실행
        cursor.execute(sql)

        # 결과 가져오기
        result = cursor.fetchall()

        # 결과 출력
        for row in result:
            data = change_data_format(row)

            if row[2] == 3:
                price, early_redempted_probabilities, final_gain_prob, loss_prob = eval_prod_with_three_prop(data)
            elif row[2] == 2:
                price, early_redempted_probabilities, final_gain_prob, loss_prob = eval_prod_with_two_prop(data)
            else:
                price, early_redempted_probabilities, final_gain_prob, loss_prob = eval_prod_with_one_prop(data)

            print(loss_prob)

finally:
    connection.close()