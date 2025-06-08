from pathlib import Path

from octopus.dsl.dsl_config import DslConfig
from octopus.orchestration.manager import TestManager


def main():
    default_config_path = Path(__file__).parent / "dsl" / "test_data" / "config_sample_v0.1.0.yaml"
    config = DslConfig.from_yaml_file(default_config_path)
    test_manager = TestManager(config)
    test_manager.start()
    test_manager.stop()


if __name__ == "__main__":
    main()
