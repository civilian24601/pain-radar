# Pain Radar (Serious Idea Validation Tool)
Version: 0.1 (Product Direction)

## 0. Purpose
Pain Radar is a decision-grade research and validation system for business ideas. It exists to replace "LLM vibes" with:
- verifiable evidence
- explicit uncertainty
- falsifiable conclusions
- concrete next actions

This is not an idea generator. It is not an optimism machine. It is not a marketing funnel disguised as a score.

## 1. Non-Negotiable Principles (what makes it serious)
### 1.1 Evidence or Silence
- Every non-trivial claim MUST be backed by a citation (URL + excerpt + date).
- If evidence is insufficient, the tool MUST say "Insufficient evidence" and stop short of conclusions.
- No invented numbers (CPC, search volume, conversion rates, market sizes) unless sourced.

### 1.2 Claims Ledger, Not Opinions
All output is composed of "claims" with:
- claim text
- evidence links (one or more)
- confidence level
- scope (who/where/when)
- known unknowns

### 1.3 Adversarial Stance Against the User's Idea
The tool acts like a skeptical analyst whose job is to *disprove* the idea quickly.
- It actively searches for disconfirming evidence.
- It identifies failure modes and reasons the idea will not sell.
- It does not soothe or encourage unless earned by evidence.

### 1.4 Validation Means Contact With Reality
The tool must end with a plan that produces signal within 7 days, not a generic roadmap.
Validation is defined as:
- money changing hands (preorder/deposit)
- signed LOI / design partner agreement
- booked calls with qualified buyers
- measurable demand (waitlist with price + conversion)
NOT:
- simulated interviews
- imagined personas
- "82/100 dreamer"
- AI-generated applause

### 1.5 No Theater Metrics
Forbidden unless cited:
- "estimated signups per 100 visitors"
- "likely CAC"
- "monthly search volume"
- "time to traction"
If the user requests these, the tool must either cite sources or refuse.

## 2. What the Tool Is
### 2.1 One Sentence
A research engine that converts an idea into an evidence-backed pain map, competitor reality check, buyer/payability assessment, and a 7-day falsifiable validation plan.

### 2.2 Core Deliverables
For every run, produce:
1) **Idea Brief (structured)**
2) **Pain Map (ranked clusters + evidence)**
3) **Payability Assessment (signals of spend/hiring/outsource)**
4) **Competitor/Saturation Snapshot (real products, real pricing pages, real positioning)**
5) **Verdict: KILL / NARROW / ADVANCE** (with reasons and evidence)
6) **7-Day Validation Plan** (specific actions + scripts + target lists)
7) **Evidence Pack** (CSV/JSON of all citations/snippets)

## 3. What the Tool Is Not (explicit anti-features)
### 3.1 Not an Upsell Funnel
- No "share your score" mechanics.
- No social virality prompts.
- No "build a landing page with our partner" CTA.
- No forced integration to a builder product.

### 3.2 Not a Generator
- No list of 50 startup ideas.
- No "blue ocean" fantasies.
- No rebranding common ideas as novel.

### 3.3 Not a Roleplay Simulator
- No simulated customer interviews.
- No pretend objections.
- No invented quotes.

### 3.4 Not a Grade/Score Toy
- No "Startup readiness score."
- No gamified archetypes.
If a single numeric score exists, it must be a transparent composite of evidenced sub-scores and include confidence intervals / caveats.

## 4. Inputs and Clarification Contract
### 4.1 Input Types
- Raw idea text (required)
- Optional: niche, geography, buyer role
- Optional: competitor names
- Optional: constraints (budget, timeline, ethics, tech stack)

### 4.2 Clarification Questions (minimal but surgical)
Ask only for information needed to avoid nonsense research. Examples:
- Who pays (job title / persona)?
- What workflow step is painful?
- What does "success" replace today (spreadsheet, VA, tool)?
- What is the "moment of pain" (deadline, loss, compliance)?
- What is excluded (no gov, no consumer, etc.)?

The tool should prefer multiple-choice / quick picks where possible.

## 5. Research Sources (source packs)
Pain Radar operates via source packs. Each pack yields citations and snippets.

