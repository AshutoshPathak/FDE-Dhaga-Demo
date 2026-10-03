from __future__ import annotations
import os, socket
from src.ui import create_dhaga_app

def find_available_port(preferred_port: int = 7860) -> int:
    configured = os.getenv("GRADIO_SERVER_PORT")
    if configured:
        return int(configured)
    for p in [preferred_port, preferred_port + 1, preferred_port + 2]:
        try:
            with socket.socket() as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("0.0.0.0", p))
                return p
        except OSError:
            continue
    with socket.socket() as sock:
        sock.bind(("0.0.0.0", 0))
        return sock.getsockname()[1]

def main():
    demo, css, theme = create_dhaga_app()
    port = find_available_port()
    demo.queue(default_concurrency_limit=4).launch(
        server_name="0.0.0.0",
        server_port=port,
        css=css,
        theme=theme,
        max_file_size="10mb"
    )

if __name__ == "__main__":
    main()
