"""
Data Access Services for AI microservice.
Handles assignment data, assignment results, and report card operations.
"""

import os
import grpc
import requests
from app.protos import ai_service_pb2
from app.services.base_service import BaseService
from app.config.logging_config import logger

# GIN Backend configuration for data access
GIN_BACKEND_URL = os.getenv("GIN_BACKEND_URL", "https://lumenslate-backend-756147067348.asia-south1.run.app")


class DataAccessService(BaseService):
    """Service for handling data access operations"""

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
