# 干嘛用的

在docker中启动Telegram客户端，将你账号收到的群聊消息（经过处理）后存入数据库，调用OpenAI兼容的API总结群聊内容。同时也支持使用Dify、Coze等工具和平台自建工作流调用。

经过的处理有：
[x] 判断是否符合黑/白名单定义，保存或丢弃消息。
[x] 命中环境变量中的关键词将被丢弃。
[x] 机器人(is_bot=true)发送的消息将被过滤。
[x] 单条消息是否超过300字符，超过的部分将被截断，减少API调用时遇到413错误的可能性。
[x] 多行文本的消息将被合并为一行，使用空格代替\\n.
[x] 不接收图片、视频等消息，仅接受文本消息。

用不用的，看到就给点个星吧，鼓励一下，我不喝咖啡。

# 怎么安装
## 前提条件

1、你需要有TG账号的API权限。 
2、你需要已经安装docker compose
3、你需要已经安装PgSQL
4、先看完下面的内容，再决定要不要用

申请TG的API权限：https://my.telegram.org/apps

# 使用方法

### 1.克隆仓库
```bash
git clone https://github.com/ShiFangJuMie/Telegram_Messages_Helper.git
cd Telegram_Messages_Helper
```

### 2.创建数据库环境

将`app/data/postgres.sql`导入到你的postgres中。

我不喜欢同一个主机上不同的项目各自部署多个postgres，所以你需要自己部署。

传送门 https://hub.docker.com/_/postgres

```bash
# 在此版本下测试通过，理论上也能兼容其他版本，根据个人喜好选择
docker pull postgres:16.1-alpine
```

### 3.编辑环境变量并部署
```bash
# 创建docker镜像
docker build -t telegram_messages_helper:latest .
# 根据你的情况修改docker compose中的环境变量
vim docker-compose.yml
# 然后开始构建镜像并部署
docker compose up -d
```
### 4.登录你的TG账号
你需要先将账号登录到容器中。在docker容器运行后，你需要以下几个步骤：

```bash
# 进入容器内部
docker exec -it telegram_messages_helper bash
# 手动执行初始化命令
python setup.py
```

在执行这个命令后，你需要和命令行进行2-3次交互，他们分别是：TG手机号、登录2FA验证码、密码示例如下

```
Please enter your phone (or bot token): +1 1234567890
Please enter the code you received: 12345
Please enter your password: 
```

如果你的登录成功了，你会看到这样的提示：

```
Signed in successfully as <你的昵称>; remember to not break the ToS or you will risk an account ban!
Group Title: 群聊名字 | Chat ID: -1001680975xxx
Group Title: 群聊名字 | Chat ID: -1001239150xxx
```

通过Group Title找到你想“总结”或不想总结的群，记下它的Chat ID。
### (可选步骤) 配置群组黑白名单

如果你需要使用群组的黑/白名单，setup之后你才拥有了Chat ID，所以再次修改你的docker-compose.yml，根据需要设置环境变量 `TELEGRAM_WHITELIST_CHAT`和`TELEGRAM_BLACKLIST_CHAT`

> 不过我建议的是先观察一阵子，然后从数据库中筛选要总结或要过滤的群组，一次性的设置。

### 5.重启容器
在你完成所有的设置后，重启一次容器。

### 6. 查看消息与总结
#### 查看聊天记录
> 当你想要使用dify、coze等平台实现工作流时，可以通过此路径获取获取原始文本。
> 输出中可以使用关键词“当前为最后一页”和“没有更多的记录了”供工作流判断。
https://xxx.com/?auth=om34V4s958c9d345&page=1

可用参数：

| 参数 | 用途                     |
| --------------------- | ---------------------- |
| page=1                | 页码，默认1                 |
| all=true              | 忽略分页，将所有记录全部输出，默认false |
| start_date=YYYY-MM-DD | 查看指定一天的记录，默认前一天        |
| auth                  | 必填，与环境变量AUTH_CODE一致    |
#### 查看AI总结后的内容
https://xxx.com/summary?auth=om34V4s958c9d345

可用参数：

| 参数                    | 用途                  |
| --------------------- | ------------------- |
| start_date=YYYY-MM-DD | 查看指定一天的记录，默认前一天     |
| auth                  | 必填，与环境变量AUTH_CODE一致 |
# 自定义设置
计划任务的触发由`script_scheduler.py`驱动

如果你希望使用dify、coze等工具进行总结，你应该删除其中的`script_aigc.py`，防止重复总结和token浪费。

| 文件 | 用途                     |
| --------------------- | ----------------------------- |
| script_aggregated.py  | 每天将群组消息合并                     |
| script_aigc.py        | 请求API进行AI总结(可删除)              |
| script_cleanup.py     | 删除7天前的消息                      |
| script_sync_wechat.py | 将微信bot接收到的群聊同步到统一数据库(此功能尚未发布) |

总结群聊时的提示词在`prompt.txt`中定义
# FAQ
### 掉线/换号怎么办
1、删除app目录下的xxxx.session这个文件，你就掉线了。修改环境变量TELEGRAM_SESSION你就换号了
2、掉线/换号后，需要使用setup.py重新登录
3、登录成功后，重启容器

### 可以与我的桌面/手机客户端同时在线吗
可以

### 如何获取Chat ID
在setup时只能获取到一部分，但并不是全部，剩下的部分建议从数据库中获取。
```sql
select chat_id,chat_name from messages_aggregated;
```

### 申请TG API权限不成功
申请时，名字和介绍不要随手乱打，有被拒的亲身经历，几点经验：
1、申请时提示ERROR没关系，可以继续点，我第一次申请点了几千次（后来确认是IP的原因）。
2、我在热心大佬的点拨之下，改用与注册手机号相同国家的**家庭宽带IP**，大陆+86手机用台湾香港IP试，试了几次就成功了。
3、登录到TG API申请页面后，更换IP会掉线，短时间内登录次数有限制，是正常情况。

### AI总结失败，413错误

413错误就是文本太长了，超出了API可以接受的上限。
你可以：
 - 检查该群组中是否存在大量无用的信息，选择性的在环境变量中过滤掉无效信息。（如重复长文本的广告和骚扰信息）
 - 更换一个支持更大上下文的模型。ChatGPT普通号的4o处理量很小，可以使用 deanxv/coze-discord-proxy 大佬的项目获取更大的gpt-4o上下文能力。感谢LinuxDo @Dean大佬。
 - 如果你使用了CDP，请将你的Bot设置中Dialog round调整到最大值（30轮）
