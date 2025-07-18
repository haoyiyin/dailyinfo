#!/bin/bash

# DailyInfo 系统服务安装脚本
# 用于在Linux服务器上安装systemd服务，实现开机自启动

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "请不要使用root用户运行此脚本"
        print_info "建议使用普通用户运行，脚本会在需要时提示输入sudo密码"
        exit 1
    fi
}

# 检查系统是否支持systemd
check_systemd() {
    if ! command -v systemctl &> /dev/null; then
        print_error "系统不支持systemd，无法安装服务"
        exit 1
    fi
    print_success "系统支持systemd"
}

# 获取当前用户和组
get_user_info() {
    CURRENT_USER=$(whoami)
    CURRENT_GROUP=$(id -gn)
    print_info "当前用户: $CURRENT_USER"
    print_info "当前用户组: $CURRENT_GROUP"
}

# 获取项目路径
get_project_path() {
    PROJECT_PATH=$(pwd)
    print_info "项目路径: $PROJECT_PATH"
    
    # 检查是否在正确的目录
    if [[ ! -f "$PROJECT_PATH/main.py" ]]; then
        print_error "未找到main.py文件，请确保在DailyInfo项目根目录下运行此脚本"
        exit 1
    fi
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "未找到python3，请先安装Python 3"
        exit 1
    fi
    
    PYTHON_PATH=$(which python3)
    print_info "Python路径: $PYTHON_PATH"
    
    # 检查依赖
    if ! python3 -c "import yaml, requests" &> /dev/null; then
        print_warning "Python依赖可能未完全安装，请确保运行过: pip install -r requirements.txt"
    fi
}

# 创建服务文件
create_service_file() {
    print_info "创建systemd服务文件..."
    
    # 复制服务文件模板
    SERVICE_FILE="/tmp/dailyinfo.service"
    cp dailyinfo.service "$SERVICE_FILE"
    
    # 替换占位符
    sed -i "s|your_username|$CURRENT_USER|g" "$SERVICE_FILE"
    sed -i "s|your_group|$CURRENT_GROUP|g" "$SERVICE_FILE"
    sed -i "s|/path/to/DailyInfo|$PROJECT_PATH|g" "$SERVICE_FILE"
    sed -i "s|/usr/bin/python3|$PYTHON_PATH|g" "$SERVICE_FILE"
    
    print_success "服务文件已准备完成"
}

# 安装服务
install_service() {
    print_info "安装systemd服务..."
    
    # 复制服务文件到系统目录
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    # 启用服务（开机自启动）
    sudo systemctl enable dailyinfo.service
    
    print_success "服务安装完成"
}

# 启动服务
start_service() {
    print_info "启动DailyInfo服务..."
    
    # 停止可能正在运行的实例
    if python3 main.py status | grep -q "正在运行"; then
        print_info "停止现有的后台实例..."
        python3 main.py stop
        sleep 2
    fi
    
    # 启动systemd服务
    sudo systemctl start dailyinfo.service
    
    # 检查服务状态
    sleep 3
    if sudo systemctl is-active --quiet dailyinfo.service; then
        print_success "DailyInfo服务启动成功"
    else
        print_error "DailyInfo服务启动失败"
        print_info "查看错误日志: sudo journalctl -u dailyinfo.service -f"
        exit 1
    fi
}

# 显示服务状态
show_status() {
    print_info "服务状态:"
    sudo systemctl status dailyinfo.service --no-pager
    
    print_info ""
    print_info "常用命令:"
    echo "  查看状态: sudo systemctl status dailyinfo"
    echo "  启动服务: sudo systemctl start dailyinfo"
    echo "  停止服务: sudo systemctl stop dailyinfo"
    echo "  重启服务: sudo systemctl restart dailyinfo"
    echo "  查看日志: sudo journalctl -u dailyinfo -f"
    echo "  禁用开机自启: sudo systemctl disable dailyinfo"
}

# 主函数
main() {
    echo "=================================================="
    echo "DailyInfo 系统服务安装脚本"
    echo "=================================================="
    echo ""
    
    check_root
    check_systemd
    get_user_info
    get_project_path
    check_python
    
    echo ""
    print_warning "即将安装DailyInfo为系统服务，实现开机自启动"
    read -p "是否继续？(y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "安装已取消"
        exit 0
    fi
    
    create_service_file
    install_service
    start_service
    
    echo ""
    print_success "🎉 DailyInfo系统服务安装完成！"
    print_success "服务已启动并设置为开机自启动"
    echo ""
    
    show_status
    
    echo ""
    print_info "现在您可以重启服务器测试开机自启动功能"
}

# 运行主函数
main "$@"
