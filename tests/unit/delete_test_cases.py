#!/usr/bin/env python3
"""
删除指定的测试用例脚本（简化版，供 Agent 使用）

用法:
    python3 delete_test_cases.py <test_file.cc> <redundant_check.md>

示例:
    python3 delete_test_cases.py smart-tests/aot-1/enhanced_aot_runtime_test.cc \
        /tmp/enhanced_aot_runtime_test_redundant_check.md
"""

import re
import sys
from pathlib import Path


def parse_redundant_check_file(filepath: str) -> list[str]:
    """从 check_redundant_tests.sh 生成的 redundant_check.md 文件中解析冗余测试列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配格式: - ❌ SuiteName.TestName
    pattern = r'-\s*❌\s*(\S+)'
    return re.findall(pattern, content)


def find_test_case_range(content: str, suite_name: str, test_name: str) -> tuple[int, int] | None:
    """查找测试用例的起始和结束位置，返回 (start_pos, end_pos) 或 None"""
    # 匹配 TEST_F, TEST, TEST_P
    for prefix in ['TEST_F', 'TEST', 'TEST_P']:
        pattern = rf'{prefix}\s*\(\s*{re.escape(suite_name)}\s*,\s*{re.escape(test_name)}\s*\)'
        match = re.search(pattern, content)
        if match:
            break
    else:
        return None
    
    start_pos = match.start()
    
    # 找到函数体的开始 {
    brace_start = content.find('{', match.end())
    if brace_start == -1:
        return None
    
    # 匹配大括号找到函数体结束
    brace_count = 0
    pos = brace_start
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    prev_char = ''
    
    while pos < len(content):
        char = content[pos]
        
        if prev_char == '\\':
            prev_char = ''
            pos += 1
            continue
        
        if in_line_comment:
            if char == '\n':
                in_line_comment = False
            pos += 1
            prev_char = char
            continue
        
        if in_block_comment:
            if char == '/' and prev_char == '*':
                in_block_comment = False
            pos += 1
            prev_char = char
            continue
        
        if char == '/' and pos + 1 < len(content):
            next_char = content[pos + 1]
            if next_char == '/' and not in_string and not in_char:
                in_line_comment = True
                pos += 2
                prev_char = next_char
                continue
            elif next_char == '*' and not in_string and not in_char:
                in_block_comment = True
                pos += 2
                prev_char = next_char
                continue
        
        if char == '"' and not in_char:
            in_string = not in_string
        if char == "'" and not in_string:
            in_char = not in_char
        
        if not in_string and not in_char:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = pos + 1
                    # 跳过后面的空行
                    while end_pos < len(content) and content[end_pos] in ' \t':
                        end_pos += 1
                    if end_pos < len(content) and content[end_pos] == '\n':
                        end_pos += 1
                    return (start_pos, end_pos)
        
        prev_char = char
        pos += 1
    
    return None


def delete_test_cases(test_file: str, redundant_file: str) -> None:
    """从测试文件中删除冗余测试用例"""
    # 解析冗余测试列表
    tests_to_delete = parse_redundant_check_file(redundant_file)
    
    if not tests_to_delete:
        print("没有需要删除的测试用例")
        return
    
    print(f"准备删除 {len(tests_to_delete)} 个测试用例")
    
    # 读取测试文件
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    deleted = []
    not_found = []
    
    for test_spec in tests_to_delete:
        # 解析 SuiteName.TestName
        if '.' in test_spec:
            suite_name, test_name = test_spec.split('.', 1)
        else:
            not_found.append(test_spec)
            continue
        
        # 查找并删除
        range_result = find_test_case_range(content, suite_name, test_name)
        if range_result is None:
            not_found.append(test_spec)
            continue
        
        start_pos, end_pos = range_result
        content = content[:start_pos] + content[end_pos:]
        deleted.append(test_spec)
    
    # 清理多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 写回文件
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 输出结果
    print(f"\n✅ 成功删除 {len(deleted)} 个测试用例:")
    for test in deleted:
        print(f"   - {test}")
    
    if not_found:
        print(f"\n⚠️ 未找到 {len(not_found)} 个测试用例:")
        for test in not_found:
            print(f"   - {test}")


def main():
    if len(sys.argv) != 3:
        print("用法: python3 delete_test_cases.py <test_file.cc> <redundant_check.md>")
        print("示例: python3 delete_test_cases.py smart-tests/aot-1/test.cc /tmp/test_redundant_check.md")
        sys.exit(1)
    
    test_file = sys.argv[1]
    redundant_file = sys.argv[2]
    
    if not Path(test_file).exists():
        print(f"错误: 测试文件不存在: {test_file}")
        sys.exit(1)
    
    if not Path(redundant_file).exists():
        print(f"错误: 冗余检查文件不存在: {redundant_file}")
        sys.exit(1)
    
    delete_test_cases(test_file, redundant_file)


if __name__ == '__main__':
    main()
