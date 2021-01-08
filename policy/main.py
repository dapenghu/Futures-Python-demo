#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 根据爆仓数据，判断买卖时机
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

from pprint import pprint
from RestClient import RestClient


client = RestClient()


