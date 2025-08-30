import subprocess
import time
import sys

def main():
    print("Starting CrawlerWebBot with Docker...")
    
    # Start Docker services
    print("Starting Docker containers...")
    docker_cmd = ["docker-compose", "up", "-d"]
    result = subprocess.run(docker_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Failed to start Docker: {result.stderr}")
        return
    
    print("Docker containers started!")
    
    print("Services status:")
    subprocess.run(["docker-compose", "ps"])
    
    print("\nCrawlerWebBot is running!")
    print("API: http://localhost:8000")
    print("MongoDB Admin: http://localhost:8081 (admin/admin123)")
    print("API Docs: http://localhost:8000/docs")
    print("\nTo stop: docker-compose down")
    print("To view logs: docker-compose logs -f")

if __name__ == "__main__":
    main()
