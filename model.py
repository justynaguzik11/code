from dataclasses import dataclass
from datetime import date
from typing import Optional, NewType


Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)


@dataclass(frozen=True)
class OrderLine:
    orderid: Reference
    sku: Sku
    qty: Quantity


class Batch:
    def __init__(self, ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()  # type: Set[OrderLine]

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        allocated_qty = 0
        for order_line in self._allocations:
            allocated_qty += order_line.qty
        return allocated_qty

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine):
        return True if self.sku == line.sku and self.available_quantity >= line.qty else False