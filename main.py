#!/usr/bin/env python3
"""
DailyInfo 智能新闻推送系统
主程序入口
"""

import sys
import signal
import time
import os
import subprocess
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


def start_daemon_service(config: dict):
    """启动后台守护进程"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pid_file = os.path.join(script_dir, "dailyinfo.pid")
    log_file = os.path.join(script_dir, "logs", "daemon.log")

    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 检查是否已经在运行
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, 0)  # 检查进程是否存在
            print(f"[INFO] DailyInfo 已在后台运行 (PID: {pid})")
            print(f"[INFO] 日志文件: {log_file}")
            print(f"[INFO] 查看日志: tail -f {log_file}")
            print(f"[INFO] 停止服务: python {__file__} stop")
            return
        except OSError:
            # 进程不存在，删除过期的PID文件
            os.remove(pid_file)

    print("[INFO] 启动 DailyInfo 后台服务...")

    # 启动后台进程
    main_script = os.path.abspath(__file__)
    with open(log_file, 'a') as log:
        process = subprocess.Popen(
            [sys.executable, main_script, "schedule"],
            stdout=log,
            stderr=log,
            cwd=script_dir,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None  # 创建新的进程组
        )

    # 保存PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))

    # 等待一下确保进程启动
    time.sleep(3)

    try:
        os.kill(process.pid, 0)  # 检查进程是否还在运行
        print(f"[INFO] DailyInfo 后台服务启动成功 (PID: {process.pid})")
        print(f"[INFO] 日志文件: {log_file}")
        print(f"[INFO] 查看日志: tail -f {log_file}")
        print(f"[INFO] 停止服务: python {main_script} stop")

        # 显示最近的日志以确认启动状态
        if os.path.exists(log_file):
            print("\n[INFO] 启动日志:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-3:]:
                        if line.strip():
                            print(f"  {line.rstrip()}")
            except Exception as e:
                print(f"  无法读取日志文件: {e}")

    except OSError:
        print("[ERROR] DailyInfo 后台服务启动失败")
        if os.path.exists(pid_file):
            os.remove(pid_file)

        # 显示错误日志
        if os.path.exists(log_file):
            print("\n[ERROR] 错误日志:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        if line.strip():
                            print(f"  {line.rstrip()}")
            except Exception as e:
                print(f"  无法读取日志文件: {e}")


def start_daemon_service_with_immediate_run(config: dict):
    """启动后台守护进程，并在启动后立即执行一次任务"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pid_file = os.path.join(script_dir, "dailyinfo.pid")
    log_file = os.path.join(script_dir, "logs", "daemon.log")

    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 检查是否已经在运行
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, 0)  # 检查进程是否存在
            print(f"[INFO] DailyInfo 已在后台运行 (PID: {pid})")
            print(f"[INFO] 日志文件: {log_file}")
            print(f"[INFO] 查看日志: tail -f {log_file}")
            print(f"[INFO] 停止服务: python {os.path.abspath(__file__)} stop")
            return
        except OSError:
            # 进程不存在，删除过期的PID文件
            os.remove(pid_file)

    print("[INFO] 启动 DailyInfo 后台服务（立即执行模式）...")

    # 启动后台进程，使用特殊参数表示立即执行
    main_script = os.path.abspath(__file__)
    with open(log_file, 'a') as log:
        process = subprocess.Popen(
            [sys.executable, main_script, "_daemon_with_immediate_run"],
            stdout=log,
            stderr=log,
            cwd=script_dir,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None  # 创建新的进程组
        )

    # 保存PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))

    # 等待一下确保进程启动
    time.sleep(3)

    try:
        os.kill(process.pid, 0)  # 检查进程是否还在运行
        print(f"[INFO] DailyInfo 后台服务启动成功 (PID: {process.pid})")
        print(f"[INFO] 服务将立即执行一次任务，然后开始定时任务")
        print(f"[INFO] 日志文件: {log_file}")
        print(f"[INFO] 查看日志: tail -f {log_file}")
        print(f"[INFO] 停止服务: python {main_script} stop")

        # 显示最近的日志以确认启动状态
        if os.path.exists(log_file):
            print("\n[INFO] 启动日志:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-3:]:
                        if line.strip():
                            print(f"  {line.rstrip()}")
            except Exception as e:
                print(f"  无法读取日志文件: {e}")

    except OSError:
        print("[ERROR] DailyInfo 后台服务启动失败")
        if os.path.exists(pid_file):
            os.remove(pid_file)

        # 显示错误日志
        if os.path.exists(log_file):
            print("\n[ERROR] 错误日志:")
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        if line.strip():
                            print(f"  {line.rstrip()}")
            except Exception as e:
                print(f"  无法读取日志文件: {e}")


def stop_daemon_service():
    """停止后台守护进程"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pid_file = os.path.join(script_dir, "dailyinfo.pid")

    if not os.path.exists(pid_file):
        print("[INFO] DailyInfo 后台服务未运行")
        return

    with open(pid_file, 'r') as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, 0)  # 检查进程是否存在
        print(f"[INFO] 停止 DailyInfo 后台服务 (PID: {pid})...")

        # 发送终止信号
        os.kill(pid, signal.SIGTERM)

        # 等待进程结束
        for i in range(10):
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except OSError:
                break

        # 如果进程仍在运行，强制杀死
        try:
            os.kill(pid, 0)
            print("[INFO] 强制停止进程...")
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

        os.remove(pid_file)
        print("[INFO] DailyInfo 后台服务已停止")

    except OSError:
        print("[INFO] DailyInfo 后台服务未运行")
        os.remove(pid_file)


def show_daemon_status():
    """显示后台服务状态"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pid_file = os.path.join(script_dir, "dailyinfo.pid")
    log_file = os.path.join(script_dir, "logs", "daemon.log")

    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, 0)  # 检查进程是否存在
            print(f"[INFO] DailyInfo 后台服务正在运行 (PID: {pid})")
            print(f"[INFO] 日志文件: {log_file}")

            # 显示最近的日志
            if os.path.exists(log_file):
                print("\n[INFO] 最近日志:")
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-5:]:
                            print(f"  {line.rstrip()}")
                except Exception:
                    print("  无法读取日志文件")
        except OSError:
            print("[INFO] DailyInfo 后台服务未运行 (PID文件过期)")
            os.remove(pid_file)
    else:
        print("[INFO] DailyInfo 后台服务未运行")


