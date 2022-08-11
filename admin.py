from .util import notify_group
from nonebot import on_command
from math import ceil

import hoshino
import re

from . import util
from .constant import config


@on_command('变更所有授权', aliases=('批量变更', '批量授权'), only_to_me=False)
async def add_time_all_chat(session):
    """
    为所有已有授权的群增加授权x天, 可用于维护补偿时间等场景
    """
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试批量授权, 已拒绝')
        await session.finish('你又不是老子的骂死塔你批量授权个🔨')
        return
    if not session.current_arg:
        await session.finish('请发送需要为所有群增加或减少的长, 例如“变更所有授权 7”')

    days = int(session.current_arg.strip())

    authed_group_list = await util.get_authed_group_list()
    for ginfo in authed_group_list:
        await util.change_authed_time(ginfo['gid'], days)
    util.log(f'已为所有群授权增加{days}天')
    await session.finish(f'已为所有群授权增加{days}天')


@on_command('授权列表', aliases=('查看授权列表', '查看全部授权', '查询全部授权'), only_to_me=True)
async def group_list_chat(session):
    """
    此指令获得的是, 所有已经获得授权的群, 其中一些群可能Bot并没有加入 \n
    分页显示, 请在authMS.py中配置
    """
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试查看授权列表, 已拒绝')
        await session.finish('你又不是老子的骂死塔你看你大爷')
        return
    if session.event.detail_type == 'group':
        # 群聊查看授权列表你也是个小天才
        await session.finish('群聊查看授权列表？你也是真个天才')

    if not session.current_arg.strip():
        # 无其他参数默认第一页
        page = 1
    else:
        page = int(session.current_arg.strip())

    msg = '======授权列表======\n'

    authed_group_list = await util.get_authed_group_list()
    length = len(authed_group_list)

    groups_in_page = config.GROUPS_IN_PAGE
    pages_all = ceil(length / groups_in_page)  # 向上取整
    if page > pages_all:
        await session.finish(f'没有那么多页, 当前共有授权信息{length}条, 共{pages_all}页')
    if page <= 0:
        await session.finish('请输入正确的页码')
    i = 0
    for item in authed_group_list:
        i = i + 1
        if i < (page - 1) * groups_in_page + 1 or i > page * groups_in_page:
            continue
        gid = int(item['gid'])
        g_time = util.check_group(gid)
        msg_new = await util.process_group_msg(gid,
                                               g_time,
                                               title=f'第{i}条信息\n',
                                               end='\n\n',
                                               group_name_sp=item['groupName'])
        msg += msg_new

    msg += f'第{page}页, 共{pages_all}页\n发送查询授权+页码以查询其他页'
    await session.send(msg)


@on_command('变更授权', aliases=('更改时间', '授权', '更改授权时间', '更新授权'), only_to_me=False)
async def add_time_chat(session):
    origin = session.current_arg.strip()
    pattern = re.compile(r'^(\d{5,15})([+-]\d{1,5})$')
    m = pattern.match(origin)
    if m is None:
        await session.finish('请发送“授权 群号±时长”来进行指定群的授权, 时长最长为99999')
    gid = int(m.group(1))
    days = int(m.group(2))

    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试为群{gid}增加{days}天授权, 已拒绝')
        await session.finish('你又不是老子的骂死塔你改个p')
        return

    result = await util.change_authed_time(gid, days)
    msg = await util.process_group_msg(gid, result, title='变更成功, 变更后的群授权信息:\n')
    await notify_group(group_id=gid, txt=f'机器人管理员已为本群增加{days}天授权时长，可在群内发送【查询授权】来查看到期时间。')
    await session.finish(msg)


