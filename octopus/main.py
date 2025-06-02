from octopus.dsl.config import TestConfig
from octopus.orchestration.manager import TestManager


def main():
    config = TestConfig.from_yaml("config.yaml")
    test_manager = TestManager(config)
    test_manager.start()
    test_manager.stop()


if __name__ == "__main__":
    main()
