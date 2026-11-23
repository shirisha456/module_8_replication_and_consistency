import contextlib
import io
import unittest

from replication_simulation import Client, ReplicatedInventory


def quiet(fn, *args):
    """Run fn without printing to the console during tests."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


class TestReplicationSimulation(unittest.TestCase):
    def setUp(self):
        self.system = ReplicatedInventory()
        self.client = Client(self.system)

    def test_initial_state(self):
        self.assertEqual(self.system.primary.stock, 10)
        self.assertEqual(self.system.secondary.stock, 10)
        self.assertIsNot(self.system.primary, self.system.secondary)

    def test_write_goes_to_primary_first(self):
        quiet(self.client.write, 8)
        self.assertEqual(self.system.primary.stock, 8)
        self.assertEqual(self.system.secondary.stock, 10)
        self.assertEqual(self.system.pending_updates, [8])

    def test_normal_replication(self):
        quiet(self.client.write, 8)
        quiet(self.system.replicate)
        self.assertEqual(self.system.secondary.stock, 8)
        self.assertTrue(self.system.is_converged())

    def test_paused_replication_causes_stale_read(self):
        quiet(self.system.pause_replication)
        quiet(self.client.write, 9)
        quiet(self.system.replicate)
        self.assertEqual(quiet(self.client.read, "primary"), 9)
        self.assertEqual(quiet(self.client.read, "secondary"), 10)
        self.assertEqual(self.system.pending_updates, [9])
        self.assertFalse(self.system.is_converged())

    def test_resume_replication_converges(self):
        quiet(self.system.pause_replication)
        quiet(self.client.write, 9)
        quiet(self.system.resume_replication)
        self.assertEqual(self.system.primary.stock, 9)
        self.assertEqual(self.system.secondary.stock, 9)
        self.assertEqual(self.system.pending_updates, [])
        self.assertTrue(self.system.is_converged())


if __name__ == "__main__":
    unittest.main()
