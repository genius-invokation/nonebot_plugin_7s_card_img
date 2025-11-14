from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.plugin import on_command,on_regex,on_command,on_keyword
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot, Event, PrivateMessageEvent
from nonebot.exception import ActionFailed
import re
import time
import urllib.parse
import requests
import json
import httpx
import asyncio
import subprocess

from .config import Config
from .fuzzymatch import match_id

__plugin_meta__ = PluginMetadata(
    name="gitcg",
    description="",
    usage="",
    config=Config,
)

ladder = on_command('天梯', priority=10)
@ladder.handle()
async def _(bot: Bot, event: Event):
    msg = event.get_message()
    uid = msg.to_rich_text().split()[-1].strip()
    global namemap

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(f"https://gi-tcg-ladder-api.guyutongxue.site/{uid}")
            response.raise_for_status()
            data = response.json()
            if data['success']:
                content = data['data']
                if content['is_block']:
                    return await ladder.finish("该用户疑似已被封禁，无法查询其天梯数据。")
                page_info = content['page_info']
                ladder_info = page_info['ladder_info']
                if ladder_info is None:
                    ladder_level_text = '已隐藏'
                    ladder_text = ''
                else:
                    ladder_level = ladder_info['large']
                    ladder_level_text = ['暂无段位', '黄铜', '星银', '赤金', '影幻'][ladder_level]
                    if ladder_level == 4:
                        ladder_text = f"/巅峰{page_info['peak_score']}分"
                    elif ladder_level == 0:
                        ladder_text = ''
                    else:
                        ladder_text = '★' * ladder_info['small']
                rank_num = page_info['rank_num']
                if rank_num in ['0', '']:
                    rank_num = '-'
                roles_text = '\n'.join([f"{role['name'] or next((item['name'] for item in namemap if item['id'] == role['card_id']), role['card_id'])} ♥ {role['proficiency']}" for role in page_info['roles']]) or '暂无'
                events_text = '\n'.join([f"{event['competition_name']} ♛ {event['label'] or event['competition_result']}" for event in page_info['entry_experience']]) or '暂无'
                result = f"{page_info['nickname']}【{ladder_level_text}{ladder_text}】\n天梯积分 {page_info['ladder_score']}\n赛事排名 {rank_num}\n赛事总分 {page_info['all_score']}\n赛事积分 {page_info['rank_score']}\n==========\n角色牌\n{roles_text}\n==========\n参赛经历\n{events_text}"
                return await ladder.finish(result)
            else:
                return await ladder.finish(f"failed: {data['message']}")
    
    except TypeError as e:
        return await ladder.finish(f'Error: {str(e)}')
    except httpx.RequestError as e:
        return await ladder.finish(f"Error: {str(e)}")

showData = on_command('七圣', aliases={'7s'}, priority=11, block=True)
showData2 = on_command('七圣2', aliases={'7s2', '7sb', '7sbeta'}, priority=10)

def load_namemap(file: str = "NameMap.json"):
    urls = [
        f"https://raw.githubusercontent.com/genius-invokation/nonebot_plugin_7s_card_img/refs/heads/main/map/{file}",
        f"http://170.106.83.133:8787/{file}?pull=true"
    ]
    local_path = f"/root/nb/dudubot/plugins/gitcg_share_code_to_image/{file}"
    for url in urls:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"远程获取NameMap失败: {e}，尝试下一个源")
    with open(local_path, "r", encoding="utf-8") as f:
        return json.load(f)

namemap = load_namemap()

SPECIAL_IMG_MAP = {
    "银狼": "https://7s-1304005994.cos.ap-singapore.myqcloud.com/银狼v6.png"
}

# 轮询（Round-Robin）尝试多个URL，并在所有尝试失败后发送最后一次错误信息
async def fetchImg(id: int | None, version: str, retry: int = 3, delay: float = 1.0):
    if id is None:
        return "未找到匹配的卡牌，请检查输入包含空格且正确。(beta: /7s2)"
    url = 'https://card-img-renderer.7shengzhaohuan.online/render'
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            payload = {
                'id': id,
                'version': version,
                'authorImageUrl': 'https://7s-1304005994.cos.ap-singapore.myqcloud.com/dudubot.png',
                'authorName': '数据来自测试服，请以正式服为准' if version == 'beta' else '谷雨同学 & clezn',
                'renderFormat': 'webp',
                'renderQuality': 0.75,
            }
            print(payload)
            response = await client.post(url, json=payload)
            data = response.json()
            if data['success']:
                img_url: str = data['url']
                _, base64 = img_url.split(',', 1)
                return MessageSegment.image(f"base64://{base64}")
            else:
                return f"failed: {response.text}"
    
    except httpx.RequestError as e:
        return f"Error: {str(e)}"

