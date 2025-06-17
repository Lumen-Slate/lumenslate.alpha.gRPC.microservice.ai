import os
import sys
import grpc
import getpass
import signal
import logging
from dotenv import load_dotenv
from concurrent import futures
from logging.handlers import RotatingFileHandler
import threading
import time
from app.api.primary_agent_handler import primary_agent_handler

# ==== Logging Setup ====
LOG_PATH = os.path.join(os.path.dirname(__file__), "grpc_server.log")
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

# ==== Load .env ====
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

# ==== Ensure imports work ====
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "protos"))

from app.protos import ai_service_pb2, ai_service_pb2_grpc
from app.logic.context_generator import generate_context_logic
from app.logic.mcq_variation_generator import generate_mcq_variations_logic
from app.logic.msq_variation_generator import generate_msq_variations_logic
from app.logic.question_segmentation import segment_question_logic
from app.logic.variable_detector import detect_variables_logic
from app.logic.variable_randomizer import extract_and_randomize_logic
from app.logic.agent_service import agent_logic

# ==== gRPC Service Implementation ====
class AIService(ai_service_pb2_grpc.AIServiceServicer):
    def GenerateContext(self, request, context):
        try:
            response_text = generate_context_logic(
                question=request.question,
                keywords=list(request.keywords),
                language=request.language,
            )
            logger.info("[GenerateContext] Successful")
            return ai_service_pb2.GenerateContextResponse(content=response_text)
        except Exception as e:
            logger.exception("[GenerateContext] Failed\nQuestion: %s\nKeywords: %s\nLanguage: %s\nError: %s", request.question, request.keywords, request.language, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.GenerateContextResponse()

    def DetectVariables(self, request, context):
        try:
            result = detect_variables_logic(request.question)
            variables = [
                ai_service_pb2.DetectedVariable(
                    name=v.name,
                    value=v.value or "",
                    namePositions=v.namePositions,
                    valuePositions=v.valuePositions,
                )
                for v in result.variables
            ]
            logger.info("[DetectVariables] Successful")
            return ai_service_pb2.VariableDetectorResponse(variables=variables)
        except Exception as e:
            logger.exception("[DetectVariables] Failed\nQuestion: %s\nError: %s", request.question, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.VariableDetectorResponse()

    def SegmentQuestion(self, request, context):
        try:
            segmented = segment_question_logic(request.question)
            logger.info("[SegmentQuestion] Successful")
            return ai_service_pb2.QuestionSegmentationResponse(segmentedQuestion=segmented)
        except Exception as e:
            logger.exception("[SegmentQuestion] Failed\nQuestion: %s\nError: %s", request.question, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.QuestionSegmentationResponse()

    def GenerateMCQVariations(self, request, context):
        try:
            result = generate_mcq_variations_logic(
                question=request.question,
                options=list(request.options),
                answerIndex=request.answerIndex,
            )
            variations = [
                ai_service_pb2.MCQQuestion(
                    question=v.question,
                    options=v.options,
                    answerIndex=v.answerIndex,
                )
                for v in result.variations
            ]
            logger.info("[GenerateMCQVariations] Successful")
            return ai_service_pb2.MCQVariation(variations=variations)
        except Exception as e:
            logger.exception("[GenerateMCQVariations] Failed\nQuestion: %s\nOptions: %s\nAnswerIndex: %d\nError: %s", request.question, request.options, request.answerIndex, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MCQVariation()

    def GenerateMSQVariations(self, request, context):
        try:
            result = generate_msq_variations_logic(
                question=request.question,
                options=list(request.options),
                answerIndices=list(request.answerIndices),
            )
            variations = [
                ai_service_pb2.MSQQuestion(
                    question=v.question,
                    options=v.options,
                    answerIndices=v.answerIndices,
                )
                for v in result.variations
            ]
            logger.info("[GenerateMSQVariations] Successful")
            return ai_service_pb2.MSQVariation(variations=variations)
        except Exception as e:
            logger.exception("[GenerateMSQVariations] Failed\nQuestion: %s\nOptions: %s\nAnswerIndices: %s\nError: %s", request.question, request.options, request.answerIndices, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MSQVariation()

    def FilterAndRandomize(self, request, context):
        try:
            result = extract_and_randomize_logic(
                question=request.question,
                user_prompt=request.userPrompt,
            )
            variables = []
            for v in result.variables:
                filters = ai_service_pb2.VariableFilter()
                if hasattr(v.filters, "range") and v.filters.range:
                    filters.range.extend(v.filters.range)
                if hasattr(v.filters, "options") and v.filters.options:
                    filters.options.extend([str(opt) for opt in v.filters.options])
                variables.append(
                    ai_service_pb2.RandomizedVariable(
                        name=v.name,
                        value=str(v.value or ""),
                        filters=filters,
                    )
                )
            logger.info("[FilterAndRandomize] Successful")
            return ai_service_pb2.FilterAndRandomizerResponse(variables=variables)
        except Exception as e:
            logger.exception("[FilterAndRandomize] Failed\nQuestion: %s\nUserPrompt: %s\nError: %s", request.question, request.userPrompt, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.FilterAndRandomizerResponse()

    def Agent(self, request, context):
        logger.info(f"[Agent] Request: userId={request.userId}, role={request.role}, fileType={request.fileType}, file={bool(request.file)}, message={request.message}, createdAt={request.createdAt}, updatedAt={request.updatedAt}")
        try:
            import asyncio
            # Create an event loop if one doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function
            response = loop.run_until_complete(primary_agent_handler(request))
            logger.info(f"[Agent] Response: {response}")
            return ai_service_pb2.AgentResponse(
                message=response["message"],
                user_id=response["user_id"],
                agent_name=response["agent_name"],
                agent_response=response["agent_response"],
                session_id=response["session_id"],
                createdAt=response["createdAt"],
                updatedAt=response["updatedAt"],
                response_time=response["response_time"],
                role=response["role"],
                feedback=response["feedback"]
            )
        except Exception as e:
            logger.exception(f"[Agent] Failed\nError: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.AgentResponse()

# ==== Server Startup ====
def serve():
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

        ai_service_pb2_grpc.add_AIServiceServicer_to_server(AIService(), server)
        server.add_insecure_port("0.0.0.0:50051")

        # === Shutdown handler ===
        def shutdown_handler(signum, _):
            logger.warning(f"🛑 Received shutdown signal: {signum}. Gracefully stopping gRPC server...")
            all_done = server.stop(grace=5)
            all_done.wait(timeout=5)
            logger.info("✅ gRPC server shut down.")
            os._exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        # === Start the server ===
        logger.info("✅ gRPC server starting on 0.0.0.0:50051")
        server.start()
        logger.info("📡 gRPC server is running. Waiting for connections...")

        # === Optional heartbeat ===
        def liveness_monitor():
            while True:
                logger.debug("💓 gRPC server heartbeat check")
                time.sleep(30)

        heartbeat_thread = threading.Thread(target=liveness_monitor, daemon=True)
        heartbeat_thread.start()

        # === Wait for shutdown ===
        server.wait_for_termination()

    except Exception as e:
        logger.exception("💥 gRPC Server crashed unexpectedly \nError : %s", str(e))

if __name__ == "__main__":
    logger.info("🚀 Launching gRPC server...")
    try:
        serve()
    except Exception as e:
        logger.exception("💥 gRPC Server exited unexpectedly:")
