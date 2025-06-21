## nonebot七圣卡图生成插件

如需部署，自己搭建后端服务[beautiful-card-img-gen](https://github.com/genius-invokation/beautiful-card-img-gen) 然后改代码，装插件。

## 别名维护

别名文件在`map`文件夹下，`NameMap.json` 是 bot 读取的版本。

### 修改别名

直接在`NameMap.json`里修改对应卡牌的aliases属性。

### 增加beta版本的新卡

请先生成带有新卡的模板。
```
python3 beta_template.py
```

（需要pip安装package pypinyin）

会生成`NameMap.wip.json`，请和`NameMap.json`比对，将新增的新卡部分修改别名，加入到`NameMap.json`里。


## 如需帮助

- bot群：1030307936 

![qrcode_1744131886442.jpg](https://7s-1304005994.cos.ap-singapore.myqcloud.com/qrcode_1744131886442.jpg)





