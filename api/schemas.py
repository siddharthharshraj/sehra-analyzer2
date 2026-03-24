"""Pydantic models (schemas) for request/response validation."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---- Auth ----

class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    username: str
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


# ---- SEHRA ----

class SEHRASummary(BaseModel):
    id: str
    country: str
    district: str = ""
    province: str = ""
    assessment_date: Optional[str] = None
    upload_date: Optional[str] = None
    status: str = "draft"
    pdf_filename: str = ""


class SEHRADetail(SEHRASummary):
    executive_summary: str = ""
    recommendations: str = ""


# ---- Component Analysis ----

class QualitativeEntrySchema(BaseModel):
    id: str
    remark_text: str = ""
    item_id: str = ""
    theme: str = ""
    classification: str = ""
    confidence: float = 0.0
    edited_by_human: bool = False


class ReportSectionSchema(BaseModel):
    id: str
    content: str = ""
    edited_by_human: bool = False


class ComponentAnalysisSchema(BaseModel):
    id: str
    component: str
    enabler_count: int = 0
    barrier_count: int = 0
    items: list[dict] = Field(default_factory=list)
    qualitative_entries: list[QualitativeEntrySchema] = Field(default_factory=list)
    report_sections: dict[str, ReportSectionSchema] = Field(default_factory=dict)


# ---- Update Requests ----

class UpdateEntryRequest(BaseModel):
    theme: Optional[str] = None
    classification: Optional[str] = None


class UpdateSectionRequest(BaseModel):
    content: str


class UpdateSehraRequest(BaseModel):
    """Partial update for SEHRA fields (inline editing)."""
    executive_summary: Optional[str] = None
    recommendations: Optional[str] = None
    status: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str


class BatchApproveRequest(BaseModel):
    confidence_threshold: float = Field(ge=0.0, le=1.0)


class BatchApproveResponse(BaseModel):
    approved_count: int


# ---- Chat ----

class ChatRequest(BaseModel):
    question: str
    sehra_id: str


class ChatResponse(BaseModel):
    text: str
    chart_spec: Optional[dict] = None


# ---- Share ----

class ShareCreateRequest(BaseModel):
    sehra_id: str
    passcode: str
    expires_days: Optional[int] = None


class ShareLinkSchema(BaseModel):
    id: str
    share_token: str
    created_by: str = ""
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_active: bool = True
    view_count: int = 0


class PublicShareResponse(BaseModel):
    valid: bool
    expired: bool = False
    needs_passcode: bool = True


class VerifyPasscodeRequest(BaseModel):
    passcode: str


class VerifyPasscodeResponse(BaseModel):
    success: bool
    html: Optional[str] = None


# ---- Codebook ----

class CodebookItemSchema(BaseModel):
    id: str
    section: str
    question: str
    type: str = ""
    has_scoring: bool = False
    is_reverse: bool = False
    score_yes: Optional[int] = None
    score_no: Optional[int] = None


class AddCodebookItemRequest(BaseModel):
    section: str
    question: str
    type: str = "yes_no"
    has_scoring: bool = True
    is_reverse: bool = False
    item_id: Optional[str] = None


class UpdateCodebookItemRequest(BaseModel):
    question: Optional[str] = None
    type: Optional[str] = None
    has_scoring: Optional[bool] = None
    is_reverse: Optional[bool] = None


# ---- Form Drafts ----

class FormDraftSchema(BaseModel):
    id: str
    user: str
    section_progress: int = 0
    responses: dict = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SaveDraftRequest(BaseModel):
    section_progress: int = 0
    responses: dict = Field(default_factory=dict)


# ---- Analysis SSE Events ----

class AnalysisProgressEvent(BaseModel):
    step: int
    total_steps: int
    label: str
    progress: float = 0.0


class AnalysisCompleteEvent(BaseModel):
    sehra_id: str
    enabler_count: int = 0
    barrier_count: int = 0


# ---- Export ----

class ExportFormat(str, enum.Enum):
    docx = "docx"
    xlsx = "xlsx"
    pdf = "pdf"
    html = "html"

# ---- Conversations ----

class SaveConversationRequest(BaseModel):
    id: str
    title: str = "New conversation"
    messages: list = Field(default_factory=list)
    sehra_id: Optional[str] = None
    sehra_label: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    title: str = ""
    sehra_id: Optional[str] = None
    sehra_label: Optional[str] = None
    message_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConversationDetail(BaseModel):
    id: str
    title: str = ""
    sehra_id: Optional[str] = None
    sehra_label: Optional[str] = None
    messages: list = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ---- AI Feedback / Corrections ----

class FeedbackRequest(BaseModel):
    message_id: str
    conversation_id: Optional[str] = None
    rating: str  # "up" or "down"
    comment: str = ""


class CorrectionRequest(BaseModel):
    original_text: str
    corrected_text: str
    context: str = ""
    sehra_id: Optional[str] = None
    message_id: Optional[str] = None


class CorrectionSchema(BaseModel):
    id: str
    user: str
    sehra_id: Optional[str] = None
    original_text: str
    corrected_text: str
    context: str = ""
    message_id: Optional[str] = None
    created_at: Optional[str] = None
