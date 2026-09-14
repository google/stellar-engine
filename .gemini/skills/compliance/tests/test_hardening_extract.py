"""Hardening tests for :mod:`extract_system_data` external command execution."""

import os
import sys
import unittest
from pathlib import Path

skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root / "scripts"))

from extract_system_data import (  # noqa: E402
    MAX_SUBPROCESS_OUTPUT_BYTES,
    _sanitized_path_env,
    safe_run_command,
)


class TestHardeningExtract(unittest.TestCase):
    """Verifies the external command boundary in extract_system_data."""

    def test_oversize_output_is_rejected_not_truncated(self) -> None:
        """Oversize stdout must raise, never return a silently clipped payload.

        This helper feeds `terraform show -json` output into the inventory. A
        truncated payload would either fail to parse or, worse, parse as a smaller
        system boundary and under-report the accreditation scope, so the only safe
        response is to refuse the result outright.
        """
        oversize = MAX_SUBPROCESS_OUTPUT_BYTES + 1024
        cmd = [sys.executable, "-c", f"print('a' * {oversize})"]
        with self.assertRaises(MemoryError):
            safe_run_command(cmd, timeout=30)

    def test_output_under_the_bound_is_returned_intact(self) -> None:
        """Output within the budget must be returned byte-for-byte."""
        payload = "b" * 1024
        cmd = [sys.executable, "-c", f"print('{payload}')"]
        result = safe_run_command(cmd, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), payload)

    def test_caller_command_list_is_not_mutated(self) -> None:
        """Resolving the binary must not rewrite the caller's list in place."""
        cmd = ["echo", "hello"]
        original = list(cmd)
        safe_run_command(cmd, timeout=10)
        self.assertEqual(
            cmd,
            original,
            "safe_run_command must not mutate the caller's command vector",
        )

    def test_path_sanitization_keeps_command_runnable(self) -> None:
        """A sanitized PATH must still resolve genuine system binaries."""
        result = safe_run_command(["echo", "hello"], timeout=10)
        self.assertIn("hello", result.stdout)

    def test_sanitized_path_excludes_cwd_and_relative_entries(self) -> None:
        """The search path must exclude the CWD and any relative entry.

        A repository under analysis is untrusted input. If its directory stayed on
        PATH, a file named `terraform` committed to that repository could be
        executed in place of the real binary (CWE-426 untrusted search path).
        """
        cwd = str(Path.cwd().resolve())
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join([cwd, "relative/bin", "", "/usr/bin"])
        try:
            entries = _sanitized_path_env()["PATH"].split(os.pathsep)
        finally:
            os.environ["PATH"] = original_path

        self.assertNotIn(cwd, entries)
        self.assertNotIn("relative/bin", entries)
        self.assertNotIn("", entries)
        self.assertIn("/usr/bin", entries)

    def test_path_prefix_is_not_confused_with_parent_directory(self) -> None:
        """'/work' is a string prefix of '/workspace' but is not its parent.

        The previous implementation filtered with str.startswith, which would drop
        unrelated sibling directories whose names merely began with the CWD string.
        """
        original_path = os.environ.get("PATH", "")
        cwd = Path.cwd().resolve()
        sibling = str(cwd) + "-sibling-not-a-child"
        os.environ["PATH"] = os.pathsep.join([sibling, "/usr/bin"])
        try:
            entries = _sanitized_path_env()["PATH"].split(os.pathsep)
        finally:
            os.environ["PATH"] = original_path

        self.assertIn(
            sibling,
            entries,
            "A sibling directory sharing a name prefix must not be filtered out",
        )

    def test_empty_command_is_rejected(self) -> None:
        """An empty argument vector must fail closed."""
        with self.assertRaises(ValueError):
            safe_run_command([], timeout=5)

    def test_unresolvable_binary_raises_file_not_found(self) -> None:
        """A binary absent from the sanitized PATH must fail fast and loudly."""
        with self.assertRaises(FileNotFoundError):
            safe_run_command(["definitely-not-a-real-binary-xyz"], timeout=5)

    def test_negative_retries_rejected(self) -> None:
        """A nonsensical retry budget must be rejected rather than silently coerced."""
        with self.assertRaises(ValueError):
            safe_run_command(["echo", "hi"], timeout=5, retries=-1)


if __name__ == "__main__":
    unittest.main()
