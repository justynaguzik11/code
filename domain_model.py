from dataclasses import dataclass
from typing import List
from datetime import date


@dataclass
class OrderLine:
    sku: str
    quantity: int



@dataclass
class SkuLines:
    lines: List[OrderLine]

    @property
    def skus(self):
        return {l.sku for l in self.lines}

    @property
    def quantities(self):
        return {l.sku: l.quantity for l in self.lines}




@dataclass
class Order(SkuLines):

    def allocate(self, stock, shipments):
        self.allocation = Allocation.for_order(self, stock, shipments)
        self.allocation.apply()


@dataclass
class Stock(SkuLines):

    def can_allocate(self, line: OrderLine):
        return line.sku in self.skus and self.quantities[line.sku] > line.quantity

    def allocate(self, sku, quantity):
        for line in self.lines:
            if line.sku == sku:
                line.quantity -= quantity
                return
        raise Exception(f'sku {sku} not found in stock skus ({self.skus})')


@dataclass
class Shipment(Stock):
    eta: date = None

    def __lt__(self, other):
        return self.eta < other.eta


@dataclass
class AllocationLine:
    sku: str
    quantity: int
    source: Stock


@dataclass
class Allocation:
    lines: List[AllocationLine]
    order: Order

    @property
    def skus(self):
        return set(l.sku for l in self.lines)

    @property
    def sources(self):
        return {l.sku: l.source for l in self.lines}

    @staticmethod
    def for_source(order: Order, source: Stock):
        return Allocation(lines=[
            AllocationLine(sku=line.sku, quantity=line.quantity, source=source)
            for line in order.lines
            if source.can_allocate(line)
        ], order=order)

    @staticmethod
    def for_order(order: Order, stock: Stock, shipments: List[Shipment]):
        split_allocation = Allocation(lines=[], order=order)
        for source in [stock] + sorted(shipments):
            source_allocation = Allocation.for_source(order, source)
            if source_allocation.is_complete:
                return source_allocation
            split_allocation.supplement_with(source_allocation)
        return split_allocation


    def supplement_with(self, other_allocation):
        self.lines.extend(
            l for l in other_allocation.lines if l.sku not in self.skus
        )

    @property
    def is_complete(self):
        return self.skus == self.order.skus

    def apply(self):
        for line in self.lines:
            line.source.allocate(line.sku, line.quantity)


