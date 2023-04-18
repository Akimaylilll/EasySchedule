import peewee as pw
from datetime import datetime
class Goods(pw.Model):
    shop_id = pw.IntegerField(verbose_name="店铺id")
    shop_name = pw.CharField(verbose_name="店铺名称")
    shop_address = pw.CharField(verbose_name="店铺地址")
    shop_city_id = pw.IntegerField(verbose_name="店铺所属城市id")
    created_time = pw.DateTimeField(default = datetime.now,verbose_name="创建时间")

    class Meta:
        db_table = 'goods'