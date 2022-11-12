import peewee as pw
from datetime import datetime
from EasySchedule import BaseModel
class Goods(BaseModel):
    shop_id = pw.IntegerField(verbose_name="店铺id")
    shop_name = pw.CharField(verbose_name="店铺名称")
    shop_address = pw.CharField(verbose_name="店铺地址")
    shop_city_id = pw.IntegerField(verbose_name="店铺所属城市id")
    created_time = pw.DateTimeField(default = datetime.now,verbose_name="创建时间")

    class Meta:
        db_table = 'tb_goods'  # 数据库的表名