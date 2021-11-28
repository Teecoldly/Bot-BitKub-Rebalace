 
import hashlib
import hmac
import json
import requests
from line_notify import LineNotify
import datetime
import time
 
# API info BItkub
API_HOST = 'https://api.bitkub.com'
API_KEY = ''
API_SECRET = b''
Coins= ['COIN']  #ชื่อเหรียญ
PerCent = [0] #เปอร์เซ็นในการคำนวน  Rebalance ไม่รวม asset Bath 
header = {
	'Accept': 'application/json',
	'Content-Type': 'application/json',
	'X-BTK-APIKEY': API_KEY,
}
 
API_LINE = '' #แจ้งเตือน LINE Notify
result= 0 #ผลต่างในการดำเนินการซ่ื้อ
notify = LineNotify(API_LINE)
def json_encode(data):
	return json.dumps(data, separators=(',', ':'), sort_keys=True)
	
def sign(data):
	j = json_encode(data)
	# print('Signing payload: ' + j)
	h = hmac.new(API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
	return h.hexdigest()
def timeserver():
    response = requests.get(API_HOST + '/api/servertime')
    ts = int(response.text)
    # print('Server time: ' + response.text)
    return ts
 
# get last price
def getprice(name):
 
	product = name
 
	rticker = requests.get(API_HOST + '/api/market/ticker')
	rticker = rticker.json()
	price = rticker[product]['last']
	return price

# get order info
def orderinfo(symbol,orderid,side):
	order_info = {
	'sym': symbol,
	'id': orderid,
	'sd': side,
	'ts': timeserver(),}

	signature = sign(order_info)
	order_info['sig'] = signature
	r = requests.post(API_HOST + '/api/market/order-info', headers=header, data=json_encode(order_info))
	return r

# get my-open-orders
def my_open_orders(symbol):
	open_orders = {
	'sym': symbol,
	'ts': timeserver(),}

	signature = sign(open_orders)
	open_orders['sig'] = signature
	r = requests.post(API_HOST + '/api/market/my-open-orders', headers=header, data=json_encode(open_orders))
	return r
 
def createbuy(symbol,amount,rate,ordertype):
	data = {
	'sym': symbol,
	'amt': amount, # THB amount you want to spend
	'rat': rate,
	'typ': ordertype,
	'ts': timeserver(),}

	signature = sign(data)
	data['sig'] = signature

	#print('Payload with signature: ' + json_encode(data))
	r = requests.post(API_HOST + '/api/market/place-bid', headers=header, data=json_encode(data))
	
	return r
def Wallet(symbol):
    data = {
       'ts': timeserver() 
    }
    signature = sign(data)
    data['sig'] = signature
    r = requests.post(API_HOST + '/api/market/wallet', headers=header, data=json_encode(data))
    resut = {
        'error' : r.json()['error'],
        'symbol':symbol,
        'amout' : r.json()['result'][symbol]
        
    }
    return(resut)
def createsell(symbol,amount,rate,ordertype):
	data = {
	'sym': symbol,
	'amt': amount, # THB amount you want to spend
	'rat': rate,
	'typ': ordertype,
	'ts': timeserver(),}

	signature = sign(data)
	data['sig'] = signature

	print('Payload with signature: ' + json_encode(data))
	r = requests.post(API_HOST + '/api/market/place-ask-by-fiat', headers=header, data=json_encode(data))
	#print('Response: ' + r.text)
	return r

#เริ่มต้นบอท
notify.send("Start Bot ", sticker_id=10858, package_id=789)

while(True):
    try:
        if datetime.datetime.now().minute % 60 == 0: 
            #ส่งทุกๆ 1 ชั่วโมง
            notify.send('BotStatus : Ok', sticker_id=10858, package_id=789)
        totalasset =Wallet('THB')['amout']
        for coin in Coins:
            price = getprice('THB_{}'.format(coin))
            coinFree = Wallet('{}'.format(coin))['amout']
            totalasset+=(coinFree*price)
        
        for index,value in enumerate(Coins):
            Rebalance_mark=(totalasset*PerCent[index])/100
            price = getprice('THB_{}'.format(value))
            coinFree = Wallet('{}'.format(value))['amout']
            Asset_Value=coinFree*price
            print('Coin:{}\nAsset Value:{}'.format(value,Asset_Value))
    
            if Asset_Value>(Rebalance_mark+(Rebalance_mark*result/100)):
                sell = Asset_Value-Rebalance_mark
           
                if sell>=10 : 
                    print('Action :Sell\nQuantity:'.format(sell))
                    history = createsell(symbol='THB_{}'.format(value),amount=sell,rate=0,ordertype='market').json()
                    print(history)
                    notify.send('Action :Sell\nAmout BATH:{}\nCoin:{}'.format(sell,value), sticker_id=1993, package_id=446)
                   
                else:
                    print('Not : Buy\nCoin:{}\nAmout BATH:{}:'.format(value,sell))
            elif Asset_Value<(Rebalance_mark-(Rebalance_mark*result/100))  :
                buy = Rebalance_mark - Asset_Value
            
                if buy>=10 : 
                    print('Action :Buy\nAmout BATH:{}'.format(buy))
                    history = createbuy(symbol='THB_{}'.format(value),amount=buy,rate=0,ordertype='market').json()
                    print(history)
                    notify.send('Action :Buy\nAmout BATH:{}\nCoin:{}'.format(buy,value), sticker_id=1993, package_id=446)
   
                else:
                    print('Not : Sell\nCoin:{}\nAmout BATH:{}:'.format(value,buy))
            else : 
                print('Action :Not Trade')
    except Exception as e:
        print(e)
     
     
    time.sleep(60)
