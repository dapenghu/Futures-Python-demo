from HuobiDMService import HuobiDM
from pprint import pprint


class RestClient:
    def __init__(self):
        self.__client = HuobiDM('https://api.hbdm.com', 'f2643261-4cfd9d14-ca908a0f-dbye2sf5t7', '34ae74a1-853da993-eac728aa-f812f')
    
    # 季度合约K线数据
    def get_contract_kline(self, period, start, end, size=150):
        """
        :param symbol  BTC_CW, BTC_NW, BTC_CQ , ...
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1week, 1mon }
        :param size: [1,2000]
        :return:
        """
        params = {'symbol': 'BTC_CQ',
                  'period': period,
                  'start': start,
                  'end' : end}
        if size:
            params['size'] = size
    
        url = self.__url + '/market/history/kline'
        resp = self.__client.http_get_request(url, params)

        return resp['data']

    # 合约下单
    def send_contract_order(self, price, volume, direction, offset):
        """ 当季合约下单, 
            Args:
            price: 价格.
            volume: 委托数量(张).
            direction: "buy":买 "sell":卖.
            offset: "open":开 "close":平
            order_price_type: 订单报价类型 "limit":限价; "opponent":对手价

            Returns:
            下单结果.
        """
        print (u' 合约下单BTC ', " price =", price, " volume =", volume, " direction =", direction, " offset =", offset )
        symbol='BTC'
        contract_type='quarter'
        client_order_id=''
        contract_code=''
        #client_order_id=''
        # direction='buy'
        #offset='open' 

        resp = self.__client.send_contract_order(symbol, contract_type, contract_code, client_order_id,
                                       price, volume, direction, offset, 
                                       lever_rate=5, order_price_type='limit')
        return resp['data']

    # 获取用户持仓信息
    def get_contract_position_info(self):
        resp = self.__client.get_contract_position_info('BTC')
        return resp['data']
        

    # 获取基差数据
    def get_history_base(self):
        resp = self.__client.get_history_base()
        return resp['data']

if __name__ == "__main__":
    """ Test

    """
    dm = RestClient()

    #print (u' 获取用户持仓信息 ')
    #position = dm.get_contract_position_info("BTC")['data'][0]
    #pprint (position)

    #dm.send_contract_order(36000, 1, 'buy', 'open',)
    #resp = dm.get_contract_position_info()
    #pprint(resp)
    resp = dm.get_history_base()
    pprint(resp)
