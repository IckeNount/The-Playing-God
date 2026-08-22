# Phase 4 — Spatial World, Mobility & Encounters

**Status:** Complete

**Roadmap:** [`Phase 4`](../ROADMAP.md#phase-4--spatial-world-mobility--encounters)

**Historical source:** Vision brief 0.2.3, normalized to the roadmap phase number on 2026-08-22.

**Purpose:** Add the missing physical-world layer that explains where NPCs are, how they travel, how they encounter others, and how geography becomes causal.

---

# 1. Core Principle

Relationships must not appear from random social-edge generation.

```text
need / goal / obligation
→ destination choice
→ movement
→ co-location / exposure
→ interaction opportunity
→ interaction
→ familiarity
→ relationship
→ social graph
```

The social graph is therefore a historical consequence of movement, exposure, and repeated interaction.

---

# 2. Spatial World Model

Use a lightweight weighted graph instead of a full SimCity-like world.

```text
PLACE = node
ROAD / PATH = edge
ROUTE = sequence of edges
NPC = current node OR moving point on an edge
```

Each node may represent:

```text
home
market
factory
school
park
shrine
hospital
cafe
bus stop
government office
institution site
```

Each physical location has fixed visualization coordinates:

```text
location
= id + type + x + y + properties
```

The same map may be reused across many simulation seeds for cleaner counterfactual experiments.

---

# 3. Roads and Travel Costs

Each edge stores travel properties:

```text
from
to
distance
travel_time
physical_energy_cost
money_cost
danger
transport_modes
```

NPC route preference is not always pure shortest distance.

```text
RouteCost
=
time
+ physical_energy
+ money
+ perceived danger
+ contextual preference
```

Different NPCs may therefore choose different routes between the same locations.

---

# 4. Pathfinding

Preferred progression:

```text
V1  Dijkstra shortest / lowest-cost path
V2  A* if maps become larger
V3  transport-mode or context-aware routing if justified
```

Do not implement pedestrian physics, collision systems, or detailed locomotion for the thesis core.

---

# 5. NPC Spatial State

Minimum travel state:

```text
current_location
destination
current_edge
edge_progress
activity
physical_energy
social_energy
```

Example:

```text
current_edge = market → factory
edge_progress = 0.63
```

The renderer converts edge progress into an `(x,y)` point between both location coordinates.

The simulation stores abstract travel state.  
The visualization draws the moving dot.

---

# 6. Movement Decision

NPCs travel because of causal reasons, not random wandering.

```text
needs
+ goals
+ obligations
+ habits
+ relationships
+ money
+ available time
+ physical energy
+ social motivation
→ destination utility
→ destination choice
→ route
→ travel
```

Possible activities:

```text
work
eat
shop
rest
socialize
visit person
worship
study
seek opportunity
seek healthcare
travel / migrate
```

Weighted stochastic choice may select among reasonable destinations.

Randomness may vary decisions; it must not invent physically impossible exposure.

---

# 7. Physical and Social Energy

Keep separate state variables.

### Physical energy

Affected by:

```text
travel
work
exercise
sleep
food
health
illness
```

### Social energy

Affected by:

```text
conversation
crowds
conflict
meeting strangers
social obligations
close relationships
solitude
rest
personality
```

A supportive interaction may restore social energy while an exhausting one may consume it.

Energy affects whether an NPC leaves home, travels farther, socializes, avoids crowds, or cancels plans.

---

# 8. Exposure Before Relationship

Maintain conceptually distinct layers:

```text
SPATIAL GRAPH
where movement is possible

EXPOSURE GRAPH
who could encounter whom

CONTACT GRAPH
who actually interacted

SOCIAL GRAPH
who developed meaningful relationships
```

Co-location creates opportunity, not guaranteed interaction.

---

# 9. Encounter Mechanism

An encounter requires overlapping spatial and temporal context.

```text
same node
OR
compatible position on same edge
+
overlapping time
→ possible exposure
```

Interaction probability may depend on:

```text
co-location duration
activity compatibility
sociability
social energy
familiarity
shared context
attention
attraction
existing relationships
mutual contacts
mood
crowding
chance
```

Randomness decides whether a valid opportunity becomes an interaction.

It does not create the opportunity itself.

---

# 10. Relationship Formation

A first encounter should normally create familiarity, not instant friendship.

```text
stranger
→ recognized stranger
→ acquaintance
→ repeated interaction
→ meaningful relationship
```

Interactions update dimensions such as:

```text
familiarity
trust
respect
attraction
hostility
dependency
loyalty
influence
```

High-impact shared events may accelerate relationship formation.

---

# 11. Relationships Change Future Movement

The causal loop becomes bidirectional.

```text
movement
→ encounters
→ relationships
→ invitations / visits / introductions
→ new movement
→ new encounters
```

Examples:

```text
coworker
→ friend
→ invitation to cafe
→ friend-of-friend encounter
→ new social edge
```

This supports organic triadic closure and network growth.

---

# 12. Geography as Causal Infrastructure

Location is not decoration.

Geography may influence:

```text
who meets whom
job access
romance
education
political exposure
religious participation
crime exposure
information spread
migration
class mobility
protest participation
innovation diffusion
```

Two NPCs may live nearby and never meet if their routines never overlap.

Two distant NPCs may become close if technology creates remote exposure.

---

# 13. Communication Technology Evolution

Before telecommunications:

```text
social exposure ≈ physical proximity
+ travel
+ migration
+ institutions
+ friend-of-friend introduction
```

Telephone:

```text
existing ties survive distance
```

Internet:

```text
shared interests create remote exposure
```

Social media:

```text
algorithmic visibility becomes an encounter generator
```

Virtual spaces may later act like locations:

```text
forum
group chat
gaming server
dating platform
social feed
online community
```

Technology changes the exposure mechanism, not the fundamental social model.

---

# 14. Lightweight Visualization

Build a debug map before a game world.

```text
fixed nodes
+ visible edges
+ NPC dots
+ highlighted routes
+ optional labels
+ simulation clock
```

NPC position:

```text
node
OR
edge + progress
```

A route may visually appear like:

```text
Home
→ Bus Stop
→ Market
→ Factory
```

No building interiors, 3D geometry, pedestrian animation, or physics are required.

The renderer must remain separate from the simulation engine.

---

# 15. Map Creation Strategy

### V1 — Hand-authored fixed map

Recommended now.

```text
15–30 meaningful locations
manual x/y coordinates
manual roads
weighted edges
```

### V2 — Procedural graph generation

Optional later for experiments or larger worlds.

Possible graph families:

```text
grid
random geometric
small-world
clustered neighbourhood
```

### V3 — Real GIS / OpenStreetMap

Only if real-world road topology becomes academically useful.

Do not make external map infrastructure a thesis dependency.

---

# 16. Simulation Loop Addition

For each meaningful time block:

```text
1. update needs and energy
2. choose activity
3. choose destination
4. calculate route
5. pay travel costs
6. update spatial state
7. detect overlapping NPCs
8. generate encounter opportunities
9. resolve interactions
10. update familiarity / relationships / memories
11. relationships may generate invitations or visits
12. continue simulation
```

Movement should remain event-driven rather than frame-driven.

---

# 17. Data Direction

Potential spatial persistence:

```text
locations
roads
agent_positions
travel_events
encounters
```

Do not create every table immediately.

The minimum world may begin with:

```text
locations
roads
current agent location
travel events
```

Spatial state must remain reproducible under deterministic seeds.

---

# 18. Design Laws

1. Relationships require causal exposure.
2. Physical geography is part of the simulation, not merely the renderer.
3. Locations are nodes; routes are weighted graph paths.
4. NPC movement follows needs, goals, obligations, resources, and energy.
5. Randomness selects among plausible possibilities; it does not create impossible contact.
6. Co-location creates exposure, not guaranteed interaction.
7. Familiarity normally precedes meaningful relationships.
8. Relationships alter future movement and exposure.
9. Physical and social energy remain separate.
10. Technology changes exposure topology.
11. The map may remain fixed while simulation seeds vary.
12. Simulation movement is event-driven; visual movement is interpolation.
13. Avoid pedestrian physics until scientifically necessary.
14. The spatial layer must remain lightweight, offline, explainable, and renderer-independent.

---

# Canonical Phase 4 Pattern

```text
SPACE
= fixed weighted graph

LOCATION
= node + coordinates + function

ROAD
= edge + travel cost

MOBILITY
= needs + goals + obligations + habits
  constrained by time + money + physical energy

ROUTE
= lowest perceived cost path

POSITION
= node OR edge + progress

EXPOSURE
= shared physical or virtual context

INTERACTION
= exposure
  × willingness
  × context
  × social energy
  × history
  + uncertainty

RELATIONSHIP
= accumulated meaningful interactions

SOCIAL GRAPH
= historical consequence of movement and interaction

TECHNOLOGY
= changes who can be exposed to whom

VISUALIZATION
= graph + routes + interpolated NPC points
```

---

## Updated Vision

**The Playing God now has a causal physical layer beneath its social layer.**

NPCs do not merely exist inside abstract relationships. They occupy places, choose destinations, spend time and energy travelling, cross paths, miss one another, repeatedly encounter familiar people, deliberately visit relationships, and eventually gain remote exposure through communication technology.

The world does not need to look like a city-building game.

It only needs enough spatial structure that the system can answer:

```text
Where was this NPC?
Why did they go there?
Which route did they take?
Who could they have encountered?
Who did they actually interact with?
How did that interaction become part of their life history?
```

**Geography creates exposure. Exposure creates interaction. Interaction creates social history.**
