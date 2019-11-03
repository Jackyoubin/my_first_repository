import pandas as pd
import numpy as np
import talib as ta
import tushare as ts
import re
import urllib.request
import matplotlib.pyplot as plt
import pickle
from matplotlib.pyplot import savefig
import heapq


def GetStockcode():  # 获取股票代码
    url = 'http://biz.finance.sina.com.cn/suggest/lookup_n.php?country=stock&q=%D2%F8%D0%D0'
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64)"}
    request = urllib.request.Request(url=url, headers=headers)
    response = urllib.request.urlopen(request)
    content = response.read().decode('gbk')
    pattern = re.compile('s[hz]\d{6}')
    item = re.findall(pattern, content)
    item = item[::2]  # 取偶
    item = item[0:24]
    stockcode = []
    for i in item:  # 去除sz/h
        stockcode.append(i[2:])
    return stockcode


'''def GetData(stk):
    pkl_file=open('%s.pkl'%stk,'rb')
    data=pickle.load(pkl_file)
    pkl_file.close()
    return data'''


def GetDataTus(stk, start, end):  # 获取交易数据
    data = ts.get_k_data(stk, start=start, end=end)
    return data


def GetBand(data, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0):
    band = pd.DataFrame(index=data.index)
    band['date'] = data['date']
    band['close'] = data['close']
    band['upper'], band['middle'], band['lower'] = ta.BBANDS(data.close.values, timeperiod=timeperiod, nbdevup=nbdevup,
                                                             nbdevdn=nbdevdn, matype=matype)
    band['MA20'] = data['close'].rolling(window=20).mean()
    band['dev'] = data['close'].rolling(window=20).std()
    band['index'] = data.index
    band = band.dropna(axis=0, how='any')  # 清除为空的行
    band = band.reset_index()  # 索引重新排序,并生成新的列，level_0
    del band['level_0']
    band['devchange'] = band['dev'] - band['dev'].shift(-1)  # i+1-i
    band = band.dropna()
    band = band.reset_index()
    del band['level_0']
    code = data.iloc[1, -1]
    df2 = ts.get_k_data(code, start='2011-01-01', end='2012-01-01')
    df3 = ts.get_k_data(code, start='2012-01-01', end='2013-01-01')
    df4 = ts.get_k_data(code, start='2013-01-01', end='2014-01-01')
    df5 = ts.get_k_data(code, start='2014-01-01', end='2015-01-01')
    df6 = ts.get_k_data(code, start='2015-01-01', end='2016-01-01')
    d2 = df2.close.rolling(window=20).std()
    d3 = df3.close.rolling(window=20).std()
    d4 = df4.close.rolling(window=20).std()
    d5 = df5.close.rolling(window=20).std()
    d6 = df6.close.rolling(window=20).std()
    c2 = []
    c3 = []
    c4 = []
    c5 = []
    c6 = []
    for i in range(20, len(d2) - 20):
        c2.append(d2[i] - d2[i - 1])
    data2 = heapq.nlargest(50, c2)
    for i in range(20, len(d3) - 20):
        c3.append(d3[i] - d3[i - 1])
    data3 = heapq.nlargest(50, c3)
    for i in range(20, len(d4) - 20):
        c4.append(d4[i] - d4[i - 1])
    data4 = heapq.nlargest(50, c4)
    for i in range(20, len(d5) - 20):
        c5.append(d5[i] - d5[i - 1])
    data5 = heapq.nlargest(50, c5)
    for i in range(20, len(d6) - 20):
        c6.append(d6[i] - d6[i - 1])
    data6 = heapq.nlargest(50, c6)
    five_dev_change = (sum(data2) / len(data2) + sum(data3) / len(data3) + sum(data4) / len(data4) + sum(data5) / len(
        data5) + sum(data6) / len(data6)) / 5
    band['closecompareMA20'] = 0
    band['devcomparedevchange'] = 0
    for index in band.index:
        if band.iloc[index, 1] - band.iloc[index, 5] >= 0:
            band.iloc[index, 9] = 1
        if band.iloc[index, 1] - band.iloc[index, 5] < 0:
            band.iloc[index, 9] = 0
        if band.iloc[index, 8] - five_dev_change >= 0:
            band.iloc[index, 10] = 1
        if band.iloc[index, 8] - five_dev_change < 0:
            band.iloc[index, 10] = 0
    band['five_dev_change'] = five_dev_change
    return band


