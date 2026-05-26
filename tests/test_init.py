from pathlib import Path

from click.testing import CliRunner

from leetpush.cli import main


def test_init_creates_expected_files(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--username", "test-user", "--repo", str(tmp_path)])
    assert result.exit_code == 0, result.output

    assert (tmp_path / ".github" / "workflows" / "sync.yml").exists()
    assert (tmp_path / ".leetpush.yml").exists()
    assert (tmp_path / "solutions.json").exists()


def test_init_workflow_contains_username(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(main, ["init", "--username", "sahu-adarsh", "--repo", str(tmp_path)])

    workflow = (tmp_path / ".github" / "workflows" / "sync.yml").read_text()
    assert "username: sahu-adarsh" in workflow
    assert "secrets.LEETCODE_SESSION" in workflow
    assert "secrets.GITHUB_TOKEN" in workflow
    assert "adarshsahu1077/leetpush@v1" in workflow


def test_init_config_contains_username(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(main, ["init", "--username", "sahu-adarsh", "--repo", str(tmp_path)])

    config = (tmp_path / ".leetpush.yml").read_text()
    assert "username: sahu-adarsh" in config


def test_init_skips_existing_files(tmp_path: Path) -> None:
    runner = CliRunner()
    # First init
    runner.invoke(main, ["init", "--username", "user1", "--repo", str(tmp_path)])
    # Second init with different username — existing files should NOT be overwritten
    runner.invoke(main, ["init", "--username", "user2", "--repo", str(tmp_path)])

    workflow = (tmp_path / ".github" / "workflows" / "sync.yml").read_text()
    assert "username: user1" in workflow  # original username preserved
    assert "username: user2" not in workflow


def test_init_output_reports_created_files(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--username", "test-user", "--repo", str(tmp_path)])

    assert "Created:" in result.output
    assert "sync.yml" in result.output
    assert ".leetpush.yml" in result.output


def test_init_output_reports_skipped_on_rerun(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(main, ["init", "--username", "test-user", "--repo", str(tmp_path)])
    result = runner.invoke(main, ["init", "--username", "test-user", "--repo", str(tmp_path)])

    assert "Skipped" in result.output


def test_init_creates_target_dir_if_missing(tmp_path: Path) -> None:
    new_dir = tmp_path / "brand-new-repo"
    runner = CliRunner()
    result = runner.invoke(main, ["init", "--username", "test-user", "--repo", str(new_dir)])

    assert result.exit_code == 0
    assert new_dir.exists()
    assert (new_dir / ".leetpush.yml").exists()
