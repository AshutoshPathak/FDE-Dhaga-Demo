# Discovery Note — draft for group approval

**Problem in the client's language**  
Dhaga & Co. has a 31% overall return rate, but 44% of return reasons land in "Other", leaving the Category team unable to consistently see and act on recurring fit problems hidden in free-text feedback.

**Owner today and current workaround**  
Neha, Category Head. She manually reads a few hundred "Other" comments to understand what is driving returns, and reports that much of what she sees is about fit.

**Evidence from the case**  
- Overall returns: 31%.
- 44% of return reasons are recorded as "Other".
- Neha says most of the "Other" comments she reads manually are about fit, but she can only read a few hundred at a time.
- Catalogue size/fit data is inconsistent across vendors, which makes structured diagnosis harder.

**Current cost / metric**  
The case gives the return rate as 31%; it does not give a rupee cost per customer return, so we should not invent one. The measurable current problem is the high return rate plus the 44% unstructured reason bucket and the manual effort required to inspect it.

**Success**  
For the MVP: accurately convert messy return comments into a controlled taxonomy, surface recurring SKU/size/fit patterns, and explicitly route uncertain comments for review. Measure primary-reason accuracy on the labeled evaluation set, escalation rate, human-review rate, and processing cost.

**Ranked shortlist**  
1. Returns / fit intelligence — high measured pain, named owner, existing free-text data, clear MVP path.
2. Customer support / WISMO automation — 58% WISMO, 9-hour first response, strong data and clear owner; easier but more generic.
3. Product listing / catalogue assistant — 6–9 day sample-to-live cycle and messy attributes; strong opportunity, but the brief does not prove copywriting is the main bottleneck.
4. Analytics assistant — two analysts and ~2-week request queue; useful but broad and harder to bound safely for a mini-project.

**Biggest assumption**  
The main assumption is that the "Other" free text contains recurring, actionable product/fit patterns at enough volume to change category decisions. We would be wrong if a representative sample shows that most comments are too vague, one-off, or unrelated to controllable product/size issues.

> Group action: approve wording and date this note before the first repository commit.
