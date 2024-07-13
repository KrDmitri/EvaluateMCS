import numpy as np
from datetime import date, datetime
import time
import pandas as pd


# 나중에 상관계수, 변동성 구하는 함수도 추가하기
def eval_prod_with_one_prop(data):
    start = time.time()

    n = 10000
    r = data["interest_rate"]
    vol = data["x_volatility"]
    coupon_rate = data["coupon_rate"]
    half_coupon_rate = coupon_rate / 2
    expiration_coupon_rate = data["expiration_coupon_rate"]
    kib = data["kib"]
    payment_conditions = data["payment_conditions"]
    initial_price_evaluation_date = data["initial_price_evaluation_date"]
    maturity_date = data["maturity_date"]
    early_repayment_evaluation_dates = data["early_repayment_evaluation_dates"]

    date_format = '%Y-%m-%d'
    n0 = date.toordinal(datetime.strptime(initial_price_evaluation_date, date_format).date())
    n1 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[0], date_format).date())
    n2 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[1], date_format).date())
    n3 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[2], date_format).date())
    n4 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[3], date_format).date())
    n5 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[4], date_format).date())
    n6 = date.toordinal(datetime.strptime(maturity_date, date_format).date())

    check_day = np.array([n1 - n0, n2 - n0, n3 - n0, n4 - n0, n5 - n0, n6 - n0])
    oneyear = 365
    tot_date = n6 - n0
    dt = 1 / oneyear
    S = np.zeros([tot_date + 1, 1])
    S[0] = 100.0
    strike_price = np.array(payment_conditions) * S[0]

    repay_n = len(strike_price)
    coupon_rate = np.array([half_coupon_rate * i for i in range(1, 7)])

    payment = np.zeros([repay_n, 1])  # 각 평가일에 지불할 금액
    facevalue = 10 ** 4
    tot_payoff = np.zeros([repay_n, 1])  # 총 수익
    # payoff = np.zeros([repay_n, 1])  # 개별 수익
    discount_payoff = np.zeros([repay_n, 1])  # 할인된 수익
    kib = kib * S[0]
    dummy = expiration_coupon_rate  # 추가 쿠폰 금리라는데 이 정보는 어디서 보는거지?

    for j in range(repay_n):
        payment[j] = facevalue * (1 + coupon_rate[j])

    wp_list = []

    for i in range(n):
        z = np.random.normal(0, 1, size=[tot_date, 1])
        for j in range(tot_date):
            S[j + 1] = S[j] * np.exp((r - 0.5 * vol ** 2) * dt + vol * np.sqrt(dt) * z[j])
        S_checkday = S[check_day]
        payoff = np.zeros([repay_n, 1])
        repay_event = 0
        for j in range(repay_n):
            if S_checkday[j] >= strike_price[j]:
                payoff[j] = payment[j]
                repay_event = 1
                break
        if repay_event == 0:
            if min(S) > kib:
                payoff[-1] = facevalue * (1 + dummy)
            else:
                payoff[-1] = facevalue * (S[-1] / S[0])
        tot_payoff += payoff

        result = np.array([item.tolist()[0] for item in S])
        wp_list.append(result)

    mean_payoff = tot_payoff / n

    for j in range(repay_n):
        discount_payoff[j] = mean_payoff[j] * np.exp(-r * check_day[j] / oneyear)
    price = np.sum(discount_payoff)
    # print(price)
    end = time.time()
    # print(end - start)

    wp_list = np.array(wp_list)
    S = np.transpose(wp_list)

    # print(S.shape)

    df = pd.DataFrame(S)
    early_redemption_times = [182, 364, 546, 728, 910, 1092]  # 각 조기 상환 시점
    early_redemption_levels = strike_price
    early_redemption_probabilities = []
    is_early_redempted = [False] * n

    # 1~5차 조기상환 확률 계산
    for i in range(5):
        temp = 0
        for j in range(n):
            if is_early_redempted[j]:
                continue
            if df[j][early_redemption_times[i]] > early_redemption_levels[i]:
                temp += 1
                is_early_redempted[j] = True
        early_redemption_probabilities.append(temp / n * 100)

    # 만기 수익 볼 확률 계산
    temp = 0
    for i in range(n):
        if is_early_redempted[i]:
            continue

        if df[i][early_redemption_times[-1]] > kib * 1:
            temp += 1


    final_gain_prob = temp / n * 100

    loss_prob = 100 - sum(early_redemption_probabilities) - final_gain_prob

    # for i in range(5):
    #     print(str(i + 1) + "차 조기상환 확률 : " + str(early_redemption_probabilities[i]) + "%")
    #
    # print("만기 수익 볼 확률 : " + str(final_gain_prob) + "%")
    # print("원금 손실 확률 : " + str(loss_prob) + "%")

    early_redemption_probabilities = [round(elem, 4) for elem in early_redemption_probabilities]
    final_gain_prob = round(final_gain_prob, 4)
    loss_prob = round(loss_prob, 4)
    # print(price)

    return price, early_redemption_probabilities, final_gain_prob, loss_prob


