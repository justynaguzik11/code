import pytest
import model
import repository
import services


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMINOUS-MIRROR", 10)
    batch = model.Batch("b1", "OMINOUS-MIRROR", 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    batch_to_add = model.Batch("b1", "BLUE-PLINTH", 100, eta=None)

    services.add_batch(batch_to_add, repo, session)
    batchref = services.allocate(line, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90

    services.deallocate(line, batchref, repo, session)
    assert batch.available_quantity == 100


# def test_deallocate_decrements_correct_quantity():
#     line = model.OrderLine("o1", "RED-LAMP", 10)
#     batch1 = model.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
#     batch2 = model.Batch("b2", "RED-LAMP", 100, eta=None)
#     repo = FakeRepository([batch1, batch2])
#     session = FakeSession()
#
#     batchref = services.allocate(line, repo, session)
#     batch = repo.get(reference="b2")
#     assert batch.available_quantity == 90
#
#     services.deallocate(line, batchref, repo, session)
#
#     assert batch.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    line = model.OrderLine("o1", "RED-LAMP", 10)
    batch1 = model.Batch("b1", "RED-LAMP", 100, eta=None)
    repo = FakeRepository([batch1])
    session = FakeSession()
    with pytest.raises(model.OrderLineNotInAllocations, match="b1"):
        services.deallocate(line, "b1", repo, session)