async def get_room_info(url: str, room_id: int):
    try:
        response = requests.get(f"{url}/api/rooms")
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        await showData.send(f"获取房间列表失败：{e}")
        return
    data = response.json()
    for item in data:
        if isinstance(item, dict) and item.get("id") == room_id:
            result = []
            result.append(f"房间号: {room_id}")
            result.append(f"观战设置: {'允许观战' if item.get('watchable') else '禁止观战'}")
            players = item.get("players", [])
            for player in players:
                name = f'玩家[{str(player.get("name", "")).strip()}]：'
                player_id = player.get("id", "")
                link = f"{url}/rooms/{room_id}?player={player_id}"
                result.extend([name, link])
            await showData.send("\n".join(result))
            return
    await showData.send("未找到{room_id}的房间信息，请检查房间号或服务器是否正确。")
    return 

@showData.handle()
async def _(bot: Bot, event: Event):
    msg = str(event.get_message())
    query = msg.split()[-1].strip()
    matched = match_id(query, namemap)
    seg = await fetchImg(id=matched, version='latest')
    await showData.finish(seg)

UnderMaintenance = False

@showData2.handle()
async def _(bot: Bot, event: Event):
    global UnderMaintenance
    global namemap
    protectGroupIds = []
    protectUserIds = []
    if event.user_id not in protectUserIds:
        if event.group_id not in protectGroupIds:
            await showData2.finish("beta数据限制群/用户使用，若需添加当前群至白名单，请联系嘟嘟可")
    msg = str(event.get_message())
    query = msg.split()[-1].strip()
    adminUser = (event.user_id in protectUserIds)
    if adminUser and query == "换班时间":
        UnderMaintenance = not UnderMaintenance
        if UnderMaintenance:
            await showData2.finish("开始维护(诚招卡牌别名维护志愿者)")
        else:
            namemap = load_namemap()
            await showData2.finish("维护完成(诚招卡牌别名维护志愿者)")
    if UnderMaintenance:
        if not adminUser:
            await showData2.finish("数据维护中，预计于次日2:00维护完成(诚招卡牌别名维护志愿者)")
        else:
            await showData2.send("有宝宝正在维护数据哦~(诚招卡牌别名维护志愿者)")
    query = msg.split()[-1].strip()
    matched = match_id(query, namemap)
    seg = await fetchImg(id=matched, version='beta')
    await showData2.finish(seg)

genshinImage = on_command('原神', aliases={'ys'}, priority=3)

@genshinImage.handle()
async def _(bot: Bot, event: Event):
    try:
        msg = str(event.get_message())
        query = msg.split()[-1].strip()
        if query == "雨酱":
            await genshinImage.finish(MessageSegment.image("https://7s-1304005994.cos.ap-singapore.myqcloud.com/ys-yujiang.jpg"))
        image = MessageSegment.image(f"https://api.guyutongxue.site/genshin-gelbooru?character={urllib.parse.quote(query)}")
        await showData.finish(image)
    except ActionFailed as e:
        await showData.finish(f'抱歉，{e}')

ciallo = on_keyword(["ciallo", "Ciallo"], block=False)

@ciallo.handle()
async def _():
    try:
        await ciallo.finish(MessageSegment.image(f"https://api.guyutongxue.site/ciallo?rand={time.time()}"))
    except ActionFailed as e:
        None

gelbooru = on_command('gelbooru', priority=10)
gelbooru_tag_search = on_command('gelbooru:tag_search', priority=11)

@gelbooru.handle()
async def _(bot: Bot, event: Event):
    try:
        msg = str(event.get_message())
        query = ' '.join(msg.split()[1:])
        await gelbooru.finish(MessageSegment.image(f"https://api.guyutongxue.site/gelbooru/?tags={urllib.parse.quote(query)}"))
    except ActionFailed as e:
        await gelbooru.finish(f'抱歉，{e}')

@gelbooru_tag_search.handle()
async def _(bot: Bot, event: Event):
    msg = str(event.get_message()).split(' ')
    if len(msg) != 2:
        await gelbooru_tag_search.finish('Usage: /gelbooru:tag_search <name_pattern>\n\n<name_pattern>: Tag name that can includes "%" as wildcard character.')
        return
    response = requests.get(f"https://api.guyutongxue.site/gelbooru/tags?pattern={urllib.parse.quote(msg[1])}")
    if response.status_code == 200:
        await gelbooru_tag_search.finish(MessageSegment.text(str(response.json())))
    else:
        await gelbooru_tag_search.finish(f"Error: {response.status_code}")

import subprocess
import threading

