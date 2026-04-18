#!/bin/bash
# WeatherOS 启动脚本
# 绑定到 0.0.0.0:8080，方便外部隧穿访问

PORT=8080
HOST=0.0.0.0

# 检测端口是否被占用
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被占用，尝试查找进程..."
    PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    echo "   占用进程 PID: $PID"
    read -p "   是否终止该进程并继续? [Y/n] " ans
    if [[ "$ans" != "n" && "$ans" != "N" ]]; then
        kill -9 $PID 2>/dev/null
        echo "   已释放端口 $PORT"
        sleep 1
    else
        echo "   退出启动"
        exit 1
    fi
fi

echo "🌤️  启动 WeatherOS 本地服务器..."
echo "   地址: http://$HOST:$PORT"
echo "   说明: 绑定 0.0.0.0 而非 localhost，确保外部隧穿可访问"

# 自动打开浏览器（尽量兼容多平台）
OPEN_URL="http://127.0.0.1:$PORT"
if command -v python3 &> /dev/null; then
    echo "   使用 Python3 http.server 启动"
    python3 -m http.server $PORT --bind $HOST &
    SERVER_PID=$!
elif command -v python &> /dev/null; then
    echo "   使用 Python http.server 启动"
    python -m http.server $PORT --bind $HOST &
    SERVER_PID=$!
elif command -v npx &> /dev/null; then
    echo "   使用 npx serve 启动"
    npx serve -l tcp://$HOST:$PORT -s . &
    SERVER_PID=$!
else
    echo "❌ 未找到 python3 或 npx，请安装后重试"
    exit 1
fi

sleep 1

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open "$OPEN_URL" >/dev/null 2>&1
elif command -v open &> /dev/null; then
    open "$OPEN_URL" >/dev/null 2>&1
elif command -v start &> /dev/null; then
    start "$OPEN_URL" >/dev/null 2>&1
fi

echo ""
echo "✅ 服务已启动，按 Ctrl+C 停止"
wait $SERVER_PID
