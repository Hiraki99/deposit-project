#!/bin/bash
# $app1 = "runDeposit.py"
# $app2 = "runGateway.py"
# $app3 = "runTrade.py"
test=`ps aux | grep "runDeposit" | grep -v grep -c`
echo 
if [ $test == 0 ]; then
        
        # python3 runDeposit.py --env=deposit >> logs-deposit.log  
        python3 runDeposit.py --env=deposit &
        celery -A apps.deposit_app.celery worker -l info --beat &
       
        echo "[INFO] Service is starting"
        exit
else
        echo "[WARN] Service is already running"
        exit
fi