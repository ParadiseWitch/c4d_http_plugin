# 仓库指南

## 项目结构与模块组织

- 根插件：`http_control_server`（Cinema 4D Python 插件, c4d执行时使用的是2.7版本的python解释器）。
- 入口模块：`http_control_server.pyp`（路由、服务器生命周期、菜单）。
- 文档：`README.md`（安装、路由、用法）。

## 构建、测试与开发命令

- 无构建步骤：该项目为基于 Python 的 C4D 插件。
- 手动路由检查（C4D 加载插件后）：
-  - `curl http://127.0.0.1:8090/ping`
-  - `curl "http://127.0.0.1:8090/show_joint?isShow=false"`
-  - `curl "http://127.0.0.1:8090/show_joint?isShow=true"`
- 界面切换：Plugins → “HTTP Control: Start/Stop”（验证菜单联动）。

## 代码风格与命名约定

- Python 风格：PEP 8；4 空格缩进；UTF-8 编码。
- 命名：函数/路由用 `snake_case`，类用 `PascalCase`，常量用 `UPPER_CASE`。
- 路由处理函数：使用清晰命名（如 `handle_show_joint`）。

## 测试指南

- 范围：通过 HTTP 路由进行手动集成测试。
- 预期：`/ping` 返回 200；`/show_joint?isShow=...` 和 `/show_polygon?isShow=...` 应更新编辑器中的可见性。
- 校验：查看 C4D Console 日志/错误；确认菜单切换能正常启停服务器。

## 提交与合并请求指南

- 提交：使用祈使句、聚焦改动。例如：`routes: add /mute_audio`，`server: fix shutdown race`。
- PR：包含摘要、复现/验证步骤（curl 命令），必要时附控制台输出或截图。
- 关联相关 issue；注明配置或 ID 变更。

## 安全与配置提示

- 本地工作流建议绑定 `127.0.0.1`；在不可信网络避免使用 `0.0.0.0`。
- 校验查询/路径输入；避免在主线程执行耗时任务。
