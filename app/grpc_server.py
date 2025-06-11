import os
import sys
import grpc
import getpass
import signal
import logging
from dotenv import load_dotenv
from concurrent import futures
from logging.handlers import RotatingFileHandler

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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "grpc_generated"))

from app.protos import ai_service_pb2, ai_service_pb2_grpc
from app.logic.context_generator import generate_context_logic
from app.logic.mcq_variation_generator import generate_mcq_variations_logic
from app.logic.msq_variation_generator import generate_msq_variations_logic
from app.logic.question_segmentation import segment_question_logic
from app.logic.variable_detector import detect_variables_logic
from app.logic.variable_randomizer import extract_and_randomize_logic

# ==== gRPC Service Implementation ====
class AIService(ai_service_pb2_grpc.AIServiceServicer):
    def GenerateContext(self, request, context):
        logger.info("[GenerateContext] Request: %s", request)
        try:
            response_text = generate_context_logic(
                question=request.question,
                keywords=list(request.keywords),
                language=request.language,
            )
            return ai_service_pb2.GenerateContextResponse(content=response_text)
        except Exception as e:
            logger.exception("[GenerateContext] Failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.GenerateContextResponse()

    def DetectVariables(self, request, context):
        logger.info("[DetectVariables] Request: %s", request)
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
            return ai_service_pb2.VariableDetectorResponse(variables=variables)
        except Exception as e:
            logger.exception("[DetectVariables] Failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.VariableDetectorResponse()

    def SegmentQuestion(self, request, context):
        logger.info("[SegmentQuestion] Request: %s", request)
        try:
            segmented = segment_question_logic(request.question)
            return ai_service_pb2.QuestionSegmentationResponse(segmentedQuestion=segmented)
        except Exception as e:
            logger.exception("[SegmentQuestion] Failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.QuestionSegmentationResponse()

    def GenerateMCQVariations(self, request, context):
        logger.info("[GenerateMCQVariations] Request: %s", request)
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
            return ai_service_pb2.MCQVariation(variations=variations)
        except Exception as e:
            logger.exception("[GenerateMCQVariations] Failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MCQVariation()

    def GenerateMSQVariations(self, request, context):
        logger.info("[GenerateMSQVariations] Request: %s", request)
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
            return ai_service_pb2.MSQVariation(variations=variations)
        except Exception as e:
            logger.exception("[GenerateMSQVariations] Failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MSQVariation()

    def FilterAndRandomize(self, request, context):
        logger.info("[FilterAndRandomize] Request: %s", request)
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
            return ai_service_pb2.FilterAndRandomizerResponse(variables=variables)
        except Exception as e:
            logger.exception("[FilterAndRandomize] extract_and_randomize_logic FAILED")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.FilterAndRandomizerResponse()

# ==== Server Startup ====
def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.keepalive_permit_without_calls', 1),
        ]
    )
    ai_service_pb2_grpc.add_AIServiceServicer_to_server(AIService(), server)
    server.add_insecure_port("0.0.0.0:50051")

    def shutdown_handler(signum, frame):
        logger.info("🛑 Shutdown signal received. Stopping gRPC server...")
        server.stop(0)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info("✅ gRPC server started on 0.0.0.0:50051")
    try:
        server.start()
        server.wait_for_termination()
    except Exception as e:
        logger.exception("💥 gRPC Server crashed unexpectedly:")

if __name__ == "__main__":
    logger.info("🚀 Launching gRPC server...")
    try:
        serve()
    except Exception as e:
        logger.exception("💥 gRPC Server exited unexpectedly:")
