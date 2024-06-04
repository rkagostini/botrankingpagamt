#!/bin/bash
while true; do
    if ! pgrep -x "python3" > /dev/null; then
        echo "Bot não está em execução. Reiniciando..."
        nohup python3 main.py > output.log &
    fi
    sleep 10  # Espera 10 segundos antes de verificar novamente
done