def GetSignals(band, holddays=5):  # 产生交易信号
    signals = pd.DataFrame(index=band.index)
    signals['index'] = band['index']
    signals['buy'] = None
    signals['sell'] = None
    for index in band.index:
        if band.iloc[index, 9] == band.iloc[index, 10] == 1:
            signals.iloc[index, 1] = 1
        if signals.iloc[index, 1] == 1:
            index += 5
            signals.iloc[index, 2] = 1
    return signals


def PlotImg(signals, portfolio, band):
    plt.figure(11, figsize=(20, 10))  # 资金图
    plt.xlabel('total')
    plt.ylabel('data')
    from matplotlib.font_manager import FontProperties
    font = FontProperties(fname=r'C:\\windows\\fonts\\simsun.ttc', size=14)
    plt.title(u'股票代码: 000001sz', fontproperties=font)
    plt.plot(portfolio['total'], label='total')
    plt.legend()
    plt.show()

    plt.figure(21, figsize=(20, 10))  # 交易信号及收盘价，布林线
    from matplotlib.font_manager import FontProperties
    font = FontProperties(fname=r'C:\\windows\\fonts\\simsun.ttc', size=14)
    plt.xlabel('index')
    plt.ylabel('contion')
    plt.title(u'股票代码: 000001sz', fontproperties=font)
    plt.plot(band['close'], label='close')
    plt.plot(band['upper'], label='upper')
    plt.plot(band['lower'], label='lower')
    plt.plot(band['MA20'], label='MA20')
    buysignals = signals['buy'].dropna()
    Bx = buysignals.index
    By = []
    for b in buysignals.index:
        a = band['close'][b]
        By.append(a)
    plt.scatter(Bx, By, label='buy')
    sellsignals = signals['sell'].dropna()
    Sx = buysignals.index
    Sy = []
    for b in sellsignals.index:
        a = band['close'][b]
        Sy.append(a)
    plt.scatter(Sx, Sy, label='sell')
    plt.legend()
    plt.show()


def BackTest(signals, band):  # 回测框架
    count = 0
    num = len(band)
    portfolio = pd.DataFrame(index=band.index)
    portfolio['date'] = band['date']
    # 总价值=剩余资金+仓位股票价值
    # 仓位股票价值=股票仓位*当前股票价值
    portfolio['total'] = 100000  # 总价值
    portfolio['cash'] = 100000  # 剩余资金
    portfolio['holding'] = 0  # 仓位股票价值
    portfolio['position'] = 0  # 股票仓位
    for index in band.index:
        count = count + 1
        if signals['buy'][index] == 1 and portfolio['position'][index] == 0:
            portfolio.iloc[index, 4] = portfolio['cash'][index] / band['close'][index]  # 持仓
            portfolio.iloc[index, 2] = 0  # 舍去
            portfolio.iloc[index, 1] = portfolio['position'][index] * band['close'][index]  # 总价值
        elif signals['sell'][index] == 1 and portfolio['position'][index] != 0:
            portfolio.iloc[index, 2] = portfolio['position'][index] * band['close'][index]  # 清仓
            portfolio.iloc[index, 4] = 0  # 仓位为零
            portfolio.iloc[index, 1] = portfolio['cash'][index]  # 总价值等于现金
        portfolio.iloc[index, 3] = portfolio['position'][index] * band['close'][index]  # 持有价值
        if portfolio['position'][index] != 0:
            portfolio.iloc[index, 1] = portfolio['position'][index] * band['close'][index]
        if count == num:
            break
        else:
            portfolio.iloc[index + 1, 1] = portfolio['total'][index]
            portfolio.iloc[index + 1, 2] = portfolio['cash'][index]
            portfolio.iloc[index + 1, 3] = portfolio['holding'][index]
            portfolio.iloc[index + 1, 4] = portfolio['position'][index]
    returns = ((portfolio['total'][len(band) - 1] - 100000) / 100000) * 100
    returns = returns * 252 / len(band)
    print('年化收益率：%.2f' % (returns) + '%')
    PlotImg(signals, portfolio, band)
    return returns


def main():
    stk = '000001'
    timeperiod = 20
    holddays = 3
    start = '2016-01-01'
    end = '2017-01-01'

    data = GetDataTus(stk=stk, start=start, end=end)
    band = GetBand(data, timeperiod=timeperiod)
    signals = GetSignals(band, holddays)
    returns = BackTest(signals, band)


main()