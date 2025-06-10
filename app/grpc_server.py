import os
import sys
import grpc
import getpass
from dotenv import load_dotenv
from concurrent import futures
import logging

# Setup logging to file
LOG_PATH = os.path.join(os.path.dirname(__file__), "grpc_server.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Ensure generated code and logic are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "grpc_generated"))

from app.protos import ai_service_pb2, ai_service_pb2_grpc

# Import logic handlers
from app.logic.context_generator import generate_context_logic
from app.logic.mcq_variation_generator import generate_mcq_variations_logic
from app.logic.msq_variation_generator import generate_msq_variations_logic
from app.logic.question_segmentation import segment_question_logic
from app.logic.variable_detector import detect_variables_logic
from app.logic.variable_randomizer import extract_and_randomize_logic

# Load environment
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

class AIService(ai_service_pb2_grpc.AIServiceServicer):
    def GenerateContext(self, request, context):
        logging.info("[gRPC] GenerateContext called")
        logging.info(f"  request: {request}")
        try:
            logging.info(f"[GenerateContext] Input question: {request.question}")
            logging.info(f"[GenerateContext] Input keywords: {request.keywords}")
            logging.info(f"[GenerateContext] Input language: {request.language}")
            response_text = generate_context_logic(
                question=request.question,
                keywords=list(request.keywords),
                language=request.language,
            )
            logging.info(f"[GenerateContext] Response content: {response_text}")
            return ai_service_pb2.GenerateContextResponse(content=response_text)
        except Exception as e:
            logging.exception("[GenerateContext] Exception")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.GenerateContextResponse()

    def DetectVariables(self, request, context):
        logging.info("[gRPC] DetectVariables called")
        logging.info(f"  request: {request}")
        try:
            logging.info(f"[DetectVariables] Input question: {request.question}")
            result = detect_variables_logic(request.question)
            logging.info(f"[DetectVariables] Logic result: {result}")
            variables = [
                ai_service_pb2.DetectedVariable(
                    name=v.name,
                    value=v.value or "",
                    namePositions=v.namePositions,
                    valuePositions=v.valuePositions,
                )
                for v in result.variables
            ]
            logging.info(f"[DetectVariables] Response variables: {variables}")
            return ai_service_pb2.VariableDetectorResponse(variables=variables)
        except Exception as e:
            logging.exception("[DetectVariables] Exception")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.VariableDetectorResponse()

    def SegmentQuestion(self, request, context):
        logging.info("[gRPC] SegmentQuestion called")
        logging.info(f"  request: {request}")
        try:
            logging.info(f"[SegmentQuestion] Input question: {request.question}")
            segmented = segment_question_logic(request.question)
            logging.info(f"[SegmentQuestion] Segmented question: {segmented}")
            return ai_service_pb2.QuestionSegmentationResponse(segmentedQuestion=segmented)
        except Exception as e:
            logging.exception("[SegmentQuestion] Exception")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.QuestionSegmentationResponse()

    def GenerateMCQVariations(self, request, context):
        logging.info("[gRPC] GenerateMCQVariations called")
        logging.info(f"  request: {request}")
        try:
            logging.info(f"[GenerateMCQVariations] Input question: {request.question}")
            logging.info(f"[GenerateMCQVariations] Input options: {request.options}")
            logging.info(f"[GenerateMCQVariations] Input answerIndex: {request.answerIndex}")
            result = generate_mcq_variations_logic(
                question=request.question,
                options=list(request.options),
                answerIndex=request.answerIndex,
            )
            logging.info(f"[GenerateMCQVariations] Logic result: {result}")
            variations = [
                ai_service_pb2.MCQQuestion(
                    question=v.question,
                    options=v.options,
                    answerIndex=v.answerIndex,
                )
                for v in result.variations
            ]
            logging.info(f"[GenerateMCQVariations] Response variations: {variations}")
            return ai_service_pb2.MCQVariation(variations=variations)
        except Exception as e:
            logging.exception("[GenerateMCQVariations] Exception")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MCQVariation()

    def GenerateMSQVariations(self, request, context):
        logging.info("[gRPC] GenerateMSQVariations called")
        logging.info(f"  request: {request}")
        try:
            logging.info(f"[GenerateMSQVariations] Input question: {request.question}")
            logging.info(f"[GenerateMSQVariations] Input options: {request.options}")
            logging.info(f"[GenerateMSQVariations] Input answerIndices: {request.answerIndices}")
            result = generate_msq_variations_logic(
                question=request.question,
                options=list(request.options),
                answerIndices=list(request.answerIndices),
            )
            logging.info(f"[GenerateMSQVariations] Logic result: {result}")
            variations = [
                ai_service_pb2.MSQQuestion(
                    question=v.question,
                    options=v.options,
                    answerIndices=v.answerIndices,
                )
                for v in result.variations
            ]
            logging.info(f"[GenerateMSQVariations] Response variations: {variations}")
            return ai_service_pb2.MSQVariation(variations=variations)
        except Exception as e:
            logging.exception("[GenerateMSQVariations] Exception")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MSQVariation()

    def FilterAndRandomize(self, request, context):
        logging.info("[gRPC] FilterAndRandomize called")
        logging.info(f"  request: {request}")
        try:
            logging.info(f"[FilterAndRandomize] Input question: {request.question}")
            logging.info(f"[FilterAndRandomize] Input userPrompt: {request.userPrompt}")
            result = extract_and_randomize_logic(
                question=request.question,
                user_prompt=request.userPrompt,
            )
            logging.info(f"[FilterAndRandomize] Logic result: {result}")
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
            logging.info(f"[FilterAndRandomize] Response variables: {variables}")
            return ai_service_pb2.FilterAndRandomizerResponse(variables=variables)
        except Exception as e:
            logging.exception("[FilterAndRandomize] Exception")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.FilterAndRandomizerResponse()

def serve():
    try:
        logging.info("[Server] Starting gRPC server setup...")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        ai_service_pb2_grpc.add_AIServiceServicer_to_server(AIService(), server)
        logging.info("[Server] Adding insecure port: localhost:50051")
        server.add_insecure_port("localhost:50051")
        server.start()
        logging.info("✅ gRPC server started on port 50051")
        server.wait_for_termination()
    except Exception as e:
        logging.exception("❌ gRPC server failed to start:")

if __name__ == "__main__":
    logging.info("[Main] Launching gRPC server...")
    serve()
