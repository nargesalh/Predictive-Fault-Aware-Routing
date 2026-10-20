
# Research Plan

## Project Title

Topology-Aware and Budget-Constrained Algorithm Selection
for Network Reliability Estimation

## 1. Research Problem

Computing network reliability exactly can be computationally
expensive for many graph structures.

Different exact, approximate, and stochastic algorithms
have different accuracy, runtime, memory requirements,
and applicability conditions.

This project investigates whether graph features and
computational constraints can help select a suitable
reliability-estimation algorithm for a given network.

## 2. Main Research Question

Can an algorithm selector choose a suitable network
reliability method based on graph topology, required
accuracy, and computational budget?

The selected method should satisfy the required accuracy
and runtime constraints whenever a suitable method exists.

## 3. Initial Research Hypothesis

A topology-aware algorithm selector may reduce computational
cost compared with using a single fixed algorithm, while
maintaining acceptable estimation accuracy.

This hypothesis must be validated experimentally.

## 4. Research Scope

The initial scope focuses on all-terminal reliability
of undirected binary-state networks.

The initial probabilistic model assumes independent edge
failures with a common failure probability q.

Extensions to non-identical edge failure probabilities,
directed networks, and temporal failures are considered
future work.

## 5. Algorithms to Investigate

### Reference Method

- Exact all-terminal reliability for small graphs.

### Approximation and Simulation Methods

- Edge Deletion Process
- First-order approximation (R1)
- Second-order approximation (R2)
- Subway-type approximation (Rs)

### Additional Candidate Methods

- Decomposition
- Binary Decision Diagrams (BDD)
- BAT and Quick BAT
- Pathsets and Cutsets
- Variance-reduction Monte Carlo methods

Additional methods will be included after checking their
assumptions, implementation feasibility, and relevance
to the common evaluation task.

## 6. Benchmark Design

The benchmark will include several graph families:

- Small graphs for exact validation
- Random and sparse graphs
- Dense graphs
- Regular graphs
- Subway-like graphs with long degree-two paths

Where possible, graph families and test cases will be
separated between training and evaluation to measure
generalization to unseen topologies.

## 7. Evaluation Metrics

- Absolute and relative estimation error
- Runtime
- Peak memory usage
- Ability to meet a specified runtime budget
- Ability to satisfy an accuracy requirement
- Selector performance compared with fixed-method baselines
- Regret relative to the best eligible method for each instance

## 8. Algorithm Selection Strategy

The initial selector will use explicit rules based on
graph characteristics and benchmark results.

A machine-learning selector will be considered after
sufficient benchmark data has been collected.

The learned selector must be evaluated on graph instances
not used during training.

## 9. Routing Extension

A later stage will investigate whether reliability estimates
and predicted link-failure risks can improve routing decisions.

This extension will be evaluated separately against
reactive routing and precomputed backup-path baselines.

## 10. Research Integrity

- Published algorithms will be implemented according to
  their documented assumptions.
- Methods will only be compared when they solve compatible
  tasks and use consistent definitions.
- Approximation error and runtime will both be reported.
- Performance improvements will only be claimed when
  supported by reproducible experiments.
- Existing methods will be properly cited.

## 11. Current Status

The repository contains a baseline routing simulator,
visualization, and initial automated tests.

The reliability benchmark, exact reference implementation,
algorithm selector, and predictive routing extension
remain future milestones.

## 12. Initial Milestones

1. Implement exact all-terminal reliability for small graphs.
2. Validate the reference implementation with known cases.
3. Implement the Edge Deletion Process.
4. Implement and test R1, R2, and Rs.
5. Build a reproducible benchmark.
6. Compare runtime and estimation accuracy.
7. Develop and evaluate an algorithm selector.
8. Investigate the predictive routing extension.
