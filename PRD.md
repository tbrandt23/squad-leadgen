# Squad Lead Gen Agent — PRD v1

---

## 1. Product Overview

An AI SDR agent that researches, qualifies, and writes personalized outreach to DTC brands running active UGC creator programs. Built as the outbound engine for Squad, a CRM for brands managing creator partnerships.

The agent runs as a Streamlit web app. Single operator adds a brand name (or pulls from a seeded list), and in ~20 seconds the agent returns a structured signal-based qualification score, the winning outreach hook with evidence, and a ready-to-send cold email.

## 2. Problem Statement

Finding and qualifying DTC brands that are actively feeling the pain Squad solves (creator sales attribution chaos, contract and IP management sprawl) is slow and manual. SDRs spend 20-40 minutes per lead doing LinkedIn, Instagram, and Google rabbit-holing to find out if a brand is even a fit. That workflow doesn't scale and it prices out early-stage startups like Squad from building an outbound motion at all.

The agent compresses that 30-minute human research loop into 20 seconds, returns a structured signal scorecard instead of a vague gut read, and writes outreach that actually references real evidence from the research.

## 3. Users

**Primary user:** Tebone and the Squad founding team. Uses the agent daily to generate qualified leads for outreach.

**Not the user:** Squad's actual customers. This tool is internal GTM infrastructure, not a feature of the Squad product.

## 4. Success Criteria

The agent is working if a fresh brand input produces a populated row in the leads table within 30 seconds, the scorecard reflects the five signals defined below, the email reads like a human founder wrote it, and the whole thing runs end-to-end without manual intervention. For the pitch, success means live-demoing one lead generation in front of the class without the app breaking.

---

## 5. Build Directives (follow during implementation)

Claude, when building this project:

- Source of truth for scope is this PRD. Do not expand scope or add features not specified here.
- Work in logical order: scaffold first, then modules bottom-up (research → qualifier → email → orchestrator → storage → UI).
- After creating a module, verify it by adding an `if __name__ == "__main__":` test block at the bottom that runs on a sample input.
- Do NOT execute any code that requires live API keys until the user confirms `.env` is set up. Scaffold `.env.example` instead.
- Commit after each completed module with conventional commit messages (`feat: add research module`, `fix: handle perplexity timeout`).
- Never commit `.env` or real API keys. Add `.env` to `.gitignore`.
- Code style: Python 3.11+, explicit over clever, type hints on public functions, docstrings on every module, one file per module under 200 lines.
- If you hit genuine ambiguity in the PRD, ask. If it's not ambiguous, don't ask, just build.

---

## 6. Architecture

```
User inputs brand name (via Streamlit sidebar OR batch CSV)
  │
  ▼
Research module (Perplexity API)
  → Returns structured research dump: creator footprint, campaigns, signals
  │
  ▼
Qualification module (Claude API)
  → Scores 5 signals 0-3 each, returns JSON scorecard with evidence
  → Picks winning hook (attribution OR contracts)
  │
  ▼
Email module (Claude API)
  → Writes cold email using hook + evidence
  │
  ▼
Storage: append row to leads.csv
  │
  ▼
UI: display in Streamlit table with expandable detail view
```

All three API-touching modules are stateless functions. Orchestration is a simple sequential chain. No queues, no async, no DB. Ship ugly, ship fast.

---

## 7. Feature Specifications

### 7.1 Research module (`src/research.py`)

Takes a brand name string. Calls Perplexity's sonar-pro model (or equivalent) with the research prompt from section 9.1. Returns a structured text dump covering six research areas. Handles Perplexity timeouts with a 45-second cap and one retry.

### 7.2 Qualification module (`src/qualifier.py`)

Takes the research dump. Calls Claude with the scoring rubric from section 9.2. Returns JSON with five signal scores (0-3 each), total score normalized to 1-10, winning hook (`attribution` or `contracts`), specific evidence string, and one-line fit summary.

**The full signal scorecard:**

