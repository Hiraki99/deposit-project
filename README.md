# deposit_app
run app:
 ./start.sh

run Celery:
celery -A apps.deposit_app.config.celery worker -l info