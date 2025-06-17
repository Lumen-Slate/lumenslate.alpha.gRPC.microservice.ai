import os
import sys
import grpc
import signal
import threading
import time
from concurrent import futures
from app.config.logging_config import logger
from app.utils.env_setup import load_and_check_env
from app.utils.auth_helper import setup_google_auth, get_project_id, is_deployed_environment
from app.services import AIService, ServiceFactory
from app.protos import ai_service_pb2_grpc

def serve():
    logger.info("🔧 Initializing gRPC server...")
    
    # Load environment variables
    load_and_check_env()
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))

    # Setup Google Cloud authentication
    logger.info("🔐 Setting up authentication...")
    auth_success = setup_google_auth()
    
    if not auth_success:
        logger.error("❌ Authentication setup failed. Server cannot start.")
        return False
    
    # Verify required environment variables
    project_id = get_project_id()
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    if not project_id:
        logger.error("❌ GOOGLE_PROJECT_ID not found. Please set this environment variable.")
        return False
    
    logger.info(f"✅ Authentication configured - Project: {project_id}, Location: {location}")
    
    # Check if we're in deployed environment
    if is_deployed_environment():
        logger.info("🌐 Running in deployed environment (using metadata service)")
    else:
        logger.info("🏠 Running in local development environment")

    # Use Cloud Run-provided PORT or fallback to 50051 for gRPC
    port = os.getenv("PORT", "50051")

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

        ai_service_pb2_grpc.add_AIServiceServicer_to_server(
            ServiceFactory.create_ai_service(logger), server
        )

        # Add health check service
        try:
            from grpc_health.v1 import health_pb2_grpc, health, health_pb2
            health_servicer = health.HealthServicer()
            health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
            # Set service status to serving
            health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
            logger.info("✅ Health check service added")
        except ImportError:
            logger.warning("⚠️ grpcio-health-checking not available, health checks disabled")

        server.add_insecure_port(f"0.0.0.0:{port}")

        def shutdown_handler(signum, _):
            logger.warning(f"Received shutdown signal: {signum}. Gracefully stopping gRPC server...")
            all_done = server.stop(grace=5)
            all_done.wait(timeout=5)
            logger.info("gRPC server shut down.")
            os._exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        logger.info(f"🚀 gRPC server starting on 0.0.0.0:{port}")
        server.start()
        logger.info("✅ gRPC server is running and ready to accept connections.")

        def liveness_monitor():
            while True:
                logger.debug("💓 gRPC server heartbeat check")
                time.sleep(30)

        heartbeat_thread = threading.Thread(target=liveness_monitor, daemon=True)
        heartbeat_thread.start()

        server.wait_for_termination()
        return True

    except Exception as e:
        logger.exception("❌ gRPC Server crashed unexpectedly \nError : %s", str(e))
        return False


if __name__ == "__main__":
    logger.info("🔧 Launching gRPC server...")
    try:
        success = serve()
        if not success:
            logger.error("❌ Server failed to start properly")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("❌ gRPC Server exited unexpectedly:")
        sys.exit(1)
