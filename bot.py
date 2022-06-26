from requests import request
import websocket, json, pprint, numpy 
import talib
from binance.client import Client
from binance.enums import *
from binance import ThreadedWebsocketManager


# instantiate client object and connect using API
API_KEY = 'insert binance API key here'
API_SECRET = 'insert binance API secret here'

client = Client(API_KEY, API_SECRET)

# RSI constants
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# trading pair and quantity
TRADE_SYMBOL = input('\nPlease select coin trading pair (ie: btcusdt) - ')
TRADE_QUANTITY = float(input('\nPlease enter your trading quantity - '))


# binance stream connection assigned to socket variable
socket = f'wss://stream.binance.com:9443/ws/{TRADE_SYMBOL}@kline_1m'

# currently trading on 1m kline/candlestick chart interval
# to change time frame see documentation https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-streams

# track series of RSI closes (global variable)
closes = []

# keep track of trade
in_position = False

# function for placing orders
def order(side,  quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print('Sending Order')
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        return False
    
    return True
    
# callback functions for websocket 
def on_open(ws):
    print('\nOpened Connection')
    print('\nStarting Trading Bot')
    
def on_close(ws):
    print('\nClosed Connection')
    
def on_message(ws, message):
    global closes 
    
    # print('\nReceived Message')
    # convert json string to python data structure
    json_message = json.loads(message)
    # pprint.pprint(json_message)

    # since we use the RSI indicator - all we need is the close of each candle stick
    candle = json_message['k']
    
    # candle stick information
    is_candle_closed = candle['x']
    open_c = candle['o']
    close = candle['c']
    coin = candle['s']
    
    if is_candle_closed:
        
        print(f'\nTrading Pair - {coin} - Candle Opened at - ${open_c}')
        print(f'\nTrading Pair - {coin} - Candle Closed at - ${close}\n')
        
        # append to closes list
        closes.append(float(close))
        print('Closing Prices')
        print(closes)
        
        if len(closes) > RSI_PERIOD:
            # convert closes list to numpy array
            np_closes = numpy.array(closes)
            
            #call RSI function apart of talib and calculate RSI
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            print(f'\nThe current RSI is - {last_rsi}\n')
            
            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print('\nCoin Overbought - now is a good time to SELL!!!')
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL,  TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print('Coin Overbought, but you do not own any - nothing to do.')
                
            elif last_rsi < RSI_OVERSOLD:
                if in_position:
                    print('Coin Oversold, but you already own it - nothing to do.')   
                else:
                    print('\nCoin Oversold - now is a good time to BUY!!!')
                    # put binance order logic here
                    order_succeeded = order(SIDE_BUY,  TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True
                    
# create websocket client 
ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close , on_message=on_message)
ws.run_forever()
