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
import requests
from multiprocessing_on_dill.dummy import Pool
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

def catch_exceptions_decorator(job_func, logger, database):
    @functools.wraps(job_func)
    def wrapper(*args, **kwargs):
        try:
            return job_func(*args, **kwargs)
        except Exception as e:
            try:
                database.close()
                logger.info('database is closed')
            except :
                logger.info('database is closed')
            import traceback
            logger.error(traceback.format_exc())
    return wrapper

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

    def __init__(self, config_path = 'config.yml', schedules_path = 'schedules', models_path = 'models', log_path = 'run.log', multiprocessing = False):
        self.CONFIG_FILE_PATH = config_path
        self.SCHEDULES_PATH = schedules_path
        self.MODELS_PATH = models_path
        self.LOG_PATH = log_path
        self.MULTIPROCESSING = multiprocessing
        self.class_list = []
        config = self.read_config()
        self.logger = self.init_logger()
        self.send_message = self.init_message(config)
        self.init_peewee(config)
        self.init_terminal()
        self.init_schedule()
        self.pool = Pool()
        pass

    def init_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(level = logging.INFO)
        if not logger.handlers:
            sh = logging.StreamHandler()
            sh.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            sh.setFormatter(formatter)
            handler = logging.FileHandler(self.LOG_PATH)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.addHandler(sh)
        return logger

    def init_message(self, config):
        def send_message(self, message):
            if not config['message']:
                return None
            message_api = config['message']['url']
            params = config['message']['params']
            params["message"] = message
            if config['message']['type'] == 'http':
                return requests.get(url = message_api, params = params)
            return
        return send_message
    def function_db(self, newFunc):
        try:
            self.database.connect()
        except:
            self.database.close()
            self.database.connect()
        newFunc()
        self.database.close()
    def process_function(self, newFunc):
        self.pool.apply_async(self.function_db, args=(newFunc,))
    def exec_do(self, name, class_):
        if(hasattr(class_,'cron') and class_.cron):
            # print(name)
            trigger = self.schedule_trigger(class_.cron)
            class_.logger = self.logger
            class_.send_message = self.send_message
            c = class_()
            newFunc = catch_exceptions_decorator(c.trigger, self.logger, self.database)
            if self.MULTIPROCESSING:
                trigger.do(self.process_function, newFunc)
            else:
                trigger.do(newFunc)
        else:
            self.class_list.append(class_)
        pass

    def run_no_cron_class_list(self, class_list):
        for class_ in class_list:
            class_.logger = self.logger
            class_.send_message = self.send_message
            c = class_()
            try:
                if self.MULTIPROCESSING:
                    self.pool.apply_async(c.trigger)
                else:
                    c.trigger()
            except Exception as e:
                import traceback
                class_.logger.error(traceback.format_exc())
        pass

    # run_pending of schedule
    def run_pending(self):
        self.logger.info("EasySchedule Framework is run_pending...")
        self.run_no_cron_class_list(self.class_list)
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

    def read_config(self):
        # yaml
        assert os.path.isfile(self.CONFIG_FILE_PATH), "'CONFIG_FILE_PATH' file does not exist"
        try:
            config_file = open(self.CONFIG_FILE_PATH, 'r', encoding="utf-8")
            config_data = config_file.read()
            config_file.close()
        except Exception as e:
            assert not e
        config = yaml.safe_load(config_data)
        return config

    #peewee
    def init_peewee(self, config):
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