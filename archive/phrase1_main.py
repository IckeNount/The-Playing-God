from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

NAMES = ["Mira", "Noah", "Lina", "Ren", "Sora", "Kai", "Ari", "Niko", "Iris", "Theo"]
TRAITS = ("discipline", "sociability", "ambition", "risk_tolerance", "empathy")
SINS = ("pride", "greed", "lust", "envy", "gluttony", "wrath", "sloth")


def clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, x))


@dataclass
class Event:
    day: int
    kind: str
    description: str
    significance: float


@dataclass
class Agent:
    id: str
    name: str
    age: int
    traits: dict[str, float]
    sins: dict[str, float]
    money: float
    employed: bool
    salary: float
    job_level: int
    skill: float
    energy: float
    stress: float
    reputation: float
    goal: str = ""
    relationships: dict[str, float] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    actions: Counter = field(default_factory=Counter)

    def normalize(self) -> None:
        self.skill = clamp(self.skill)
        self.energy = clamp(self.energy)
        self.stress = clamp(self.stress)
        self.reputation = clamp(self.reputation, -1.0, 1.0)
        for other in self.relationships:
            self.relationships[other] = clamp(self.relationships[other], -1.0, 1.0)


class World:
    def __init__(self, seed: int = 1947, population: int = 10):
        self.seed = seed
        self.rng = random.Random(seed)
        self.day = 0
        self.agents = self._create_agents(population)
        self._create_relationships()

    def _create_agents(self, population: int) -> list[Agent]:
        people = []
        for i in range(population):
            traits = {k: round(self.rng.uniform(0.15, 0.85), 3) for k in TRAITS}
            sins = {k: round(self.rng.uniform(0.10, 0.90), 3) for k in SINS}
            employed = self.rng.random() < 0.70
            skill = self.rng.uniform(0.20, 0.60)
            level = self.rng.choice([1, 1, 1, 2]) if employed else 0
            salary = 22 + 7 * level + 8 * skill if employed else 0

            people.append(Agent(
                id=f"npc_{i+1:03d}",
                name=NAMES[i],
                age=self.rng.randint(20, 38),
                traits=traits,
                sins=sins,
                money=self.rng.uniform(120, 520),
                employed=employed,
                salary=salary,
                job_level=level,
                skill=skill,
                energy=self.rng.uniform(0.55, 0.95),
                stress=self.rng.uniform(0.10, 0.45),
                reputation=self.rng.uniform(-0.10, 0.20),
            ))
        return people

    def _create_relationships(self) -> None:
        for a in self.agents:
            for b in self.agents:
                if a.id != b.id:
                    a.relationships[b.id] = self.rng.uniform(-0.08, 0.08)

    def record(self, a: Agent, kind: str, description: str, significance: float) -> None:
        a.events.append(Event(self.day, kind, description, significance))

    def money_pressure(self, a: Agent) -> float:
        return clamp((260 - a.money) / 260)

    def belonging_need(self, a: Agent) -> float:
        positive_ties = [max(0, x) for x in a.relationships.values()]
        average = sum(positive_ties) / len(positive_ties)
        return clamp(0.55 - average)

    def status_need(self, a: Agent) -> float:
        current_status = 0.18 * a.job_level + 0.25 * max(0, a.reputation)
        return clamp(0.65 - current_status)

    def update_goal(self, a: Agent) -> None:
        if not a.employed:
            new_goal = "find_job"
        elif a.money < 180:
            new_goal = "build_savings"
        elif a.skill < 0.58:
            new_goal = "improve_skill"
        elif self.belonging_need(a) > 0.46:
            new_goal = "build_relationships"
        else:
            new_goal = "advance_career"

        if new_goal != a.goal:
            old = a.goal or "none"
            a.goal = new_goal
            self.record(a, "goal", f"Goal changed: {old} -> {new_goal}", 0.62)

    def scores(self, a: Agent) -> dict[str, float]:
        t, s = a.traits, a.sins
        money = self.money_pressure(a)
        belonging = self.belonging_need(a)
        status = self.status_need(a)
        tired = 1 - a.energy

        return {
            "work": (
                1.2*t["discipline"] + 0.7*t["ambition"] + 0.5*s["greed"]
                + money - s["sloth"] - 0.7*tired
            ) if a.employed else -99,
            "job_hunt": (
                1.3*t["ambition"] + 0.8*t["discipline"] + 1.2*money
                + 0.4*s["greed"] - 0.8*s["sloth"]
            ) if not a.employed else -99,
            "train": 1.0*t["ambition"] + 0.9*t["discipline"] + 0.7*status - 0.8*s["sloth"] - 0.5*tired,
            "socialize": 1.3*t["sociability"] + belonging + 0.35*s["lust"] - 0.5*tired - 0.3*a.stress,
            "help": 1.4*t["empathy"] + 0.5*belonging + 0.2*s["pride"] - 0.8*money - 0.4*tired,
            "compete": 0.9*t["ambition"] + 0.75*s["envy"] + 0.6*s["pride"] + 0.4*status - 0.7*t["empathy"] + 0.2*s["wrath"],
            "risky_move": 1.1*t["risk_tolerance"] + 0.9*s["greed"] + 0.6*money + 0.4*t["ambition"] - 0.5*t["discipline"],
            "rest": 1.5*tired + 1.1*a.stress + 0.45*s["sloth"] + 0.25*s["gluttony"],
        }

    def choose(self, a: Agent) -> str:
        available = [(name, score) for name, score in self.scores(a).items() if score > -50]
        peak = max(score for _, score in available)
        temperature = 0.75
        weights = [math.exp((score - peak) / temperature) for _, score in available]
        return self.rng.choices([name for name, _ in available], weights=weights, k=1)[0]

    def other_person(self, a: Agent) -> Agent:
        others = [b for b in self.agents if b.id != a.id]
        weights = [0.25 + abs(a.relationships[b.id]) for b in others]
        return self.rng.choices(others, weights=weights, k=1)[0]

    def act(self, a: Agent, action: str) -> None:
        a.actions[action] += 1

        if action == "work":
            a.money += a.salary * 0.25
            a.energy -= 0.11
            a.stress += 0.025 + 0.035*a.sins["wrath"]
            a.skill += 0.0025 * (0.5 + a.traits["discipline"])
            a.reputation += 0.002 * (a.traits["discipline"] - a.sins["sloth"])

            promotion = 0.0012 + 0.003*a.skill + 0.002*a.traits["ambition"] + 0.0015*max(0, a.reputation)
            fired = 0.0005 + 0.0018*a.stress + 0.0015*a.sins["wrath"] - 0.001*a.traits["discipline"]
            if self.rng.random() < max(0, promotion) and a.job_level < 5:
                a.job_level += 1
                a.salary *= 1.18
                a.reputation += 0.10
                self.record(a, "career", f"Promoted to job level {a.job_level}", 0.92)
            elif self.rng.random() < max(0, fired):
                a.employed = False
                a.job_level = 0
                a.salary = 0
                a.stress += 0.22
                self.record(a, "career", "Lost their job", 0.96)

        elif action == "job_hunt":
            a.money -= 4
            a.energy -= 0.07
            a.stress += 0.025
            chance = 0.04 + 0.14*a.skill + 0.05*max(0, a.reputation) + 0.04*a.traits["sociability"]
            if self.rng.random() < chance:
                a.employed = True
                a.job_level = 1
                a.salary = 24 + 9*a.skill + 4*a.reputation
                a.stress -= 0.15
                self.record(a, "career", f"Found a job paying {a.salary:.0f}/day", 0.94)

        elif action == "train":
            before = a.skill
            a.money -= 7
            a.energy -= 0.08
            a.stress += 0.015
            a.skill += 0.009 + 0.006*a.traits["discipline"]
            if before < 0.60 <= a.skill:
                self.record(a, "growth", "Reached skilled-worker level", 0.80)
            if before < 0.75 <= a.skill:
                self.record(a, "growth", "Reached expert-skill level", 0.86)

        elif action == "socialize":
            b = self.other_person(a)
            before = a.relationships[b.id]
            change = 0.06*a.traits["sociability"] + 0.05*a.traits["empathy"] - 0.05*a.sins["wrath"] - 0.03*a.sins["envy"] + self.rng.uniform(-0.055, 0.055)
            a.relationships[b.id] += change
            b.relationships[a.id] += change * self.rng.uniform(0.65, 1.05)
            a.money -= 5
            a.energy -= 0.06
            a.stress -= 0.035
            after = a.relationships[b.id]
            if before < 0.42 <= after:
                self.record(a, "relationship", f"Became close with {b.name}", 0.84)
            elif before > -0.42 >= after:
                self.record(a, "relationship", f"Relationship with {b.name} turned hostile", 0.86)

        elif action == "help":
            b = self.other_person(a)
            cost = min(10, max(2, a.money * 0.025))
            before = a.relationships[b.id]
            gain = 0.035 + 0.045*a.traits["empathy"]
            a.money -= cost
            b.money += cost * 0.65
            a.relationships[b.id] += gain
            b.relationships[a.id] += gain * 1.1
            a.reputation += 0.012
            a.energy -= 0.045
            if before < 0.42 <= a.relationships[b.id]:
                self.record(a, "relationship", f"Helping {b.name} created a close alliance", 0.84)

        elif action == "compete":
            b = self.other_person(a)
            edge = a.skill + 0.4*a.traits["ambition"] + self.rng.uniform(-0.35, 0.35) - (b.skill + 0.2*b.traits["ambition"])
            a.relationships[b.id] -= 0.025 + 0.035*a.sins["envy"]
            b.relationships[a.id] -= 0.020 + 0.025*b.sins["pride"]
            a.energy -= 0.07
            a.stress += 0.05
            if edge > 0:
                a.reputation += 0.025
                a.money += 12
                if edge > 0.48:
                    self.record(a, "status", f"Outperformed {b.name} in competition", 0.72)
            else:
                a.reputation -= 0.018
                a.stress += 0.035
                if edge < -0.48:
                    self.record(a, "status", f"Lost badly to {b.name} in competition", 0.72)

        elif action == "risky_move":
            a.energy -= 0.05
            chance = 0.28 + 0.24*a.traits["risk_tolerance"] + 0.18*a.skill - 0.10*a.stress
            if self.rng.random() < chance:
                gain = self.rng.uniform(25, 90) * (0.7 + a.sins["greed"])
                a.money += gain
                a.stress -= 0.025
                a.reputation += 0.01
                if gain > 110:
                    self.record(a, "fortune", f"A risky move paid off: +{gain:.0f}", 0.80)
            else:
                loss = self.rng.uniform(18, 65)
                a.money -= loss
                a.stress += 0.08
                if loss > 60:
                    self.record(a, "misfortune", f"A risky move failed: -{loss:.0f}", 0.78)

        elif action == "rest":
            a.money -= 3
            a.energy += 0.22
            a.stress -= 0.11

        a.normalize()

    def end_day(self, a: Agent) -> None:
        # Employment is a background condition. The chosen action is the person's
        # main discretionary focus that day, not literally their entire 24 hours.
        if a.employed:
            a.money += a.salary * 0.85
        a.money -= 24  # food, rent, transport, basic living

        if not a.employed:
            a.stress += 0.018 + 0.025*self.money_pressure(a)
        if a.money < 0:
            a.stress += 0.055
            a.reputation -= 0.006
        if a.money < -250 and not any(e.kind == "crisis" for e in a.events[-30:]):
            self.record(a, "crisis", "Entered severe debt", 0.90)

        # Small external shock. It is a world rule, not a story script.
        if a.employed and self.rng.random() < 0.0008:
            a.employed = False
            a.job_level = 0
            a.salary = 0
            a.stress += 0.20
            self.record(a, "career", "Lost job in workplace downsizing", 0.95)

        a.energy += 0.035
        a.stress -= 0.012
        a.normalize()
        self.update_goal(a)

    def run(self, days: int = 365) -> None:
        for day in range(1, days + 1):
            self.day = day
            order = self.agents[:]
            self.rng.shuffle(order)
            for a in order:
                self.update_goal(a)
                self.act(a, self.choose(a))
                self.end_day(a)
        for a in self.agents:
            a.age += days // 365

    def report(self) -> str:
        names = {a.id: a.name for a in self.agents}
        lines = [f"THE PLAYING GOD | seed={self.seed} | day={self.day}", "=" * 74]

        for a in self.agents:
            best = max(a.relationships.items(), key=lambda x: x[1])
            worst = min(a.relationships.items(), key=lambda x: x[1])
            major = [e for e in a.events if e.significance >= 0.78]
            major = sorted(major, key=lambda e: (e.significance, e.day), reverse=True)[:8]
            major = sorted(major, key=lambda e: e.day)
            behavior = ", ".join(f"{k}:{v}" for k, v in a.actions.most_common(3))

            lines += [
                "",
                f"{a.id} | {a.name} | age {a.age}",
                f"  job={'L'+str(a.job_level) if a.employed else 'unemployed'}  money={a.money:.0f}  skill={a.skill:.2f}  stress={a.stress:.2f}",
                f"  reputation={a.reputation:+.2f}  goal={a.goal}",
                f"  dominant behavior: {behavior}",
                f"  strongest tie: {names[best[0]]} {best[1]:+.2f} | weakest: {names[worst[0]]} {worst[1]:+.2f}",
                "  major life events:",
            ]
            if major:
                lines += [f"    day {e.day:03d} [{e.kind}] {e.description}" for e in major]
            else:
                lines.append("    none above threshold")

        return "\n".join(lines)

    def _agent_dict(self, a: Agent) -> dict:
        data = asdict(a)
        data["actions"] = dict(a.actions)
        return data

    def save(self) -> None:
        out = Path("tests/fixtures")
        out.mkdir(exist_ok=True)
        payload = {
            "seed": self.seed,
            "day": self.day,
            "agents": [self._agent_dict(a) for a in self.agents],
        }
        (out / f"phase1_seed_{self.seed}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        (out / f"report_{self.seed}.txt").write_text(self.report(), encoding="utf-8")


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1947
    world = World(seed=seed, population=10)
    world.run(365)
    world.save()
    print(world.report())
