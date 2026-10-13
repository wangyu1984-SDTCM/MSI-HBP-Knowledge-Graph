# Independent evaluation materials

Materials for the blinded question-answering evaluation reported in the manuscript
"A Traditional Chinese Medicine Knowledge Graph for Hypertension With Emotional
Comorbidity: Development and Blinded Question-Answering Evaluation" (submitted to
JMIR Medical Informatics, manuscript 101606).

## Contents of this directory

| File | Contents | Manuscript reference |
|---|---|---|
| `question_set_73.json` | The 73 evaluation questions with reference answer points, sources and question types | Methods, *Evaluation design* |
| `rating_rubric.md` | The four-category rubric, fixed before rating commenced | Methods, *Evaluation design* |
| `ratings_round1_three_conditions.json` | Item-level ratings, 219 responses (73 questions x 3 conditions: complete system, retrieval only, model only; Qwen2.5-7B-Instruct, no output-token limit) | Results, *Independent blinded evaluation*; Table 4 |
| `ratings_round3_model_comparison.json` | Item-level ratings, 146 responses (73 questions x 2 generation models under a 6000-token limit: Qwen2.5-7B-Instruct and DeepSeek-V4-Pro) | Results, *Comparison of generation models*; Table 5 |
| `summary_results.json` | Aggregate counts by condition and by model for the two rounds above | Tables 4 and 5 |
| `retrieval_ablation.py` | The six retrieval configurations (A0, D1, D1.5, D2, D3, D4) and the graph-level statistics underlying the failure analysis | Results, *Retrieval strategy ablation* and *Failure analysis*; Table 6 |

Each rating record carries both independent ratings (`rater1`, `rater2`), the
consensus category, and the separately recorded `fabrication` and `safety_flag`
fields. Where the two raters disagreed, the consensus is the more conservative of
the two categories. In `summary_results.json`, `strict_accuracy` is the proportion
of fully correct responses and `directional_accuracy` is the correct-or-partially-
correct proportion; the latter is a combination of two rubric categories and is not
a measure of clinical acceptability.

## Materials provided with the manuscript rather than in this directory

The following item-level materials are supplied as Multimedia Appendices of the
manuscript and are not part of release v2.0 of this repository:

- the six-configuration (retrieval-strategy) ratings, 438 responses (Table 6);
- the additional matched DeepSeek-V4-Pro comparison with and without graph
  retrieval, 146 responses, including the exact prompts, recognized entities and
  the exported run record (Table 7);
- the original answer texts for the initial, generation-model and matched
  comparisons, and the 73 reference-answer keys with scoring instructions;
- the 100 sampled curated relations with both reviewers' labels and consensus
  outcomes (Methods, *Validation of curated relations*).

Note that the DeepSeek-V4-Pro answers rated in `ratings_round3_model_comparison.json`
are the same 73 A0 answers that were rated in the six-configuration round; they were
rated in two separate blinded rounds by the same two physicians and the two sets of
labels are reported separately in the manuscript (Tables 5 and 6). They are not
independent generations.

## Provenance of the question set

Three practising TCM clinicians who had taken no part in constructing the system each
contributed questions arising from their own clinical practice and teaching: a chief
physician (28 years), and two associate chief physicians (18 and 15 years). While
authoring questions they were given no access to the system, the knowledge graph, or
the corpus record list. Of 75 submitted items, 3 were returned for rewording because
they could not be scored against a determinate answer and 2 were removed as substantive
duplicates, yielding the final set of 73.

The 73 questions name 35 distinct formulas, of which 9 are retrievable from the
knowledge graph. This is a measure of graph coverage of the question set, not a test
of question-set independence.

## Rating procedure

Responses were rated by two further TCM clinicians who had taken no part in question
authoring, working independently and without knowledge of which condition produced each
response. Within each question the responses were presented in independently randomized
order and labelled neutrally, with the label-to-condition mapping redrawn for every
question. Initial inter-rater agreement was 186/219 (84.9%; Gwet AC1 = 0.82) in Round 1
and 132/146 (90.4%; Gwet AC1 = 0.87) in Round 3.

## Evaluation rounds

- Round 1 compared three conditions using the generation call as originally
  configured, without an output-token limit; 3 of 73 responses
  degenerated into repetition or emitted chat-template artefacts and were rated as
  produced.
- Round 2 compared six retrieval configurations with DeepSeek-V4-Pro as the generation
  model (`retrieval_ablation.py`; ratings in the manuscript appendices).
- Round 3 compared generation models under a 6000-token output limit with the same
  graph, retrieval procedure, prompts and raters.
- An additional matched comparison (October 2026) ran DeepSeek-V4-Pro with and without
  graph retrieval on the same 73 questions, one response per condition per question,
  using the JSON retrieval backend; materials are in the manuscript appendices.

All rounds used the same 73 questions, the same rubric and the same two raters. The
rounds are reported separately in the manuscript; results from different rounds are
not pooled and are not interpreted as controlled estimates of improvement over time.

## Reproducing the graph-level analysis

```bash
python evaluation/retrieval_ablation.py .
```

Requires only `data/triples.json` and `data/entities.json` from this repository. The script
prints the graph statistics on which the failure analysis rests, including the hub
threshold derivation (degree greater than five times the mean degree; mean 6.18,
threshold 30.9), the proportion of hub-directed relations (173/312), and the
hub-coverage distribution of treatment-side terms.

## Note on the source corpus

`data/extracted/literature_records.json` lists the 419 source records as bibliographic
metadata (authors, title, journal, year, volume/issue/pages, keywords, database):
257 from Wanfang, 95 from CNKI, 62 from VIP, and 5 records whose database field was not
recorded in the export. Abstracts have been removed from the public release in
accordance with the terms of use of the source databases (Wanfang, CNKI, VIP).
Abstracts are available from the corresponding author on reasonable request for
verification purposes.
