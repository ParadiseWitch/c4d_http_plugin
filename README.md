# CloudView Animation HTTP Control（Cinema 4D Python 插件）

该插件会在 Cinema 4D 内启动一个本地 HTTP 服务，外部程序可通过 `GET` 路由查询场景状态或触发编辑器操作。

当前代码基于 Cinema 4D R19 的 Python 2.7 环境编写。

## 功能概览

- 默认监听地址：`127.0.0.1:8090`
- 支持通过 HTTP 查询当前工程是否包含骨骼、动画、是否正在播放
- 支持通过 HTTP 控制关节、多边形显示状态
- 支持一键切入摄像机视角或自动居中几何体模型
- 支持打开工程、切换视图显示模式、切换布局
- 支持设置当前活动视图的近裁剪与远裁剪范围
- 所有会操作 C4D 文档或界面的逻辑，都会切回主线程执行

## 项目结构

- `main.pyp`：插件入口，负责注册命令插件、消息插件，以及启动/停止 HTTP 服务
- `routes.py`：业务路由注册与处理逻辑
- `utils.py`：场景遍历、显示控制、布局切换等工具函数
- `http/core.py`：HTTP 服务、请求封装、主线程任务调度
- `http/runtime.py`：当前 HTTP 服务实例共享状态
- `http/__init__.py`：HTTP 子模块导出入口

## 安装

1. 将整个 `cloudview_animation` 文件夹复制到 Cinema 4D 的 `plugins` 目录。
2. 重启 Cinema 4D。
3. 插件加载后会自动启动 HTTP 服务。
4. 也可以通过菜单 `Plugins -> HTTP Control: Start/Stop` 手动切换服务状态。

## 配置

可通过环境变量覆盖默认监听地址：

- `C4D_HTTP_HOST`：默认 `127.0.0.1`
- `C4D_HTTP_PORT`：默认 `8090`

PowerShell 示例：

```powershell
$env:C4D_HTTP_HOST = '127.0.0.1'
$env:C4D_HTTP_PORT = '8090'
```

## 返回格式

成功时统一返回：

```json
{"status":"succ","data":{}}
```

失败时统一返回：

```json
{"status":"erro","msg":"错误信息"}
```

## 路由列表

### 1. 健康检查

- `GET /ping`
- 返回示例：

```json
{"status":"succ","data":{"msg":"pong"}}
```

### 2. 查询是否存在关节

- `GET /get_joint`
- 返回字段：
  - `hasJoint`：当前文档中是否存在关节或骨骼对象

示例：

```json
{"status":"succ","data":{"hasJoint":true}}
```

### 3. 查询是否存在动画

- `GET /get_animation`
- 返回字段：
  - `hasAnimation`：当前文档中是否检测到关键帧动画

示例：

```json
{"status":"succ","data":{"hasAnimation":false}}
```

### 4. 播放动画

- `GET /play`
- 行为：
  - 切换为单次播放
  - 跳转到第一帧
  - 开始播放

示例：

```json
{"status":"succ","data":{}}
```

### 5. 查询播放状态

- `GET /is_playing`
- 返回字段：
  - `is_playing`：当前是否处于播放状态

示例：

```json
{"status":"succ","data":{"is_playing":true}}
```

### 6. 显示或隐藏关节

- `GET /show_joint?isShow=true|false`
- 参数：
  - `isShow`：可选，默认 `true`
- 行为：
  - 批量设置关节对象编辑器可见性
  - 同步切换当前活动视图的关节显示过滤器

示例：

```json
{"status":"succ","data":{"visible":false}}
```

### 7. 显示或隐藏多边形

- `GET /show_polygon?isShow=true|false`
- 参数：
  - `isShow`：可选，默认 `true`
- 行为：
  - 批量设置多边形对象编辑器可见性
  - 同步切换活动视图中的多边形、样条、生成器等显示过滤器

示例：

```json
{"status":"succ","data":{"visible":true}}
```

### 8. 选中或取消选中权重标签

- `GET /show_weight?isShow=true|false`
- 参数：
  - `isShow`：可选，默认 `false`

示例：

