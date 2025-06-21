from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.plugin import on_command,on_regex,on_command,on_keyword
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.exception import ActionFailed
import re
import time
import urllib.parse
import requests
import json
import httpx
import asyncio

from .config import Config
from .fuzzymatch import match_id

__plugin_meta__ = PluginMetadata(
    name="7s_card_img",
    description="七圣召唤卡牌图片生成，支持别名",
    usage="/7s <卡牌名称> （仅正式服） ；  \n/7s2 <卡牌名称> （含测试服） \n /7s3 <卡牌名称> （wip文件）",
    config=Config,
)

showData = on_command('七圣', aliases={'7s'}, priority=11, block=True)
showData2 = on_command('七圣2', aliases={'7s2'}, priority=10)
showData3 = on_command('七圣3', aliases={'7s3'}, priority=10)


with open("./NameMap.json", "r", encoding="utf-8") as f:
    namemap = json.load(f)

# 下方base_url 实际后端url来自仓库 https://github.com/genius-invokation/beautiful-card-img-gen 的服务
async def fetchImg(urls: list[str], query: str, retry: int = 5, delay: float = 1.0):
    for base_url in urls:
        url = f"{base_url}{urllib.parse.quote(query)}"
        print(f"尝试 URL: {url}")
        for attempt in range(1, retry + 1):
            try:
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    response = await client.get(url)
                    status = response.status_code
                    content_type = response.headers.get("Content-Type", "")

                    if status == 200 and "image" in content_type:
                        await showData.send(MessageSegment.image(url))
                        return
                    elif status == 500:
                        print(response.text)
                        await showData.send(f"\"{query}\" not found. Code {status}.")
                        return
                    else:
                        await showData.send(f"Code {status}: Unknown Error.")
                        return
            except httpx.RequestError as e:
                print(f"请求失败（第 {attempt} 次）：{e}")
                if attempt < retry:
                    await asyncio.sleep(delay)
                else:
                    break
        await showData.send(f"Auto Retry(/)")
    await showData.send("Failed: Network Error.")
    return
                

@showData.handle()
async def _(bot: Bot, event: Event):
    msg = str(event.get_message())
    query = msg.split()[-1].strip()
    metch_query = match_id(query, namemap)
    base_url = "http://localhost:8013/render?q="
    base_url2 = "http://170.106.83.133:8013/render?q="
    await fetchImg([base_url, base_url2], metch_query)

UnderMaintenance = False

@showData2.handle()
async def _(bot: Bot, event: Event):
    global UnderMaintenance
    global namemap
    protectGroupIds = [] # 白名单群号，自配
    protectUserIds = [] # 白名单qq号，自配
    if event.user_id not in protectUserIds:
        if event.group_id not in protectGroupIds:
            await showData2.finish("beta数据限制群/用户使用，若需添加当前群至白名单，请联系嘟嘟可")
    msg = str(event.get_message())
    query = msg.split()[-1].strip()
    adminUser = (event.user_id in protectUserIds)
    if adminUser and query == "换班时间":
        UnderMaintenance = not UnderMaintenance
        if UnderMaintenance:
            await showData2.finish("开始维护")
        else:
            with open("/root/nb/dudubot/plugins/gitcg_share_code_to_image/NameMap.json", "r", encoding="utf-8") as f:
                namemap = json.load(f)
            await showData2.finish("维护完成")
    if UnderMaintenance:
        if not adminUser:
            await showData2.finish("数据维护中，预计于次日2:00维护完成")
        else:
            await showData2.send("有宝宝正在维护数据哦~")
    query = msg.split()[-1].strip()
    metch_query = match_id(query, namemap)
    base_url = "http://localhost:8013/render?beta=true&q="
    base_url2 = "http://localhost:8013/render?beta=true&q="
    await fetchImg([base_url, base_url2], metch_query)

@showData3.handle()
async def _(bot: Bot, event: Event):
    msg = str(event.get_message())
    query = msg.split()[-1].strip()
    with open("./NameMap.wip.json", "r", encoding="utf-8") as f:
        namemap2 = json.load(f)
        metch_query = match_id(query, namemap2)
        base_url = "http://localhost:8013/render?q="
        await fetchImg([base_url], metch_query)