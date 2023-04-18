# -*- coding: utf-8 -*-
from EasySchedule import EasySchedule

CONFIG_FILE_PATH = "config.yml"
SCHEDULES_PATH = "schedules"
MODELS_PATH = "models"

easySchedule = EasySchedule(CONFIG_FILE_PATH, SCHEDULES_PATH, MODELS_PATH)
easySchedule.run_pending()