@on_command('转移授权', only_to_me=False)
async def group_change_chat(session):
    if not session.current_arg:
        await session.finish('请发送“转移授权 旧群群号*新群群号”来进行群授权转移')
    origin = session.current_arg.strip()
    pattern = re.compile(r'^(\d{5,15})\*(\d{5,15})$')
    m = pattern.match(origin)
    if m is None:
        await session.finish('格式错误或者群号错误XD\n请发送“转移授权 旧群群号*新群群号”来转移群授权时长\n如果新群已经授权，则会增加对应时长。')
    old_gid = int(m.group(1))
    new_gid = int(m.group(2))

    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试转移授权{old_gid}到{new_gid}, 已拒绝')
        session.finish('又不是老子的骂死塔，还想转移？想p吃呢')
        return

    gtime_old = util.check_group(old_gid)
    if gtime_old == 0:
        await session.finish('旧群无授权, 不可进行转移')
    if old_gid == new_gid:
        await session.finish('宁搁这儿原地TP呢？')

    await util.transfer_group(old_gid, new_gid)
    gtime_new = util.check_group(new_gid)
    msg = await util.process_group_msg(new_gid, expiration=gtime_new, title=f'旧群{old_gid}授权已清空, 新群授权状态：\n')
    await notify_group(group_id=old_gid, txt=f'机器人管理员已转移本群授权时长至其他群。')

    await session.finish(msg)


# noinspection PyUnboundLocalVariable
@on_command('授权状态', only_to_me=False)
async def auth_status_chat(session):
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试查看授权状态, 已拒绝')
        await session.finish('你又不是老子的骂死塔你查个🥚🥚')
        return
    for sid in hoshino.get_self_ids():
        sgl = set(g['group_id']
                  for g in await session.bot.get_group_list(self_id=sid))
        frl = set(f['user_id']
                  for f in await session.bot.get_friend_list(self_id=sid))
    # 直接从service里抄了, 面向cv编程才是真
    gp_num = len(sgl)
    fr_num = len(frl)
    key_num = len(util.get_key_list())
    agp_num = len(await util.get_authed_group_list())
    msg = f'Bot账号：{sid}\n所在群数：{gp_num}\n好友数：{fr_num}\n授权群数：{agp_num}\n未使用卡密数：{key_num}'
    await session.send(msg)


@on_command('清除授权', aliases=('删除授权', '移除授权', '移除群授权', '删除群授权'), only_to_me=True)
async def remove_auth_chat(session):
    """
    完全移除一个群的授权 \n
    不需要二次确认, 我寻思着你rm /* -rf的时候也没人让你二次确认啊  \n
    """
    if not session.current_arg.strip():
        await session.finish('请输入正确的群号, 例如“清除授权 123456789”')
    gid = int(session.current_arg.strip())
    time_left = util.check_group(gid)

    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试为群{gid}清除授权, 已拒绝')
        await session.finish('你不是骂死塔还想删授权，是不是要老子把你🐴删了')

    if not time_left:
        await session.finish('此群未获得授权')
    msg = await util.process_group_msg(gid=gid, expiration=time_left, title='已移除授权,原授权信息如下\n')
    await util.change_authed_time(gid=gid, operate='clear')

    if config.AUTO_LEAVE:
        await util.gun_group(group_id=gid, reason='机器人管理员移除授权')
        msg += '\n已尝试退出该群聊'
    await session.send(msg)


# noinspection PyUnboundLocalVariable
@on_command('不检查人数', aliases='设置人数白名单', only_to_me=False)
async def no_number_check_chat(session):
    """
    不检查一个群的人数是否超过人数限制, 在群聊中发送则为不检查本群
    """
    if session.event.detail_type == 'group':
        gid = session.event.group_id
    elif session.event.detail_type == 'private':
        if not session.current_arg.strip():
            await session.finish('请输入正确的群号, 例如“不检查人数 123456789”')
        gid = int(session.current_arg.strip())

    uid = session.event.user_id
    if uid not in hoshino.config.SUPERUSERS:
        util.log(f'{uid}尝试为群{gid}清除设置不检查人数, 已拒绝')
        await session.finish('你不是主人你设你个大头鬼的人数白名单')
        return

    util.allowlist(group_id=gid, operator='add', nocheck='no_number_check')
    util.log(f'管理员{uid}已将群{gid}添加至白名单, 类型为不检查人数')
    await notify_group(group_id=gid, txt='机器人管理员已添加本群为白名单，将不会检查本群人数是否超标。')
    await session.finish(f'已将群{gid}添加至白名单, 类型为不检查人数')


