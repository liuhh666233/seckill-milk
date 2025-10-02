#!/usr/bin/env python3
"""
秒杀系统主入口

提供统一的命令行接口
"""

import sys
import os
from pathlib import Path
from typing import Optional

import click
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.seckill import SeckillManager
from core.scheduler import SeckillScheduler
from config import ConfigManager


def setup_logging(verbose: bool = False):
    """设置日志"""
    logger.remove()

    level = "DEBUG" if verbose else "INFO"
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 输出到控制台
    logger.add(sys.stdout, format=format_str, level=level)

    # 确保logs目录存在
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # 输出到文件, 每天一个文件 - 使用绝对路径
    log_file_path = logs_dir / "seckill_{time:YYYY-MM-DD}.log"
    logger.add(
        str(log_file_path),
        format=format_str,
        level=level,
        rotation="1 day",
        retention="10 days",
        enqueue=True
    )


def ensure_configs_dir():
    """确保configs目录存在"""
    configs_dir = Path("configs")
    configs_dir.mkdir(exist_ok=True)
    return configs_dir


def get_config_path(config_name: str) -> str:
    """获取配置文件路径，确保在configs目录下"""
    configs_dir = ensure_configs_dir()

    # 如果config_name已经是完整路径，直接返回
    if Path(config_name).is_absolute():
        return config_name

    # 如果包含路径分隔符，说明是相对路径，需要检查是否在configs目录下
    if "/" in config_name or "\\" in config_name:
        config_path = Path(config_name)
        # 如果是相对路径，尝试在configs目录下查找
        if not config_path.is_absolute():
            config_path = configs_dir / config_name
        if not config_path.suffix:
            config_path = config_path.with_suffix(".json")
        return str(config_path)

    # 确保在configs目录下
    config_path = configs_dir / config_name
    if not config_path.suffix:
        config_path = config_path.with_suffix(".json")

    return str(config_path)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.pass_context
def cli(ctx, verbose):
    """秒杀系统 - 多用户、多策略的通用秒杀系统"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@cli.command()
@click.option(
    "--config", "-c", default="default.json", help="配置文件名称（在configs目录下）"
)
@click.pass_context
def seckill(ctx, config):
    """运行秒杀任务"""
    config_path = get_config_path(config)

    try:
        logger.info(f"加载配置文件: {config_path}")
        manager = SeckillManager(config_file=config_path)
        manager.run()
    except Exception as e:
        logger.error(f"秒杀运行失败: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["watch", "now", "hour"]),
    default="watch",
    help="运行模式",
)
@click.option("--hour", help="指定运行小时 (HH格式)")
@click.pass_context
def scheduler(ctx, mode, hour):
    """运行调度器"""
    try:
        scheduler = SeckillScheduler()

        if mode == "watch":
            logger.info("启动监视模式")
            scheduler.watch_mode()
        elif mode == "hour" and hour:
            logger.info(f"运行 {hour} 点的任务")
            scheduler.run_hour_tasks(hour)
        else:
            logger.info("运行当前小时的任务")
            scheduler.run_current_tasks()

    except KeyboardInterrupt:
        logger.info("程序已停止")
    except Exception as e:
        logger.error(f"调度器运行失败: {e}")
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", required=True, help="配置文件名称（在configs目录下）")
@click.pass_context
def validate(ctx, config):
    """验证配置文件"""
    config_path = get_config_path(config)

    try:
        config_manager = ConfigManager()
        config_obj = config_manager.load_seckill_config(config_path)

        logger.info("配置文件验证成功")
        logger.info(f"开始时间: {config_obj.start_time}")
        logger.info(f"用户数量: {len(config_obj.users)}")
        logger.info(f"代理配置: {'是' if config_obj.proxies else '否'}")

        for i, user in enumerate(config_obj.users):
            logger.info(
                f"用户 {i+1}: {user.account_name} ({user.strategy_flag or 'default'})"
            )

    except Exception as e:
        logger.error(f"配置文件验证失败: {e}")
        sys.exit(1)


@cli.command()
@click.option("--name", "-n", default="default.json", help="配置文件名称")
@click.option("--category", default="general", help="配置分类目录")
@click.pass_context
def create_config(ctx, name, category):
    """创建默认配置文件"""
    configs_dir = ensure_configs_dir()
    category_dir = configs_dir / category
    category_dir.mkdir(exist_ok=True)

    config_path = category_dir / name
    if not config_path.suffix:
        config_path = config_path.with_suffix(".json")

    try:
        config_manager = ConfigManager()
        success = config_manager.create_default_config(str(config_path))

        if success:
            logger.info(f"默认配置文件已创建: {config_path}")
        else:
            logger.error("创建配置文件失败")
            sys.exit(1)

    except Exception as e:
        logger.error(f"创建配置文件失败: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_tasks(ctx):
    """列出所有任务"""
    try:
        from core.scheduler import TaskManager

        task_manager = TaskManager()
        all_tasks = task_manager.list_all_tasks()

        if not all_tasks:
            logger.info("没有配置任何任务")
            return

        for hour, tasks in all_tasks.items():
            logger.info(f"=== {hour} 点的任务 ===")
            for task in tasks:
                status = "启用" if task["enabled"] else "禁用"
                logger.info(f"  {task['index']}: {task['description']} ({status})")
                logger.info(f"      时间: {task['start_time']}")
                logger.info(f"      配置: {task['config_file']}")

    except Exception as e:
        logger.error(f"列出任务失败: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_configs(ctx):
    """列出所有配置文件"""
    configs_dir = ensure_configs_dir()

    logger.info("可用的配置文件:")

    # 列出所有配置文件
    for config_file in sorted(configs_dir.rglob("*.json")):
        relative_path = config_file.relative_to(configs_dir)
        logger.info(f"  {relative_path}")

    if not any(configs_dir.rglob("*.json")):
        logger.info("  没有找到配置文件")


if __name__ == "__main__":
    cli()
