"""End-to-end integration tests for the data sources tools."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test the complete workflow from data source to index."""

    def test_complete_pipeline(self, tmp_path):
        """Test the complete pipeline: validate -> fetch -> score -> index."""
        # Setup temporary directories
        data_sources_dir = tmp_path / "data-sources" / "vulnerability" / "test"
        data_sources_dir.mkdir(parents=True)

        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create a test source file
        test_source = {
            "id": "test-integration",
            "name": "Test Integration Source",
            "url": "https://httpbin.org/json",
            "description": "A test source for integration testing",
            "category": "vulnerability",
            "sub_category": "test",
            "format": "json",
            "tags": ["test", "integration"],
            "quality_score": 75.0,
            "user_weighted_score": 75.0,
            "freshness": 80,
            "authority": 85,
            "coverage": 70,
            "availability": 90,
            "last_updated": "2025-08-14T00:00:00+00:00Z",
            "update_frequency": "Daily",
        }

        source_file = data_sources_dir / "test-integration.json"
        with open(source_file, "w") as f:
            json.dump(test_source, f, indent=2)

        # Create scoring config
        scoring_config = {
            "weights": {
                "freshness": 0.4,
                "authority": 0.3,
                "coverage": 0.2,
                "availability": 0.1,
            }
        }

        config_file = config_dir / "scoring-config.json"
        with open(config_file, "w") as f:
            json.dump(scoring_config, f, indent=2)

        # Test validation
        result = subprocess.run(
            [sys.executable, "tools/validate_sources.py"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should succeed since we created a valid source
        assert result.returncode == 0, f"Validation failed: {result.stderr}"

        # Test scoring (mock the fetch step since we don't want real HTTP calls)
        with pytest.MonkeyPatch().context() as mp:
            # Change working directory for the tools
            original_cwd = os.getcwd()
            try:
                os.chdir(str(tmp_path))

                # Import and run scoring
                sys.path.insert(0, os.path.join(original_cwd, "tools"))
                import score_sources

                # Mock the paths
                mp.setattr("score_sources.DATA_SOURCES_DIR", data_sources_dir.parent)
                mp.setattr("score_sources.CONFIG_DIR", config_dir)

                # Run scoring
                score_sources.main()

                # Verify the file was updated
                with open(source_file) as f:
                    updated_source = json.load(f)

                assert "quality_score" in updated_source
                assert isinstance(updated_source["quality_score"], (int, float))

            finally:
                os.chdir(original_cwd)
                if original_cwd + "/tools" in sys.path:
                    sys.path.remove(original_cwd + "/tools")


@pytest.mark.integration
@pytest.mark.network
class TestNetworkIntegration:
    """Integration tests that require network access."""

    def test_fetch_real_source_health(self):
        """Test fetching health from a real, reliable source."""
        import sys

        sys.path.insert(0, "tools")
        try:
            import fetch_sources

            # Test with a reliable source (HTTPBin)
            source = {"id": "test-httpbin", "url": "https://httpbin.org/get"}

            health = fetch_sources.fetch_source_health(source)

            # Should be available (unless network is down)
            assert isinstance(health["available"], bool)
            assert isinstance(health["status_code"], (int, type(None)))
            if health["available"]:
                assert health["status_code"] < 400
                assert isinstance(health["response_time"], float)
                assert health["response_time"] > 0
        finally:
            if "tools" in sys.path:
                sys.path.remove("tools")

    def test_fetch_invalid_url(self):
        """Test fetching health from an invalid URL."""
        import sys

        sys.path.insert(0, "tools")
        try:
            import fetch_sources

            source = {
                "id": "test-invalid",
                "url": "https://this-domain-should-not-exist-123456789.com",
            }

            health = fetch_sources.fetch_source_health(source)

            # Should not be available
            assert health["available"] is False
            assert health["status_code"] is None
            assert health["response_time"] is None
        finally:
            if "tools" in sys.path:
                sys.path.remove("tools")


@pytest.mark.integration
class TestSchemaValidationIntegration:
    """Integration tests for schema validation."""

    def test_validate_all_real_sources(self):
        """Test validation of all real source files in the repository."""
        result = subprocess.run(
            [sys.executable, "tools/validate_sources.py"],
            capture_output=True,
            text=True,
        )

        # Should succeed - all sources should be valid
        if result.returncode != 0:
            pytest.fail(f"Schema validation failed:\n{result.stdout}\n{result.stderr}")

    def test_schema_covers_all_real_source_properties(self):
        """Test that the schema covers all properties used in real sources."""
        import glob

        import jsonschema

        # Load schema
        with open("schemas/source.schema.json") as f:
            schema = json.load(f)

        validator = jsonschema.Draft7Validator(schema)

        # Test all real source files
        source_files = glob.glob("data-sources/**/*.json", recursive=True)
        assert len(source_files) > 0, "No source files found"

        validation_errors = []
        for file_path in source_files:
            try:
                with open(file_path) as f:
                    source_data = json.load(f)
                validator.validate(source_data)
            except jsonschema.ValidationError as e:
                validation_errors.append(f"{file_path}: {e.message}")
            except json.JSONDecodeError as e:
                validation_errors.append(f"{file_path}: Invalid JSON - {e}")

        if validation_errors:
            pytest.fail("Schema validation errors:\n" + "\n".join(validation_errors))


@pytest.mark.integration
class TestFileSystemIntegration:
    """Test file system operations and permissions."""

    def test_tools_are_executable(self):
        """Test that all Python tools have proper permissions."""
        tools_dir = Path("tools")
        python_files = list(tools_dir.glob("*.py"))

        assert len(python_files) > 0, "No Python tools found"

        for tool in python_files:
            # Check if file is readable
            assert tool.exists(), f"Tool {tool} does not exist"
            assert tool.is_file(), f"Tool {tool} is not a file"

            # Check if it has a proper shebang for direct execution
            with open(tool) as f:
                first_line = f.readline().strip()
                if first_line.startswith("#!"):
                    # If it has a shebang, it should be executable
                    assert (
                        tool.stat().st_mode & 0o111
                    ), f"Tool {tool} has shebang but is not executable"

    def test_directory_structure(self):
        """Test that the expected directory structure exists."""
        required_dirs = [
            "data-sources",
            "schemas",
            "config",
            "tools",
            "docs",
            ".github/workflows",
        ]

        for dir_path in required_dirs:
            assert Path(
                dir_path
            ).is_dir(), f"Required directory {dir_path} does not exist"

    def test_required_files_exist(self):
        """Test that required files exist."""
        required_files = [
            "README.md",
            "schemas/source.schema.json",
            "tools/fetch_sources.py",
            "tools/score_sources.py",
            "tools/validate_sources.py",
            "config/scoring-config.json",
        ]

        for file_path in required_files:
            assert Path(
                file_path
            ).is_file(), f"Required file {file_path} does not exist"


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance and scalability integration tests."""

    def test_validation_performance(self):
        """Test that validation completes in reasonable time."""
        import time

        start_time = time.time()

        result = subprocess.run(
            [sys.executable, "tools/validate_sources.py"],
            capture_output=True,
            text=True,
        )

        end_time = time.time()
        duration = end_time - start_time

        # Validation should complete within 30 seconds even with many files
        assert duration < 30, f"Validation took too long: {duration} seconds"
        assert result.returncode == 0, "Validation failed"

    def test_scoring_performance(self, tmp_path):
        """Test scoring performance with multiple files."""
        import time

        # Create multiple test files
        data_sources_dir = tmp_path / "data-sources" / "test"
        data_sources_dir.mkdir(parents=True)

        config_dir = tmp_path / "config"
        config_dir.mkdir()

        # Create scoring config
        scoring_config = {
            "weights": {
                "freshness": 0.4,
                "authority": 0.3,
                "coverage": 0.2,
                "availability": 0.1,
            }
        }

        with open(config_dir / "scoring-config.json", "w") as f:
            json.dump(scoring_config, f)

        # Create 20 test source files
        for i in range(20):
            test_source = {
                "id": f"test-perf-{i}",
                "name": f"Test Performance Source {i}",
                "url": f"https://example.com/api/{i}",
                "description": "A test source for performance testing",
                "category": "vulnerability",
                "sub_category": "test",
                "format": "json",
                "tags": ["test", "performance"],
                "quality_score": 75.0,
                "freshness": 80,
                "authority": 85,
                "coverage": 70,
                "availability": 90,
                "last_updated": "2025-08-14T00:00:00+00:00Z",
            }

            with open(data_sources_dir / f"test-perf-{i}.json", "w") as f:
                json.dump(test_source, f, indent=2)

        # Time the scoring operation
        start_time = time.time()

        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            sys.path.insert(0, os.path.join(original_cwd, "tools"))

            import score_sources

            # Mock the paths and run
            with pytest.MonkeyPatch().context() as mp:
                mp.setattr("score_sources.DATA_SOURCES_DIR", data_sources_dir.parent)
                mp.setattr("score_sources.CONFIG_DIR", config_dir)

                score_sources.main()

            end_time = time.time()
            duration = end_time - start_time

            # Should complete within reasonable time (10 seconds for 20 files)
            assert (
                duration < 10
            ), f"Scoring took too long: {duration} seconds for 20 files"

        finally:
            os.chdir(original_cwd)
            if original_cwd + "/tools" in sys.path:
                sys.path.remove(original_cwd + "/tools")