| Signal | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Creator volume** | No visible creator partnerships | 1-5 creators in last 90d | 6-20 creators | 20+ creators |
| **Attribution pain** | No creator program, or clean per-creator codes | Generic codes, one creator at a time | Multiple creators, non-unique tracking | Heavy multi-creator campaigns with obvious attribution chaos |
| **Contract/IP pain** | No content reuse | Occasional creator repost | Consistent UGC repurposing in marketing | Creator UGC in paid ads, product pages, heavy rights complexity |
| **Buyer fit** | <$1M or >$200M revenue | Edge of range | Solid fit ($5M-$50M) | Bullseye ($10M-$30M, Series A/B) |
| **Intent/urgency** | No active signals | Steady creator program | Recent hire or ops growth | Active creator job listing, recent funding, public pain signals |

Total out of 15, normalized: `score = round((total / 15) * 10)`.

**Hook selection logic:** whichever of "attribution pain" or "contract/IP pain" scored higher. Tie-breaker: attribution wins (broader problem, easier cold email hook).

### 7.3 Email module (`src/email_writer.py`)

Takes brand name, hook pain, and hook evidence. Calls Claude with the email prompt from section 9.3. Returns subject + body under 80 words. Enforces no em dashes, no semicolons, no fluff words (streamline, leverage, solution, unlock, revolutionize). If the output violates rules, retry once with explicit correction.

### 7.4 Orchestrator (`src/lead_agent.py`)

Single function `process_lead(brand_name: str) -> dict` that chains research → qualifier → email and returns a dict matching the data model in section 8. Handles errors gracefully (if any stage fails, log and return partial data).

### 7.5 Storage (`src/storage.py`)

Reads and appends to `data/leads.csv`. Uses Python's csv module (proper escaping for multi-line fields). Functions: `append_lead(lead_dict)`, `load_leads() -> list[dict]`, `init_csv_if_missing()`.

### 7.6 Batch runner (`scripts/batch_run.py`)

Reads `data/seed_brands.csv`, calls `process_lead` for each brand, appends results to `leads.csv`. Prints progress. Handles rate limits with a 2-second sleep between calls.

### 7.7 Streamlit UI (`app.py`)

**Sidebar:**
- Text input: "Add a brand"
- Button: "Run agent"
- Button: "Download leads.csv"

**Main area:**
- Leads table with columns: brand, score (color-coded: green 8+, yellow 5-7, red below 5), hook, summary
- Click row to expand: full research dump, full scorecard breakdown, full email

No auth. No multi-page. One file.

### 7.8 V2 (roadmap only, do not build)

