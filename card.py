import base64
import re
from math import ceil

from nonebot import on_command

import hoshino
from hoshino import aiorequests
from hoshino.config.__bot__ import SUPERUSERS
from hoshino.typing import CommandSession
from . import util
from .constant import config

headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "zh-cn"
           }


@on_command('生成卡密', only_to_me=True)
async def creat_key_chat(session):
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        # 非超管, 忽略
        util.log(f'{session.event.user_id}尝试生成卡密，已拒绝')
        await session.finish('你不是管理员你是在生🥚🐴')
        return
    if session.event.detail_type == 'group':
        # 群聊生成卡密你可真是个小天才
        await session.finish('群聊生成卡密你可真是个小天才')
        return
    origin = session.current_arg.strip()
    pattern = re.compile(r'^(\d{1,5})\*(\d{1,3})$')
    m = pattern.match(origin)
    if m is None:
        await session.finish('格式输错了啦憨批！请按照“生成卡密 时长*数量”进行输入！')
    duration = int(m.group(1))
    key_num = int(m.group(2))
    if key_num <= 0 or duration <= 0:
        await session.finish('你搁那生你🐴空气呢？')
    key_list = []
    for _ in range(key_num):
        new_key = util.add_key(duration)
        hoshino.logger.info(f'已生成新卡密{new_key}, 有效期{duration}天')
        key_list.append(new_key)
    await session.send(f'已生成{key_num}份{duration}天的卡密：\n' + '\n'.join(key_list))


@on_command('卡密列表', only_to_me=True)
async def key_list_chat(session):
    if session.event.user_id not in hoshino.config.SUPERUSERS:
        util.log(f'{session.event.user_id}尝试查看卡密列表，已拒绝')
        await session.finish('你不是管理员你看你个√8️⃣')
        return
    if session.event.detail_type == 'group':
        # 群聊查看卡密你可真是个小天才
        await session.finish('憨批！私聊我查看剩余卡密啦！')
    if not session.current_arg.strip():
        # 无其他参数默认第一页
        page = 1
    else:
        page = int(session.current_arg.strip())
    cards_in_page = config.CARDS_IN_PAGE
    key_list = util.get_key_list()
    length = len(key_list)
    pages_all = ceil(length / cards_in_page)

    if page > pages_all:
        await session.finish(f'没有那么多页, 当前共有卡密共{length}条, 共{pages_all}页')
    if page <= 0:
        await session.finish('请输入正确的页码')

    if not length:
        await session.finish('无可用卡密信息')

    msg = '======卡密列表======\n'
    i = 0
    for items in key_list:
        i = i + 1
        if i < (page - 1) * cards_in_page + 1 or i > page * cards_in_page:
            continue
        msg += '卡密:' + items['key'] + '\n时长:' + str(items['duration']) + '天\n'
    msg += f'第{page}页, 共{pages_all}页\n发送卡密列表+页码以查询其他页'
    await session.send(msg)


@on_command('充值', only_to_me=False)
async def reg_group_chat(session: CommandSession):
    key = session.get('key', prompt="请输入卡密（直接发送）")
    if len(key) != 32:
        session.finish('卡密错误，请检查后重新开始。')
    days = util.query_key(key)
    if days == 0:
        session.finish("卡密无效，请检查后重新开始。")
    if session.event.detail_type == 'private':
        # 私聊充值
        end = "\n如果我尚未加入您的群聊，您可以邀请我进群~"
        gid = session.get('group_id', prompt=f"卡密有效，时长{days}天。\n请输入群号（直接发送）")
        if not gid.isdigit():
            session.finish("群号错误，请重新开始。")
    else:
        end = ""
        gid = session.event.group_id

    if gid is None:
        return
    if session.event.detail_type == 'private':
        group_info = await util.get_group_info(gid)
        group_head = f"https://p.qlogo.cn/gh/{gid}/{gid}/0"
        msg = "这群都没加呢你充个🐔8️⃣"
        try:
            response = await aiorequests.get(group_head, headers=headers)
            base64_str = f'base64://{base64.b64encode(await response.content).decode()}'
            msg = f"[CQ:image,file={base64_str}]\n" \
                  f"群号:{gid}\n" \
                  f"群名:{group_info[int(gid)]}\n" \
                  f"※请确认以上信息后，回复“确认”来完成本次操作。\n" \
                  f"※回复其他内容会终止。"
        except KeyError:
            await session.bot.finish(session.event, msg)
        except Exception as e:
            print(repr(e))
            await session.bot.finish(session.event, "未知错误，请联系管理员")
        ensure = session.get("ensure", prompt=msg)
        if ensure != "确认":
            session.finish("已取消本次充值")
    days = util.query_key(key)
    result = await util.reg_group(gid, key)
    print(result)
    if not result:
        # 充值失败
        msg = '卡密无效, 请检查是否有误或已被使用, 如果无此类问题请联系发卡方'
    else:
        nickname = await util.get_nickname(user_id=session.event.user_id)
        log_info = f'{nickname}({session.event.user_id})使用了卡密{key}\n为群{gid}成功充值{days}天'
        util.log(log_info, 'card_use')
        await util.notify_master(log_info)
        msg = await util.process_group_msg(gid, result, '充值成功\n', end)
    session.finish(msg)


@on_command('检验卡密', aliases='检查卡密', only_to_me=False)
async def check_card_chat(session):
    if not session.current_arg:
        await session.finish('检验卡密请发送“检验卡密 卡密”哦~')
    else:
        origin = session.current_arg.strip()
        pattern = re.compile(r'^(\w{32})$')
        m = pattern.match(origin)
        if m is None:
            await session.finish('格式输错了啦憨批！请按照“检验卡密 卡密”进行输入！')
        key = m.group(1)
        if duration := util.query_key(key):
            util.log(f'{session.event.user_id}检查卡密{key},有效期{duration}天')
            await session.finish(f'该卡密有效!\n授权时长:{duration}天')
        else:
            util.log(f'{session.event.user_id}检查卡密{key},无效')
            await session.finish(f'该卡密无效!')


@on_command('查询授权', only_to_me=False)
async def auth_query_chat(session):
    uid = session.event.user_id
    if not session.current_arg:
        # 无参，检查群聊与否
        if session.event.detail_type == 'private':
            # 私聊禁止无参数查询授权
            await session.finish('私聊查询授权请发送“查询授权 群号”来进行指定群的授权查询（请注意空格）')
            return
        else:
            # 群聊，获取gid
            gid = session.event.group_id
    else:
        # 有参数，检查权限
        if uid not in SUPERUSERS:
            await session.finish('抱歉，您的权限不足')
            return
        else:
            # 权限为超级管理员
            gid = session.current_arg.strip()
            if not gid.isdigit():
                await session.finish('请输入正确的群号')
                return

    result = util.check_group(gid)
    if not result:
        msg = '此群未获得授权'
    else:
        msg = await util.process_group_msg(gid, result, title='授权查询结果\n')
    await session.finish(msg)
