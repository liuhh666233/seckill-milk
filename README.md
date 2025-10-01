# 多用户秒杀系统 v2.0

一个支持多用户、多策略的通用秒杀系统，支持定时任务和多种通知功能。

## ✨ 新特性 (v2.0)

- 🏗️ **全新架构**：采用分层架构设计，模块化程度更高
- 🔧 **策略模式**：支持多种加密和请求策略，易于扩展
- 📝 **配置管理**：统一的配置管理和验证系统
- 🔔 **多通知服务**：支持飞书、微信等多种通知方式
- ⏰ **精确调度**：高精度时间同步和任务调度
- 🛡️ **错误处理**：统一的异常处理和日志系统
- 📚 **完整文档**：详细的API文档和使用示例

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js (用于JavaScript执行)
- Nix (推荐使用nix develop环境)

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/seckill-milk.git
cd seckill-milk

# 使用nix开发环境（推荐）
nix develop

```

### 基本使用

```bash
# 在nix develop环境中运行
nix develop 
python main.py seckill --config kudicookie.json

# 启动调度器
python main.py scheduler --mode watch

# 验证配置文件
python main.py validate --config kudicookie.json

# 创建默认配置
python main.py create-config --output default.json
```

### Python API

```python
from core.seckill import SeckillManager
from core.scheduler import SeckillScheduler

# 运行秒杀
manager = SeckillManager(config_file="kudicookie.json")
manager.run()

# 启动调度器
scheduler = SeckillScheduler()
scheduler.watch_mode()
```

## 📁 项目结构

```
seckill-milk/
├── core/                    # 核心业务层
│   ├── seckill/            # 秒杀核心模块
│   ├── scheduler/          # 调度核心模块
│   └── notification/       # 通知核心模块
├── strategies/             # 策略层
│   ├── encryption/         # 加密策略
│   └── request/            # 请求策略
├── config/                 # 配置层
├── utils/                  # 工具层
├── legacy/                 # 原有代码（保持兼容）
├── examples/               # 使用示例
├── main.py                 # 主入口
└── requirements.txt        # 依赖文件
```

## 🔧 配置说明

### 秒杀配置文件

```json
{
    "start_time": "12:00:00.000",
    "proxies": "http://proxy.example.com",
    "users": [
        {
            "account_name": "用户1",
            "cookie_id": "cookie_id",
            "cookie_name": "cookie",
            "basurl": "https://example.com/api",
            "headers": {
                "User-Agent": "Mozilla/5.0"
            },
            "data": {
                "param1": "value1"
            },
            "max_attempts": 10,
            "thread_count": 5,
            "strategy_flag": "mixue",
            "strategy_params": {
                "marketingId": "test_id"
            }
        }
    ],
    "mixues": [
        {
            "marketingId": "test_id",
            "round": "test_round",
            "secretword": "test_word"
        }
    ],
    "bw_keywords": "关键词1,关键词2"
}
```

### 调度配置文件

```json
{
    "10": [
        {
            "start_time": "09:59:59.950",
            "config_file": "./configs/jd/301-300.json",
            "enabled": true,
            "description": "09点59分整点秒杀任务"
        }
    ]
}
```

## 🎯 支持策略

### 请求策略

- **default**: 默认策略
- **mixue**: 蜜雪冰城策略
- **kudi**: 库迪咖啡策略
- **jd**: 京东策略
- **mt**: 美团策略
- **bw**: BW策略

### 加密策略

- **default**: 默认加密
- **mixue**: 蜜雪冰城加密
- **kudi**: 库迪咖啡加密

## 🔔 通知服务

### 飞书通知

```python
from core.notification import NotificationManager, LarkNotificationService

notification_manager = NotificationManager()
lark_service = LarkNotificationService(
    webhook_url="your_webhook_url",
    secret="your_secret"
)
notification_manager.register_service("lark", lark_service, is_default=True)
notification_manager.send_message("测试消息")
```

### 微信通知

```python
from core.notification import WeChatNotificationService

wechat_service = WeChatNotificationService(
    app_id="your_app_id",
    app_secret="your_app_secret", 
    template_id="your_template_id"
)
notification_manager.register_service("wechat", wechat_service)
```

## 🛠️ 高级功能

### 自定义策略

```python
from strategies.base import ISeckillStrategy

