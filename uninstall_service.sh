#!/bin/bash

# DailyInfo 系统服务卸载脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查systemd
check_systemd() {
    if ! command -v systemctl &> /dev/null; then
        print_error "系统不支持systemd"
        exit 1
    fi
}

# 卸载服务
uninstall_service() {
    print_info "卸载DailyInfo系统服务..."
    
    # 停止服务
    if sudo systemctl is-active --quiet dailyinfo.service; then
        print_info "停止服务..."
        sudo systemctl stop dailyinfo.service
    fi
    
    # 禁用开机自启动
    if sudo systemctl is-enabled --quiet dailyinfo.service; then
        print_info "禁用开机自启动..."
        sudo systemctl disable dailyinfo.service
    fi
    
    # 删除服务文件
    if [[ -f /etc/systemd/system/dailyinfo.service ]]; then
        print_info "删除服务文件..."
        sudo rm /etc/systemd/system/dailyinfo.service
    fi
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    print_success "DailyInfo系统服务已完全卸载"
}

# 主函数
main() {
    echo "=================================================="
    echo "DailyInfo 系统服务卸载脚本"
    echo "=================================================="
    echo ""
    
    check_systemd
    
    print_warning "即将卸载DailyInfo系统服务"
    read -p "是否继续？(y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "卸载已取消"
        exit 0
    fi
    
    uninstall_service
    
    echo ""
    print_success "🎉 DailyInfo系统服务卸载完成！"
    print_info "您仍然可以使用 python main.py start 手动启动服务"
}

main "$@"
