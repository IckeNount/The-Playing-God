from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from playing_god.core.agent import Agent


@dataclass(frozen=True)
class EconomySnapshot:
    population: int
    employed_count: int
    unemployed_count: int
    employment_rate: float
    job_capacity: int
    vacancies: int
    total_agent_money: float
    median_agent_money: float
    negative_balance_count: int


@dataclass(frozen=True)
class EconomyState:
    """The world's finite shared supply of jobs."""

    job_capacity: int

    def __post_init__(self) -> None:
        if self.job_capacity < 0:
            raise ValueError("Job capacity cannot be negative")

    @classmethod
    def from_agents(
        cls,
        agents: Sequence[Agent],
    ) -> EconomyState:
        population = len(agents)
        employed_count = sum(agent.employed for agent in agents)
        baseline_capacity = (population * 7 + 5) // 10
        return cls(
            job_capacity=max(
                employed_count,
                baseline_capacity,
            )
        )

    def occupied_jobs(
        self,
        agents: Sequence[Agent],
    ) -> int:
        return sum(agent.employed for agent in agents)

    def vacancies(
        self,
        agents: Sequence[Agent],
    ) -> int:
        return self.job_capacity - self.occupied_jobs(agents)

    def snapshot(
        self,
        agents: Sequence[Agent],
    ) -> EconomySnapshot:
        population = len(agents)
        employed_count = self.occupied_jobs(agents)
        balances = [agent.money for agent in agents]

        return EconomySnapshot(
            population=population,
            employed_count=employed_count,
            unemployed_count=population - employed_count,
            employment_rate=(
                employed_count / population
                if population
                else 0.0
            ),
            job_capacity=self.job_capacity,
            vacancies=self.job_capacity - employed_count,
            total_agent_money=float(sum(balances)),
            median_agent_money=(
                float(median(balances))
                if balances
                else 0.0
            ),
            negative_balance_count=sum(
                balance < 0
                for balance in balances
            ),
        )