# 여러 경로 중 낙인 찍고 올라온 것들 있는지 확인
def eval_prod_with_two_prop(data):
    start = time.time()

    n = 10000
    r = data["interest_rate"]
    x_vol = data["x_volatility"]
    y_vol = data["y_volatility"]
    coupon_rate = data["coupon_rate"]
    half_coupon_rate = coupon_rate / 2
    expiration_coupon_rate = data["expiration_coupon_rate"]
    kib = data["kib"]
    payment_conditions = data["payment_conditions"]
    rho = data["rho_xy"]
    initial_price_evaluation_date = data["initial_price_evaluation_date"]
    maturity_date = data["maturity_date"]
    early_repayment_evaluation_dates = data["early_repayment_evaluation_dates"]

    date_format = '%Y-%m-%d'
    n0 = date.toordinal(datetime.strptime(initial_price_evaluation_date, date_format).date())
    n1 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[0], date_format).date())
    n2 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[1], date_format).date())
    n3 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[2], date_format).date())
    n4 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[3], date_format).date())
    n5 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[4], date_format).date())
    n6 = date.toordinal(datetime.strptime(maturity_date, date_format).date())
    check_day = np.array([n1 - n0, n2 - n0, n3 - n0, n4 - n0, n5 - n0, n6 - n0])
    rho = rho
    corr = np.array([[1, rho], [rho, 1]])
    coupon_rate = ([half_coupon_rate * i for i in range(1, 7)])
    oneyear = 365
    tot_date = n6 - n0
    dt = 1 / oneyear
    k = np.linalg.cholesky(corr)
    S1 = np.zeros((tot_date + 1, 1))
    S2 = np.zeros((tot_date + 1, 1))
    S1[0] = 100
    S2[0] = 100
    ratio_S1 = S1[0]
    ratio_S2 = S2[0]
    strike_price = (payment_conditions)
    repay_n = len(strike_price)
    payment = np.zeros([repay_n, 1])
    payoff = np.zeros([repay_n, 1])
    tot_payoff = np.zeros([repay_n, 1])
    discount_payoff = np.zeros([repay_n, 1])
    face_value = 10000
    dummy = expiration_coupon_rate
    kib = kib

    for j in range(repay_n):
        payment[j] = face_value * (1 + coupon_rate[j])

    wp_list = []

    for i in range(n):
        w0 = np.random.normal(0, 1, size=[tot_date, 2])
        w0 = np.transpose(w0)
        w = np.matmul(k, w0)

        for j in range(tot_date):
            S1[j + 1] = S1[j] * np.exp((r - 0.5 * x_vol ** 2) * dt + x_vol * w[0, j] * np.sqrt(dt))
            S2[j + 1] = S2[j] * np.exp((r - 0.5 * y_vol ** 2) * dt + y_vol * w[1, j] * np.sqrt(dt))

        R1 = S1 / ratio_S1
        R2 = S2 / ratio_S2
        WP = np.minimum(R1, R2)

        result = np.array([item.tolist()[0] for item in WP])
        wp_list.append(result)

        WP_checkday = WP[check_day]
        payoff = np.zeros([repay_n, 1])
        repay_event = 0
        for j in range(repay_n):
            if WP_checkday[j] >= strike_price[j]:
                payoff[j] = payment[j]
                repay_event = 1
                break
        if repay_event == 0:
            if min(WP) > kib:
                payoff[-1] = face_value * (1 + dummy)
            else:
                payoff[-1] = face_value * WP[-1]
        tot_payoff = tot_payoff + payoff

    mean_payoff = tot_payoff / n
    for j in range(repay_n):
        discount_payoff[j] = mean_payoff[j] * np.exp(-r * check_day[j] / oneyear)

    price = np.sum(discount_payoff)

    end = time.time()

    # print(end - start)

    wp_list = np.array(wp_list)
    S = np.transpose(wp_list)
    # print(S.shape)

    df = pd.DataFrame(S)
    early_redemption_times = [182, 364, 546, 728, 910, 1091]  # 각 조기 상환 시점
    early_redemption_levels = strike_price
    early_redemption_probabilities = []
    is_early_redempted = [False] * n

    # 1~5차 조기상환 확률 계산
    for i in range(5):
        temp = 0
        for j in range(n):
            if is_early_redempted[j]:
                continue
            if df[j][early_redemption_times[i]] > early_redemption_levels[i]:
                temp += 1
                is_early_redempted[j] = True
        early_redemption_probabilities.append(temp / n * 100)

    # 만기 수익 볼 확률 계산
    temp = 0
    for i in range(n):
        if is_early_redempted[i]:
            continue
        if df[i][early_redemption_times[-1]] > kib * 1:
            temp += 1

    final_gain_prob = temp / n * 100
    loss_prob = 100 - sum(early_redemption_probabilities) - final_gain_prob

    # print(price)
    # for i in range(5):
    #     print(str(i + 1) + "차 조기상환 확률 : " + str(early_redemption_probabilities[i]) + "%")
    #
    # print("만기 수익 볼 확률 : " + str(final_gain_prob) + "%")
    # print("원금 손실 확률 : " + str(loss_prob) + "%")

    early_redemption_probabilities = [round(elem, 4) for elem in early_redemption_probabilities]
    final_gain_prob = round(final_gain_prob, 4)
    loss_prob = round(loss_prob, 4)
    # print(loss_prob)

    return price, early_redemption_probabilities, final_gain_prob, loss_prob


