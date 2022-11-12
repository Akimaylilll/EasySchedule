# -*- coding: utf-8 -*-
import importlib
import os
import inspect
import yaml
import peewee as pw
import schedule
import time

database_porxy = pw.Proxy()
class EasySchedule:
    peewee = pw
    schedule = schedule
    CONFIG_FILE_PATH = 'config.yml'
    SCHEDULE_PATH = 'schedules'
    database = database_porxy

    def __init__(self):
        self.init_peewee()
        self.init_schedule()
        pass

    # run_pending of schedule
    def run_pending(self):
        while True:
            schedule.run_pending() # 运行所有可运行的任务
            time.sleep(1)

    #peewee
    def init_peewee(self):
        # yaml
        assert os.path.isfile(self.CONFIG_FILE_PATH), "config.yml no found"
        try:
            config_file = open(self.CONFIG_FILE_PATH, 'r', encoding="utf-8")
            config_data = config_file.read()
            config_file.close()
        except Exception as e:
            assert not e
        config = yaml.safe_load(config_data)

        #mysql config
        mysql_config = config['mysql']
        self.database = pw.MySQLDatabase(\
            database = mysql_config['database'],\
                passwd = mysql_config['passwd'],\
                    user = mysql_config['user'],\
                        host = mysql_config['host'],\
                            port = mysql_config['port'])
        #mysql init
        database_porxy.initialize(self.database)
        try:
            self.database.connect()
            self.database.close()
        except Exception as e:
            assert not e
        pass

    #schedule
    def init_schedule(self):
        assert os.path.isdir(self.SCHEDULE_PATH), "dir schedules no found"
        modules = self.get_all_modules(self.SCHEDULE_PATH)
        for module in modules:
            members = inspect.getmembers(module, inspect.isclass)
            for(name, class_) in members:
                if(str(class_).find('schedules') != -1):
                    if(hasattr(class_,'cron') and class_.cron):
                        trigger = self.schedule_trigger(class_.cron)
                        trigger.do(class_)
                    else:
                        class_()
        pass

    def get_all_modules(self, dir):
        all_modules = []
        for root, dirs, files in os.walk(dir):
            for file in files:
                if file.endswith(".py") and file != '__init__.py':
                    module_path = os.path.join(dir, os.path.splitext(file)[0])
                    module_path = module_path.replace('\\','/')\
                        .replace('../', '..')\
                            .replace('./', '.')\
                                .replace('/', '.')
                    if module_path[0] == '.' and module_path[1] != '.':
                        module_path = module_path[1:]
                    module = importlib.import_module(module_path)
                    all_modules.append(module)
        return all_modules

    def schedule_trigger(self, cron):
        crons = cron.split(' ')
        trigger = schedule.every()
        ix = crons.index('*')
        if(ix == 0):
            trigger = trigger.seconds
        elif(ix == 1):
            trigger = trigger.minutes
        elif(ix == 2):
            trigger = trigger.hour
        elif(ix == 3):
            trigger = trigger.day
        elif(ix == 4):
            trigger = trigger.week
        mark = ''
        for inx, c in enumerate(crons[0:3]):
            if(c.find('*') < 0):
                if(inx == 2):
                    mark =  c + mark
                else:
                    mark =  ':' + c + mark
        if(mark != ''):
            trigger = trigger.at(mark)
        return trigger

class BaseModel(pw.Model):
    class Meta:
        database = database_porxy