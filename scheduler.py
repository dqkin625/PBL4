import asyncio
import aiohttp
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urljoin

# Import configuration
from schedule_config import (
    API_CONFIG, 
    SCHEDULE_CONFIG, 
    BULLETIN_CONFIG
)


class CryptoNewsScheduler:    
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
    
    async def run_get_all_news(self) -> bool:
        """Chạy API get_all_news"""
        print("Starting get_all_news task")
        
        try:
            result = await self.call_api(API_CONFIG["endpoints"]["get_all_news"])
            
            if result:
                # Log thống kê
                data = result.get("data", {})
                summary = data.get("summary", {})
                
                print(
                    f"get_all_news completed - "
                    f"Sources: {summary.get('successful_sources', 0)}/{summary.get('total_sources', 0)}, "
                    f"Articles: {summary.get('total_articles', 0)}, "
                    f"Time: {data.get('execution_time_seconds', 0)}s"
                )
                
                return True
            else:
                print("get_all_news failed")
                return False
                
        except Exception as e:
            print(f"Error in run_get_all_news: {str(e)}")
            return False
    
    async def run_create_bulletin(self) -> bool:
        """Chạy API create_bulletin"""
        print("Starting create_bulletin task")
        
        try:
            params = {
                "hours": BULLETIN_CONFIG["hours"],
                "limit": BULLETIN_CONFIG["limit"]
            }
            
            if BULLETIN_CONFIG["sources"]:
                params["sources"] = BULLETIN_CONFIG["sources"]
            
            result = await self.call_api(
                API_CONFIG["endpoints"]["create_bulletin"], 
                method="POST",
                params=params
            )
            
            if result:
                # Log thống kê
                data = result.get("data", {})
                metadata = data.get("metadata", {})
                
                print(
                    f"create_bulletin completed - "
                    f"Articles processed: {metadata.get('articles_processed', 0)}, "
                    f"Sources used: {len(metadata.get('sources_used', []))}"
                )
                
                return True
            else:
                print("create_bulletin failed")
                return False
                
        except Exception as e:
            print(f"Error in run_create_bulletin: {str(e)}")
            return False
    
    async def run_scheduled_task(self):
        """Chạy 1 chu trình hoàn chỉnh: get_all_news -> create_bulletin"""
        start_time = datetime.now()
        print("=" * 50)
        print("Starting scheduled task cycle")
        
        try:
            # Step 1: Chạy get_all_news
            news_success = await self.run_get_all_news()
            
            if news_success:
                print(f"Waiting {SCHEDULE_CONFIG['delay_between_tasks']} seconds before creating bulletin...")
                await asyncio.sleep(SCHEDULE_CONFIG["delay_between_tasks"])
                
                # Step 2: Chạy create_bulletin
                bulletin_success = await self.run_create_bulletin()
                
                if bulletin_success:
                    success_msg = f"Scheduled task completed successfully in {(datetime.now() - start_time).total_seconds():.2f}s"
                    print(success_msg)
                else:
                    error_msg = "create_bulletin failed in scheduled task"
                    print(error_msg)
            else:
                error_msg = "get_all_news failed in scheduled task"
                print(error_msg)
        
        except Exception as e:
            error_msg = f"Scheduled task error: {str(e)}"
            print(error_msg)
        
        finally:
            end_time = datetime.now()
            print(f"Scheduled task cycle ended. Duration: {(end_time - start_time).total_seconds():.2f}s")
            print("=" * 50)
    
    async def start_scheduler(self):
        """Bắt đầu scheduler"""
        print("Starting Crypto News Scheduler")
        print(f"Schedule: Every {SCHEDULE_CONFIG['interval_minutes']} minutes")
        print(f"Bulletin config: {BULLETIN_CONFIG['hours']} hours, {BULLETIN_CONFIG['limit']} articles limit")
        
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
                
                if self.is_running:  # Kiểm tra lại nếu đã bị dừng
                    await self.run_scheduled_task()
                    
            except KeyboardInterrupt:
                print("Received interrupt signal, stopping scheduler...")
                self.is_running = False
            except Exception as e:
                print(f"Scheduler loop error: {str(e)}")
                await asyncio.sleep(60)  # Chờ 1 phút trước khi thử lại
    
    def stop_scheduler(self):
        """Dừng scheduler"""
        print("Stopping scheduler...")
        self.is_running = False


async def main():
    """Main function"""
    print("Crypto News Scheduler")
    print(f"Configuration: {SCHEDULE_CONFIG['interval_minutes']} minutes interval")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    async with CryptoNewsScheduler() as scheduler:
        try:
            await scheduler.start_scheduler()
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
        except Exception as e:
            print(f"Scheduler error: {str(e)}")
        finally:
            print("Scheduler shutdown complete")


if __name__ == "__main__":
    # Thiết lập event loop cho Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEND!")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
