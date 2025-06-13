import grpc
import sys
import os
from app.protos import ai_service_pb2, ai_service_pb2_grpc
from app.logic.context_generator import generate_context_logic
from app.logic.mcq_variation_generator import generate_mcq_variations_logic
from app.logic.msq_variation_generator import generate_msq_variations_logic
from app.logic.question_segmentation import segment_question_logic
from app.logic.variable_detector import detect_variables_logic
from app.logic.variable_randomizer import extract_and_randomize_logic
from app.logic.agent_service import agent_logic
from app.api.primary_agent_handler import primary_agent_handler
from app.api.rag_agent_handler import rag_agent_handler
import logging
import asyncio
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# gRPC and AI service imports
import grpc
from app.protos import ai_service_pb2
from app.protos import ai_service_pb2_grpc

# Config and logging
from app.config.logging_config import logger

# GIN Backend configuration for corpus management
GIN_BACKEND_URL = os.getenv("GIN_BACKEND_URL", "http://localhost:8080")

class AIService(ai_service_pb2_grpc.AIServiceServicer):
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def _run_in_executor(self, func, *args):
        """Helper to run sync functions in executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    def GenerateContext(self, request, context):
        try:
            response_text = generate_context_logic(
                question=request.question,
                keywords=list(request.keywords),
                language=request.language,
            )
            self.logger.info("[GenerateContext] Successful")
            return ai_service_pb2.GenerateContextResponse(content=response_text)
        except Exception as e:
            self.logger.exception("[GenerateContext] Failed\nQuestion: %s\nKeywords: %s\nLanguage: %s\nError: %s", request.question, request.keywords, request.language, str(e))
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
            self.logger.info("[DetectVariables] Successful")
            return ai_service_pb2.VariableDetectorResponse(variables=variables)
        except Exception as e:
            self.logger.exception("[DetectVariables] Failed\nQuestion: %s\nError: %s", request.question, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.VariableDetectorResponse()

    def SegmentQuestion(self, request, context):
        try:
            segmented = segment_question_logic(request.question)
            self.logger.info("[SegmentQuestion] Successful")
            return ai_service_pb2.QuestionSegmentationResponse(segmentedQuestion=segmented)
        except Exception as e:
            self.logger.exception("[SegmentQuestion] Failed\nQuestion: %s\nError: %s", request.question, str(e))
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
            self.logger.info("[GenerateMCQVariations] Successful")
            return ai_service_pb2.MCQVariation(variations=variations)
        except Exception as e:
            self.logger.exception("[GenerateMCQVariations] Failed\nQuestion: %s\nOptions: %s\nAnswerIndex: %d\nError: %s", request.question, request.options, request.answerIndex, str(e))
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
            self.logger.info("[GenerateMSQVariations] Successful")
            return ai_service_pb2.MSQVariation(variations=variations)
        except Exception as e:
            self.logger.exception("[GenerateMSQVariations] Failed\nQuestion: %s\nOptions: %s\nAnswerIndices: %s\nError: %s", request.question, request.options, request.answerIndices, str(e))
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
            self.logger.info("[FilterAndRandomize] Successful")
            return ai_service_pb2.FilterAndRandomizerResponse(variables=variables)
        except Exception as e:
            self.logger.exception("[FilterAndRandomize] Failed\nQuestion: %s\nUserPrompt: %s\nError: %s", request.question, request.userPrompt, str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.FilterAndRandomizerResponse()

    def Agent(self, request, context):
        self.logger.info(f"[Agent] Request: teacherId={request.teacherId}, role={request.role}, fileType={request.fileType}, file={bool(request.file)}, message={request.message}, createdAt={request.createdAt}, updatedAt={request.updatedAt}")
        try:
            # Run the async handler in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(primary_agent_handler(request))
                self.logger.info(f"[Agent] Response: {response}")
                return ai_service_pb2.AgentResponse(
                    message=response["message"],
                    teacherId=response["teacherId"],
                    agentName=response["agentName"],
                    agentResponse=response["agentResponse"],
                    sessionId=response["sessionId"],
                    createdAt=response["createdAt"],
                    updatedAt=response["updatedAt"],
                    responseTime=response["responseTime"],
                    role=response["role"],
                    feedback=response["feedback"]
                )
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.exception(f"[Agent] Failed\nError: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.AgentResponse()

    def RAGAgent(self, request, context):
        self.logger.info(f"[RAGAgent] Request: teacherId={request.teacherId}, role={request.role}, file={bool(request.file)}, message={request.message}, createdAt={request.createdAt}, updatedAt={request.updatedAt}")
        try:
            # Run the async handler in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                response = loop.run_until_complete(rag_agent_handler(request))
                self.logger.info(f"[RAGAgent] Response: {response}")
                return ai_service_pb2.RAGAgentResponse(
                    message=response["message"],
                    teacherId=response["teacherId"],
                    agentName=response["agentName"],
                    agentResponse=response["agentResponse"],
                    sessionId=response["sessionId"],
                    createdAt=response["createdAt"],
                    updatedAt=response["updatedAt"],
                    responseTime=response["responseTime"],
                    role=response["role"],
                    feedback=response["feedback"]
                )
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.exception(f"[RAGAgent] Failed\nError: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.RAGAgentResponse()

    # ─────────────────────────────────────────────────────────────────────────────
    # RAG Corpus Management Services
    # ─────────────────────────────────────────────────────────────────────────────

    def CreateCorpus(self, request, context):
        """Create a corpus by calling GIN backend HTTP API"""
        try:
            corpus_payload = {
                "corpusName": request.corpusName
            }
            
            response = requests.post(
                f"{GIN_BACKEND_URL}/ai/rag-agent/create-corpus",
                json=corpus_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return ai_service_pb2.CreateCorpusResponse(
                    status="success",
                    message=response_data.get("message", "Corpus created successfully"),
                    corpusName=response_data.get("corpusName", request.corpusName),
                    corpusId=response_data.get("corpusId", ""),
                    corpusCreated=response_data.get("corpusCreated", True)
                )
            elif response.status_code == 409:  # Already exists
                return ai_service_pb2.CreateCorpusResponse(
                    status="success",
                    message="Corpus already exists",
                    corpusName=request.corpusName,
                    corpusId="",
                    corpusCreated=False
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.CreateCorpusResponse(
                    status="error",
                    message=f"Failed to create corpus: {response.text}",
                    corpusName=request.corpusName,
                    corpusId="",
                    corpusCreated=False
                )
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling GIN backend for corpus creation: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Network error: {str(e)}")
            return ai_service_pb2.CreateCorpusResponse(
                status="error",
                message=f"Network error: {str(e)}",
                corpusName=request.corpusName,
                corpusId="",
                corpusCreated=False
            )
        except Exception as e:
            logger.error(f"Unexpected error in CreateCorpus: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Unexpected error: {str(e)}")
            return ai_service_pb2.CreateCorpusResponse(
                status="error",
                message=f"Unexpected error: {str(e)}",
                corpusName=request.corpusName,
                corpusId="",
                corpusCreated=False
            )

    def ListCorpusContent(self, request, context):
        """List corpus content by calling GIN backend HTTP API"""
        try:
            corpus_payload = {
                "corpusName": request.corpusName
            }
            
            response = requests.post(
                f"{GIN_BACKEND_URL}/ai/rag-agent/list-corpus-content",
                json=corpus_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Convert documents to protobuf format
                documents = []
                for doc in response_data.get("documents", []):
                    pb_doc = ai_service_pb2.CorpusDocument(
                        displayName=doc.get("displayName", ""),
                        documentId=doc.get("documentId", ""),
                        createTime=doc.get("createTime", ""),
                        updateTime=doc.get("updateTime", "")
                    )
                    documents.append(pb_doc)
                
                return ai_service_pb2.ListCorpusContentResponse(
                    status="success",
                    message=response_data.get("message", ""),
                    corpusName=response_data.get("corpusName", request.corpusName),
                    documents=documents,
                    documentCount=response_data.get("documentCount", len(documents))
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.ListCorpusContentResponse(
                    status="error",
                    message=f"Failed to list corpus content: {response.text}",
                    corpusName=request.corpusName,
                    documents=[],
                    documentCount=0
                )
                
        except Exception as e:
            logger.error(f"Error in ListCorpusContent: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.ListCorpusContentResponse(
                status="error",
                message=f"Error: {str(e)}",
                corpusName=request.corpusName,
                documents=[],
                documentCount=0
            )

    def DeleteCorpusDocument(self, request, context):
        """Delete corpus document by calling GIN backend HTTP API"""
        try:
            payload = {
                "corpusName": request.corpusName,
                "fileDisplayName": request.fileDisplayName
            }
            
            response = requests.post(
                f"{GIN_BACKEND_URL}/ai/rag-agent/delete-corpus-document",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return ai_service_pb2.DeleteCorpusDocumentResponse(
                    status="success",
                    message=response_data.get("message", "Document deleted successfully"),
                    corpusName=response_data.get("corpusName", request.corpusName),
                    fileDisplayName=response_data.get("fileDisplayName", request.fileDisplayName),
                    documentDeleted=response_data.get("documentDeleted", True)
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.DeleteCorpusDocumentResponse(
                    status="error",
                    message=f"Failed to delete document: {response.text}",
                    corpusName=request.corpusName,
                    fileDisplayName=request.fileDisplayName,
                    documentDeleted=False
                )
                
        except Exception as e:
            logger.error(f"Error in DeleteCorpusDocument: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.DeleteCorpusDocumentResponse(
                status="error",
                message=f"Error: {str(e)}",
                corpusName=request.corpusName,
                fileDisplayName=request.fileDisplayName,
                documentDeleted=False
            )

    def AddCorpusDocument(self, request, context):
        """Add document to corpus by calling GIN backend HTTP API"""
        try:
            payload = {
                "corpusName": request.corpusName,
                "fileLink": request.fileLink
            }
            
            response = requests.post(
                f"{GIN_BACKEND_URL}/ai/rag-agent/add-corpus-document",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for document upload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return ai_service_pb2.AddCorpusDocumentResponse(
                    status="success",
                    message=response_data.get("message", "Document added successfully"),
                    operationName=response_data.get("operationName", ""),
                    fileDisplayName=response_data.get("fileDisplayName", ""),
                    sourceUrl=response_data.get("sourceUrl", request.fileLink),
                    corpusName=response_data.get("corpusName", request.corpusName),
                    documentAdded=response_data.get("documentAdded", True)
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.AddCorpusDocumentResponse(
                    status="error",
                    message=f"Failed to add document: {response.text}",
                    operationName="",
                    fileDisplayName="",
                    sourceUrl=request.fileLink,
                    corpusName=request.corpusName,
                    documentAdded=False
                )
                
        except Exception as e:
            logger.error(f"Error in AddCorpusDocument: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.AddCorpusDocumentResponse(
                status="error",
                message=f"Error: {str(e)}",
                operationName="",
                fileDisplayName="",
                sourceUrl=request.fileLink,
                corpusName=request.corpusName,
                documentAdded=False
            )

    def ListAllCorpora(self, request, context):
        """List all corpora by calling GIN backend HTTP API"""
        try:
            response = requests.post(
                f"{GIN_BACKEND_URL}/ai/rag-agent/list-all-corpora",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Convert corpora to protobuf format
                corpora = []
                for corpus in response_data.get("corpora", []):
                    pb_corpus = ai_service_pb2.CorpusInfo(
                        corpusName=corpus.get("corpusName", ""),
                        corpusId=corpus.get("corpusId", ""),
                        displayName=corpus.get("displayName", ""),
                        createTime=corpus.get("createTime", ""),
                        updateTime=corpus.get("updateTime", "")
                    )
                    corpora.append(pb_corpus)
                
                return ai_service_pb2.ListAllCorporaResponse(
                    status="success",
                    message=response_data.get("message", ""),
                    corpora=corpora,
                    corporaCount=response_data.get("corporaCount", len(corpora))
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.ListAllCorporaResponse(
                    status="error",
                    message=f"Failed to list corpora: {response.text}",
                    corpora=[],
                    corporaCount=0
                )
                
        except Exception as e:
            logger.error(f"Error in ListAllCorpora: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.ListAllCorporaResponse(
                status="error",
                message=f"Error: {str(e)}",
                corpora=[],
                corporaCount=0
            )

    # ─────────────────────────────────────────────────────────────────────────────
    # Data Access Services
    # ─────────────────────────────────────────────────────────────────────────────

    def GetAssignment(self, request, context):
        """Get assignment by ID by calling GIN backend HTTP API"""
        try:
            response = requests.get(
                f"{GIN_BACKEND_URL}/assignments/{request.assignmentId}",
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success") and response_data.get("data"):
                    assignment = response_data["data"]
                    
                    # Convert to protobuf format
                    assignment_data = ai_service_pb2.AssignmentData(
                        id=assignment.get("id", ""),
                        title=assignment.get("title", ""),
                        description=assignment.get("description", ""),
                        teacherId=assignment.get("teacherId", ""),
                        classroomId=assignment.get("classroomId", ""),
                        dueDate=assignment.get("dueDate", ""),
                        points=int(assignment.get("points", 0)),
                        createdAt=assignment.get("createdAt", ""),
                        updatedAt=assignment.get("updatedAt", "")
                    )
                    
                    return ai_service_pb2.GetAssignmentResponse(
                        status="success",
                        message="Assignment found",
                        assignment=assignment_data
                    )
                else:
                    return ai_service_pb2.GetAssignmentResponse(
                        status="error",
                        message="Assignment not found in response",
                        assignment=ai_service_pb2.AssignmentData()
                    )
            elif response.status_code == 404:
                return ai_service_pb2.GetAssignmentResponse(
                    status="not_found",
                    message=f"Assignment with ID {request.assignmentId} not found",
                    assignment=ai_service_pb2.AssignmentData()
                )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.GetAssignmentResponse(
                    status="error",
                    message=f"Error fetching assignment: {response.text}",
                    assignment=ai_service_pb2.AssignmentData()
                )
                
        except Exception as e:
            logger.error(f"Error in GetAssignment: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.GetAssignmentResponse(
                status="error",
                message=f"Error: {str(e)}",
                assignment=ai_service_pb2.AssignmentData()
            )

    def GetAssignmentResults(self, request, context):
        """Get assignment results by student ID by calling GIN backend HTTP API"""
        try:
            response = requests.get(
                f"{GIN_BACKEND_URL}/api/assignment-results?studentId={request.studentId}",
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success") and response_data.get("data"):
                    results = response_data["data"]
                    
                    # Convert to protobuf format
                    assignment_results = []
                    for result in results:
                        result_data = ai_service_pb2.AssignmentResultData(
                            id=result.get("id", ""),
                            assignmentId=result.get("assignmentId", ""),
                            studentId=result.get("studentId", ""),
                            totalPointsAwarded=int(result.get("totalPointsAwarded", 0)),
                            totalMaxPoints=int(result.get("totalMaxPoints", 0)),
                            percentageScore=float(result.get("percentageScore", 0.0)),
                            createdAt=result.get("createdAt", ""),
                            updatedAt=result.get("updatedAt", "")
                        )
                        assignment_results.append(result_data)
                    
                    return ai_service_pb2.GetAssignmentResultsResponse(
                        status="success",
                        message="Assignment results found",
                        assignmentResults=assignment_results,
                        resultCount=len(assignment_results)
                    )
                else:
                    return ai_service_pb2.GetAssignmentResultsResponse(
                        status="success",
                        message="No assignment results found",
                        assignmentResults=[],
                        resultCount=0
                    )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.GetAssignmentResultsResponse(
                    status="error",
                    message=f"Error fetching assignment results: {response.text}",
                    assignmentResults=[],
                    resultCount=0
                )
                
        except Exception as e:
            logger.error(f"Error in GetAssignmentResults: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.GetAssignmentResultsResponse(
                status="error",
                message=f"Error: {str(e)}",
                assignmentResults=[],
                resultCount=0
            )

    def GetReportCard(self, request, context):
        """Get report cards by student ID by calling GIN backend HTTP API"""
        try:
            response = requests.get(
                f"{GIN_BACKEND_URL}/api/agent-report-cards/student/{request.studentId}",
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("agent_report_cards"):
                    report_cards_data = response_data["agent_report_cards"]
                    
                    # Convert to protobuf format
                    report_cards = []
                    for card in report_cards_data:
                        report_card = ai_service_pb2.ReportCardData(
                            id=card.get("id", ""),
                            studentId=card.get("studentId", ""),
                            studentName=card.get("studentName", ""),
                            subject=card.get("subject", ""),
                            gradeLetter=card.get("gradeLetter", ""),
                            score=float(card.get("score", 0.0)),
                            className=card.get("className", ""),
                            instructorName=card.get("instructorName", ""),
                            term=card.get("term", ""),
                            remarks=card.get("remarks", ""),
                            createdAt=card.get("createdAt", ""),
                            updatedAt=card.get("updatedAt", "")
                        )
                        report_cards.append(report_card)
                    
                    return ai_service_pb2.GetReportCardResponse(
                        status="success",
                        message="Report cards found",
                        reportCards=report_cards,
                        reportCardCount=len(report_cards)
                    )
                else:
                    return ai_service_pb2.GetReportCardResponse(
                        status="success",
                        message="No report cards found",
                        reportCards=[],
                        reportCardCount=0
                    )
            else:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"GIN backend error: {response.status_code} - {response.text}")
                return ai_service_pb2.GetReportCardResponse(
                    status="error",
                    message=f"Error fetching report cards: {response.text}",
                    reportCards=[],
                    reportCardCount=0
                )
                
        except Exception as e:
            logger.error(f"Error in GetReportCard: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error: {str(e)}")
            return ai_service_pb2.GetReportCardResponse(
                status="error",
                message=f"Error: {str(e)}",
                reportCards=[],
                reportCardCount=0
            )