def eval_prod_with_three_prop(data):
    start = time.time()

    n = 10000
    r = data["interest_rate"]
    x_vol = data["x_volatility"]
    y_vol = data["y_volatility"]
    z_vol = data["z_volatility"]

    coupon_rate = data["coupon_rate"]
    half_coupon_rate = coupon_rate / 2
    expiration_coupon_rate = data["expiration_coupon_rate"]
    kib = data["kib"]
    payment_conditions = data["payment_conditions"]
    rho_xy = data["rho_xy"]
    rho_xz = data["rho_xz"]
    rho_yz = data["rho_yz"]
    initial_price_evaluation_date = data["initial_price_evaluation_date"]
    maturity_date = data["maturity_date"]
    early_repayment_evaluation_dates = data["early_repayment_evaluation_dates"]

    date_format = '%Y-%m-%d'
    n0 = date.toordinal(datetime.strptime(initial_price_evaluation_date, date_format).date())
    n1 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[0], date_format).date())
    n2 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[1], date_format).date())
    n3 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[2], date_format).date())
    n4 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[3], date_format).date())
    n5 = date.toordinal(datetime.strptime(early_repayment_evaluation_dates[4], date_format).date())
    n6 = date.toordinal(datetime.strptime(maturity_date, date_format).date())
    check_day = np.array([n1 - n0, n2 - n0, n3 - n0, n4 - n0, n5 - n0, n6 - n0])

    corr = np.array([[1, rho_xy, rho_xz], [rho_xy, 1, rho_yz], [rho_xz, rho_yz, 1]])
    k = np.linalg.cholesky(corr)
    oneyear = 365
    tot_date = n6 - n0
    dt = 1 / oneyear

    S1 = np.zeros((tot_date + 1, 1))
    S2 = np.zeros((tot_date + 1, 1))
    S3 = np.zeros((tot_date + 1, 1))
    S1[0] = 100
    S2[0] = 100
    S3[0] = 100
    ratio_S1 = S1[0]
    ratio_S2 = S2[0]
    ratio_S3 = S3[0]
    strike_price = (payment_conditions)
    repay_n = len(strike_price)
    coupon_rate = ([half_coupon_rate * i for i in range(1, 7)])
    payment = np.zeros([repay_n, 1])
    payoff = np.zeros([repay_n, 1])
    tot_payoff = np.zeros([repay_n, 1])
    discount_payoff = np.zeros([repay_n, 1])
    face_value = 10000
    dummy = expiration_coupon_rate
    kib = kib

    for j in range(repay_n):
        payment[j] = face_value * (1 + coupon_rate[j])

    wp_list = []

    for i in range(n):
        w0 = np.random.normal(0, 1, size=[tot_date, 3])
        w0 = np.transpose(w0)
        w = np.matmul(k, w0)
        repay_event = 0

        for j in range(tot_date):
            S1[j + 1] = S1[j] * np.exp((r - 0.5 * x_vol ** 2) * dt + x_vol * w[0, j] * np.sqrt(dt))
            S2[j + 1] = S2[j] * np.exp((r - 0.5 * y_vol ** 2) * dt + y_vol * w[1, j] * np.sqrt(dt))
            S3[j + 1] = S3[j] * np.exp((r - 0.5 * z_vol ** 2) * dt + z_vol * w[2, j] * np.sqrt(dt))

        R1 = S1 / ratio_S1
        R2 = S2 / ratio_S2
        R3 = S3 / ratio_S3
        WP = np.minimum(R1, R2, R3)

        result = np.array([item.tolist()[0] for item in WP])
        wp_list.append(result)

        WP_checkday = WP[check_day]
        payoff = np.zeros([repay_n, 1])
        repay_event = 0
        for j in range(repay_n):
            if WP_checkday[j] >= strike_price[j]:
                payoff[j] = payment[j]
                repay_event = 1
                break
        if repay_event == 0:
            if min(WP) > kib:
                payoff[-1] = face_value * (1 + dummy)
            else:
                payoff[-1] = face_value * WP[-1]
        tot_payoff = tot_payoff + payoff

    mean_payoff = tot_payoff / n
    for j in range(repay_n):
        discount_payoff[j] = mean_payoff[j] * np.exp(-r * check_day[j] / oneyear)

    price = np.sum(discount_payoff)

    end = time.time()


    wp_list = np.array(wp_list)
    S = np.transpose(wp_list)
    df = pd.DataFrame(S)

    early_redemption_times = [182, 364, 546, 728, 910, 1091]  # 각 조기 상환 시점
    early_redemption_levels = strike_price
    early_redemption_probabilities = []
    is_early_redempted = [False] * n

    # 1~5차 조기상환 확률 계산
    for i in range(5):
        temp = 0
        for j in range(n):
            if is_early_redempted[j]:
                continue
            if df[j][early_redemption_times[i]] > early_redemption_levels[i]:
                temp += 1
                is_early_redempted[j] = True
        early_redemption_probabilities.append(temp / n * 100)

    # 만기 수익 볼 확률 계산
    temp = 0
    for i in range(n):
        if is_early_redempted[i]:
            continue
        if df[i][early_redemption_times[-1]] > kib * 1:
            temp += 1

    final_gain_prob = temp / n * 100

    loss_prob = 100 - sum(early_redemption_probabilities) - final_gain_prob

    # print(price)
    # for i in range(5):
    #     print(str(i + 1) + "차 조기상환 확률 : " + str(early_redemption_probabilities[i]) + "%")
    #
    # print("만기 수익 볼 확률 : " + str(final_gain_prob) + "%")
    # print("원금 손실 확률 : " + str(loss_prob) + "%")

    early_redemption_probabilities = [round(elem, 4) for elem in early_redemption_probabilities]
    final_gain_prob = round(final_gain_prob, 4)
    loss_prob = round(loss_prob, 4)

    return price, early_redemption_probabilities, final_gain_prob, loss_prob
