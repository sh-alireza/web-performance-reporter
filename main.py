import csv
import logging
import os
import signal
from datetime import datetime, timedelta
from urllib.parse import urljoin


from celery import Celery
from celery.result import AsyncResult
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from lighthouse import LighthouseRepeatRunner
from tqdm import tqdm


USERNAME = str(os.getenv("RABBITMQ_DEFAULT_USER","admin"))
PASSWORD = str(os.getenv("RABBITMQ_DEFAULT_PASS","admin"))
HOST = str(os.getenv("BROKER_SERVICE_HOST","localhost"))
CRAWLER_HOST = str(os.getenv("CRAWLER_SERVICE_HOST","lighthouse_python"))
PORT = "5672"
OUTPUT_PATH = "outputs"

FORM_FACTORS_OPTIONS = ["mobile", "desktop"]
SPEED_OPTIONS = ["slow-4g","normal"]
MORE_SETTINGS = [
"--throttling.cpuSlowdownMultiplier=4",
"--throttling.connectionType=4g",
"--throttling.downloadThroughputKbps=1638.4",
"--throttling.rttMs=150",
"--screenEmulation.disabled=false",
"--screenEmulation.width=412",
"--screenEmulation.height=823",
"--screenEmulation.deviceScaleFactor=1.75",
"--axe.enable=true",
"--axe.version=4.7.0",
]
BASE_TIMINGS = [
    'first-contentful-paint',
    'largest-contentful-paint',
    'cumulative-layout-shift',
    'speed-index',
    'total-blocking-time',
    'server-response-time',
    'max-potential-fid',
    'interactive'
]

# Create a new FastAPI instance
app = FastAPI(
    title="Web Performance Analyzer: A Lighthouse-Powered API for Website Comparison",
    description="Web Performance Analyzer is an easy-to-use API powered by Lighthouse that compares website performance metrics. \
        Get valuable insights by analyzing performance data of two websites such as loading speed, accessibility, and SEO.",
    version="1.0.0",
)

# Create a new Celery application instance
celery_app = Celery(
    'tasks',
    broker=f'amqp://{USERNAME}:{PASSWORD}@{HOST}:{PORT}//', # Set the broker URL to connect to a message broker
    backend='rpc://', # Set the backend URL to specify how Celery should store task results
)

