import asyncio
import aiohttp
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urljoin

# Import Docker configuration
from schedule_config_docker import (
    API_CONFIG, 
    SCHEDULE_CONFIG, 
    BULLETIN_CONFIG
)


class DockerCryptoNewsScheduler:    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=API_CONFIG["timeout"]),
            headers=API_CONFIG["headers"]
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def call_api(self, endpoint: str, method: str = "GET", params: Dict = None) -> Optional[Dict[Any, Any]]:
        """Gọi API với retry mechanism"""
        url = urljoin(API_CONFIG["base_url"], endpoint)
        
        for attempt in range(SCHEDULE_CONFIG["max_retries"]):
            try:
                print(f"Calling API: {method} {url} (attempt {attempt + 1})")
                
                if method.upper() == "GET":
                    async with self.session.get(url, params=params) as response:
                        response_data = await response.json()
                        
                        if response.status == 200:
                            print(f"API call successful: {url}")
                            return response_data
                        else:
                            print(f"API call failed with status {response.status}: {response_data}")
                
                elif method.upper() == "POST":
                    async with self.session.post(url, params=params) as response:
                        response_data = await response.json()
                        
                        if response.status == 200:
                            print(f"API call successful: {url}")
                            return response_data
                        else:
                            print(f"API call failed with status {response.status}: {response_data}")
                            
            except Exception as e:
                print(f"API call attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < SCHEDULE_CONFIG["max_retries"] - 1:
                    print(f"Retrying in {SCHEDULE_CONFIG['retry_delay']} seconds...")
                    await asyncio.sleep(SCHEDULE_CONFIG["retry_delay"])
        
        print(f"All API call attempts failed for {url}")
        return None
    
    async def run_scheduled_task(self):
        """Chạy 1 chu trình hoàn chỉnh: get_all_news -> create_bulletin"""
        start_time = datetime.now()
        print("=" * 50)
        print("Starting Docker scheduled task cycle")
        
        try:
            # Step 1: Chạy get_all_news
            print("Starting get_all_news task")
            news_result = await self.call_api(API_CONFIG["endpoints"]["get_all_news"])
            
            if news_result:
                data = news_result.get("data", {})
                summary = data.get("summary", {})
                print(f"get_all_news completed - Sources: {summary.get('successful_sources', 0)}/{summary.get('total_sources', 0)}, Articles: {summary.get('total_articles', 0)}")
                
                print(f"Waiting {SCHEDULE_CONFIG['delay_between_tasks']} seconds...")
                await asyncio.sleep(SCHEDULE_CONFIG["delay_between_tasks"])
                
                # Step 2: Chạy create_bulletin
                print("Starting create_bulletin task")
                params = {
                    "hours": BULLETIN_CONFIG["hours"],
                    "limit": BULLETIN_CONFIG["limit"]
                }
                
                bulletin_result = await self.call_api(
                    API_CONFIG["endpoints"]["create_bulletin"], 
                    method="POST",
                    params=params
                )
                
                if bulletin_result:
                    data = bulletin_result.get("data", {})
                    metadata = data.get("metadata", {})
                    print(f"create_bulletin completed - Articles: {metadata.get('articles_processed', 0)}")
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    print(f"Docker scheduled task completed successfully in {duration:.2f}s")
                else:
                    print("create_bulletin failed")
            else:
                print("get_all_news failed")
        
        except Exception as e:
            print(f"Docker scheduled task error: {str(e)}")
        
        finally:
            end_time = datetime.now()
            print(f"⏱Task duration: {(end_time - start_time).total_seconds():.2f}s")
            print("=" * 50)
    
    async def start_scheduler(self):
        """Bắt đầu scheduler"""
        print("Starting Docker Crypto News Scheduler")
        print(f"Schedule: Every {SCHEDULE_CONFIG['interval_minutes']} minutes")
        print(f"Bulletin: {BULLETIN_CONFIG['hours']} hours, {BULLETIN_CONFIG['limit']} articles")
        
        self.is_running = True
        
        # Chạy ngay lần đầu nếu được cấu hình
        if SCHEDULE_CONFIG["run_on_startup"]:
            print("Running initial task on startup...")
            await self.run_scheduled_task()
        
        # Vòng lặp chính
        while self.is_running:
            try:
                next_run = datetime.now() + timedelta(minutes=SCHEDULE_CONFIG["interval_minutes"])
                print(f"Next run scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Chờ đến lần chạy tiếp theo
                await asyncio.sleep(SCHEDULE_CONFIG["interval_minutes"] * 60)
                
                if self.is_running:
                    await self.run_scheduled_task()
                    
            except KeyboardInterrupt:
                print("Received interrupt signal, stopping Docker scheduler...")
                self.is_running = False
            except Exception as e:
                print(f"Docker scheduler loop error: {str(e)}")
                await asyncio.sleep(60)


async def main():
    """Main function for Docker"""
    print("Docker Crypto News Scheduler")
    print("API Server: http://app:8000")
    print("Running in Docker container")
    print("-" * 50)
    
    async with DockerCryptoNewsScheduler() as scheduler:
        try:
            await scheduler.start_scheduler()
        except KeyboardInterrupt:
            print("\nDocker scheduler stopped by user")
        except Exception as e:
            print(f"Docker scheduler error: {str(e)}")
        finally:
            print("Docker scheduler shutdown complete")


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDocker End!")
    except Exception as e:
        print(f"Docker fatal error: {str(e)}")