Document these in the README as "coming soon":
- Creator-first discovery: scrape TikTok/IG hashtags (#paidpartnership, #gifted) via Apify, extract tagged brands, auto-qualify them
- Intent monitoring: daily scrape of LinkedIn Jobs for creator manager roles at DTC brands
- Lookalike expansion: feed best-fit leads into Apollo similar-companies API
- Direct push to Instantly or Smartlead for send

---

## 8. Data Model

Single CSV file `data/leads.csv` with these columns:

```
brand_name, date_added, score, creator_volume, attribution_pain,
contract_pain, buyer_fit, intent_urgency, hook_pain, hook_evidence,
summary, research_dump, email_subject, email_body
```

Research dump and email body may contain newlines. Use proper CSV escaping via Python's csv module.

---

## 9. The Three Core Prompts

Use these VERBATIM. They are tuned.

### 9.1 Perplexity research prompt

```
Research {brand_name}, a DTC brand that works with UGC content creators.

Find and report on these six areas. Be specific. Cite sources.
Skip filler and intros.

1. UGC platforms: which of TikTok, Instagram Reels, YouTube Shorts they
   actively post creator-made content on.

2. Creator volume estimate: roughly how many creators have partnered
   with them in the last 90 days. Give a range (1-5, 6-20, 20+) with
   reasoning.

3. Attribution signals: do they appear to use unique discount codes per
   creator, generic site-wide codes, or no codes at all? Are multiple
   creators running simultaneous campaigns?

4. Contract and IP signals: do they repost creator content to their own
   feed? Does creator UGC appear in their paid ads or on their product
   pages? Any evidence of content rights complexity?

5. Buyer fit signals: estimated company size (employees, revenue tier,
   funding stage if known).

6. Urgency signals: any active job listings for creator ops, influencer
   management, or partnerships roles. Recent funding rounds. Public
   complaints from founders or marketers about creator operations.

Return structured sections with clear headers.
```

### 9.2 Claude qualification prompt

```
You are a lead qualification analyst for Squad, a CRM built for DTC
brands managing UGC creator partnerships.

Squad solves two core pains:
  ATTRIBUTION: brands can't tell which creator actually drove sales
  CONTRACTS/IP: brands lose track of contracts, renewal dates, and
  content usage rights

Score the brand below on five signals, 0-3 each, using this rubric:

CREATOR VOLUME
  0: no visible creator partnerships
  1: 1-5 creators in last 90 days
  2: 6-20 creators
  3: 20+ creators

ATTRIBUTION PAIN
  0: no creator program, or clean per-creator codes
  1: generic codes, one creator at a time
  2: multiple creators with non-unique tracking
  3: heavy multi-creator campaigns with obvious attribution chaos

CONTRACT/IP PAIN
  0: no content reuse visible
  1: occasional creator repost
  2: consistent UGC repurposing in marketing
  3: creator UGC in paid ads and product pages, heavy rights complexity

BUYER FIT
  0: too small (<$1M) or too big (>$200M)
  1: edge of ideal range
  2: solid fit ($5M-$50M)
  3: bullseye ($10M-$30M, Series A/B)

INTENT/URGENCY
  0: no active signals
  1: steady creator program running
  2: recent hire or ops growth
  3: active creator job listing, recent funding, public pain signals

Hook selection: whichever of attribution or contracts scored higher wins.
Tie goes to attribution.

Research:
{research_dump}

Return JSON ONLY, no preamble:
{
  "creator_volume": <0-3>,
  "attribution_pain": <0-3>,
  "contract_pain": <0-3>,
  "buyer_fit": <0-3>,
  "intent_urgency": <0-3>,
  "total_score": <int 1-10, normalized>,
  "hook_pain": "attribution" or "contracts",
  "hook_evidence": "specific fact from research supporting the hook",
  "summary": "one sentence on why they fit"
}
```

### 9.3 Claude email prompt

```
Write a cold email from the founder of Squad to a marketing ops or
growth lead at {brand_name}.

Hard rules:
  Max 80 words in the body
  No em dashes, no semicolons
  No "I hope this finds you well," "quick question," "circling back"
  No fluff words: streamline, leverage, unlock, revolutionize, solution
  Sound like a real human founder who knows the creator ops space
  Reference the specific hook evidence naturally, not robotically
  One CTA: "Worth a 15-min look next week?"

Hook pain: {hook_pain}
Hook evidence: {hook_evidence}

Structure:
  Line 1: reference something real about their creator program
  Line 2: name what's probably hard about it (attribution OR contracts),
          without calling it a "pain point"
  Line 3: one concrete sentence on what Squad does for that
  Line 4: CTA

Subject line: 6 words max, specific, no clickbait.

Return exactly this format:
Subject: <subject line>
Body: <email body>
```

---

## 10. Technical Stack & Directory Structure

Python 3.11+. Streamlit for UI. Anthropic Python SDK for Claude calls. Requests or openai SDK (with custom base_url) for Perplexity. python-dotenv for config. Standard csv module for storage.

```
squad-leadgen/
  .env                    # API keys, gitignored (DO NOT CREATE, user supplies)
  .env.example            # template with key names only, no values
  .gitignore              # include .env, __pycache__, *.pyc, data/leads.csv
  requirements.txt
  README.md
  PRD.md                  # this file
  app.py                  # Streamlit UI entry point
  src/
    __init__.py
    config.py             # loads env vars via dotenv
    research.py           # Perplexity research module
    qualifier.py          # Claude qualification module
    email_writer.py       # Claude email module
    lead_agent.py         # orchestrator chaining all three
    storage.py            # csv read/write
  data/
    seed_brands.csv       # 20 ICP brands (create from Appendix A)
    leads.csv             # created on first batch run, gitignored
  scripts/
    batch_run.py          # runs agent on seed_brands.csv
```

**requirements.txt:**
```
streamlit>=1.30
anthropic>=0.40
openai>=1.50
python-dotenv>=1.0
requests>=2.31
```

**.env.example:**
```
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
```

---

## 11. Acceptance Criteria for V1

The build is done when:

1. Running `streamlit run app.py` opens the app without errors
2. Typing "Alo Yoga" and clicking Run returns a populated table row within 60 seconds
3. The row has a score between 1-10, a hook pain, evidence, and an email with subject and body
4. `data/leads.csv` has been updated with the new row
5. `scripts/batch_run.py` processes `data/seed_brands.csv` and produces 15+ rows
6. Score color coding works (green/yellow/red)
7. Detail view expands to show research dump and full email
8. No hardcoded API keys anywhere
9. `.env` is in `.gitignore`
10. `README.md` has setup and run instructions with the three steps: install requirements, set up .env, run batch_run then streamlit

**Do NOT run the live acceptance tests (items 1-7) until the user confirms .env is set up with real API keys.**

---

## Appendix A: Seed ICP Brand List

Create `data/seed_brands.csv` with one column header `brand_name` and these 20 rows:

```
brand_name
Alo Yoga
Vuori
Ghost Energy
Liquid Death
Jolie
Saie Beauty
Rhode
Kosas
Youth to the People
Merit Beauty
Branch Basics
Graza
Fly By Jing
Omsom
Haus Labs
Parade
HexClad
Caraway
Our Place
Lalo
```

---

## Appendix B: README Template

Generate `README.md` with this structure:

```markdown
# Squad Lead Gen Agent

AI SDR agent for Squad. Researches DTC brands, scores them on a 5-signal rubric,
writes personalized cold emails hitting attribution and contract/IP pain points.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Copy .env.example to .env and fill in your API keys:
   ```
   cp .env.example .env
   # edit .env with your real keys
   ```

3. Pre-populate leads:
   ```
   python scripts/batch_run.py
   ```

4. Launch the app:
   ```
   streamlit run app.py
   ```

## What it does

Input a DTC brand name. In ~20 seconds the agent:
1. Researches the brand's UGC creator footprint via Perplexity
2. Scores them 1-10 against Squad's ICP using a 5-signal rubric
3. Writes a personalized cold email referencing real evidence

## Scoring rubric

5 signals, 0-3 each, normalized to 1-10:
- Creator volume
- Attribution pain
- Contract/IP pain
- Buyer fit
- Intent/urgency

## Roadmap

V2 (not yet built):
- Autonomous creator-first discovery via TikTok/IG hashtag scraping
- Intent monitoring (LinkedIn Jobs scraping for creator manager roles)
- Lookalike expansion via Apollo
- Direct push to Instantly/Smartlead for send
```

---

## Appendix C: Pitch Narrative (reference for the demo)

> "Every DTC brand working with creators has the same two problems. They can't figure out which creator actually drove sales, and their contracts and usage rights are a mess. That's what Squad fixes.
>
> But to sell Squad, we have to find brands actively feeling those pains. So we built an AI SDR agent. It does three things: scrapes each brand's creator footprint using Perplexity, scores them on five signals against our ICP, and drafts a personalized cold email. All in 20 seconds per lead.
>
> Here's 18 DTC brands we qualified last night. Each is scored, tagged with the winning hook, and has a ready-to-send email.
>
> Pick one. I'll live-add it.
>
> This is our outbound engine. Zero SDR cost, fully personalized, scales with compute. And the v2 layer flips it: instead of us picking brands, the agent scrapes TikTok for creators running paid partnerships and surfaces every brand they tag. The discovery mechanism IS the product's use case. Our GTM motion and our product are the same thing."
