import os

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = os.getenv("TIMEZONE", "Europe/Moscow")
