import sys
import os
import grpc
from concurrent import futures
import getpass
from dotenv import load_dotenv

# Ensure grpc_generated is in sys.path for imports to work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "grpc_generated"))

from app.protos import ai_service_pb2, ai_service_pb2_grpc

# Import logic functions from refactored route modules
from app.routes.context_generator import generate_context_logic
from app.routes.mcq_variation_generator import generate_mcq_variations_logic
from app.routes.msq_variation_generator import generate_msq_variations_logic
from app.routes.question_segmentation import segment_question_logic
from app.routes.variable_detector import detect_variables_logic
from app.routes.variable_randomizer import extract_and_randomize_logic

load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass(
        "You have not entered the GOOGLE_API_KEY in .env file. Enter your Google AI API key: "
    )

class AIService(ai_service_pb2_grpc.AIServiceServicer):
    def GenerateContext(self, request, context):
        response_text = generate_context_logic(
            question=request.question,
            keywords=list(request.keywords),
            language=request.language
        )
        return ai_service_pb2.GenerateContextResponse(content=response_text)

    def DetectVariables(self, request, context):
        result = detect_variables_logic(request.question)
        variables = []
        for v in result.variables:
            variables.append(ai_service_pb2.DetectedVariable(
                name=v.name,
                value=v.value if v.value is not None else "",
                namePositions=v.namePositions,
                valuePositions=v.valuePositions
            ))
        return ai_service_pb2.VariableDetectorResponse(variables=variables)

    def SegmentQuestion(self, request, context):
        segmented = segment_question_logic(request.question)
        return ai_service_pb2.QuestionSegmentationResponse(segmentedQuestion=segmented)

    def GenerateMCQVariations(self, request, context):
        result = generate_mcq_variations_logic(
            question=request.question,
            options=list(request.options),
            answerIndex=request.answerIndex
        )
        variations = []
        for v in result.variations:
            variations.append(ai_service_pb2.MCQQuestion(
                question=v.question,
                options=v.options,
                answerIndex=v.answerIndex
            ))
        return ai_service_pb2.MCQVariation(variations=variations)

    def GenerateMSQVariations(self, request, context):
        result = generate_msq_variations_logic(
            question=request.question,
            options=list(request.options),
            answerIndices=list(request.answerIndices)
        )
        variations = []
        for v in result.variations:
            variations.append(ai_service_pb2.MSQQuestion(
                question=v.question,
                options=v.options,
                answerIndices=v.answerIndices
            ))
        return ai_service_pb2.MSQVariation(variations=variations)

    def FilterAndRandomize(self, request, context):
        result = extract_and_randomize_logic(
            question=request.question,
            user_prompt=request.userPrompt
        )
        variables = []
        for v in result.variables:
            filter_msg = ai_service_pb2.VariableFilter()
            if hasattr(v.filters, "range") and v.filters.range:
                filter_msg.range.extend(v.filters.range)
            if hasattr(v.filters, "options") and v.filters.options:
                filter_msg.options.extend([str(opt) for opt in v.filters.options])
            variables.append(ai_service_pb2.RandomizedVariable(
                name=v.name,
                value=str(v.value) if v.value is not None else "",
                filters=filter_msg
            ))
        return ai_service_pb2.FilterAndRandomizerResponse(variables=variables)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ai_service_pb2_grpc.add_AIServiceServicer_to_server(AIService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