@celery_app.task
def check_urls(
    cols,
    output_path,
    rows,
    check_priority,
    priority,
    speed,
    host_1,
    form_factor,
    host_2_check,
    host_2,
    quiet,
    loop
    ):
    
    additional_settings = ['--chrome-flags="--disable-dev-shm-usage"']
        
    if speed and speed != "":
        
        if speed == "slow-4g":
            additional_settings += MORE_SETTINGS
            additional_settings.append("--throttling-method='simulate'")
        elif speed == "normal":
            additional_settings += MORE_SETTINGS
            additional_settings.append("--throttling-method='provided'")
            
    additional_settings = list(set(additional_settings))
        
    for i,row in tqdm(enumerate(rows)):
        file_w = open(output_path, 'a',encoding="utf8")
        writer = csv.writer(file_w, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if i==0:
            writer.writerow(cols)
        
        print(f"\nProcessing URL-{i+1}\n")
        if len(row) > 1:
            p = row[1].strip() if len(row[1])!=0 else "1"
        else:
            p = "1"
        
        url = row[0].strip().lower()
        
        if url == "":
            continue
        
        if check_priority and (p != priority):
            continue
        
        try:
            old_url = urljoin(host_1,url)
            old_report = LighthouseRepeatRunner(old_url, form_factor=form_factor, quiet=quiet, additional_settings=additional_settings, repeats=loop, timings=BASE_TIMINGS).report
            old_FCP = old_report.timings['first-contentful-paint'].total_seconds()
            old_LCP = old_report.timings['largest-contentful-paint'].total_seconds()
            old_CLS = old_report.timings['cumulative-layout-shift'].total_seconds()
            old_SI = old_report.timings['speed-index'].total_seconds()
            old_TBT = old_report.timings['total-blocking-time'].total_seconds()
            old_TTFB = old_report.timings['server-response-time'].total_seconds()
            old_FID = old_report.timings['max-potential-fid'].total_seconds()
            old_TTI = old_report.timings['interactive'].total_seconds()
            old_performance = old_report.score['performance'] or 0
            
            if host_2_check:
                new_url = urljoin(host_2,url)
                new_report = LighthouseRepeatRunner(new_url, form_factor=form_factor, quiet=quiet, additional_settings=additional_settings, repeats=loop, timings=BASE_TIMINGS).report
                new_FCP = new_report.timings['first-contentful-paint'].total_seconds()
                new_LCP = new_report.timings['largest-contentful-paint'].total_seconds()
                new_CLS = new_report.timings['cumulative-layout-shift'].total_seconds()
                new_SI = new_report.timings['speed-index'].total_seconds()
                new_TBT = new_report.timings['total-blocking-time'].total_seconds()
                new_TTFB = new_report.timings['server-response-time'].total_seconds()
                new_FID = new_report.timings['max-potential-fid'].total_seconds()
                new_TTI = new_report.timings['interactive'].total_seconds()
                new_performance = new_report.score['performance'] or 0
                
                failed = "0"
                new_row = [url,p,failed,old_performance,new_performance,old_FCP,new_FCP,old_LCP,new_LCP,\
                    old_CLS,new_CLS,old_TTFB,new_TTFB,old_SI,new_SI,old_TBT,new_TBT,old_FID,new_FID,old_TTI,new_TTI]
            
            else:
                failed = "0"
                new_row = [url,p,failed,old_performance,old_FCP,old_LCP,old_CLS,old_TTFB,old_SI,old_TBT,old_FID,old_TTI]
            
        except Exception as e:
            
            logging.error(f"error: {str(e)}")
            failed = "1"
            new_row = [url,p,failed]

        writer.writerow(new_row)
        file_w.close()

app.mount("/static", StaticFiles(directory="/outputs"), name="static")

@app.get("/",include_in_schema=False)
async def root():
    return {"message": "got to /docs"}

@app.post("/lighthouse",tags=["App"])
async def start(
    host_1 : str,
    host_2 : str = None,
    priority : str = None,
    form_factor : str = Query(None, enum=FORM_FACTORS_OPTIONS),
    speed : str = Query(None, enum=SPEED_OPTIONS),
    quiet : bool = True,
    loop : int = 1,
    Input_urls : UploadFile = File(...)
    ):
    
    if loop <= 0:
        logging.error("loop is incorrect, it has to be more than zero")
        return {"error": "loop is incorrect, it has to be more than zero"}
    
    if Input_urls.content_type != "text/csv":
        logging.error("your file is not a CSV file")
        return {"error": "your file is not a CSV file"}
    
    if "http" not in host_1:
        logging.error("host_1 most have 'http'")
        return {"error": "host_1 most have 'http'"}
        
    if not host_2:
        host_2 = ""
        
    if not priority:
        priority = ""
    
    if not form_factor:
        form_factor = "mobile"
        
    if "http" not in host_2 and host_2.strip() != "":
        logging.error("host_2 most have 'http'")
        return {"error": "host_2 most have 'http'"}

    
    # Create a new directory to store the output file
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Generate a timestamped filename for the output file
    delta = timedelta(hours=3.5)
    time_now = str(datetime.now()+delta).replace(" ","_")
    output_file_path=os.path.join(OUTPUT_PATH,time_now+"_output.csv")
    output_path = os.path.abspath(output_file_path)
    
    

    if host_2.strip() == "":
        host_2_check = False
        cols = ['URLs','Priority','Failed','Performance','FCP (s)','LCP (s)','CLS (s)','TTFB (s)','SI (s)','TBT (s)','FID (s)','TTI (s)']
    else:
        host_2_check = True
        cols = ['URLs','Priority','Failed','Old Performance','New Performance','Old FCP (s)','New FCP (s)','Old LCP (s)','New LCP (s)',\
            'Old CLS (s)','New CLS (s)', 'Old TTFB (s)','New TTFB (s)','Old SI (s)','New SI (s)','Old TBT (s)','New TBT (s)','Old FID (s)',\
            'New FID (s)','Old TTI (s)','New TTI (s)']

    if priority.strip() == "":
        check_priority = False
    else:
        check_priority = True

    
    # Read the contents of the uploaded file and parse it as CSV
    contents = await Input_urls.read()
    decoded_content = contents.decode('utf-8').splitlines()
    rows = csv.reader(decoded_content)
    
    # Call a Celery task to process the uploaded file in the background
    task = check_urls.delay(
        cols,
        output_path,
        list(rows),
        check_priority,
        priority,
        speed,
        host_1,
        form_factor,
        host_2_check,
        host_2,
        quiet,
        loop
        )
    
    return {"task_id":task.id,
            "output_link":f"/static/{output_path.replace('/outputs/','')}"}

# Define a new endpoint for checking the status of a Celery task
@app.get('/status/{task_id}',tags=["Task Manager"])
async def get_task_status(task_id: str):
    
    # Get the Celery task object with the specified task ID
    task = AsyncResult(task_id, app=celery_app)
    
    # Get a list of all pending tasks
    i = celery_app.control.inspect()
    pending_tasks = i.active()
    task_ids = [p['id'] for p in pending_tasks[f"celery@{CRAWLER_HOST}"]]
    
    # Check the status of the task and return a response
    if task.state in ["SUCCESS","FAILURE"]:
        return {'status': task.state}
    elif task.state == "PENDING":
        if task_id in task_ids:
            return {'status': "PENDING"}

    return {'status': "Not Exist"}

# Define a new endpoint for getting a list of pending Celery tasks
@app.get('/pending_tasks',tags=["Task Manager"])
async def get_pending_tasks():
    
    # Use the Celery Inspect class to get a list of all active tasks
    i = celery_app.control.inspect()
    pending_tasks = i.active()
    
    # Extract relevant information from each pending task and add it to the result list
    result = []
    for task in pending_tasks[f"celery@{CRAWLER_HOST}"]:
        task_id = task['id']
        task_start_time = datetime.fromtimestamp(task['time_start'] + 3.5*3600)
        task_pid = task['worker_pid']
        result.append({
            "task_id":task_id,
            "task_start_time":str(task_start_time).replace("T","  "),
            "task_pid":task_pid
        })
        
    return {"result":result}

# Define a new endpoint for terminating a running Celery task
@app.delete('/process/{task_id}',tags=["Task Manager"])
async def delete_process(task_id: str):
    
    try:
        
        # Use the Celery Inspect class to get a list of all active tasks
        i = celery_app.control.inspect()
        pending_tasks = i.active()
        
        # Find the worker PID for the specified task ID
        try:
            task_pid = [p['worker_pid'] for p in pending_tasks[f"celery@{CRAWLER_HOST}"] if p['id'] == task_id][0]
        except Exception as e:
            return {"error":str(e)}
        
        # Send a SIGTERM signal to the worker process to terminate the task
        os.kill(task_pid, signal.SIGTERM)
        
        return {'message': f'task with ID {task_id} has been terminated'}
    
    except ProcessLookupError:
        
        return {'error': f'task with ID {task_id} not found'}


