#!/bin/bash

# ============================
# 股票新闻资讯看板 - 服务管理脚本
# ============================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_DIR/.pids"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

# ---------- 颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ---------- 工具函数 ----------
log_info()  { echo -e "${GREEN}✅ $1${NC}"; }
log_warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

is_running() {
    local pid_file="$PID_DIR/$1.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        rm -f "$pid_file"
    fi
    return 1
}

get_pid() {
    local pid_file="$PID_DIR/$1.pid"
    [ -f "$pid_file" ] && cat "$pid_file"
}

# ---------- 启动数据库 ----------
start_db() {
    echo -e "${CYAN}📦 启动 PostgreSQL 数据库...${NC}"
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 未运行，请先启动 Docker"
        return 1
    fi
    cd "$PROJECT_DIR" && docker compose up -d
    echo "⏳ 等待数据库就绪..."
    sleep 3
    log_info "数据库已启动"
}

# ---------- 启动后端 ----------
start_backend() {
    if is_running "backend"; then
        log_warn "后端已在运行 (PID: $(get_pid backend))"
        return 0
    fi

    echo -e "${CYAN}� 启动 FastAPI 后端...${NC}"
    cd "$PROJECT_DIR/backend"

    if [ ! -f ".env" ]; then
        log_warn "未找到 backend/.env 文件，从 .env.example 创建..."
        cp .env.example .env 2>/dev/null || true
    fi

    if [ ! -d "venv" ]; then
        echo "📦 创建 Python 虚拟环境..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt 2>/dev/null

    nohup uvicorn app.main:app --reload --port 8110 \
        > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"

    log_info "后端已启动 → http://localhost:8110  (PID: $!, 日志: logs/backend.log)"
}

# ---------- 启动前端 ----------
start_frontend() {
    if is_running "frontend"; then
        log_warn "前端已在运行 (PID: $(get_pid frontend))"
        return 0
    fi

    echo -e "${CYAN}⚛️  启动 Next.js 前端...${NC}"
    cd "$PROJECT_DIR/frontend"

    if [ ! -d "node_modules" ]; then
        echo "📦 安装前端依赖..."
        npm install
    fi

    nohup npm run dev \
        > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"

    log_info "前端已启动 → http://localhost:3000  (PID: $!, 日志: logs/frontend.log)"
}

# ---------- 停止服务 ----------
stop_service() {
    local name=$1
    if is_running "$name"; then
        local pid=$(get_pid "$name")
        kill "$pid" 2>/dev/null
        # 也杀掉子进程
        pkill -P "$pid" 2>/dev/null
        rm -f "$PID_DIR/$name.pid"
        log_info "$name 已停止 (PID: $pid)"
    else
        echo "  $name 未在运行"
    fi
}

stop_all() {
    echo -e "${CYAN}🛑 停止所有服务...${NC}"
    stop_service "frontend"
    stop_service "backend"
    cd "$PROJECT_DIR" && docker compose stop
    log_info "所有服务已停止"
}

# ---------- 查看状态 ----------
show_status() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}       📊 服务运行状态${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"

    # 数据库
    if docker compose ps --format '{{.State}}' 2>/dev/null | grep -q "running"; then
        echo -e "  PostgreSQL  : ${GREEN}● 运行中${NC}"
    else
        echo -e "  PostgreSQL  : ${RED}○ 已停止${NC}"
    fi

    # 后端
    if is_running "backend"; then
        echo -e "  FastAPI 后端: ${GREEN}● 运行中${NC} (PID: $(get_pid backend))"
    else
        echo -e "  FastAPI 后端: ${RED}○ 已停止${NC}"
    fi

    # 前端
    if is_running "frontend"; then
        echo -e "  Next.js 前端: ${GREEN}● 运行中${NC} (PID: $(get_pid frontend))"
    else
        echo -e "  Next.js 前端: ${RED}○ 已停止${NC}"
    fi

    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""
}

# ---------- 查看日志 ----------
show_logs() {
    echo ""
    echo -e "${CYAN}选择要查看的日志:${NC}"
    echo "  1) 后端日志 (backend.log)"
    echo "  2) 前端日志 (frontend.log)"
    echo "  3) 返回"
    echo ""
    read -p "请选择 [1-3]: " log_choice
    case $log_choice in
        1) tail -f "$LOG_DIR/backend.log" ;;
        2) tail -f "$LOG_DIR/frontend.log" ;;
        3) return ;;
        *) log_warn "无效选择" ;;
    esac
}

# ---------- 启动全部 ----------
start_all() {
    echo ""
    echo -e "${CYAN}🚀 启动股票新闻资讯看板${NC}"
    echo ""
    start_db || return 1
    start_backend
    start_frontend
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ 所有服务已在后台启动！${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "  前端:     ${CYAN}http://localhost:3000${NC}"
    echo -e "  后端 API: ${CYAN}http://localhost:8110/docs${NC}"
    echo -e "  日志目录: ${CYAN}$LOG_DIR/${NC}"
    echo ""
}

# ---------- 重启全部 ----------
restart_all() {
    stop_all
    sleep 2
    start_all
}

# ---------- 主菜单 ----------
show_menu() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}   📈 股票新闻资讯看板 - 服务管理${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""
    echo "  1) 🚀 启动全部服务"
    echo "  2) 🛑 停止全部服务"
    echo "  3) 🔄 重启全部服务"
    echo "  4) 📊 查看服务状态"
    echo "  5) 📋 查看日志"
    echo "  6) 🚪 退出"
    echo ""
    read -p "请选择 [1-6]: " choice
    case $choice in
        1) start_all ;;
        2) stop_all ;;
        3) restart_all ;;
        4) show_status ;;
        5) show_logs ;;
        6) echo "👋 再见！"; exit 0 ;;
        *) log_warn "无效选择，请重试" ;;
    esac
}

# ---------- 命令行参数支持 ----------
case "${1:-}" in
    start)   start_all ;;
    stop)    stop_all ;;
    restart) restart_all ;;
    status)  show_status ;;
    logs)    show_logs ;;
    *)
        # 无参数时显示交互式菜单
        while true; do
            show_menu
        done
        ;;
esac