class CustomStrategy(ISeckillStrategy):
    def prepare_request(self, current_time, data, headers, base_url):
        # 实现自定义请求准备逻辑
        return url, data, headers
    
    def process_response(self, response):
        # 实现自定义响应处理逻辑
        return response.json()

# 注册策略
from strategies import RequestStrategyManager
strategy_manager = RequestStrategyManager()
strategy_manager.register_strategy("custom", CustomStrategy())
```

### 配置验证

```python
from config import ConfigManager

config_manager = ConfigManager()
is_valid = config_manager.validate_config(config_dict)
```

### 任务管理

```python
from core.scheduler import TaskManager

task_manager = TaskManager()

# 添加任务
from config import TaskSchedule
from datetime import datetime

task = TaskSchedule(
    start_time=datetime.strptime("12:00:00.000", "%H:%M:%S.%f").time(),
    config_file="./config.json",
    description="测试任务"
)
task_manager.add_task("12", task)
```

## 📖 使用示例

### 基础示例

```python
# examples/basic_usage.py
from core.seckill import SeckillManager

# 使用配置文件运行秒杀
manager = SeckillManager(config_file="kudicookie.json")
manager.run()
```

### 高级示例

```python
# examples/advanced_usage.py
from core.seckill import SeckillManager
from strategies import RequestStrategyManager
from core.notification import NotificationManager

# 自定义策略
strategy_manager = RequestStrategyManager()
strategy_manager.update_strategy_params("mixue", {
    "marketingId": "test_id",
    "round": "test_round",
    "secretword": "test_word"
})

# 多通知服务
notification_manager = NotificationManager()
# ... 注册多个通知服务

# 运行秒杀
manager = SeckillManager(config_file="kudicookie.json")
manager.run()
```

## 🔄 兼容性

### 向后兼容

- ✅ 配置文件格式完全兼容
- ✅ 原有API继续工作
- ✅ 原有代码移动到 `legacy/` 目录

### 快速迁移

```python
# v1.x 方式（仍然支持）
from legacy.multiuserseckill import Seckkiller
from legacy.managerun import SeckillManager

# v2.0 方式（推荐）
from core.seckill import SeckillManager
from core.scheduler import SeckillScheduler
```

## 🧪 测试

```bash
# 在nix develop环境中运行测试
nix develop --command python -c "from core.seckill import SeckillManager; print('测试通过')"

# 运行示例
nix develop --command python examples/basic_usage.py
```

## 📝 开发

### 代码风格

```bash
# 格式化代码
black .

# 检查代码风格
flake8 .

# 类型检查
mypy .
```

### 添加新策略

1. 继承相应的基类
2. 实现必要的方法
3. 注册到管理器中

```python
from strategies.base import ISeckillStrategy

class NewStrategy(ISeckillStrategy):
    def prepare_request(self, ...):
        # 实现逻辑
        pass
    
    def process_response(self, ...):
        # 实现逻辑
        pass

# 注册
strategy_manager.register_strategy("new", NewStrategy())
```

## 📚 历史版本

### v1.x 功能特点

- 支持多用户并发秒杀
- 多种秒杀策略（MT、Mixue、库迪、JD等）
- 代理IP支持
- 定时任务调度
- 微信实时通知

### 参数说明

- `start_time`: 开始时间，格式为"HH:mm:ss:ms"，例如"00:00:00:000"
- `users`: 用户配置列表
- `cookie_id`: 用户id，授权的关键字段
- `account_name`: 备注名
- `cookie`: 用户的cookie
- `basurl`: 请求地址
- `max_attempts`: 最大尝试次数
- `thread_count`: 线程数
- `key_message`: 重发请求返回json格式中需要提取的key
- `key_value`: 返回的key中的value，可用于停止脚本
- `headers`: 请求头
- `data`: 请求参数
- `proxy_flag`: 启用代理的标志
- `strategy_flag`: 是否使用加密算法，默认重发方法可以设置成None
- `proxies`: 代理地址
- `mixues`: mixue加密算法的配置

### mixue使用方法

1. 必须有node的环境，自行安装
2. cookie.yaml中设置use_encryption: true
3. 抓包小程序的AccessToken，填入cookie.yaml
4. 配置代理ip，mixue建议一定要配置，我使用的是json格式的提取

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有贡献者和开源社区的支持！

## 📞 支持

如有问题，请：

1. 查看文档
2. 搜索 Issues
3. 创建新的 Issue
4. 联系维护者

---

**注意**: 本项目仅供学习和研究使用，请遵守相关法律法规和平台规则。
