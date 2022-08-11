from sqlitedict import SqliteDict

import os
import hoshino
from hoshino.config import authMS

__version__ = '0.2.2'

try:
    config = authMS.auth_config
except Exception as e:
    # 保不准哪个憨憨又不读README呢
    hoshino.logger.error('authMS无配置文件!请仔细阅读README!详细报错：\n' + str(e))

if authMS.auth_config.ENABLE_COM:
    path_first = authMS.auth_config.DB_PATH
else:
    path_first = os.path.dirname(__file__)
    path_first = os.path.join(path_first, "sqlite")

key_dict = SqliteDict(os.path.join(path_first, 'key.sqlite'), autocommit=True)
group_dict = SqliteDict(os.path.join(path_first, 'group.sqlite'), autocommit=True)
trial_list = SqliteDict(os.path.join(path_first, 'trial.sqlite'), autocommit=True)  # 试用列表
