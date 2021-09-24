from quart import request, Blueprint, jsonify, render_template

import nonebot

from . import util



activate = Blueprint('activate', __name__, url_prefix='/activate', template_folder="./activate"
                     , static_folder='./activate', static_url_path='')
bot = nonebot.get_bot()
app = bot.server_app


@activate.route("/", methods=["GET", "POST"])
async def activate_group():
    if request.method == "GET":
        if key := request.args.get("key"):
            if gid := request.args.get('group'):
                group_id = int(gid)
                days = util.query_key(key)
                result = await util.reg_group(group_id, key)
                if result:
                    log_info = f'卡密{key}通过网页被激活\n为群聊{group_id}增加了{days}天授权时长'
                    util.log(log_info,'card_use')
                    await util.notify_master(log_info)
        return await render_template("activate.html")
