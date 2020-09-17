from sqlitedict import SqliteDict
from hoshino import priv, Service

import os
import hoshino


__version__ = '0.2.0.3'


if hoshino.config.authMS.auth_config.ENABLE_COM:
    path_first = hoshino.config.authMS.auth_config.DB_PATH
else:
    path_first = ''


key_dict = SqliteDict(os.path.join(path_first, 'key.sqlite'), autocommit=True)
group_dict = SqliteDict(os.path.join(path_first, 'group.sqlite'),autocommit=True)
trial_list = SqliteDict(os.path.join(path_first, 'trial.sqlite'),autocommit=True)  # 试用列表


try:
    config = hoshino.config.authMS.auth_config
except:
    # 保不准哪个憨憨又不读README呢
    hoshino.logger.error('authMS无配置文件!请仔细阅读README')


sv = Service('authMS',
             manage_priv=priv.SUPERUSER,
             enable_on_default=True,
             visible=False)
