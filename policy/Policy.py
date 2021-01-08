#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 策略思路：爆仓多单是买入时机，如果伴随2轮爆仓，而且成交量放大，就放大购买量，

 基础数据：
 - 当前仓位数据，可用资金量，杠杆率
 - 5分钟K线，15分钟K线数据
 - 爆仓数据

 策略：
 - 应用范围：中期上涨过程中
 - 建仓：如果15分钟内出现阈值 A 以上的强平多单，则认为是合适的买入时机，开多单；
 - 平仓: 根据基差判断是否现货吸血，躲避合约调仓，躲避周末，以及其它宏观变量导致的流动性短缺

 策略参数
 - LiqB: 多单爆仓数量
 - LiqS: 空单爆仓数量
 - A: 多单开仓数量
 - MaxLev： 最大杠杆率

 核心变量
 - Account Rest Client: 查询账户资产信息
 - Order Rest Client: 下单
 - WebSocket Client: 订阅 K线数据，爆仓数据，
 - PolicyManager：管理数据，执行策略

 流程
 - 获取当前仓位信息
 - 建立强平数据缓存
 - 订阅强平订单数据，每次获得数据都保存到缓存区
 - 订阅K线数据，作为定时器。
    - 每15分钟检查缓存区，如果达到触发条件，就建仓
 
@author: damonhu
"""
from datetime import *

# 当前的季度合约代码
BTC_CQ = 'BTC20210326'

# 孤立的、一次性的爆仓策略，适合于行情变化比较缓慢的时期
#   买入：每5分钟检查一次，发现爆仓数据达到阈值，即可买入
#   卖出：
# 复杂的连环爆仓模式下，
#   买入： 发现爆仓先做一个准备标记，然后分析1分钟 MA7 平均线，如果平均线价格反弹，就买入
#   卖出： 如果反弹的成交量没有放大，价格也没有明显反弹，立刻卖出。否则就持仓不动

class Policy:

    # 初始化强平缓存、策略参数
    def __init__(self, maxPrice, minPrice, liquidationVolume, tradeVolume):
        self.__liquidation_volume = liquidationVolume # 15分钟内强平多单
        self.__trade_volume = tradeVolume             # 15分钟内交易量
        self.__max_price = maxPrice      # 最高成交价     确定交易区间
        self.__min_price = minPrice      # 最高成交价     确定交易区间

        #  totalBuy, totalSell
        self.__cache_liquidation_min5 = []   # 5分钟级别强平数据
        self.__cache_kindle_min5 = []        # 5分钟级别K线数据
        self.__cache_kindle_min1 = []        # 1分钟级别K线数据
    
    # 接收强平数据，更新缓存
    def acceptLiquidatoin(self, data):
        """
        param data:
        [
            {
                "contract_code": "BTC201225",
                "symbol": "BTC",
                "direction": "buy",
                "offset": "close",
                "volume": 26,                   # 张数
                "price": 19674.96,
                "created_at": 1606293144641,
                "amount": 0.132147663832607537  # 币数
            }
        ]
        """

        # 如果 cache 空，返回
        if(len(self.__cache_buy) == 0 or len(self.__cache_sell) == 0):
            return

        # 遍历所有强平单，写入到 cache 尾部的统计数据中
        for order in data:
            # 只接受当季合约数据
            if order['contract_code'] == BTC_CQ :
                if order['direction'] == 'buy':
                    # 强平多单
                    self.__cache_liquidation_min5[-1]['totalBuy'] += order['volume']
                else:
                    # 强平空单
                    self.__cache_liquidation_min5[-1]['totalSell'] += order['volume']

    # 接受1分钟K线数据
    # 更新缓存数据
    # 根据强平数据和交易量数据，触发交易策略
    def acceptKindleMin1(self, kindle):
        """
        kindle: 
            {
            "id":1604385120,
            "mrid":113842458873,
            "open":13436.12,
            "close":13436.12,
            "high":13436.12,
            "low":13436.12,
            "amount":0,
            "vol":0,
            "count":0
            }
        """
        self.__cache_kindle_min1.append(kindle)

    # 接受5分钟K线数据
    # 更新缓存数据
    # 根据强平数据和交易量数据，触发交易策略
    def acceptKindleMin5(self, kindle):
        """
        kindle: 
            {
            "id":1604385120,
            "mrid":113842458873,
            "open":13436.12,
            "close":13436.12,
            "high":13436.12,
            "low":13436.12,
            "amount":0,
            "vol":0,
            "count":0
            }
        """
        self.__cache_kindle_min5.append(kindle)

        self.executePolicy()
        # 增加新的 cache
        self.__cache_liquidation_min5.append(
            {
                'totalBuy': 0,
                'totalSell': 0
            }
        )
    
    # 执行交易策略
    def executePolicy(self):
        # 注意，此策略要规避高位深度下跌，这种情况下有可能抄到半山腰
        # 计算15分钟内的强平多单量，volumeBuy
        # 计算15分钟内的交易量     volumeTrade
        # 如果 volumeBuy >= 5K, volumeTrade >= 1.2M

        # 至少需要15分钟的数据
        if len(self.__cache_liquidation_min5 < 3):
            return
        
        # 累计 trade volume 和 liquidation volume
        tradeVolume = 0 
        liquidationVolume = 0 

        for item in self.__cache_kindle_min5[-3:-1]:
            tradeVolume += item['vol']

        for item in self.__cache_liquidation_min5[-3:-1]:
            liquidationVolume += item['totalBuy']
        
        # 检查触发条件

