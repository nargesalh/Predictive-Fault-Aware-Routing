
# Project Scope

## Goal

Investigate whether link-failure risk prediction can improve
routing recovery in simulated computer networks.

## Initial Model

- The network is represented as a graph.
- Nodes are assumed to be reliable.
- Links may fail.
- Route selection initially minimizes total latency.
- Link failures are injected explicitly in the baseline simulator.

## Initial Assumptions

- The initial graph is undirected.
- Each link has a latency attribute.
- Link reliability probabilities may be stored as metadata.
- Probabilistic failure simulation will be implemented later.
- No machine-learning model is part of Milestone 0.

## Planned Evaluation Metrics

- Route recovery time
- Packet loss
- End-to-end latency
- Failure detection quality
- False alarm rate
- Computational overhead

## Non-Goals for the First Milestone

- Real router integration
- Physical hardware experiments
- Deep learning
- Claims of superiority over existing routing methods

## Research Integrity

Performance claims must be supported by reproducible
experiments and comparisons against appropriate baselines.
