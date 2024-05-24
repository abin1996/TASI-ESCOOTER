from ob_scenario_extract_task import extract_ob_scenario

# Send a task to the worker
with open('/home/abinmath@ads.iu.edu/TASI/TASI-ESCOOTER/data_processing_scripts/celery_tasker/OB_Scenarios_to_extract.txt') as f:
    video_names = f.readlines()
    video_names = [x.strip() for x in video_names]
    for video_name in video_names:
        result = extract_ob_scenario.delay(video_name)
        print(f'Processing video: {video_name}, Task ID: {result.id}')
        #Save the task id to a file
        with open('/home/abinmath@ads.iu.edu/TASI/TASI-ESCOOTER/data_processing_scripts/celery_tasker/ob_folders_task_id.txt', 'a') as f:
            f.write(f'{video_name} - {result.id}\n')
