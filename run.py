import subprocess
import time
import sys

def main():    
    # Start API server
    print("Starting API server on http://localhost:8000")
    api_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    api_process = subprocess.Popen(api_cmd)
    
    # Start scheduler
    print("Starting scheduler...")
    scheduler_cmd = [sys.executable, "scheduler.py"]
    scheduler_process = subprocess.Popen(scheduler_cmd)
    
    print("Both services started!")
    print("API: http://localhost:8000")
    print("Scheduler: Running every 3 hours")
    print("Press Ctrl+C to stop")
    
    try:
        # Wait for scheduler to finish (it runs forever)
        scheduler_process.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        scheduler_process.terminate()
        api_process.terminate()
        print("Stopped!")

if __name__ == "__main__":
    main()
