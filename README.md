# HTTP 控制服务器（Cinema 4D Python 插件）

该插件在 Cinema 4D 内部启动本地 HTTP 服务器，通过路由触发脚本动作。

- 默认主机/端口：`127.0.0.1:8090`
- 路由：
  - `GET /ping` → 健康检查，返回 `pong`
  - `GET /hide_joint` → 隐藏所有关节/骨骼（同步：完成后返回 `{visible:false}`）
  - `GET /show_joint` → 显示所有关节/骨骼（同步：完成后返回 `{visible:true}`）
- 同步行为：所有变更路由在 C4D 主线程执行并完成后才返回响应。
- 菜单：在“Plugins > HTTP Control: Start/Stop”切换服务器状态。
 - 配置环境变量：`C4D_HTTP_HOST`、`C4D_HTTP_PORT`

## 安装

1. 将整个 `http_control_server` 文件夹复制到 Cinema 4D 的 `plugins` 目录，例如：
   - Windows：`C:\\Program Files\\Maxon Cinema 4D Rxx\\plugins\\`
   - 或用户首选项的插件目录。复制完成后重启 Cinema 4D。
2. 启动时服务器会自动启动，也可在插件菜单中手动切换。

## 使用与测试

- 使用浏览器或 curl 访问：
  - `http://127.0.0.1:8090/ping`
  - `http://127.0.0.1:8090/hide_joint` → 返回 `{"ok":true,"visible":false}`
  - `http://127.0.0.1:8090/show_joint` → 返回 `{"ok":true,"visible":true}`
  
PowerShell 设置端口示例：
```
$env:C4D_HTTP_HOST='127.0.0.1'; $env:C4D_HTTP_PORT='8090'
```

## 项目结构

- `http_control_server.pyp`：插件入口，注册组件
- `plugin.py`：Command/Message 插件与注册逻辑
- `server.py`：HTTP 服务器与路由
- `tasks.py`：任务队列与主线程处理（SpecialEvent）
- `operations.py`：场景操作（设置关节可见性）
- `constants.py`：插件 ID、环境配置读取

## 备注

- 网络在后台线程处理；对场景的任何修改均在 C4D 主线程执行，安全可靠。
- 首次运行可能触发防火墙提示，请允许本地访问。
