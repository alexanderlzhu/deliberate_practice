# Investigative Learning Protocol

This document defines the generalized process for improving mental models and resolving performance gaps, adapted from the `corporate_crime_detective` and `deliberate_practice` workflows.

## Core Philosophy
Learning is an investigative process. We don't just "practice"; we **observe**, **hypothesize**, and **test** our mental models against reality.

## Operational Subroutines

### Subroutine: OBSERVATION
1. **CAPTURE:** Record the raw data point (e.g., a specific move, a feeling, a result).
2. **CATEGORIZE:** Link the observation to an existing **Model** (e.g., "Egoism") or an **Activity** (e.g., "Chess").
3. **ANALYZE:** Determine if the observation supports or contradicts the model.

### Subroutine: GAP_RESOLUTION (Scientific Method)
When a recurring error or an unexplained phenomenon is identified, create a directory in `gaps/{gap-name}/` and execute:

1. **1-question.md:** Define the specific mystery or weakness. Why do existing models fail to explain/prevent this?
2. **2-hypothesis.md:** Propose a falsifiable candidate model or explanation.
3. **3-predictions.md:** "If the hypothesis is true, what *else* should I see?" List testable outcomes.
4. **4-tests.md:** Design and execute specific drills or sessions to validate/falsify predictions. Record raw results in tables.
5. **5-conclusion.md:** 
   - **Accept:** Update/promote the mental model.
   - **Reject:** Document the failure and generate a new hypothesis.
   - **Refine:** Narrow the focus and re-test.

### Subroutine: MODEL_PROMOTION
When a hypothesis is validated across multiple observations:
1. Update the central model file in `models/`.
2. Add the validated causal links to the knowledge graph.
3. Retroactively check past observations to see if the new model explains old failures.

## Workflow Integration

1. **Pre-Session (Orient):** Select a **Model** to test or a **Gap** to investigate.
2. **Session (Act):** Execute the activity while monitoring for specific **Triggers**.
3. **Post-Session (Observe/Decide):** 
   - Record an **Observation**.
   - Link to the graph: `link-obs <slug> SUPPORTS|CONTRADICTS <model>`.
   - If a gap is detected, start a new `GAP_RESOLUTION` cycle.
