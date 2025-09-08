"""
Agent Services for AI microservice.
Handles primary agent and RAG agent interactions.
"""

import grpc
import asyncio
from app.protos import ai_service_pb2
from app.utils.base_service import BaseService
from app.api.lumen_agent_handler import lumen_agent_handler
from app.api.rag_agent_handler import rag_agent_handler
from app.agents.independent_agents.assignment_generator_general.agent import assignment_generator_general


class AgenticServices(BaseService):
    """Service for handling AI agent interactions"""

    def LumenAgent(self, request, context):
        """Handle primary AI agent requests"""
        # Safely log request without exposing sensitive data
        safe_request_data = {
            "teacherId": request.teacherId,
            "role": request.role,
            "fileType": request.fileType,
            "file": bool(request.file),
            "message": request.message,
            "createdAt": request.createdAt,
            "updatedAt": request.updatedAt
        }
        self._safe_log_request("Agent", safe_request_data)

        try:
            # Run the async handler in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(lumen_agent_handler(request))

                # Safely log response without exposing sensitive data
                safe_response_data = {
                    "message": response["message"],
                    "teacherId": response["teacherId"],
                    "agentName": response["agentName"],
                    "sessionId": response["sessionId"],
                    "responseTime": response["responseTime"],
                    "role": response["role"]
                }
                self._safe_log_response("Agent", safe_response_data)

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
        """Handle RAG (Retrieval-Augmented Generation) agent requests"""
        # Safely log request without exposing sensitive data
        safe_request_data = {
            "corpusName": request.corpusName,
            "role": request.role,
            "message": request.message[:100] + "..." if len(request.message) > 100 else request.message,  # Truncate long messages
            "createdAt": request.createdAt,
            "updatedAt": request.updatedAt
        }
        self._safe_log_request("RAGAgent", safe_request_data)

        try:
            # Run the async handler in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(rag_agent_handler(request))

                # Safely log response without exposing sensitive data
                safe_response_data = {
                    "message": response["message"][:100] + "..." if len(response["message"]) > 100 else response["message"],
                    "corpusName": response["corpusName"],
                    "agentName": response["agentName"],
                    "sessionId": response["sessionId"],
                    "responseTime": response["responseTime"],
                    "role": response["role"]
                }
                self._safe_log_response("RAGAgent", safe_response_data)

                return ai_service_pb2.RAGAgentResponse(
                    message=response["message"],
                    corpusName=response["corpusName"],
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

    def AssignmentGeneratorAgent(self, request, context):
        """Handle assignment generator agent requests"""
        safe_request_data = {
            "teacherId": getattr(request, "teacherId", None),
            "role": getattr(request, "role", None),
            "message": getattr(request, "message", "")[:100] + "..." if len(getattr(request, "message", "")) > 100 else getattr(request, "message", ""),
            "createdAt": getattr(request, "createdAt", None),
            "updatedAt": getattr(request, "updatedAt", None)
        }
        self._safe_log_request("AssignmentGeneratorAgent", safe_request_data)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(assignment_generator_general.run(request))

                safe_response_data = {
                    "message": response.get("message", "")[:100] + "..." if len(response.get("message", "")) > 100 else response.get("message", ""),
                    "teacherId": response.get("teacherId"),
                    "agentName": response.get("agentName"),
                    "sessionId": response.get("sessionId"),
                    "responseTime": response.get("responseTime"),
                    "role": response.get("role")
                }
                self._safe_log_response("AssignmentGeneratorAgent", safe_response_data)

                return ai_service_pb2.AgentResponse(
                    message=response.get("message", ""),
                    teacherId=response.get("teacherId", ""),
                    agentName=response.get("agentName", ""),
                    agentResponse=response.get("agentResponse", ""),
                    sessionId=response.get("sessionId", ""),
                    createdAt=response.get("createdAt", ""),
                    updatedAt=response.get("updatedAt", ""),
                    responseTime=response.get("responseTime", ""),
                    role=response.get("role", ""),
                    feedback=response.get("feedback", "")
                )
            finally:
                loop.close()
        except Exception as e:
            self.logger.exception(f"[AssignmentGeneratorAgent] Failed\nError: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ai_service_pb2.AgentResponse()
