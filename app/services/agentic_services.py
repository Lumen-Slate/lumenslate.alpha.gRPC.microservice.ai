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
            "message": request.message[:100] + "..." if len(request.message) > 100 else request.message,  # Truncate long messages
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
                    "message": response["message"][:100] + "..." if len(response["message"]) > 100 else response["message"],
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
