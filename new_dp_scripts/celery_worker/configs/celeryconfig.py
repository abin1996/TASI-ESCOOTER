from re import T


broker_url="redis://:tasi12345!@134.68.77.118:6379/0"
result_backend="redis://:tasi12345!@134.68.77.118:6379/0"
broker_connection_max_retries=1
broker_connection_retry_on_startup = False
worker_deduplicate_successful_tasks = True
broker_transport_options = {"visibility_timeout": 360000}
task_acks_late = True
worker_prefetch_multiplier = 1