# -*- coding: utf-8 -*-
import importlib
import os
import inspect
import yaml
import peewee as pw
import schedule
import time
import sys
import functools
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

LOG_PATH = "test.log"
def catch_exceptions_decorator(job_func, logger):
    @functools.wraps(job_func)
    def wrapper(*args, **kwargs):
        try:
            return job_func(*args, **kwargs)
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
    return wrapper

def logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(level = logging.INFO)
    if not logger.handlers:
        sh = logging.StreamHandler()
        sh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sh.setFormatter(formatter)
        handler = logging.FileHandler(LOG_PATH)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.addHandler(sh)
    return logger

database_porxy = pw.Proxy()
class EasySchedule:
    peewee = pw
    schedule = schedule
    CONFIG_FILE_PATH = 'config.yml'
    SCHEDULES_PATH = 'schedules'
    MODELS_PATH = 'models'
    LOG_PATH = 'run.log'
    logger = None
    database = database_porxy

    def __init__(self, config_path, schedules_path, models_path, log_path):
        self.CONFIG_FILE_PATH = config_path
        self.SCHEDULES_PATH = schedules_path
        self.MODELS_PATH = models_path
        self.LOG_PATH = log_path
        global LOG_PATH
        LOG_PATH = self.LOG_PATH
        self.logger = logger()
        self.init_peewee()
        self.init_terminal()
        self.init_schedule()
        pass

    def exec_do(self, name, class_):
        if(hasattr(class_,'cron') and class_.cron):
            # print(name)
            trigger = self.schedule_trigger(class_.cron)
            class_.logger = self.logger
            c = class_()
            newFunc = catch_exceptions_decorator(c.trigger, self.logger)
            trigger.do(newFunc)
        else:
            class_.logger = self.logger
            c = class_()
            try:
                c.trigger()
            except Exception as e:
                import traceback
                class_.logger.error(traceback.format_exc())
        pass

    # run_pending of schedule
    def run_pending(self):
        self.logger.info("EasySchedule Framework is run_pending...")
        while True:
            schedule.run_pending() # 运行所有可运行的任务
            time.sleep(1)

    #init_terminal
    def init_terminal(self):
        self.logger.info(
            """
                            
                   ____                ____    __          __     __   
                  / __/__ ____ __ __  / __/___/ /  ___ ___/ /_ __/ /__ 
                 / _// _ `(_-</ // / _\ \/ __/ _ \/ -_) _  / // / / -_)
                /___/\_,_/___/\_, / /___/\__/_//_/\__/\_,_/\_,_/_/\__/ 
                             /___/ 
                
            """
        )
        pass

    #peewee
    def init_peewee(self):
        # yaml
        assert os.path.isfile(self.CONFIG_FILE_PATH), "'CONFIG_FILE_PATH' file does not exist"
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
        
        assert os.path.isdir(self.MODELS_PATH), "'MODELS_PATH' folder does not exist"
        modules = self.get_all_modules(self.MODELS_PATH)
        bindModels = []
        for module in modules:
            members = inspect.getmembers(module["model"], inspect.isclass)
            for(name, class_) in members:
                if(name == module["file"]):
                    bindModels.append(class_)
        self.database.bind(bindModels)
        self.database.connect()
        self.database.create_tables(bindModels)
        self.database.close()

    #schedule
    def init_schedule(self):
        assert os.path.isdir(self.SCHEDULES_PATH), "'SCHEDULES_PATH' folder does not exist"
        modules = self.get_all_modules(self.SCHEDULES_PATH)
        for module in modules:
            members = inspect.getmembers(module["model"], inspect.isclass)
            for(name, class_) in members:
                if(str(class_).find('schedules') != -1):
                    self.exec_do(name, class_)
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
                    all_modules.append({"model": module, "file": os.path.splitext(file)[0]})
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

# class BaseModel(pw.Model):
#     class Meta:
#         database = database_porxy