# app.py
"""主应用入口"""

from server_app import ServerMonitorApp

if __name__ == "__main__":
    app = ServerMonitorApp()
    app.run()