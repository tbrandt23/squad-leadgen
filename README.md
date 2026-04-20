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