### 5.1 Source Pack: Public Complaint Channels (Pain Discovery)
- Reddit
- niche forums
- Hacker News (when relevant)
- community posts

Goal: find recurring pain, language intensity, workarounds, willingness to pay.

### 5.2 Source Pack: Reviews & Support Complaints (Failure Modes)
- G2/Capterra (B2B)
- Chrome Web Store / App Store / Play reviews (B2C tools)
- GitHub issues for dev tools

Goal: identify where existing tools fail, what users complain about, what they request.

### 5.3 Source Pack: Competitor Reality Check
- competitor websites
- pricing pages
- docs and onboarding flows
- "alternatives" pages

Goal: saturation, differentiation, distribution angle, pricing anchors.

### 5.4 Source Pack: Hiring & Outsourcing Signals (Payability)
- job posts referencing the task
- agencies/services offering the task
- templates and SOPs

Goal: if companies pay humans to do it, payability is real.

### 5.5 Source Pack: Regulation/Compliance Context (if applicable)
- government docs
- standards pages
- legal/regulatory guidance

Goal: capture constraints; avoid handwaving "compliance."

## 6. Clustering + Scoring (transparent rubric)
### 6.1 Pain Clusters
Group evidence into 5–20 clusters. Each cluster includes:
- one-sentence pain statement
- who experiences it
- what triggers it
- current workaround(s)
- representative citations

### 6.2 Scoring Dimensions (0–5)
Each cluster receives sub-scores, each justified by citations:
- Frequency (how often across sources)
- Severity (language intensity, "this is killing us")
- Urgency (deadlines, immediate blockers)
- Payability (explicit spend/hiring/outsource signals)
- Workaround Cost (time/money complexity)
- Saturation (number of tools clearly targeting it; inverse)
- Accessibility (reachable channels exist)

### 6.3 Confidence
Every cluster has a confidence rating derived from:
- evidence volume
- cross-source corroboration
- recency

## 7. Verdict Logic (falsifiable)
The tool must output one verdict:
- **KILL**: weak evidence or weak payability or saturated with no wedge
- **NARROW**: pain exists but ICP/wedge must tighten
- **ADVANCE**: pain + payability + wedge are evidenced

Each verdict includes:
- top 3 evidence-backed reasons
- top 3 risks
- the narrowest viable wedge
- what would change the verdict (new evidence needed)

## 8. 7-Day Validation Plan (required output)
This is the practical heart. It must include:
- a shortlist of channels/threads/communities to engage
- 20 outreach targets (or a method to generate them)
- interview script (non-leading)
- 2 landing page hypotheses with pricing shown
- a concierge MVP procedure (manual fulfillment in 1 day)
- a measurable success threshold (e.g., 3 deposits at $X)

## 9. Output Format Requirements
### 9.1 Report Structure
- Executive Summary (verdict + top reasons)
- Pain Map (ranked)
- Competitor Table
- Payability Signals
- Recommended Wedge
- 7-Day Plan
- Evidence Appendix (citations)

### 9.2 Evidence Appendix
- every citation must include:
  - URL
  - excerpt
  - date published (if available)
  - retrieved timestamp

## 10. Red Team / Skeptic Mode (mandatory)
Before final output, run an internal skeptic pass that checks:
- any uncited claim -> remove or add citation
- any invented numeric -> remove
- any overconfident language -> downgrade confidence
- any contradictory evidence -> highlight as conflict

## 11. Tone and User Handling
- Blunt, analytical, non-salesy.
- No motivational fluff.
- Encouragement only when evidence supports it (e.g., "payability signals strong because hiring posts exist").

## 12. Product Success Criteria (what "good" looks like)
A run is successful if:
- It produces a verdict that the user can act on immediately.
- It provides at least 20 citations when evidence exists (or clearly explains why not).
- It produces a 7-day plan that can generate real market signal.
- It is auditable: user can click sources and verify.

## 13. MVP Scope (for first build)
MVP must support:
- Reddit + competitor web + reviews (where accessible)
- pain clustering
- scoring + confidence
- citations + evidence pack export
- 7-day validation plan

Defer:
- full "entire web crawl"
- complex integrations
- paid data sources
- fully automated outreach
