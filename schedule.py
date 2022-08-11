from nonebot import scheduler

import pytz
from hoshino.config.authMS import auth_config as config

from .group import check_auth

tz = pytz.timezone('Asia/Shanghai')

hour = config.FREQUENCY_H
minute = config.FREQUENCY_M
second = config.FREQUENCY_S


@scheduler.scheduled_job('interval', hours=hour, minutes=minute, seconds=second)
async def check_auth_sdj():
    """
    自动检查Bot已加入的群的授权是否过期  \n
    注意只会检查已加入的群, 未加入而有授权的群, 不会被检查, 但是授权时间照样流逝(-1s), 在加入该群后才会在日志显示 \n
    例如1月5日给A群3天授权, 那么当A群7日邀请时剩余授权时间会是1天, 9日邀请时会拒绝加群 \n
    v0.1.1后新增特性, 在配置ENABLE_AUTH为0, 则不会自动检查, 并且整个授权系统不生效, 但是可以充值, 生成卡密等,
    以度过刚装上授权系统后的过渡期
    """
    if not config.ENABLE_AUTH:
        return
    await check_auth()
