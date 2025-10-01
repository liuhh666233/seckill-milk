"""
任务管理器

从原有的schedule_config.py重构而来
"""

import json
import glob
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from loguru import logger

from config import TaskSchedule, ConfigManager


class TaskManager:
    """任务管理器"""

    def __init__(self, schedule_file: str = "configs/schedule.json"):
        self.schedule_file = schedule_file
        self.schedules: Dict[str, List[TaskSchedule]] = {}
        self.config_manager = ConfigManager()
        self.load_schedules()

    def load_schedules(self):
        """加载调度配置"""
        try:
            schedules = self.config_manager.load_schedule_config(self.schedule_file)
            self.schedules = schedules
            logger.info(f"加载调度配置: {self.schedule_file}")
        except FileNotFoundError:
            logger.warning(f"调度文件未找到: {self.schedule_file}")
        except Exception as e:
            logger.error(f"加载调度配置失败: {e}")

    def get_current_tasks(self) -> List[TaskSchedule]:
        """获取当前小时的任务"""
        current_hour = datetime.now().strftime("%H")
        return self.schedules.get(current_hour, [])

    def get_tasks_by_hour(self, hour: str) -> List[TaskSchedule]:
        """获取指定小时的任务"""
        return self.schedules.get(hour, [])

    def add_task(self, hour: str, task: TaskSchedule):
        """添加任务"""
        if hour not in self.schedules:
            self.schedules[hour] = []
        self.schedules[hour].append(task)
        self.save_schedules()
        logger.info(f"添加任务到 {hour} 点: {task.description}")

    def remove_task(self, hour: str, task_index: int):
        """删除任务"""
        if hour in self.schedules and 0 <= task_index < len(self.schedules[hour]):
            task = self.schedules[hour].pop(task_index)
            self.save_schedules()
            logger.info(f"删除任务: {task.description}")
        else:
            logger.warning(f"任务不存在: {hour}:{task_index}")

    def update_task(self, hour: str, task_index: int, task: TaskSchedule):
        """更新任务"""
        if hour in self.schedules and 0 <= task_index < len(self.schedules[hour]):
            self.schedules[hour][task_index] = task
            self.save_schedules()
            logger.info(f"更新任务: {task.description}")
        else:
            logger.warning(f"任务不存在: {hour}:{task_index}")

    def save_schedules(self):
        """保存调度配置"""
        data = {
            hour: [
                {
                    "start_time": task.start_time.strftime("%H:%M:%S.%f"),
                    "config_file": task.config_file,
                    "enabled": task.enabled,
                    "description": task.description,
                }
                for task in tasks
            ]
            for hour, tasks in self.schedules.items()
        }

        try:
            with open(self.schedule_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"调度配置已保存: {self.schedule_file}")
        except Exception as e:
            logger.error(f"保存调度配置失败: {e}")

    @staticmethod
    def scan_config_files(config_dir: str = "./configs") -> List[str]:
        """扫描配置文件目录"""
        return glob.glob(f"{config_dir}/**/*.json", recursive=True)

    def list_all_tasks(self) -> Dict[str, List[Dict]]:
        """列出所有任务"""
        result = {}
        for hour, tasks in self.schedules.items():
            result[hour] = [
                {
                    "index": i,
                    "start_time": task.start_time.strftime("%H:%M:%S.%f"),
                    "config_file": task.config_file,
                    "enabled": task.enabled,
                    "description": task.description,
                }
                for i, task in enumerate(tasks)
            ]
        return result
