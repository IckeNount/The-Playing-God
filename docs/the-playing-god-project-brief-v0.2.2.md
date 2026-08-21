# THE PLAYING GOD — V0.2.2

**Vision Update:** 2026-08-17  
**Base:** V0.2 remains canonical. V0.2.2 adds the developmental, generational, discovery, recurrence, vector, and open-ended-civilization direction discussed afterward.

---

## Evolved Identity

**The Playing God** is a lightweight, reproducible artificial-life, artificial-society, artificial-history, and counterfactual-civilization engine.

The world should evolve from:

```text
agents acting inside developer-defined possibilities
```

toward:

```text
agents developing
→ reproducing
→ transmitting culture
→ discovering new capabilities
→ creating institutions / knowledge
→ altering possibilities available to later generations
```

The developer defines the **physics of possibility**.  
Agents increasingly create the **history inside it**.

---

# 1. Developmental NPCs

NPCs are not born as finished personalities.

```text
birth priors
+ capabilities
+ family / class / location
+ exposure
+ relationships
+ events
+ memory
+ learning
→ developing character
→ life trajectory
```

### Latent / relatively stable priors

```text
threat sensitivity
novelty seeking
reward sensitivity
self-regulation
learning rate
memory capacity
reasoning potential
social inference
motor aptitude
auditory aptitude
spatial aptitude
creative aptitude
```

### Dynamic state

```text
fear
anger
hope
envy
guilt
stress
confidence
attachment
belief
motivation
```

Dynamic emotions should usually emerge from appraisal:

```text
reality
→ imperfect perception
→ belief
→ appraisal
→ emotion
→ desire
→ intention
→ action
→ consequence
→ memory / learning
→ changed character
```

**Rule:** potential ≠ destiny.

---

# 2. Founder Generation → Full Generations

### G0 — Founder Generation

Start the main simulation with seeded adults around age 25.

Generate compact causal backstories so their initial state is explained by prior life events rather than arbitrary values.

```text
seed
→ birth conditions
→ childhood / school / relationships / failures / successes
→ G0 age-25 state
```

### G1+

Children born inside the simulation are tracked from Day 0.

```text
G0
→ reproduction
→ G1 babies
→ development
→ adulthood
→ reproduction
→ G2 ... Gn
```

Later generations become the cleanest developmental dataset because their full simulated history is known.

---

# 3. Reproduction, Family and Identity

Child starting state:

```text
parental priors
+ bounded variation
+ prenatal / household conditions
+ resources
+ upbringing
+ culture
+ chance
```

Possible systems:

```text
attraction
relationships
sexual orientation
gender identity
pregnancy
birth
abortion
parenthood
family structures
inheritance
```

Do not encode cultural phenomena as crude sliders such as `wokeness` or `cancel_culture`.

Model mechanisms:

```text
identity
norms
rights
belief
reputation
information diffusion
social sanctions
activism
group alignment
institutional rules
```

Labels belong to culture/language. Mechanisms belong to the simulation.

---

# 4. Latent Capability Expression

Do not encode fixed destinies such as:

```text
artist = 0.91
politician = 0.82
```

Use:

```text
latent aptitude
× exposure
× practice
× opportunity
× resources
× feedback
× social environment
× chance
→ developed capability
```

A strong aptitude may never be discovered. A moderate aptitude may dominate under exceptional opportunity and practice.

---

# 5. The Art of Discovery

NPCs or groups may eventually create **new world-level capabilities** from existing primitives.

```text
persistent problem
→ observation
→ experimentation
→ recombination
→ candidate discovery
→ world validation
→ success / failure
→ knowledge enters society
→ new affordances become possible
```

Possible creations:

```text
tool
technology
recipe
procedure
art style
scientific theory
business model
organization
law
religion
ideology
social norm
manufacturing process
language term
```

The system should not require a developer-authored scenario such as `invent_water_filter()` for every discovery.

LLMs may **name / describe / narrate** discoveries after the simulation validates them.

---

# 6. Restricted World Mutation

NPCs do **not** receive unrestricted database or source-code control.

### Immutable kernel

```text
simulation clock
seed / RNG rules
core causality
schema invariants
validation rules
engine source code
```

### Evolvable civilization layer

```text
knowledge
technologies
artifacts
actions / affordances
institutions
laws
norms
belief systems
organizations
markets
cultural concepts
```

Pattern:

```text
NPC / group
→ proposed innovation
→ validator
→ accepted / rejected
→ registry update
→ future NPC possibilities change
```

Agents may mutate **civilization**, not **physics**.

---

# 7. Evolving World Registries

Conceptually separate:

```text
CORE_SCHEMA
WORLD_STATE
KNOWLEDGE_REGISTRY
ACTION_REGISTRY
CULTURE_REGISTRY
INSTITUTION_REGISTRY
CAUSAL_HISTORY
```

History can therefore expand what later agents can know, create, believe, or do.

---

# 8. Three Coupled Evolution Loops

```text
INDIVIDUAL
aptitude → experience → learning → character

GENERATIONAL
parents → children → descendants

CULTURAL
invention → diffusion → institutions → inherited world
```

These loops interact continuously:

```text
individual
↕
family / generation
↕
culture / institutions
↕
economy / politics / history
```

