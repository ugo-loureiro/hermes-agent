"""#111105: the profile re-scan watcher must rebuild adapters after a config.yaml replacement
that keeps mtime and size (``cp -p``, ``rsync -t``, a timestamp-pinning writer)."""
import os
import shutil
from unittest.mock import patch

import pytest

from gateway.run_profile_reconcile import profile_serve_signature


@pytest.mark.parametrize("name", ["config.yaml", ".env"])
def test_profile_serve_signature_changes_on_replacement_with_pinned_mtime(tmp_path, name):
    cfg = tmp_path / name
    cfg.write_text("x" * 64, encoding="utf-8")
    before = profile_serve_signature(tmp_path)
    assert profile_serve_signature(tmp_path) == before  # unchanged file: stable
    st = cfg.stat()
    other = tmp_path / "other"
    other.write_text("y" * 64, encoding="utf-8")
    shutil.copy2(other, cfg)
    os.utime(cfg, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert (cfg.stat().st_mtime_ns, cfg.stat().st_size) == (st.st_mtime_ns, st.st_size)
    # Model an in-place copy within one filesystem tick: EVERY stat field matches.
    real_stat = os.stat

    def pinned_stat(path, *args, **kwargs):
        return st if os.fspath(path) == str(cfg) else real_stat(path, *args, **kwargs)

    with patch("gateway.run_profile_reconcile.os.stat", side_effect=pinned_stat):
        after = profile_serve_signature(tmp_path)
        assert after != before
        assert profile_serve_signature(tmp_path) == after


def test_profile_signatures_keep_homes_and_file_lifecycle_isolated(tmp_path):
    homes = [tmp_path / name for name in ("a", "b")]
    for home, content in zip(homes, ("aaa", "bbb")):
        home.mkdir()
        (home / "config.yaml").write_text(content)
    a, b, a_again = [profile_serve_signature(home) for home in (homes[0], homes[1], homes[0])]
    assert a == a_again
    assert a != b
    env = homes[1] / ".env"
    env.write_text("TEST_VALUE=synthetic\n")
    assert profile_serve_signature(homes[1]) != b
    assert profile_serve_signature(homes[0]) == a
    env.unlink()
    assert profile_serve_signature(homes[1]) == b