# noinspection PyUnboundLocalVariable
@on_command('不检查授权', aliases='设置授权白名单', only_to_me=False)
async def no_auth_check_chat(session):
    if session.event.detail_type == 'group':
        gid = session.event.group_id
    elif session.event.detail_type == 'private':
        if not session.current_arg.strip():
            await session.finish('请输入正确的群号, 例如“不检查授权 123456789”')
        gid = int(session.current_arg.strip())

    uid = session.event.user_id
    if uid not in hoshino.config.SUPERUSERS:
        util.log(f'{uid}尝试为群{gid}清除设置不检查授权, 已拒绝')
        await session.finish('你不是主人你设你个大头鬼的授权白名单')
        return
    util.allowlist(group_id=gid, operator='add', nocheck='no_auth_check')
    util.log(f'已将群{gid}添加至白名单, 类型为不检查授权')
    await notify_group(group_id=gid, txt='机器人管理员已添加本群为白名单，将不会检查本群授权是否过期。')
    await session.finish(f'已将群{gid}添加至白名单, 类型为不检查授权')


# noinspection PyUnboundLocalVariable
@on_command('添加白名单', only_to_me=False)
async def no_check_chat(session):
    """
    最高级别白名单, 授权与人数都检查
    """
    if session.event.detail_type == 'group':
        gid = session.event.group_id
    elif session.event.detail_type == 'private':
        if not session.current_arg.strip():
            await session.finish('请输入正确的群号, 例如“添加白名单 123456789”')
        gid = int(session.current_arg.strip())

    uid = session.event.user_id
    if uid not in hoshino.config.SUPERUSERS:
        util.log(f'{uid}尝试为群{gid}清除设置添加白名单, 已拒绝')
        await session.finish('不是主人还想设白名单？你是不是憨批')
        return

    util.allowlist(group_id=gid, operator='add', nocheck='no_check')
    util.log(f'已将群{gid}添加至白名单, 类型为全部不检查')
    await notify_group(group_id=gid, txt='机器人管理员已添加本群为白名单，将不会检查本群授权以及人数。')
    await session.finish(f'已将群{gid}添加至白名单, 类型为全部不检查')


@on_command('移除白名单', aliases='删除白名单')
async def remove_allowlist_chat(session):
    if not session.current_arg.strip():
        await session.finish('请输入正确的群号, 例如“移除白名单 123456789”')
    gid = int(session.current_arg.strip())
    uid = session.event.user_id

    if uid not in hoshino.config.SUPERUSERS:
        util.log(f'{uid}尝试移除白名单{gid}, 已拒绝')
        await session.finish('不是主人还想设白名单？你是不是憨批')
        return

    re_code = util.allowlist(group_id=gid, operator='remove')
    if re_code == 'not in':
        await session.finish(f'群{gid}不在白名单中')
    await notify_group(group_id=gid, txt='机器人管理员已移除本群的白名单资格')
    util.log(f'已将群{gid}移出白名单')
    await session.finish(f'已将群{gid}移出白名单')


@on_command('全部白名单', aliases=('白名单列表', '所有白名单'))
async def get_allowlist_chat(session):
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试查看白名单, 已拒绝')
        await session.finish('不是主人还想看白名单？你是不是憨批')
        return

    allow_list = util.get_list(list_type='allowlist')

    msg = '白名单信息\n'
    gids = list(allow_list.keys())
    gname_dir = await util.get_group_info(group_ids=gids, info_type='group_name')
    # 考虑到一般没有那么多白名单, 因此此处不做分页
    i = 1
    for gid in gname_dir:
        msg += f'第{i}条:   群号{gid}\n'
        gname = gname_dir[gid]
        gnocheck = allow_list[gid]
        msg += f'群名:{gname}\n类型:{gnocheck}\n\n'
        i = i + 1
    session.finish(msg)


@on_command('刷新事件过滤器')
async def reload_ef(session):
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}刷新事件过滤器, 已拒绝')
        await session.finish('刷你🐴，给👴爪巴')
        return
    await util.flush_group()
    await session.send("刷新成功!")
