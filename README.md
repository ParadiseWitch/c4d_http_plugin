# HTTP 控制服务器（Cinema 4D Python 插件）

该插件在 Cinema 4D 内部启动本地 HTTP 服务器，通过路由触发脚本动作。

- 默认主机/端口：`127.0.0.1:8090`
- 路由：
  - `GET /ping` → 健康检查，返回 `{"status":"succ","data":{"msg":"服务正常"}}`
  - `GET /get_joint` → 检查当前 C4D 文件中是否存在关节对象，返回 `{"status":"succ","data":{"hasJoint":true|false}}`
  - `GET /get_animation` → 检查当前 C4D 文件中是否存在动画，返回 `{"status":"succ","data":{"hasAnimation":true|false}}`
  - `GET /play` → 跳转到第一帧后执行一次单次播放
  - `GET /get_play_status` → 查询当前工程的播放状态，可用于客户端轮询
  - `GET /show_joint?isShow=true|false` → 控制所有关节/骨骼显隐（同步），返回 `{"status":"succ","data":{"visible":true|false}}`
  - `GET /show_polygon?isShow=true|false` → 控制所有多边形对象显隐（同步），返回 `{"status":"succ","data":{"visible":true|false}}`
  - `GET /open_project?path=...` → 打开指定 C4D 文件（会关闭之前的文档）
  - `GET /set_display_mode?displayMode=光影着色` → 切换当前文件活动视图的显示模式
  - `GET /select_weight_tag?isSelect=true|false` → 选中或取消选中当前文档中的权重标签
  - `GET /set_layout?layoutName=111` → 切换到名为 `111` 的界面布局
- 同步行为：所有变更路由在 C4D 主线程执行并完成后才返回响应。
- 菜单：在“Plugins > HTTP Control: Start/Stop”切换服务器状态。
 - 配置环境变量：`C4D_HTTP_HOST`、`C4D_HTTP_PORT`

## 模块化 API

HTTP 服务和主线程任务切换已经抽到 `http/` 包中，插件层按下面的方式注册路由：

```python
from http import Http

http = Http(port=8090, host="127.0.0.1", message_plugin_id=MESSAGE_PLUGIN_ID)
http.route("ping", handle_ping)
http.route("show_joint", handle_show_joint)


def handle_ping():
    return json.dumps({"status": "succ", "data": {"msg": "服务正常"}}, ensure_ascii=False)


def handle_show_joint(request):
    is_show = request.get_param("isShow", "true")
    return json.dumps({"status": "succ", "data": {"isShow": is_show}}, ensure_ascii=False)
```

其中 `request` 参数是可选的。处理函数不接参数时，`Http` 会直接调用；需要读取查询参数时，可以接收一个 `HttpRequest` 实例并通过 `get_param()` 取值。

## 安装

1. 将整个 `http_control_server` 文件夹复制到 Cinema 4D 的 `plugins` 目录，例如：
   - Windows：`C:\\Program Files\\Maxon Cinema 4D Rxx\\plugins\\`
   - 或用户首选项的插件目录。复制完成后重启 Cinema 4D。
2. 启动时服务器会自动启动，也可在插件菜单中手动切换。

## 使用与测试

- 使用浏览器或 curl 访问：
  - `http://127.0.0.1:8090/ping`
  - `http://127.0.0.1:8090/get_joint` → 返回 `{"status":"succ","data":{"hasJoint":true}}`
  - `http://127.0.0.1:8090/get_animation` → 返回 `{"status":"succ","data":{"hasAnimation":true}}`
  - `http://127.0.0.1:8090/play` → 立即启动播放并返回 `{"status":"succ","data":{"toggled":true}}`
  - `http://127.0.0.1:8090/get_play_status` → 返回当前播放状态，例如 `{"status":"succ","data":{"isPlaying":false}}`
  - `http://127.0.0.1:8090/show_joint?isShow=false` → 返回 `{"status":"succ","data":{"visible":false}}`
  - `http://127.0.0.1:8090/show_joint?isShow=true` → 返回 `{"status":"succ","data":{"visible":true}}`
  - `http://127.0.0.1:8090/show_polygon?isShow=false`
  - `http://127.0.0.1:8090/open_project?path=C:%5Cpath%5Cto%5Cscene.c4d`
  - `http://127.0.0.1:8090/set_display_mode?displayMode=%E5%85%89%E5%BD%B1%E7%9D%80%E8%89%B2`
  - `http://127.0.0.1:8090/select_weight_tag?isSelect=true`
  - `http://127.0.0.1:8090/set_layout?layoutName=111`

`set_display_mode` 当前支持的显示模式名称：

- `光影着色`
- `快速着色`
- `常量着色`
- `隐藏线条`
- `线框`
  
PowerShell 设置端口示例：
```
$env:C4D_HTTP_HOST='127.0.0.1'; $env:C4D_HTTP_PORT='8090'
```

## 项目结构

- `http_control_server.pyp`：插件入口，注册组件
- `http_control_server.pyp`：插件 ID、环境配置、Command/Message 注册逻辑
- `http/`：通用 HTTP 服务、请求对象、主线程任务派发
- `routes.py`：业务路由注册与 C4D 场景操作

## 备注

- 网络在后台线程处理；对场景的任何修改均在 C4D 主线程执行，安全可靠。
- 首次运行可能触发防火墙提示，请允许本地访问。
