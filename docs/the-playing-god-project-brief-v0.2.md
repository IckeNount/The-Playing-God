# THE PLAYING GOD — V0.2

## Identity

**The Playing God** is a lightweight, reproducible artificial-society and counterfactual-history simulator for a Master of Computer Engineering thesis.

It studies how **heterogeneous agents, capabilities, psychology, resources, relationships, institutions, information, environment, chance, and sparse indirect intervention** generate divergent lives and histories.

It is not an LLM swarm, a real-world prediction engine, a scripted story generator, or a claim to simulate the human mind accurately.

---

## Core Research Question

> How do small differences in agents, social conditions, historical events, and indirect interventions propagate through an artificial society and produce different long-term trajectories?

Counterfactual extension:

> How can sparse indirect interventions alter individual and societal futures without directly controlling the target agent?

---

## Current Foundation

### Phase 1 — Ten Invisible Humans ✅
Autonomous agents, traits, seven sins, needs, internal state, weighted stochastic decisions, relationships, events, deterministic seeds, divergent trajectories.

### Phase 2 — Persistent World ✅
Modular core, SQLite persistence, save/load, agent state, relationships, events, reproducible runs.

### Phase 3 — Social World ✅
Explicit social relationships, influence, interaction-driven state changes, cross-agent causality.

**What exists now:** a reproducible, persistent, socially coupled causal simulation engine.

---

# World Primitives

Scale through reusable primitives rather than hard-coded scenarios.

```text
WORLD
├── Agents
├── Relationships
├── Resources
├── Locations
├── Institutions
├── Information / Beliefs
├── Economy / Markets
├── Rules / Laws
├── Events
├── Historical Memory
└── Interventions
```

Complex phenomena are combinations:

```text
propaganda = information + trust + repetition + identity + network
revolution = grievance + network + threshold + opportunity + weak legitimacy
migration = location + opportunity + risk + resources + ties + restrictions
monopoly = ownership + capital + competition + institutional rules
mass hysteria = fear + uncertainty + conformity + diffusion + social proof
```

---

# NPC Model

```text
NPC
├── Identity
├── Baseline traits
├── Behavioral drives / seven sins
├── Capabilities
├── Needs
├── Dynamic psychological state
├── Goals
├── Resources
├── Habits / coping strategies
├── Memories
├── Relationships
├── Beliefs / faith
├── Social position
└── Current context
```

### Rule
Complex behavior is an **outcome**, not a personality slider.

```text
traits
+ vulnerabilities
+ current state
+ memory
+ social context
+ opportunity
+ inhibition
+ uncertainty
→ action probabilities
```

Do not encode scenario-specific attributes such as `suicide_tendency`, `drug_abuse`, or `jealous_assault` as deterministic switches.

---

# Functional Intelligence

Do not assign fictional psychometric IQ/EQ scores. Model capability mechanisms.

### Cognitive
```text
perception_accuracy
memory_capacity
learning_rate
planning_depth
problem_solving
risk_estimation
adaptability
```

### Social / Emotional
```text
emotion_perception
empathy
self_regulation
social_inference
persuasion
conflict_resolution
relationship_memory
```

Capabilities alter what an NPC can perceive, estimate, remember, plan, learn, and execute.

---

# Decision Engine

```text
situation
→ candidate actions
→ estimate reward / cost / risk
→ traits + needs + goals + memory + beliefs + social influence
→ capability limits + uncertainty
→ stochastic choice
→ action
→ consequence
→ state / memory / learning update
```

Preferred progression:

```text
weighted utility
stochastic choice
rule / state systems
contextual bandits
tabular Q-learning
small tree search
```

Deep learning is optional and must justify its cost.

---

# Survival, Capability and Contribution

Track separate dimensions instead of reducing a person to one fitness number:

```text
cognitive competence
economic stability
social support
emotional regulation
adaptability
physical wellbeing
goal progress
social contribution
```

A derived **Life Viability Index** may summarize stability for experiments, but NPCs may value goals differently.

Contribution is measured through downstream effects:

```text
jobs created
skills transferred
resources produced
relationships strengthened
institutional effects
stability / instability created
indirect causal effects
```

Counterfactual contribution:

```text
Contribution(X)
= WorldOutcome(with X) - WorldOutcome(without X)
```

---

# Social Dynamics

Relationships form a graph with dimensions such as:

