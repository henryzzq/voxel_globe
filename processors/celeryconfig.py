CELERYD_CONCURRENCY = 2; #default is #num of cores
CELERYD_LOG_COLOR = True;

BROKER_URL = 'amqp://guest@localhost:5672//';
CELERY_RESULT_BACKEND = 'amqp://';

CELERY_TASK_SERIALIZER='json';
CELERY_ACCEPT_CONTENT=['json'];  # Ignore other content
CELERY_RESULT_SERIALIZER='json';

CELERY_SEND_EVENTS=True;


