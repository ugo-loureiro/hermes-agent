"""Real rebuilt-summary preparation under the managed_workers opt-in."""

from tests.gateway.test_session_mutation_compress import run_compress_case


def test_managed_compress_rebuilt_preserves_configured_history_and_admission_owner(tmp_path):
    run_compress_case(tmp_path, "managed", False)
