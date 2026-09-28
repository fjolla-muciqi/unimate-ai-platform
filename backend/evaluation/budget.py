"""Kufiri i shpenzimeve për thirrjet reale te Claude.

Vlerësimi ekzekutohet me kredit të kufizuar. `BudgetedClient`
mbështjell klientin e Anthropic, llogarit koston e çdo thirrjeje nga
`usage` dhe refuzon thirrjen e radhës sapo shuma arrin kufirin, në
vend që ta zbulojmë tejkalimin pas faturës.
"""

from dataclasses import dataclass, field
from types import SimpleNamespace


# USD për 1M tokena, `claude-sonnet-5` (çmimet e Anthropic API).
# Shkrimi në cache kushton 1.25x input-in, leximi 0.1x.
PRICES = {
    "claude-sonnet-5": {
        "input": 2.00,
        "cache_write": 2.50,
        "cache_read": 0.20,
        "output": 10.00,
    },
}


class BudgetExceeded(RuntimeError):
    """Thirrja e radhës do ta kalonte kufirin e shpenzimeve."""


def cost_of(usage, model: str) -> float:
    prices = PRICES[model]

    def tokens(name: str) -> int:
        return getattr(usage, name, 0) or 0

    return (
        tokens("input_tokens") * prices["input"]
        + tokens("cache_creation_input_tokens") * prices["cache_write"]
        + tokens("cache_read_input_tokens") * prices["cache_read"]
        + tokens("output_tokens") * prices["output"]
    ) / 1_000_000


@dataclass
class BudgetedClient:
    client: object
    model: str
    max_cost: float
    spent: float = 0.0
    calls: int = 0
    log: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.model not in PRICES:
            raise ValueError(
                f"Nuk ka çmim për modelin {self.model}; shtoje te PRICES."
            )

        # E njëjta formë si `anthropic.Anthropic().messages`, që kodi
        # i agjentëve ta përdorë pa ditur se ka një kufi sipër.
        self.messages = SimpleNamespace(
            create=self._wrap(self.client.messages.create),
            parse=self._wrap(self.client.messages.parse),
        )

    def _wrap(self, method):
        def call(**kwargs):
            if self.spent >= self.max_cost:
                raise BudgetExceeded(
                    f"U arrit kufiri {self.max_cost:.2f} $ "
                    f"(shpenzuar {self.spent:.4f} $)."
                )

            response = method(**kwargs)
            usage = getattr(response, "usage", None)
            cost = cost_of(usage, self.model) if usage is not None else 0.0

            self.spent += cost
            self.calls += 1
            self.log.append({"call": self.calls, "cost": round(cost, 6)})

            return response

        return call
