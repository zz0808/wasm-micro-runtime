#!/usr/bin/env python3
"""
获取指定测试文件的当前覆盖率

用法:
    python3 get_current_coverage.py <test_file.cc>

示例:
    python3 get_current_coverage.py smart-tests/aot-1/enhanced_aot_runtime_test.cc

输出:
    Lines: 2.5% (708/28308)
    Functions: 4.2% (80/1895)
"""

import subprocess
import sys
import re
from pathlib import Path


def get_module_name(test_file: str) -> str:
    """从测试文件路径提取模块名"""
    # smart-tests/aot-1/test.cc → aot-1
    parts = Path(test_file).parts
    for i, part in enumerate(parts):
        if part == 'smart-tests' and i + 1 < len(parts):
            return parts[i + 1]
    return None


def get_test_suite_name(test_file: str) -> str:
    """从测试文件提取测试 suite 名称（用于 ctest 过滤）"""
    # 从文件中提取 TEST_F(SuiteName, ...) 的 SuiteName
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        match = re.search(r'TEST_F\s*\(\s*(\w+)\s*,', content)
        if match:
            return match.group(1)
    except:
        pass
    
    # 回退：从文件名推断
    basename = Path(test_file).stem
    parts = basename.split('_')
    return ''.join(word.capitalize() for word in parts)


def run_command(cmd: str, verbose: bool = False) -> tuple[int, str]:
    """执行命令并返回 (返回码, 输出)"""
    if verbose:
        print(f"[CMD] {cmd}", file=sys.stderr)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if verbose and output.strip():
        print(f"[OUTPUT] {output[:500]}", file=sys.stderr)
    return result.returncode, output


def get_coverage(test_file: str, verbose: bool = False) -> dict:
    """获取指定测试文件的覆盖率"""
    module_name = get_module_name(test_file)
    if not module_name:
        print(f"错误: 无法从路径提取模块名: {test_file}", file=sys.stderr)
        sys.exit(1)
    
    suite_name = get_test_suite_name(test_file)
    build_dir = f"build/smart-tests/{module_name}"
    
    if verbose:
        print(f"[INFO] module_name: {module_name}", file=sys.stderr)
        print(f"[INFO] suite_name: {suite_name}", file=sys.stderr)
        print(f"[INFO] build_dir: {build_dir}", file=sys.stderr)
    
    # 1. 清理之前的覆盖率数据
    run_command(f"find {build_dir} -name '*.gcda' -delete 2>/dev/null", verbose)
    
    # 2. 只运行指定测试文件的测试（通过 suite 名称过滤）
    ret, output = run_command(f"ctest --test-dir {build_dir} -R '{suite_name}' --output-on-failure 2>&1", verbose)
    if verbose:
        print(f"[INFO] ctest return code: {ret}", file=sys.stderr)
    if ret != 0:
        print(f"警告: 部分测试失败", file=sys.stderr)
    
    # 3. 收集覆盖率
    run_command(f"lcov --capture --directory {build_dir} --output-file coverage.all.info 2>&1", verbose)
    run_command(f"lcov --extract coverage.all.info '*/core/iwasm/*' '*/core/shared/*' --output-file coverage.info 2>&1", verbose)
    
    # 4. 获取覆盖率摘要
    ret, summary = run_command("lcov --summary coverage.info 2>&1", verbose)
    
    if verbose:
        print(f"[INFO] lcov summary:\n{summary}", file=sys.stderr)
    
    # 5. 解析覆盖率
    # 格式: lines......: 2.8% (795 of 28308 lines)
    lines_match = re.search(r'lines\.+:\s*([\d.]+)%\s*\((\d+)\s+of\s+(\d+)', summary)
    funcs_match = re.search(r'functions\.+:\s*([\d.]+)%\s*\((\d+)\s+of\s+(\d+)', summary)
    
    result = {
        'lines_percent': 0.0,
        'lines_covered': 0,
        'lines_total': 0,
        'functions_percent': 0.0,
        'functions_covered': 0,
        'functions_total': 0,
    }
    
    if lines_match:
        result['lines_percent'] = float(lines_match.group(1))
        result['lines_covered'] = int(lines_match.group(2))
        result['lines_total'] = int(lines_match.group(3))
    
    if funcs_match:
        result['functions_percent'] = float(funcs_match.group(1))
        result['functions_covered'] = int(funcs_match.group(2))
        result['functions_total'] = int(funcs_match.group(3))
    
    return result


def main():
    if len(sys.argv) < 2:
        print("用法: python3 get_current_coverage.py <test_file.cc> [-v]")
        print("示例: python3 get_current_coverage.py smart-tests/aot-1/enhanced_aot_runtime_test.cc")
        print("      python3 get_current_coverage.py smart-tests/aot-1/enhanced_aot_runtime_test.cc -v  # verbose模式")
        sys.exit(1)
    
    test_file = sys.argv[1]
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    if not Path(test_file).exists():
        print(f"错误: 文件不存在: {test_file}", file=sys.stderr)
        sys.exit(1)
    
    coverage = get_coverage(test_file, verbose)
    
    print(f"Lines: {coverage['lines_percent']}% ({coverage['lines_covered']}/{coverage['lines_total']})")
    print(f"Functions: {coverage['functions_percent']}% ({coverage['functions_covered']}/{coverage['functions_total']})")


if __name__ == '__main__':
    main()