def start_scheduled_daemon(workflow_manager: WorkflowManager, config: dict):
    """启动后台定时任务"""
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

    # 内容抓取配置
    content_extraction_enabled = config.get('content_extraction', {}).get('enabled', True)
    firecrawl_key = config.get('firecrawl_api_key', '')
    zyte_key = config.get('zyte_api_key', '')

    print(f"\n内容抓取配置:")
    print(f"  内容抓取: {'启用' if content_extraction_enabled else '禁用'}")
    if content_extraction_enabled:
        print(f"  FireCrawl: {'已配置' if firecrawl_key and not firecrawl_key.startswith('YOUR_') else '未配置'}")
        print(f"  Zyte: {'已配置' if zyte_key and not zyte_key.startswith('YOUR_') else '未配置'}")
    else:
        print(f"  FireCrawl: 已禁用")
        print(f"  Zyte: 已禁用")

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
    print("  run                    - 立即执行一次新闻处理任务")
    print("  start                  - 启动后台定时任务")
    print("  stop                   - 停止后台服务")
    print("  restart                - 重启后台服务")
    print("  run-schedule           - 启动后台定时任务并立即执行一次")
    print("  status                 - 显示系统配置和服务状态")
    print("  help                   - 显示此帮助信息")
    print()
    print("示例:")
    print("  python main.py run                # 立即执行一次")
    print("  python main.py start              # 启动后台定时任务")
    print("  python main.py run-schedule       # 后台启动并立即执行一次")
    print("  python main.py stop               # 停止后台服务")
    print("  python main.py restart            # 重启后台服务")
    print("  python main.py status             # 查看状态")
    print()
    print("后台服务管理:")
    print("  启动: python main.py start")
    print("  立即启动: python main.py run-schedule")
    print("  停止: python main.py stop")
    print("  重启: python main.py restart")
    print("  状态: python main.py status")
    print("  日志: tail -f logs/daemon.log")


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
            
        elif command == "start":
            # 启动后台定时任务
            start_daemon_service(config)

        elif command == "stop":
            # 停止后台服务
            stop_daemon_service()

        elif command == "restart":
            # 重启后台服务
            stop_daemon_service()
            time.sleep(2)
            start_daemon_service(config)

        elif command == "run-schedule":
            # 启动后台服务，并在启动后立即执行一次任务
            print("[INFO] 启动后台定时任务，并立即执行一次...")
            start_daemon_service_with_immediate_run(config)

        elif command == "status":
            show_status(config_manager)
            print("\n" + "="*50)
            show_daemon_status()

        elif command == "_daemon_with_immediate_run":
            # 特殊的后台模式：立即执行一次后启动定时任务
            print("[INFO] 后台服务启动，立即执行一次任务...")

            # 立即执行一次任务
            try:
                execute_task(workflow_manager)
                print("[INFO] 立即执行完成，开始定时任务...")
            except Exception as e:
                print(f"[ERROR] 立即执行失败: {e}")
                print("[INFO] 继续启动定时任务...")

            # 启动定时任务
            start_scheduled_daemon(workflow_manager, config)

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