```json
{ "status": "succ", "data": { "visible": false } }
```

### 9. 打开工程文件

- `GET /open_project?path=...`
- 参数：
  - `path`：必填，目标 `.c4d` 文件路径
- 行为：
  - 加载目标工程
  - 切换为活动文档
  - 尝试关闭之前的活动文档

成功示例：

```json
{"status":"succ","data":{"opened":"C:\\path\\to\\scene.c4d"}}
```

失败示例：

```json
{"status":"erro","msg":"工程文件不存在: C:\\path\\to\\scene.c4d"}
```

### 10. 切换活动视图显示模式

- `GET /set_display_mode?displayMode=...`
- 参数：
  - `displayMode`：必填，显示模式名称

当前支持：

- `光影着色`
- `快速着色`
- `常量着色`
- `隐藏线条`
- `线框`

成功示例：

```json
{"status":"succ","data":{"displayMode":6,"displayModeName":"光影着色"}}
```

### 11. 切换布局

- `GET /set_layout?layoutName=...`
- 参数：
  - `layoutName`：必填，布局名称或 `.l4d` 文件路径
- 行为：
  - 在常见布局目录中递归查找目标布局文件
  - 找到后加载布局并刷新界面

成功示例：

```json
{"status":"succ","data":{"layoutName":"111","layoutPath":"C:\\...\\111.l4d"}}
```

### 12. 设置活动视图裁剪范围

- `GET /set_view_clipping?nearCm=0&farCm=2147483647`
- 参数：
  - `nearCm`：可选，近裁剪距离，单位厘米，默认 `0`
  - `farCm`：可选，远裁剪距离，单位厘米，默认 `2147483647`
- 行为：
  - 设置当前文档“工程设置”中的视图近裁剪与远裁剪范围
  - 自动将裁剪预设切换为自定义
  - 刷新当前活动视图

成功示例：

```json
{"status":"succ","data":{"nearCm":0.0,"farCm":2147483647.0}}
```

### 13. 切入摄像机或居中模型

- `GET /center_model`
- 行为：
  - 如果场景中存在摄像机对象，则将当前活动视图切换到第一个摄像机视角
  - 如果场景中没有摄像机对象，则切回编辑器摄像机并执行 `Frame Geometry`

成功示例：

```json
{"status":"succ","data":{"mode":"camera","cameraName":"Camera"}}
```

```json
{"status":"succ","data":{"mode":"geometry"}}
```

## 手动验证

Cinema 4D 加载插件后，可使用以下命令检查：

```bash
curl http://127.0.0.1:8090/ping
curl http://127.0.0.1:8090/get_joint
curl http://127.0.0.1:8090/get_animation
curl http://127.0.0.1:8090/is_playing
curl "http://127.0.0.1:8090/show_joint?isShow=false"
curl "http://127.0.0.1:8090/show_joint?isShow=true"
curl "http://127.0.0.1:8090/show_polygon?isShow=false"
curl "http://127.0.0.1:8090/show_polygon?isShow=true"
curl "http://127.0.0.1:8090/show_weight?isShow=true"
curl "http://127.0.0.1:8090/open_project?path=C:%5Cpath%5Cto%5Cscene.c4d"
curl "http://127.0.0.1:8090/set_display_mode?displayMode=%E5%85%89%E5%BD%B1%E7%9D%80%E8%89%B2"
curl "http://127.0.0.1:8090/set_view_clipping?nearCm=0&farCm=2147483647"
curl "http://127.0.0.1:8090/set_layout?layoutName=111"
curl "http://127.0.0.1:8090/center_model"
```

建议同时检查：

- C4D Console 中是否有异常日志
- 菜单 `Plugins -> HTTP Control: Start/Stop` 是否可以正常启停服务
- `show_joint` 和 `show_polygon` 是否正确影响编辑器可见性

## 开发说明

- HTTP 请求由后台线程接收
- 路由处理会被投递到 C4D 主线程执行，以避免直接跨线程操作场景
- 当前插件仅注册 `GET` 路由
- 建议默认绑定 `127.0.0.1`，避免在不可信网络暴露服务
