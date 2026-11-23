"""
CMPE 273 - Module 8: Replication & Consistency

A tiny, deterministic, in-memory simulation of a replicated inventory:

    - 1 Primary replica   (accepts all writes)
    - 1 Secondary replica (receives updates via simulated async replication)
    - 1 Client            (writes to Primary, can read from either replica)

Replication is simulated with an explicit pending-updates queue on the Primary.
Pausing replication leaves updates in the queue, so the Secondary falls behind
(stale reads). Resuming replication drains the queue, so the replicas converge.

Run:
    python3 replication_simulation.py
"""

INITIAL_STOCK = 10


class Replica:
    """One copy of the inventory. Each replica owns its own separate state."""

    def __init__(self, name, stock):
        self.name = name
        self.stock = stock  # this replica's own copy of the value

    def read(self):
        return self.stock


class ReplicatedInventory:
    """Primary + Secondary with simulated asynchronous replication."""

    def __init__(self, initial_stock=INITIAL_STOCK):
        # Two separate Replica objects -> two separate copies of `stock`.
        self.primary = Replica("primary", initial_stock)
        self.secondary = Replica("secondary", initial_stock)

        # Updates written on the Primary that have not reached the Secondary yet.
        self.pending_updates = []
        self.replication_enabled = True

    # ---- writes (Primary only) -------------------------------------------
    def write(self, new_stock):
        """Write to the Primary first, then queue the update for replication."""
        self.primary.stock = new_stock
        print(f"replica=primary action=write stock={new_stock}")

        self.pending_updates.append(new_stock)
        print(f"replication=pending pending_updates={self.pending_updates}")

    # ---- replication control ---------------------------------------------
    def pause_replication(self):
        self.replication_enabled = False
        print("replication=paused")

    def resume_replication(self):
        self.replication_enabled = True
        print("replication=resumed")
        self.replicate()

    def replicate(self):
        """Apply pending updates to the Secondary, in order, if enabled."""
        if not self.replication_enabled:
            print(
                f"replication=paused secondary_not_updated "
                f"pending_updates={self.pending_updates}"
            )
            return

        while self.pending_updates:
            value = self.pending_updates.pop(0)
            old = self.secondary.stock
            self.secondary.stock = value
            print(f"replica=secondary action=replicated stock={old}->{value}")
        print(f"replication=complete pending_updates={self.pending_updates}")

    # ---- status ------------------------------------------------------------
    def is_converged(self):
        return self.primary.stock == self.secondary.stock and not self.pending_updates

    def print_status(self):
        print(
            f"primary={self.primary.stock} secondary={self.secondary.stock} "
            f"converged={self.is_converged()}"
        )


class Client:
    """Reads from a chosen replica and reports whether the read was stale."""

    def __init__(self, system):
        self.system = system

    def write(self, new_stock):
        self.system.write(new_stock)

    def read(self, replica_name):
        replica = self.system.primary if replica_name == "primary" else self.system.secondary
        value = replica.read()
        line = f"read_from={replica_name} stock={value}"
        if replica_name == "secondary":
            # Stale = Secondary returns something older than the Primary's latest.
            stale = value != self.system.primary.stock
            line += f" stale_read={stale}"
        print(line)
        return value


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------
def successful_replication_demo():
    print("=== Successful Replication Demo ===")
    system = ReplicatedInventory()
    client = Client(system)
    system.print_status()

    client.write(8)
    print("-- before replication is processed --")
    client.read("primary")
    client.read("secondary")

    system.replicate()
    print("-- after replication --")
    client.read("primary")
    client.read("secondary")
    system.print_status()
    print()


def stale_read_and_recovery_demo():
    # Fresh state: Primary = 10, Secondary = 10
    print("=== Stale Read Demo ===")
    system = ReplicatedInventory()
    client = Client(system)
    system.print_status()

    system.pause_replication()
    client.write(9)
    system.replicate()  # attempt replication while paused -> Secondary unchanged
    client.read("primary")
    client.read("secondary")
    system.print_status()
    print()

    print("=== Recovery and Convergence Demo ===")
    system.resume_replication()
    client.read("primary")
    client.read("secondary")
    system.print_status()
    print(f"replicas_converged={system.is_converged()}")


def main():
    successful_replication_demo()
    stale_read_and_recovery_demo()


if __name__ == "__main__":
    main()