```text
trust
attraction
hostility
respect
dependency
familiarity
loyalty
influence
```

Collective behavior emerges through network mechanisms:

```text
network diffusion
threshold cascades
opinion dynamics
social proof
conformity
reputation propagation
```

Belief change may depend on:

```text
source trust
repetition
emotional resonance
group alignment
social confirmation
skepticism
contradictory evidence
```

Idolization / blind following emerges from charisma, status, identity, perceived competence, visibility, success history, uncertainty, and social proof.

---

# Institutions and Power

Possible institutions:

```text
government
businesses
banks
schools
religious institutions
media
police
courts
political parties
unions
military
NGOs
```

Institutions are structured entities, not necessarily AI agents.

Possible state:

```text
resources
leadership
rules
legitimacy
capacity
corruption
loyalty
policies
```

Power remains multidimensional:

```text
economic
political
coercive
informational
social
institutional
```

---

# Economy

Use a minimal agent-based economy to create constraints and feedback:

```text
employment
wages
ownership
businesses
production
consumption
prices
credit
wealth distribution
competition
taxation / redistribution
```

Economic effects must propagate across agents, classes, institutions, and locations. Both collapse and stabilizing feedback must be possible.

---

# Politics and Collective Action

Possible mechanisms:

```text
voting
coalitions
legitimacy
protests
repression
reform
revolution
coups
war
```

Collective action can use individual participation thresholds. One early actor may trigger a cascade without being hard-coded as "the revolutionary."

Political outcomes remain conditional and stochastic.

---

# Culture and Collective Memory

Culture evolves from repeated behavior and then shapes future behavior.

Possible dimensions:

```text
institutional trust
violence tolerance
religiosity
individualism / collectivism
corruption tolerance
outgroup hostility
risk tolerance
family norms
```

Societies retain significant memories such as wars, crashes, revolutions, migration waves, epidemics, mass violence, golden ages, and political betrayals.

Collective memory influences later identity, trust, policy, belief, and conflict.

---

# Geography and Migration

Neighbourhoods may differ in:

```text
jobs
housing
resources
laws
institutions
culture
wealth
safety
population
```

Migration emerges from opportunity, risk, social ties, costs, and restrictions, then changes both origin and destination.

Neighbourhoods may later evolve into larger political entities with trade, alliances, sanctions, conflict, and war.

---

# Events, Butterfly Effects and Path Dependence

Events form a causal graph, not only a timeline.

```text
EVENT
├── causes
├── participants
├── affected systems
├── immediate effects
├── opportunities created / removed
├── downstream effects
└── significance
```

History emerges from:

```text
initial conditions
+ path dependence
+ feedback loops
+ network effects
+ stochastic events
```

Small events may create large downstream divergence if they alter later opportunities or networks.

---

# Counterfactual Timeline Engine

```text
Seed X + no intervention
→ baseline timeline

Seed X + intervention
→ counterfactual timeline
```

Future exploration should not enumerate every possible universe.

Progression:

```text
deterministic forks
Monte Carlo rollouts
beam search
Monte Carlo Tree Search
optional learned outcome predictor
optional model-based RL
```

Possible metric:

```text
ButterflyImpact(event)
= distance(actual future, counterfactual future without event)
```

Compare variables such as wealth, inequality, employment, relationships, belief, migration, stability, conflict, health, population, and goal completion.

---

# God / Intervention Model

The player changes **conditions**, not guaranteed outcomes.

Possible interventions:

```text
dream
sign
opportunity
warning
luck modifier
encounter
protection
misfortune
```

Interventions may propagate indirectly through other NPCs, institutions, markets, or events before reaching the intended target.

Every causal link can fail, be misunderstood, or create unintended effects.

God mechanics are therefore a **counterfactual planning problem**, not direct character control.

---

# Belief and Faith

NPCs never receive proof that the player exists.

```text
prayer / desire
→ possible intervention
→ outcome
→ interpretation
→ faith / skepticism update
→ future behavior
```

The same event may be interpreted as miracle, coincidence, personal achievement, manipulation, or noise.

---

# Artificial History

```text
MICRO
individual psychology / capability
↓
MESO
families / groups / firms / institutions
↓
MACRO
economy / politics / culture / migration
↓
HISTORY
crises / movements / revolutions / wars / eras
↓
COUNTERFACTUAL
what could have happened differently?
↓
INTERVENTION
where can a small change redirect the causal chain?
```

