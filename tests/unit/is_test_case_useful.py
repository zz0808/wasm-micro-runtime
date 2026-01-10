#!/usr/bin/env python3
"""
检查某个测试用例是否对覆盖率有贡献（相对于同一测试文件的其他测试）

用法:
    python3 is_test_case_useful.py <test_file.cc> <test_case_name>

示例:
    python3 is_test_case_useful.py smart-tests/aot-1/enhanced_aot_runtime_test.cc \
        EnhancedAotRuntimeTest.aot_resolve_import_func_Success

输出 (有用):
    ✅ USEFUL: Test case contributes to coverage
    New lines covered: 15
    Coverage change: +0.05%

输出 (无用):
    ❌ NOT USEFUL: Test case does not contribute to coverage
    New lines covered: 0
    Coverage change: 0%
"""

import subprocess
import sys
import re
from pathlib import Path


def get_module_name(test_file: str) -> str:
    """从测试文件路径提取模块名"""
    parts = Path(test_file).parts
    for i, part in enumerate(parts):
        if part == 'smart-tests' and i + 1 < len(parts):
            return parts[i + 1]
    return None


def get_suite_name_from_test_case(test_case: str) -> str:
    """从测试用例名称提取 suite 名称"""
    # EnhancedAotRuntimeTest.aot_memory_init_xxx → EnhancedAotRuntimeTest
    if '.' in test_case:
        return test_case.split('.')[0]
    return test_case


def run_command(cmd: str) -> tuple[int, str]:
    """执行命令并返回 (返回码, 输出)"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def get_covered_lines(coverage_file: str) -> set[tuple[str, int]]:
    """从 coverage.info 提取已覆盖的行 (文件, 行号)"""
    covered = set()
    current_file = None
    
    try:
        with open(coverage_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('SF:'):
                    current_file = line[3:]
                elif line.startswith('DA:') and current_file:
                    parts = line[3:].split(',')
                    if len(parts) >= 2 and int(parts[1]) > 0:
                        covered.add((current_file, int(parts[0])))
    except FileNotFoundError:
        pass
    
    return covered


def run_tests_except_one(module_name: str, suite_name: str, exclude_test: str) -> set[tuple[str, int]]:
    """运行该测试文件中除指定测试外的所有测试，返回覆盖的行"""
    build_dir = f"build/smart-tests/{module_name}"
    
    # 清理覆盖率数据
    run_command(f"find {build_dir} -name '*.gcda' -delete 2>/dev/null")
    
    # 只运行该 suite 的测试，但排除指定的测试
    # ctest -R "SuiteName" -E "^SuiteName\.TestName$"
    # 注意：只需要转义点号，不要用 re.escape（会产生双反斜杠问题）
    exclude_pattern = exclude_test.replace('.', r'\.')
    run_command(f"ctest --test-dir {build_dir} -R '{suite_name}' -E '^{exclude_pattern}$' --output-on-failure 2>&1")
    
    # 收集覆盖率
    run_command(f"lcov --capture --directory {build_dir} --output-file coverage.without.info 2>&1")
    run_command(f"lcov --extract coverage.without.info '*/core/iwasm/*' '*/core/shared/*' --output-file coverage.without.filtered.info 2>&1")
    
    return get_covered_lines("coverage.without.filtered.info")


def run_all_tests_in_file(module_name: str, suite_name: str) -> set[tuple[str, int]]:
    """运行该测试文件的所有测试，返回覆盖的行"""
    build_dir = f"build/smart-tests/{module_name}"
    
    # 清理覆盖率数据
    run_command(f"find {build_dir} -name '*.gcda' -delete 2>/dev/null")
    
    # 只运行该 suite 的测试
    run_command(f"ctest --test-dir {build_dir} -R '{suite_name}' --output-on-failure 2>&1")
    
    # 收集覆盖率
    run_command(f"lcov --capture --directory {build_dir} --output-file coverage.all.info 2>&1")
    run_command(f"lcov --extract coverage.all.info '*/core/iwasm/*' '*/core/shared/*' --output-file coverage.all.filtered.info 2>&1")
    
    return get_covered_lines("coverage.all.filtered.info")


def check_test_usefulness(test_file: str, test_case: str) -> dict:
    """检查测试用例是否有用（相对于同一文件的其他测试）"""
    module_name = get_module_name(test_file)
    if not module_name:
        print(f"错误: 无法从路径提取模块名: {test_file}", file=sys.stderr)
        sys.exit(1)
    
    suite_name = get_suite_name_from_test_case(test_case)
    
    # 获取该测试文件所有测试的覆盖行
    all_covered = run_all_tests_in_file(module_name, suite_name)
    
    # 获取排除该测试后的覆盖行
    without_covered = run_tests_except_one(module_name, suite_name, test_case)
    
    # 计算该测试独有贡献的行
    unique_lines = all_covered - without_covered
    
    result = {
        'useful': len(unique_lines) > 0,
        'new_lines': len(unique_lines),
        'total_lines': len(all_covered),
        'without_lines': len(without_covered),
    }
    
    if result['total_lines'] > 0:
        result['change_percent'] = (len(unique_lines) / result['total_lines']) * 100
    else:
        result['change_percent'] = 0.0
    
    return result


def main():
    if len(sys.argv) != 3:
        print("用法: python3 is_test_case_useful.py <test_file.cc> <test_case_name>")
        print("示例: python3 is_test_case_useful.py smart-tests/aot-1/test.cc SuiteName.TestName")
        sys.exit(1)
    
    test_file = sys.argv[1]
    test_case = sys.argv[2]
    
    if not Path(test_file).exists():
        print(f"错误: 文件不存在: {test_file}", file=sys.stderr)
        sys.exit(1)
    
    result = check_test_usefulness(test_file, test_case)
    
    if result['useful']:
        print(f"✅ USEFUL: Test case contributes to coverage")
        print(f"New lines covered: {result['new_lines']}")
        print(f"Coverage change: +{result['change_percent']:.2f}%")
        sys.exit(0)
    else:
        print(f"❌ NOT USEFUL: Test case does not contribute to coverage")
        print(f"New lines covered: 0")
        print(f"Coverage change: 0%")
        sys.exit(1)


if __name__ == '__main__':
    main()
