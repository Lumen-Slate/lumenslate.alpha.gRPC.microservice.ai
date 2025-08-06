"""
Corpus Management Services for AI microservice.
Handles RAG corpus operations like creation, listing, and document management.
"""

import os
import grpc
import requests
from app.protos import ai_service_pb2
from app.services.base_service import BaseService
from app.config.logging_config import logger

# GIN Backend configuration for corpus management
GIN_BACKEND_URL = os.getenv("GIN_BACKEND_URL")


class CorpusManagementService(BaseService):
    """Service for handling RAG corpus management operations"""

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
