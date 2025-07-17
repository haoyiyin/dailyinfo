#!/usr/bin/env python3
"""
定时任务调度器
负责管理每日定时运行任务
"""

import schedule
import time
import logging
import threading
from datetime import datetime, timedelta
import pytz
from typing import Callable, Optional

from .config_manager import ConfigManager

class DailyScheduler:
    """每日定时任务调度器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        # 获取配置
        config = self.config_manager.load_config()
        self.daily_run_time = config.get('daily_run_time', '06:00')
        self.timezone_str = config.get('timezone', 'Asia/Shanghai')
        
        try:
            self.timezone = pytz.timezone(self.timezone_str)
        except Exception as e:
            self.logger.warning(f"无效时区 {self.timezone_str}，使用默认时区 Asia/Shanghai: {e}")
            self.timezone = pytz.timezone('Asia/Shanghai')
        
        self.logger.info(f"定时任务配置: 每日 {self.daily_run_time} ({self.timezone_str})")
    
    def schedule_daily_task(self, task_func: Callable):
        """安排每日定时任务"""
        try:
            # 清除现有任务
            schedule.clear()
            
            # 安排每日任务
            schedule.every().day.at(self.daily_run_time).do(self._run_task_with_timezone, task_func)
            
            self.logger.info(f"✅ 已安排每日任务: {self.daily_run_time} ({self.timezone_str})")
            
            # 显示下次运行时间
            next_run = schedule.next_run()
            if next_run:
                local_time = next_run.astimezone(self.timezone)
                self.logger.info(f"📅 下次运行时间: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
        except Exception as e:
            self.logger.error(f"❌ 安排定时任务失败: {e}")
            raise
    
    def _run_task_with_timezone(self, task_func: Callable):
        """在指定时区运行任务"""
        try:
            current_time = datetime.now(self.timezone)
            self.logger.info(f"🚀 开始执行定时任务: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # 执行任务
            task_func()
            
            self.logger.info(f"✅ 定时任务执行完成: {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
        except Exception as e:
            self.logger.error(f"❌ 定时任务执行失败: {e}")
    
    def start_scheduler(self, task_func: Callable):
        """启动调度器"""
        if self.running:
            self.logger.warning("调度器已在运行中")
            return
        
        try:
            # 安排任务
            self.schedule_daily_task(task_func)
            
            # 启动调度器线程
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            self.logger.info("🎯 定时调度器已启动")
            
        except Exception as e:
            self.logger.error(f"❌ 启动调度器失败: {e}")
            self.running = False
            raise
    
    def _scheduler_loop(self):
        """调度器主循环"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                self.logger.error(f"调度器循环错误: {e}")
                time.sleep(60)
    
    def stop_scheduler(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("🛑 定时调度器已停止")
    
    def run_once_now(self, task_func: Callable):
        """立即运行一次任务"""
        try:
            current_time = datetime.now(self.timezone)
            self.logger.info(f"🚀 手动执行任务: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            task_func()
            
            self.logger.info(f"✅ 手动任务执行完成: {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
        except Exception as e:
            self.logger.error(f"❌ 手动任务执行失败: {e}")
            raise
    
    def get_next_run_time(self) -> Optional[datetime]:
        """获取下次运行时间"""
        next_run = schedule.next_run()
        if next_run:
            return next_run.astimezone(self.timezone)
        return None
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        next_run = self.get_next_run_time()
        
        return {
            'running': self.running,
            'daily_run_time': self.daily_run_time,
            'timezone': self.timezone_str,
            'next_run_time': next_run.strftime('%Y-%m-%d %H:%M:%S %Z') if next_run else None,
            'current_time': datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'scheduled_jobs': len(schedule.jobs)
        }

class SchedulerManager:
    """调度器管理器 - 单例模式"""
    
    _instance = None
    _scheduler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, config_manager: ConfigManager):
        """初始化调度器"""
        if self._scheduler is None:
            self._scheduler = DailyScheduler(config_manager)
        return self._scheduler
    
    def get_scheduler(self) -> Optional[DailyScheduler]:
        """获取调度器实例"""
        return self._scheduler
    
    def cleanup(self):
        """清理资源"""
        if self._scheduler:
            self._scheduler.stop_scheduler()
            self._scheduler = None

# 全局调度器管理器实例
scheduler_manager = SchedulerManager()