def run_process_with_timeout(executable, args, timeout):
    def target():
        nonlocal result, error
        try:
            completed_process = subprocess.run([executable] + args, capture_output=True, text=True, check=True)
            result = completed_process.stdout
            error = None
        except subprocess.CalledProcessError as e:
            result = None
            error = e.stderr

    result = None
    error = None
    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return f"Process exceeded timeout of {timeout} seconds"

    if error:
        return error
    return result

def truncate_string(input_string, max_length):
    if len(input_string) <= max_length:
        return input_string
    return input_string[:max_length] + "..."

node = on_command('js', priority=10)

import random
@node.handle()
async def _(bot: Bot, event: Event):
    message = event.get_message().extract_plain_text()[3:]
    is_danger = "pid" in message or "process" in message
    if is_danger or event.user_id in []:
        await node.finish("👆坏人哦")
        return
    is_esm = "import" in message or "export" in message
    output = run_process_with_timeout("/usr/bin/env", [
        "node",
        "--experimental-transform-types",
        "--experimental-permission",
        "--no-warnings=ExperimentalWarning",
        "-e" if is_esm else "-p",
        message
    ], 300)
    if matches := re.match(r"^data:image/[^;]+;base64,([A-Za-z0-9+/=]+)$", output.strip()):
        return await node.finish(MessageSegment.image(f"base64://{matches.group(1)}"))
    await node.finish(truncate_string(output, random.randint(60, 120)), at_sender=True)

rebase = on_command('rebase', priority=10)
@rebase.handle()
async def _(bot: Bot, event: Event):
    if event.user_id not in []:
        return await rebase.finish('no permission')
    
    response = requests.post('https://api.guyutongxue.site/github-api/repos/genius-invokation/genius-invokation-beta/actions/workflows/rebase_beta.yml/dispatches',
            json={"ref":"beta"},
            headers={
                "Authorization": "Bearer ghp_",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            })
    return await rebase.finish(f"Rebase request sent, status code: {response.status_code}, response: {response.text}")

from plugins.chat_oneapi import wrapMessageForward

yu7s = on_command("yu7s", aliases = {"y7s"})

import json
from collections import deque
from typing import List, Dict

def fetch_name_from_api(id: int) -> str:
    url = f"https://beta.assets.gi-tcg.guyutongxue.site/api/v3/data/{id}"
    try:
        data = requests.get(url, timeout=10)
        return data.json().get("name", f"{id} not found")
    except Exception as e:
        return "network error"

def process_dependencies(json_str: str, start_id: int) -> List[str]:
    """处理依赖关系并生成字符串列表"""
    # 解析JSON数据
    items = json.loads(json_str)
    data = {item["id"]: item for item in items}

    # 结果列表
    result = []
    # 待处理队列：(当前ID, 父ID)
    queue = deque([(start_id, None)])
    # 已处理集合，防止循环依赖
    processed = set()

    while queue:
        current_id, parent_id = queue.popleft()

        if current_id in processed:
            continue
        processed.add(current_id)

        item = data.get(current_id)
        if not item:
            continue

        # 获取名称
        name = fetch_name_from_api(current_id)
        # 位置信息
        loc = item["location"]
        location_str = f"{loc['filename']}:{loc['line']},{loc['column']}"

        # 构建条目字符串
        # 第一行显示父ID关系
        entry_lines = []
        if parent_id is None:
            entry_lines.append(f"{current_id}")
        else:
            entry_lines.append(f"child of {parent_id}: {current_id}")

        # 添加详细信息
        entry_lines.append(f"id: {current_id}")
        entry_lines.append(f"name: {name}")
        entry_lines.append(f"Location: {location_str}")
        entry_lines.append(f"dependencies: {item['dependencies']}")
        entry_lines.append("code:")
        # 格式化代码块（每行前加4空格）
        for line in item["code"].splitlines():
            entry_lines.append(f"    {line}")

        # 添加到结果
        result.append("\n".join(entry_lines))

        # 将依赖项加入队列
        for dep_id in item["dependencies"]:
            if dep_id not in processed:
                queue.append((dep_id, current_id))

    return result

@yu7s.handle()
async def _(bot: Bot, event: Event):
    msg = str(event.get_message())
    query = msg.split()[-1].strip()
    match_query = match_id(query, namemap)
    try:
        url = "https://gi-tcg.guyutongxue.site/data-code-analyze-result.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.text
            result = process_dependencies(data, int(match_query))
            print(result)
            msgs = wrapMessageForward(f"{match_query}", result)
            await bot.call_api("send_group_forward_msg", group_id=event.group_id, messages=msgs)
            base_url = "http://localhost:8013/render?q="
            base_url2 = "http://170.106.83.133:8013/render?q="
            await fetchImg([base_url, base_url2], match_query)
    except Exception as e:
        await yu7s.finish(f"{e}")
    

 

