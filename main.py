#!/usr/bin/env python3
"""
DailyInfo 智能新闻推送系统
主程序入口
"""

import sys
import signal
import time
from datetime import datetime

from utils.config_manager import ConfigManager
from utils.workflow_manager import WorkflowManager


def execute_task(workflow_manager: WorkflowManager):
    """执行新闻处理任务"""
    try:
        result = workflow_manager.execute_daily_task()
        
        print(f"\n[INFO] ========== 任务执行结果 ==========")
        print(f"[INFO] 收集新闻: {result.get('collected_count', 0)} 条")
        print(f"[INFO] 处理新闻: {result.get('processed_count', 0)} 条")
        print(f"[INFO] 推送新闻: {result.get('sent_count', 0)} 条")
        print(f"[INFO] 执行状态: {result.get('status', 'Unknown')}")
        
        if result.get('error'):
            print(f"[ERROR] 错误信息: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"[ERROR] 任务执行异常: {str(e)}")
        return {
            'collected_count': 0,
            'processed_count': 0,
            'sent_count': 0,
            'status': 'Failed',
            'error': str(e)
        }


def start_scheduled_tasks(workflow_manager: WorkflowManager, config: dict):
    """启动定时任务"""
    from utils.scheduler import scheduler_manager
    
    daily_run_time = config.get('daily_run_time', '06:00')
    timezone = config.get('timezone', 'Asia/Shanghai')
    
    print(f"[INFO] 配置定时任务: 每天 {daily_run_time} ({timezone})")
    
    try:
        # 初始化调度器
        config_manager = ConfigManager()
        scheduler = scheduler_manager.initialize(config_manager)
        
        # 定义任务函数
        def daily_task():
            execute_task(workflow_manager)
        
        # 启动调度器
        scheduler.start_scheduler(daily_task)
        
        # 显示调度器状态
        status = scheduler.get_status()
        print(f"[INFO] 定时任务已设置，等待执行...")
        print(f"[INFO] 下次执行时间: {status.get('next_run_time', 'N/A')}")
        print("[INFO] 按 Ctrl+C 退出程序")
        
        # 设置信号处理
        def signal_handler(signum, frame):
            print("\n[INFO] 收到退出信号，正在停止定时任务...")
            scheduler_manager.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 保持程序运行
        while True:
            time.sleep(60)
            
    except Exception as e:
        print(f"[ERROR] 定时任务启动失败: {str(e)}")
        scheduler_manager.cleanup()
        raise


def show_status(config_manager: ConfigManager):
    """显示系统状态"""
    print("=" * 60)
    print("DailyInfo 系统状态")
    print("=" * 60)
    
    # 基本配置信息
    config = config_manager.load_config()
    print(f"配置文件: config.yaml")
    print(f"时区设置: {config.get('timezone', 'Asia/Shanghai')}")
    print(f"每日运行时间: {config.get('daily_run_time', '06:00')}")
    print(f"最大推送数量: {config.get('max_send_limit', 10)}")

    
    # AI配置
    ai_config = config_manager.get_ai_config()
    print(f"\nAI配置:")
    print(f"  Gemini模型: {ai_config.get('gemini_model', 'N/A')}")
    print(f"  OpenRouter模型: {ai_config.get('openrouter_model', 'N/A')}")
    print(f"  最低评分: {ai_config.get('min_relevance_score', 6.0)}")
    
    # 新闻源配置
    rss_config = config.get('rss_settings', {})
    news_sources = config.get('news_sources', {})

    print(f"\n新闻源配置:")
    print(f"  RSS源: 启用 (每源文章数: {rss_config.get('max_articles_per_feed', 10)})")
    print(f"  MediaStack: {'启用' if news_sources.get('mediastack', {}).get('enabled') else '禁用'}")
    print(f"  News API: {'启用' if news_sources.get('newsapi', {}).get('enabled') else '禁用'}")
    
    # 推送配置
    webhook_url = config.get('webhook_url', '')
    if webhook_url:
        print(f"\n推送配置:")
        print(f"  飞书Webhook: 已配置")
    else:
        print(f"\n推送配置:")
        print(f"  飞书Webhook: 未配置")
    
    print("=" * 60)


def show_help():
    """显示帮助信息"""
    print("DailyInfo 智能新闻推送系统")
    print()
    print("用法:")
    print("  python main.py [命令]")
    print()
    print("命令:")
    print("  run       立即运行一次新闻处理任务")
    print("  schedule  启动定时任务模式（默认）")
    print("  status    显示系统配置状态")
    print("  help      显示此帮助信息")
    print()
    print("示例:")
    print("  python main.py run      # 立即执行一次")
    print("  python main.py schedule # 启动定时任务")
    print("  python main.py status   # 查看系统状态")


def main():
    """主函数"""
    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # 初始化工作流管理器
        workflow_manager = WorkflowManager(config)
        
        # 解析命令行参数
        command = sys.argv[1] if len(sys.argv) > 1 else "schedule"
        
        if command == "run":
            print("[INFO] 立即执行模式")
            execute_task(workflow_manager)
            
        elif command == "schedule":
            print("[INFO] 定时任务模式")
            start_scheduled_tasks(workflow_manager, config)
            
        elif command == "status":
            show_status(config_manager)
            
        elif command == "help" or command == "--help" or command == "-h":
            show_help()
            
        else:
            print(f"[ERROR] 未知命令: {command}")
            print("使用 'python main.py help' 查看帮助")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] 程序被用户中断")
        sys.exit(0)
        
    except Exception as e:
        print(f"[ERROR] 程序异常: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
