[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/c1pher-cn-ha-mcp-for-xiaozhi-badge.png)](https://mseep.ai/app/c1pher-cn-ha-mcp-for-xiaozhi)


## ha-mcp-for-xiaozhi

<p align="center">
  <img src="https://raw.githubusercontent.com/c1pher-cn/brands/refs/heads/master/custom_integrations/ws_mcp_server/icon.png" alt="Alt Text" align="center">
</p>  

<p align="center"> 
Homeassistant MCP server for 小智AI，直连小智AI官方服务器。
</p>



### 插件能力介绍
#### 1.HomeAssistant自身作为mcp server 以websocket协议直接对接虾哥服务器，无需中转
#### 2.在一个实体里同时选择多个API组（HomeAssistant自带控制API、用户自己配置的MCPServer）并将它们一起代理给小智
#### 3.支持同时配置多个实体

！！！注意，v0.0.8 版本需要使用2025.7.0及以后版的HomeAssistant， 2025.3-2025.6版本的homeassistant 请使用 v0.0.7 谢谢配合！！！
---
### 功能演示（为爱发电不易，有币投投币、没币点点赞、刷几个弹幕也行）

<a href="https://www.bilibili.com/video/BV1FMFyejExX" > 接入演示视频 </a>

<a href="https://www.bilibili.com/video/BV18DM8zuEYV" > 控制电视演示（通过自定义script实现）</a>

---
 
### 安装方法：

确保Home Assistant中已安装HACS

1.打开HACS, 点击[Custom repositories], Repository 输入本项目地址: https://github.com/c1pher-cn/ha-mcp-for-xiaozhi

2.Category 选择 [Integration]

![5e1048c4fbd23d3385c09985fd09b50e](https://github.com/user-attachments/assets/db5431c6-35cf-49b4-bd0e-f2c2296df641)

3.下载插件
![d20fa7d2367fecc35bd8914b1f508ea6](https://github.com/user-attachments/assets/a8447eb4-7659-4c3e-98b1-4dbe5a6d4b30)

4.重启Home Assistant.


### 配置方法：

[设置 > 设备与服务 > 添加集成] > 搜索“Mcp” >找到MCP Server for Xiaozhi
![8ca5334a2d15f59325f3d5acb12083c8](https://github.com/user-attachments/assets/89212647-d572-45d2-98f2-60ba59203b04)


下一步 > 请填写小智MCP接入点地址 > 提交。
![6f4b22e8bd8190d4f0faeaba731481f9](https://github.com/user-attachments/assets/2f70b30c-7ced-4505-ac80-00d1a6a8280e)

配置完成！！！稍等一分钟后到小智的接入点页面点击刷新，检查状态。
![bd06b555b9e5c24fbf819c43397c97ee](https://github.com/user-attachments/assets/ace79a44-6197-4e94-8c49-ab9048ed4502)



---

### 调试说明

 1.暴露的工具取决于你公开给Homeassistant语音助手的实体的种类
 
    设置 -> 语音助手 -> 公开
   
 2.尽量使用最新版本的homeassistant，单单看5月版本跟3月版本提供的工具就有明显差异

 3.调试时未达到预期，优先看小智的聊天记录，看看小智对这句指令如何处理的，是否有调用homeassistant的工具。目前已知比较大的问题是灯光控制和音乐控制会和内置的屏幕控制、音乐控制逻辑冲突，需要等下个月虾哥服务器支持内置工具选择后可解。

 4.如果流程正确的调用了ha内置的function，可以打开本插件的调试日志再去观测实际的执行情况。
 
---

<a href="https://star-history.com/#c1pher-cn/ha-mcp-for-xiaozhi&Date"></a>

 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=c1pher-cn/ha-mcp-for-xiaozhi&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=c1pher-cn/ha-mcp-for-xiaozhi&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=c1pher-cn/ha-mcp-for-xiaozhi&type=Date" />
 </picture>
</a>


 
 

