// TypeScript interfaces mirroring api/schemas.py

export interface UserInfo {
  username: string;
  name: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface SEHRASummary {
  id: string;
  country: string;
  district: string;
  province: string;
  assessment_date: string | null;
  upload_date: string | null;
  status: string;
  pdf_filename: string;
}

export interface SEHRADetail extends SEHRASummary {
  executive_summary: string;
  recommendations: string;
}

export interface QualitativeEntry {
  id: string;
  remark_text: string;
  item_id: string;
  theme: string;
  classification: string;
  confidence: number;
  edited_by_human: boolean;
}

export interface ReportSection {
  id: string;
  content: string;
  edited_by_human: boolean;
}

export interface ComponentAnalysis {
  id: string;
  component: string;
  enabler_count: number;
  barrier_count: number;
  items: Record<string, unknown>[];
  qualitative_entries: QualitativeEntry[];
  report_sections: Record<string, ReportSection>;
}

export interface ChatResponse {
  text: string;
  chart_spec: ChartSpec | null;
}

export interface ChartSpec {
  type: "bar" | "pie" | "radar";
  title: string;
  data: { label: string; value: number; group?: string }[];
}

export interface ShareLink {
  id: string;
  share_token: string;
  created_by: string;
  created_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  view_count: number;
}

export interface PublicShareResponse {
  valid: boolean;
  expired: boolean;
  needs_passcode: boolean;
}

export interface VerifyPasscodeResponse {
  success: boolean;
  html: string | null;
}

export interface CodebookItem {
  id: string;
  section: string;
  question: string;
  type: string;
  has_scoring: boolean;
  is_reverse: boolean;
  score_yes: number | null;
  score_no: number | null;
}

export interface FormDraft {
  id: string;
  user: string;
  section_progress: number;
  responses: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

export interface AnalysisProgressEvent {
  event: "progress";
  step: number;
  total_steps: number;
  label: string;
  progress: number;
}

export interface AnalysisCompleteEvent {
  event: "complete";
  sehra_id: string;
  enabler_count: number;
  barrier_count: number;
}

export interface AnalysisErrorEvent {
  event: "error";
  message: string;
}

export type AnalysisEvent =
  | AnalysisProgressEvent
  | AnalysisCompleteEvent
  | AnalysisErrorEvent;

export interface BatchApproveResponse {
  approved_count: number;
}

export interface ExecutiveSummary {
  executive_summary: string;
  recommendations: string;
}

// --- Copilot Types ---

export interface CopilotAction {
  label: string;
  description: string;
  api_call: {
    method: string;
    path: string;
    body?: Record<string, unknown>;
    download?: boolean;
  };
}

export interface CopilotToolCall {
  tool: string;
  arguments: Record<string, unknown>;
  result_preview?: string;
  status: "running" | "done" | "error";
}

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  chart?: ChartSpec | null;
  actions?: CopilotAction[];
  tool_calls?: CopilotToolCall[];
  status?: "streaming" | "done" | "error";
  edited?: boolean;
  editedContent?: string;
  feedback?: "up" | "down" | null;
}

export type CopilotSSEEventType =
  | "thinking"
  | "tool_call"
  | "tool_result"
  | "message"
  | "chart"
  | "actions"
  | "error"
  | "done";

export interface CopilotSSEEvent {
  type: CopilotSSEEventType;
  text?: string;
  tool?: string;
  arguments?: Record<string, unknown>;
  preview?: string;
  spec?: ChartSpec;
  actions?: CopilotAction[];
}

export interface StoredConversation {
  id: string;
  title: string;
  sehraId: string | null;
  sehraLabel: string | null;
  messages: CopilotMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  sehra_id: string | null;
  sehra_label: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface CorrectionEntry {
  id: string;
  original_text: string;
  corrected_text: string;
  context: string;
  created_at: string;
}
