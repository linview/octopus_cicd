#!/usr/bin/env python3
"""
测试TestManager的功能
"""

from pathlib import Path

from octopus.dsl.dsl_config import DslConfig
from octopus.orchestration.manager import TestManager, create_test_manager_from_config


def test_manager_creation():
    """测试TestManager创建"""
    print("🔍 测试TestManager创建...")

    # 查找配置文件
    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        return False

    try:
        # 创建TestManager
        manager = create_test_manager_from_config(config_path)
        print(f"✅ TestManager创建成功，使用配置文件: {config_path}")

        # 获取执行状态
        status = manager.get_execution_status()
        print("📊 执行状态:")
        print(f"   总节点数: {status['total_nodes']}")
        print(f"   执行计划: {status['execution_plan']}")
        print(f"   状态统计: {status['summary']}")

        return True

    except Exception as e:
        print(f"❌ TestManager创建失败: {e}")
        return False


def test_dependency_analysis():
    """测试依赖关系分析"""
    print("\n🔍 测试依赖关系分析...")

    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        return False

    try:
        # 创建TestManager
        manager = create_test_manager_from_config(config_path)

        # 分析依赖关系
        status = manager.get_execution_status()

        print("📋 节点依赖关系:")
        for node_name, node_info in status["node_status"].items():
            print(f"   {node_name} ({node_info['type']}):")
            print(f"     状态: {node_info['status']}")
            print(f"     依赖: {node_info['dependencies']}")
            print(f"     被依赖: {node_info['dependents']}")
            print()

        return True

    except Exception as e:
        print(f"❌ 依赖关系分析失败: {e}")
        return False


def test_execution_plan():
    """测试执行计划生成"""
    print("\n🔍 测试执行计划生成...")

    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        return False

    try:
        # 创建TestManager
        manager = create_test_manager_from_config(config_path)

        # 获取执行计划
        execution_plan = manager.execution_plan
        print(f"📊 执行计划: {execution_plan}")

        # 验证执行顺序
        print("🔍 验证执行顺序:")
        for i, node_name in enumerate(execution_plan, 1):
            node = manager.execution_nodes[node_name]
            print(f"   {i}. {node_name} ({node.node_type})")

            # 检查依赖是否在前面
            dependencies = manager._get_node_dependencies(node_name)
            for dep in dependencies:
                dep_index = execution_plan.index(dep) if dep in execution_plan else -1
                if dep_index >= i:
                    print(f"      ⚠️  警告: 依赖 {dep} 在执行计划中的位置 ({dep_index + 1}) 晚于当前节点 ({i})")
                else:
                    print(f"      ✅ 依赖 {dep} 正确地在位置 {dep_index + 1}")

        return True

    except Exception as e:
        print(f"❌ 执行计划生成失败: {e}")
        return False


def test_dsl_config_integration():
    """测试与DslConfig的集成"""
    print("\n🔍 测试与DslConfig的集成...")

    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        return False

    try:
        # 直接加载DslConfig
        config = DslConfig.from_yaml_file(Path(config_path))
        print(f"✅ DslConfig加载成功: {config.name}")

        # 创建TestManager
        manager = TestManager(config)
        print("✅ TestManager创建成功")

        # 比较执行计划
        dsl_execution_plan = config._dag_manger.generate_execution_plan()
        manager_execution_plan = manager.execution_plan

        print(f"📊 DslConfig执行计划: {dsl_execution_plan}")
        print(f"📊 TestManager执行计划: {manager_execution_plan}")

        if dsl_execution_plan == manager_execution_plan:
            print("✅ 执行计划一致")
        else:
            print("⚠️  执行计划不一致")

        return True

    except Exception as e:
        print(f"❌ DslConfig集成测试失败: {e}")
        return False


def test_dag_functionality():
    """测试DAG功能"""
    print("\n🔍 测试DAG功能...")

    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        return False

    try:
        # 创建TestManager
        manager = create_test_manager_from_config(config_path)

        # 获取DAG信息
        dag_info = manager.get_dag_info()
        print("📊 DAG信息:")
        print(f"   是否有效DAG: {dag_info['is_valid_dag']}")
        print(f"   总节点数: {dag_info['total_nodes']}")
        print(f"   总边数: {dag_info['total_edges']}")
        print(f"   拓扑排序: {dag_info['topological_order']}")
        print(f"   执行计划: {dag_info['execution_plan']}")

        # 验证DAG有效性
        if dag_info["is_valid_dag"]:
            print("✅ DAG验证通过")
        else:
            print("❌ DAG验证失败")
            return False

        # 验证拓扑排序和执行计划的一致性
        if set(dag_info["topological_order"]) == set(dag_info["execution_plan"]):
            print("✅ 拓扑排序和执行计划节点一致")
        else:
            print("⚠️  拓扑排序和执行计划节点不一致")

        return True

    except Exception as e:
        print(f"❌ DAG功能测试失败: {e}")
        return False


def test_dependency_consistency():
    """测试依赖关系一致性"""
    print("\n🔍 测试依赖关系一致性...")

    config_paths = [
        "octopus/dsl/test_data/config_sample_v0.1.0.yaml",
        "test_data/config_sample_v0.1.0.yaml",
        "config_sample_v0.1.0.yaml",
    ]

    config_path = None
    for path in config_paths:
        if Path(path).exists():
            config_path = path
            break

    if not config_path:
        print("❌ 未找到配置文件")
        return False

    try:
        # 创建TestManager
        manager = create_test_manager_from_config(config_path)

        # 获取DslConfig的DAG管理器
        dag_manager = manager.config._dag_manger
        dag_graph = dag_manager._gen_subgraph()

        print("🔍 验证依赖关系一致性:")

        # 检查每个节点的依赖关系
        for node_name in manager.execution_nodes.keys():
            # 从DAG图获取依赖
            dag_dependencies = list(dag_graph.predecessors(node_name))

            # 从TestManager获取依赖
            manager_dependencies = manager._get_node_dependencies(node_name)

            if set(dag_dependencies) == set(manager_dependencies):
                print(f"   ✅ {node_name}: 依赖关系一致")
            else:
                print(f"   ❌ {node_name}: 依赖关系不一致")
                print(f"      DAG依赖: {dag_dependencies}")
                print(f"      Manager依赖: {manager_dependencies}")
                return False

        return True

    except Exception as e:
        print(f"❌ 依赖关系一致性测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试TestManager功能")
    print("=" * 60)

    tests = [
        test_manager_creation,
        test_dependency_analysis,
        test_execution_plan,
        test_dsl_config_integration,
        test_dag_functionality,
        test_dependency_consistency,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")


if __name__ == "__main__":
    main()
