// TypeScript types mirroring Python Pydantic schemas

export type SourceType = "reddit" | "review" | "competitor" | "job_post" | "web";
export type OnboardingModel = "self_serve" | "sales_led" | "unknown";
export type VerdictDecision = "KILL" | "NARROW" | "ADVANCE" | "INSUFFICIENT_EVIDENCE";
export type ClusterCategory = "core" | "context";
export type CompetitorRelationship = "direct" | "substitute" | "adjacent";
export type JobStatus =
  | "created"
  | "clarifying"
  | "researching"
  | "analyzing"
  | "reviewing"
  | "complete"
  | "failed";

export interface Citation {
  url: string;
  excerpt: string;
  source_type: SourceType;
  date_published: string | null;
  date_retrieved: string;
  recency_months: number | null;
  snapshot_hash: string;
}

export interface EvidencedClaim {
  text: string;
  citation_indices: number[];
  evidence_excerpts?: string[];
}

export interface ScoredDimension {
  score: number;
  justification: EvidencedClaim;
}

export interface ClusterScores {
  frequency: ScoredDimension;
  severity: ScoredDimension;
  urgency: ScoredDimension;
  payability: ScoredDimension;
  workaround_cost: ScoredDimension;
  saturation: ScoredDimension;
  accessibility: ScoredDimension;
}

export interface PainCluster {
  id: string;
  statement: EvidencedClaim;
  who: string;
  trigger: string;
  workarounds: string[];
  citation_indices: number[];
  scores: ClusterScores;
  confidence: number;
  recency_weight: number;
  category?: ClusterCategory;
}

export interface Competitor {
  name: string;
  url: string;
  pricing_page_exists: boolean;
  min_price_observed: string | null;
  target_icp: EvidencedClaim | null;
  onboarding_model: OnboardingModel;
  positioning: string;
  relationship?: CompetitorRelationship;
  strengths: EvidencedClaim[];
  weaknesses: EvidencedClaim[];
  citation_indices: number[];
}

export interface ConflictReport {
  description: string;
  side_a: EvidencedClaim;
  side_b: EvidencedClaim;
  relevance: "strong" | "weak";
}

export interface EvidenceQualityMetrics {
  cluster_confidences: number[];
  median_confidence: number;
  high_confidence_count: number;
  total_clusters: number;
  total_citations: number;
  unique_domains: number;
  unique_source_types: number;
  topic_relevance_ratio: number | null;
  gate_triggered: string | null;
}

export interface Verdict {
  decision: VerdictDecision;
  reasons: EvidencedClaim[];
  risks: EvidencedClaim[];
  narrowest_wedge: string;
  what_would_change: string;
  conflicts: ConflictReport[];
  evidence_quality_notes: string[];
}

export interface ValidationPlan {
  verdict_context: VerdictDecision;
  objective: string;
  channels: string[];
  outreach_targets: string[];
  interview_script: string;
  landing_page_hypotheses: string[];
  concierge_procedure: string;
  success_threshold: string;
  reversal_criteria: string | null;
}

export interface PayabilityAssessment {
  hiring_signals: EvidencedClaim[];
  outsourcing_signals: EvidencedClaim[];
  template_sop_signals: EvidencedClaim[];
  overall_strength: "strong" | "moderate" | "weak" | "none";
  summary: string;
}

export interface IdeaBrief {
  raw_idea: string;
  one_liner: string;
  buyer_persona: string;
  workflow_replaced: string;
  moment_of_pain: string;
  keywords: string[];
}

export interface ClarificationQuestion {
  question: string;
  options: string[] | null;
}

export interface JobProgress {
  stage: string;
  source_packs_total: number;
  source_packs_done: number;
  citations_found: number;
  current_action: string;
}

export interface ResearchReport {
  id: string;
  idea_brief: IdeaBrief;
  pain_map: PainCluster[];
  payability: PayabilityAssessment;
  competitors: Competitor[];
  verdict: Verdict;
  validation_plan: ValidationPlan;
  evidence_pack: Citation[];
  skeptic_flags: string[];
  conflicts: ConflictReport[];
  evidence_quality: EvidenceQualityMetrics;
}

// API types
export interface RunRequest {
  idea: string;
  niche?: string;
  geography?: string;
  buyer_role?: string;
  competitor_names?: string[];
  constraints?: string;
}

export interface RunResponse {
  job_id: string;
}

export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  progress: JobProgress | null;
  clarification_questions: ClarificationQuestion[] | null;
}

export interface ReportResponse {
  job_id: string;
  status: string;
  report: ResearchReport | null;
  error: string | null;
}