The long-term identity is a **reproducible artificial-history engine built from autonomous artificial lives**.

---

# Optional Future Systems

Add only when emergence or research requires them:

```text
family / inheritance
education
health / disease
crime / law
environment / disasters
technology / innovation
religion / ideology
trade
international relations
war
birth / death
generational change
```

These are not thesis-MVP requirements.

---

# Cheap Algorithm Map

```text
individual decisions  → weighted utility + stochastic choice
learning              → contextual bandits / tabular Q-learning
planning              → small tree search
social structure      → graph algorithms
belief / propaganda   → diffusion + opinion dynamics
collective action     → threshold cascades
economy               → agent-based market rules
migration             → utility-based movement
politics              → voting / coalition / legitimacy rules
institutions          → state machines / rule systems
counterfactuals       → Monte Carlo rollouts
future search         → beam search / MCTS later
history               → causal event graph
```

Most of the universe requires neither deep learning nor continuous API calls.

---

# LLM Boundary

**The world must function with no API key.**

```text
Simulation decides WHAT happened.
LLM decides HOW it is expressed.
```

Optional LLM tasks:

```text
dialogue
diaries
prayers
dream interpretation
rumour prose
biographies
historical summaries
player explanations
thesis case narratives
```

Never send the full universe to an LLM.

```text
structured database
→ query significant events
→ algorithmic compression
→ small context
→ optional generation
```

NPC intelligence comes from simulation mechanisms, not persistent LLM calls.

---

# Research Identity

The Playing God does **not** primarily ask which LLM survives best or whether an LLM swarm can predict real-world events.

It asks:

> How do heterogeneous artificial individuals and institutions generate divergent causal histories inside a reproducible society, and how do sparse indirect interventions alter those histories?

Primary experimental variables:

```text
traits
capabilities
resources
social position
beliefs
institutional structure
information environment
world conditions
seed
intervention type / timing
```

Primary outcomes:

```text
life-trajectory divergence
survival / stability
goal completion
wealth / inequality
social cohesion
belief propagation
institutional stability
migration
conflict
collective action
intervention effectiveness
butterfly impact
```

---

# Academic Boundary

Do not claim to:

```text
accurately reproduce human psychology
diagnose mental illness
predict specific real humans
measure real IQ / EQ
prove free will
prove supernatural causation
predict real history
```

All psychology, morality, belief, attraction, culture, violence, status, and social categories are explicit computational abstractions inside a fictional artificial society.

---

# Stable Design Laws

1. Simulation first; visualization later.
2. The LLM is a language layer, not the soul.
3. Complex behavior emerges from interacting factors, not scenario-specific sliders.
4. Events form causal history, not merely chronological logs.
5. Relationships and institutions create cross-agent causality.
6. The player alters conditions, not guaranteed outcomes.
7. Outcomes must remain traceable to state, rules, randomness, history, or intervention.
8. Counterfactual runs must be reproducible.
9. Prefer cheap, explainable algorithms before ML/DL.
10. The world must work offline and on weak hardware.
11. Scale through reusable primitives, not thousands of scripted scenarios.
12. Feedback loops must operate between individuals, groups, institutions, economy, culture, and history.
13. Emergence matters more than content volume.
14. Scientific claims remain narrower than the fictional world.

---

# Canonical Pattern

```text
AGENT
= traits + capabilities + needs + state + goals + resources + memory + relationships + beliefs

DECISION
= perceived state + context + expected outcomes + capability limits + uncertainty

SOCIETY
= agents + networks + institutions + information + economy + geography + culture

HISTORY
= events + causal links + feedback loops + path dependence

FATE
= seeded baseline + stochastic variation

GOD
= sparse indirect intervention

MULTIVERSE
= fork + rollout + compare

LLM
= optional language interface over structured reality
```

---

# Final Vision

**The Playing God is a computational laboratory for artificial lives, societies, histories, and counterfactual intervention.**

The NPC is the unit. Relationships connect units. Institutions organize power and resources. Information alters belief. Economies create incentives and constraints. Culture and collective memory create path dependence. Events propagate across the system. Counterfactual timelines expose butterfly effects. The player perturbs the causal network without directly controlling outcomes.

The goal is not to simulate everything that makes humans human.

The goal is to define a small set of understandable mechanisms rich enough that **unexpected lives, collective behavior, institutions, crises, movements, and histories emerge from their interaction**.
