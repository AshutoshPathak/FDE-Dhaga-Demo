# Project compliance checklist

## Discovery
- [x] Named owner: Neha, Category Head.
- [x] Evidence-backed problem: 31% overall returns; 44% of return reasons are "Other"; manual reading suggests fit is a major theme.
- [x] Ranked shortlist of at least four problems prepared.
- [x] Success can be measured using existing return data.
- [x] Biggest assumption identified: useful recurring fit patterns exist consistently enough in the "Other" text to support action.
- [ ] Group must date and approve the Discovery Note before the repository's first commit.

## MVP / technical rules
- [x] Visible Gradio frontend.
- [x] Real-shaped 300-row Hinglish/English synthetic input.
- [x] Two models configured: Gemini 2.5 Flash-Lite + Gemini 2.5 Flash.
- [x] Two purposeful patterns: parallelization + routing.
- [x] Deterministic code/model boundary documented.
- [x] Classification/review temperatures 0.1; insight temperature 0.3.
- [x] Structured Pydantic schemas at every model boundary.
- [x] Structured-output retry implemented; unresolved records become visible Needs Review cases.
- [x] Visible failure states.
- [x] README supports a local cold start in under five minutes.
- [x] Token usage capture and cost arithmetic implemented.
- [x] Cost scaling includes a clearly labelled derived weekly volume estimate.
- [ ] Live Gemini API path must be tested with the team's API key.
- [ ] Fill current official Gemini prices in Space secrets/environment before final cost demo.

## Delivery
- [x] Hugging Face-ready Gradio repository structure.
- [ ] Create the Hugging Face Space and add GEMINI_API_KEY secret.
- [ ] Test the public URL on a device/browser that did not build the app.
- [ ] Run live-model evaluation against the labeled CSV and record results.
- [ ] Finalize the 1-page Discovery Note.
- [ ] Finalize the max-2-page Build Note, including a real unexpected breakage from development.
- [ ] Prepare a deliberate failure-case demo.
- [ ] All five members rehearse and can explain the whole system.
