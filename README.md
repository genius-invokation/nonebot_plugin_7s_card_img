## nonebot七圣卡图生成插件

如需部署，自己搭建后端服务[beautiful-card-img-gen](https://github.com/genius-invokation/beautiful-card-img-gen) 然后改代码，装插件。

## 别名维护

`map`文件夹下有 2 个你需要关注的文件：
- `NameMap.json`，目前正在使用的别名表
- `NameMap.wip.json`，第1步运行Python脚本得到的带有新卡的别名表，已合并使用中的别名表。

你需要做的是：

1. 如果你是增加beta版本的新卡，请先生成新模板。否则跳过此步。

```
python3 beta_template.py
```

（需要pip安装package pypinyin）


2. 修改`NameMap.wip.json`，具体地，修改各个卡牌的aliases即可。

3. 比对`NameMap.json` 和 `NameMap.wip.json`，看看是否符合你的预期。

（如果你很熟练，可以直接改`NameMap.json`）



## 如需帮助

- bot群：1030307936 

![qrcode_1744131886442.jpg](https://7s-1304005994.cos.ap-singapore.myqcloud.com/qrcode_1744131886442.jpg)





