"""
MEMBER 1 ADAPTER — API GATEWAY & ORCHESTRATION
Defines the communication interface between Member 1's API Gateway
and the downstream Member 2 AI Analysis module.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class GatewayAnalysisRequest(BaseModel):
    client_id: str = Field(default="gateway-default", description="Client identifier from gateway")
    content: str = Field(..., description="Raw untrusted message or email payload")
    source_type: str = Field(default="unknown", description="Source channel (sms, email, etc.)")
    enable_gemini: bool = Field(default=True)
    enable_virustotal: bool = Field(default=True)
    redact_pii: bool = Field(default=True)

class Member1GatewayAdapter:
    """
    Adapter ensuring incoming requests from Member 1 Gateway
    are validated and routed to Member 2 Scam Engine without schema mismatches.
    """
    def __init__(self):
        self.is_connected = False
        self.gateway_url: Optional[str] = None

    def validate_request_payload(self, raw_data: Dict[str, Any]) -> GatewayAnalysisRequest:
        return GatewayAnalysisRequest(**raw_data)

    def route_to_ai_engine(self, validated_request: GatewayAnalysisRequest) -> Dict[str, Any]:
        """Routes validated payload to Member 2 AI engine."""
        from backend.app.engine.facade import ScamAnalysisFacade
        facade = ScamAnalysisFacade()
        return facade.analyze_message(
            content=validated_request.content,
            source_type=validated_request.source_type,
            enable_gemini=validated_request.enable_gemini,
            enable_virustotal=validated_request.enable_virustotal,
            redact_pii=validated_request.redact_pii
        )
