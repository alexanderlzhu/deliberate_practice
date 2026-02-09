# Deliberate Practice Journal

This directory serves as an LLM-assisted deliberate practice journal, applying the `DELIBERATE_PRACTICE` protocol to hobby activities.

## Operational Protocol

1.  **DEFINE:** Set specific, measurable target criteria $C_{target}$.
2.  **DECONSTRUCT:** Break $C_{target}$ into small, actionable sub-components $\{c_1, c_2, ...\}$.
3.  **EXECUTE:** Perform focused practice on a single component $c_i$.
4.  **FEEDBACK:** Record performance $O$ and calculate Error $E = |O - c_i|$.
5.  **CORRECT:** Analyze errors and adjust parameters for the next iteration.
6.  **INTEGRATE:** Move to the next component once $E \le threshold$.

## Structure

-   `{activity}/curriculum.md`: The deconstruction of the skill into components.
-   `{activity}/journal/`: Daily/session-specific logs following the `TEMPLATE.md`.
