import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, os, asyncpg

DATABASE_URL = os.getenv("DATABASE_URL")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            # Running async in sync handler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            status = loop.run_until_complete(self.get_status())
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    async def get_status(self):
        status = {"bot": True, "db": False, "users": 0, "recent_feedback": 0}
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            users = await conn.fetchval("SELECT COUNT(*) FROM users")
            feedback = await conn.fetchval("SELECT COUNT(*) FROM feedback")
            await conn.close()
            status["db"] = True
            status["users"] = users
            status["recent_feedback"] = feedback
        except Exception as e:
            print(f"DB error: {e}")
        return status

def run():
    server = HTTPServer(("0.0.0.0", 8080), Handler)
    print("✅ Monitor API running on port 8080")
    server.serve_forever()

if __name__ == "__main__":
    run()
