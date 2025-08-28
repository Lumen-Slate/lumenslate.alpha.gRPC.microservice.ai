"""
Main AI Service that combines all individual service modules.
This provides a single entry point while maintaining modular structure.
"""

from app.protos import ai_service_pb2_grpc
from app.services.question_fine_control_services import QuestionFineControlServices
from app.services.agentic_services import AgenticServices
from app.services.corpus_management_services import CorpusManagementServices
from app.services.data_access_services import DataAccessServices


class GRPCAIMicroService(ai_service_pb2_grpc.AIServiceServicer):
    """
    Main AI Service that delegates to specialized service modules.
    This approach provides better organization and scalability.
    """

    def __init__(self, logger=None):
        # Initialize all service modules
        self.question_service = QuestionFineControlServices(logger)
        self.agent_service = AgenticServices(logger)
        self.corpus_service = CorpusManagementServices(logger)
        self.data_service = DataAccessServices(logger)

    # ─────────────────────────────────────────────────────────────────────────────
    # Question Generation Services
    # ─────────────────────────────────────────────────────────────────────────────

    def GenerateContext(self, request, context):
        """Generate contextual passage for a question"""
        return self.question_service.GenerateContext(request, context)

    def DetectVariables(self, request, context):
        """Detect variables in a question"""
        return self.question_service.DetectVariables(request, context)

    def SegmentQuestion(self, request, context):
        """Break a question into smaller parts"""
        return self.question_service.SegmentQuestion(request, context)

    def GenerateMCQVariations(self, request, context):
        """Create MCQ variations"""
        return self.question_service.GenerateMCQVariations(request, context)

    def GenerateMSQVariations(self, request, context):
        """Create MSQ variations"""
        return self.question_service.GenerateMSQVariations(request, context)

    def FilterAndRandomize(self, request, context):
        """Extract and randomize variable filters"""
        return self.question_service.FilterAndRandomize(request, context)

    # ─────────────────────────────────────────────────────────────────────────────
    # Agent Services
    # ─────────────────────────────────────────────────────────────────────────────

    def Agent(self, request, context):
        """Handle primary AI agent requests"""
        return self.agent_service.Agent(request, context)

    def RAGAgent(self, request, context):
        """Handle RAG (Retrieval-Augmented Generation) agent requests"""
        return self.agent_service.RAGAgent(request, context)

    # ─────────────────────────────────────────────────────────────────────────────
    # RAG Corpus Management Services
    # ─────────────────────────────────────────────────────────────────────────────

    def CreateCorpus(self, request, context):
        """Create a corpus by calling GIN backend HTTP API"""
        return self.corpus_service.CreateCorpus(request, context)

    def ListCorpusContent(self, request, context):
        """List corpus content by calling GIN backend HTTP API"""
        return self.corpus_service.ListCorpusContent(request, context)

    def DeleteCorpusDocument(self, request, context):
        """Delete corpus document by calling GIN backend HTTP API"""
        return self.corpus_service.DeleteCorpusDocument(request, context)

    def AddCorpusDocument(self, request, context):
        """Add document to corpus by calling GIN backend HTTP API"""
        return self.corpus_service.AddCorpusDocument(request, context)

    def ListAllCorpora(self, request, context):
        """List all corpora by calling GIN backend HTTP API"""
        return self.corpus_service.ListAllCorpora(request, context)

    # ─────────────────────────────────────────────────────────────────────────────
    # Data Access Services
    # ─────────────────────────────────────────────────────────────────────────────

    def GetAssignment(self, request, context):
        """Get assignment by ID by calling GIN backend HTTP API"""
        return self.data_service.GetAssignment(request, context)

    def GetAssignmentResults(self, request, context):
        """Get assignment results by student ID by calling GIN backend HTTP API"""
        return self.data_service.GetAssignmentResults(request, context)

    def GetReportCard(self, request, context):
        """Get report cards by student ID by calling GIN backend HTTP API"""
        return self.data_service.GetReportCard(request, context)
