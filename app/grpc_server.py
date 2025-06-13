import os
import sys
import grpc
import signal
import threading
import time
from concurrent import futures
from app.config.logging_config import logger
from app.config.settings import settings
from app.utils.env_setup import load_and_check_env
from app.services.grpc_service import AIService
from app.protos import ai_service_pb2_grpc

def serve():
    load_and_check_env()
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))
    try:
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ("grpc.keepalive_time_ms", 60000),
                ("grpc.keepalive_timeout_ms", 20000),
                ("grpc.keepalive_permit_without_calls", 1),
                ("grpc.http2.max_pings_without_data", 0),
            ]
        )
        ai_service_pb2_grpc.add_AIServiceServicer_to_server(AIService(logger=logger), server)
        server.add_insecure_port(f"0.0.0.0:{settings.PORT if hasattr(settings, 'PORT') else 8080}")

        def shutdown_handler(signum, _):
            logger.warning(f"Received shutdown signal: {signum}. Gracefully stopping gRPC server...")
            all_done = server.stop(grace=5)
            all_done.wait(timeout=5)
            logger.info("gRPC server shut down.")
            os._exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        logger.info(f"gRPC server starting on 0.0.0.0:{settings.PORT if hasattr(settings, 'PORT') else 8080}")
        server.start()
        logger.info("gRPC server is running. Waiting for connections...")

        def liveness_monitor():
            while True:
                logger.debug("gRPC server heartbeat check")
                time.sleep(30)

        heartbeat_thread = threading.Thread(target=liveness_monitor, daemon=True)
        heartbeat_thread.start()

        server.wait_for_termination()

    except Exception as e:
        logger.exception("gRPC Server crashed unexpectedly \nError : %s", str(e))

if __name__ == "__main__":
    logger.info("Launching gRPC server...")
    try:
        serve()
    except Exception as e:
        logger.exception("gRPC Server exited unexpectedly:")
