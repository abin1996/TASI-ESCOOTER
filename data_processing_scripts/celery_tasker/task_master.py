from video_task import process_video

# Send a task to the worker
for i in range(10):
    result = process_video.delay(f"video_{i}")
    print(f'Task {i} , id: {result.id}')
# result = add.delay(4, 6)
# print(f'Task result: {result.get(timeout=10)}')