Player intervention may perturb any layer and propagate through the others.

---

# 9. Ouroboros — Deep Generational Recurrence

Run the simulation across many generations and detect later agents/world states that strongly resemble earlier ones.

Do **not** require exact float equality and do **not** force recurrence.

```text
G0 vector
→ generations pass
→ Gn candidate
→ similarity / distance
→ recurrence threshold
→ OUROBOROS event
```

Possible recurrence classes:

```text
Type I   similar birth / latent configuration
Type II  similar developed personality
Type III similar life trajectory
Type IV  similar societal configuration
```

Core question:

```text
similar starting person
+ radically different historical context
→ similar destiny or divergent destiny?
```

Ouroboros is a **detector and research metaphor**, not a supernatural claim or scripted cycle.

---

# 10. Vectors, Embeddings and ML

Use different vector systems for different jobs.

### Numeric state vectors

```text
NPC_VECTOR
= [temperament, capabilities, needs, beliefs, social position, ...]
```

Uses:

```text
similarity
nearest-neighbour search
Ouroboros detection
trajectory comparison
clustering
classification
anomaly detection
```

### Semantic embeddings

Use for meaning-based retrieval:

```text
memory retrieval
similar historical events
relevant discoveries
rumours
beliefs
knowledge search
semantic event grouping
```

Embeddings are an index over meaning, not the NPC soul.

### ML over accumulated simulation data

Possible later tasks:

```text
trajectory classification
social-role clustering
migration / conflict prediction
innovation adoption
institutional instability
Ouroboros candidate detection
```

ML/DL remains optional and must solve a measurable problem.

---

# 11. Decision / Cognition Direction

Preferred progression:

```text
weighted stochastic utility
→ perceived-world state
→ belief / desire / intention
→ appraisal-driven emotion
→ habits / coping
→ contextual bandits / tabular RL
→ limited planning / tree search
```

NPCs act on **perceived reality**, not omniscient database truth.

Therefore misunderstanding, propaganda, incomplete information, false belief, and social influence become causal mechanisms rather than scripted events.

---

# 12. Open-Ended Civilization Principle

Target pattern:

```text
agents inherit a world
→ encounter constraints
→ adapt / learn / create
→ modify available possibilities
→ transmit changes
→ descendants inherit a different world
```

The action-space may expand through validated discovery.

Unexpected history should emerge because previous generations modify the conditions faced by later ones.

---

# 13. Updated LLM Boundary

The world must still function with no API key.

```text
SIMULATION
creates structured reality

LLM
names / explains / narrates / summarizes reality
```

Possible LLM tasks:

```text
dialogue
biographies
dream interpretation
historical summaries
discovery naming
institution naming
cultural terminology
rumour prose
player explanations
```

The LLM must not silently overwrite causal truth.

---

# 14. V0.2.2 Design Laws

1. V0.2 remains the foundation; V0.2.2 extends it.
2. NPCs begin with priors/capacities, not finished destinies.
3. Emotions are mostly dynamic appraisals, not permanent random sliders.
4. Later generations should be observable from birth.
5. Reproduction creates variation; environment and culture drive development.
6. Potential requires exposure, practice, opportunity, and history.
7. Sensitive social phenomena emerge from reusable mechanisms, not ideology switches.
8. Agents may create new civilization-level possibilities.
9. The simulation kernel remains immutable to NPCs.
10. Discoveries must pass world constraints before becoming real.
11. LLMs may name discoveries but do not validate reality.
12. Cultural inheritance may become as important as biological-like inheritance.
13. The action-space may expand through valid discovery.
14. Vectors measure structured similarity; embeddings retrieve semantic relevance.
15. Ouroboros detects recurrence; it never manufactures it.
16. Similar agents in different historical contexts are valuable counterfactual experiments.
17. Prefer causal, traceable mechanisms before opaque DL policies.
18. Preserve reproducibility, offline operation, weak-hardware viability, and optional AI layers.

---

# Canonical V0.2.2 Pattern

```text
BIRTH
= priors + bounded variation + environment

DEVELOPMENT
= aptitude × exposure × opportunity × experience × learning

MIND
= perception → belief → appraisal → emotion → desire → intention

LIFE
= action → consequence → memory → learning → changed character

GENERATION
= reproduction + inheritance + upbringing + culture

DISCOVERY
= problem + primitives + experimentation → validated novelty

CIVILIZATION
= agents + knowledge + institutions + culture + evolving affordances

HISTORY
= causal events + feedback loops + path dependence + generational inheritance

OUROBOROS
= deep-time recurrence detected through state-space similarity

VECTORS
= structured similarity / clustering / recurrence

EMBEDDINGS
= semantic relevance / retrieval

GOD
= sparse intervention into an evolving causal world

LLM
= optional language layer over structured reality
```

---

## Updated Vision

**The Playing God is no longer only about artificial people choosing inside a world designed by the developer.**

It is becoming a world where people are born with potentials, develop through experience, reproduce, transmit culture, misunderstand reality, discover capabilities, create institutions, alter the future possibility-space, and leave descendants inside a civilization partially created by previous NPCs.

**The developer defines the possible. The agents increasingly define what actually becomes real.**
