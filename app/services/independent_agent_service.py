"""
Question Generation Services for AI microservice.
Handles context generation, variable detection, question segmentation, and variations.
"""

import grpc
from typing import Any
from app.protos import ai_service_pb2
from app.services.base_service import BaseService
from app.agents.independent_agents.context_generator.context_generator import generate_context_logic
from app.agents.independent_agents.variable_detector.variable_detector import detect_variables_logic
from app.agents.independent_agents.question_segmentator.question_segmentator import segment_question_logic
from app.agents.independent_agents.mcq_variation_generator.mcq_variation_generator import generate_mcq_variations_logic
from app.agents.independent_agents.msq_variation_generator.msq_variation_generator import generate_msq_variations_logic
from app.agents.independent_agents.variable_randomizer.variable_randomizer import extract_and_randomize_logic


class IndependentAgentService(BaseService):
    """Service for handling question generation and processing."""

    def GenerateContext(self, request: Any, context: grpc.ServicerContext) -> ai_service_pb2.GenerateContextResponse:
        """Generate contextual passage for a question."""
        try:
            response_text = generate_context_logic(
                question=request.question,
                keywords=list(request.keywords),
                language=request.language,
            )
            return ai_service_pb2.GenerateContextResponse(content=response_text)
        except Exception as e:
            self.logger.exception("[GenerateContext] Failed | Question: %s | Keywords: %s | Language: %s | Error: %s", 
                                  request.question, request.keywords, request.language, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.GenerateContextResponse()

    def DetectVariables(self, request: Any, context: grpc.ServicerContext) -> ai_service_pb2.VariableDetectorResponse:
        """Detect variables in a question."""
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
            self.logger.exception("[DetectVariables] Failed | Question: %s | Error: %s", request.question, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.VariableDetectorResponse()

    def SegmentQuestion(self, request: Any, context: grpc.ServicerContext) -> ai_service_pb2.QuestionSegmentationResponse:
        """Break a question into smaller parts."""
        try:
            segmented = segment_question_logic(request.question)
            return ai_service_pb2.QuestionSegmentationResponse(segmentedQuestion=segmented)
        except Exception as e:
            self.logger.exception("[SegmentQuestion] Failed | Question: %s | Error: %s", request.question, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.QuestionSegmentationResponse()

    def GenerateMCQVariations(self, request: Any, context: grpc.ServicerContext) -> ai_service_pb2.MCQVariation:
        """Create MCQ variations."""
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
            self.logger.exception("[GenerateMCQVariations] Failed | Question: %s | Options: %s | AnswerIndex: %d | Error: %s", 
                                  request.question, request.options, request.answerIndex, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MCQVariation()

    def GenerateMSQVariations(self, request: Any, context: grpc.ServicerContext) -> ai_service_pb2.MSQVariation:
        """Create MSQ variations."""
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
            self.logger.exception("[GenerateMSQVariations] Failed | Question: %s | Options: %s | AnswerIndices: %s | Error: %s", 
                                  request.question, request.options, request.answerIndices, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.MSQVariation()

    def FilterAndRandomize(self, request: Any, context: grpc.ServicerContext) -> ai_service_pb2.FilterAndRandomizerResponse:
        """Extract and randomize variable filters."""
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
            self.logger.exception("[FilterAndRandomize] Failed | Question: %s | UserPrompt: %s | Error: %s", 
                                  request.question, request.userPrompt, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.FilterAndRandomizerResponse()
