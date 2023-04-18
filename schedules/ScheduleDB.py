# -*- coding: utf-8 -*-
from models.Goods import Goods
class ScheduleDB:
    cron = '01 30 15 * *'#每天第15点30分1秒
    def __init__(self):
        print('ScheduleDB is running...')
        self.listGoods()
        pass

    def listGoods(self):
        goods = Goods.select()
        for good in goods:
            print(good.shop_name)