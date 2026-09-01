# Independent evaluation materials

Materials for the independent blinded evaluation reported in the manuscript
"From internal consistency to clinical generalization: independent blinded evaluation
of a traditional Chinese medicine knowledge graph question-answering system for
hypertension with emotional comorbidity" (JMIR Medical Informatics).

## Contents

| File | Contents | Manuscript reference |
|---|---|---|
| `question_set_73.json` | The 73 evaluation questions with reference answer points, sources and question types | Methods, *Evaluation design* |
| `rating_rubric.md` | The four-category rubric, fixed and signed before rating commenced | Methods, *Evaluation design* |
| `ratings_round1_three_conditions.json` | Item-level ratings, 219 responses (73 questions x 3 conditions) | Table 5 |
| `ratings_round3_model_comparison.json` | Item-level ratings, 146 responses (73 questions x 2 models) | Results, *Model capacity versus retrieval strategy* |
| `summary_results.json` | Aggregate results by condition and by model | Tables 4 and 5 |
| `retrieval_ablation.py` | Retrieval-strategy configurations and the graph-level statistics underlying the failure analysis | Table 4; Results, *Failure analysis* |

## Provenance of the question set

Three practising TCM clinicians who had taken no part in constructing the system each
contributed questions arising from their own clinical practice and teaching: a chief
physician (28 years), and two associate chief physicians (18 and 15 years). While
authoring questions they were given no access to the system, the knowledge graph, or
the corpus record list. Of 75 submitted items, 3 were returned for rewording because
they could not be scored against a determinate answer and 2 were removed as substantive
duplicates, yielding the final set of 73.

Independence can be quantified: the 73 questions name 35 distinct formulas, of which 9
(26%) are retrievable from the knowledge graph and 24 do not appear in it in any form.

## Rating procedure

Responses were rated by two further TCM clinicians who had taken no part in question
authoring, working independently and without knowledge of which condition produced each
response. Within each question the responses were presented in independently randomized
order and labelled neutrally, with the label-to-condition mapping redrawn for every
question. Observed inter-rater agreement was 85% in Round 1 (Gwet AC1 = 0.82) and 90%
in Round 3 (Gwet AC1 = 0.87).

## Evaluation rounds

Round 1 compared three conditions using the generation call as originally configured,
without an output token limit; 3 of 73 responses degenerated into repetition or emitted
chat-template artefacts and were rated as produced. Round 2 compared retrieval strategies.
Round 3 compared generation models under a 6,000-token output limit. All rounds used the
same 73 questions, the same rubric and the same two raters.

The complete system with Qwen2.5-7B-Instruct accordingly appears with a directional
accuracy of 40% in Round 1 and 48% in Round 3; the difference reflects the token-limit
correction and is reported as an engineering fix rather than a methodological finding.

## Reproducing the graph-level analysis

```bash
python evaluation/retrieval_ablation.py .
```

Requires only `data/triples.json` and `data/entities.json` from this repository. The script
prints the graph statistics on which the failure analysis rests, including the hub
threshold derivation, the proportion of hub-directed relations, and the hub-coverage
distribution of treatment-side terms.

## Note on the source corpus

`data/extracted/literature_records.json` lists the 419 source records as bibliographic
metadata (authors, title, journal, year, volume/issue/pages, keywords, database). Abstracts
have been removed from the public release in accordance with the terms of use of the
source databases (Wanfang, CNKI, VIP). Abstracts are available from the corresponding
author on reasonable request for verification purposes.
