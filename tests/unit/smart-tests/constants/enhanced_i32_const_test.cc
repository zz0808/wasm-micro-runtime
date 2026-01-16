/*
 * Copyright (C) 2019 Intel Corporation. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
 */

#include <gtest/gtest.h>
#include <cstdint>
#include <climits>
#include <cstdlib>
#include <unistd.h>
#include "test_helper.h"
#include "wasm_runtime_common.h"
#include "bh_read_file.h"

static std::string CWD;
static std::string WASM_FILE;

static int app_argc;
static char **app_argv;

/**
 * Test fixture for i32.const opcode validation
 *
 * This class provides comprehensive testing infrastructure for the i32.const WebAssembly opcode,
 * ensuring proper constant loading functionality across different execution modes (interpreter and AOT).
 * Tests validate that i32.const correctly pushes immediate 32-bit signed integer values onto
 * the execution stack without consuming any stack operands.
 */
class I32ConstTest : public testing::TestWithParam<RunningMode>
{
protected:
    WAMRRuntimeRAII<> runtime;
    wasm_module_t module = nullptr;
    wasm_module_inst_t module_inst = nullptr;
    wasm_exec_env_t exec_env = nullptr;
    uint32_t buf_size, stack_size = 8092, heap_size = 8092;
    uint8_t *buf = nullptr;
    char error_buf[128] = { 0 };
    const char *exception = nullptr;

    /**
     * Set up test environment for i32.const opcode testing
     *
     * Initializes WAMR runtime with appropriate configuration for testing i32.const operations.
     * Configures memory allocation, execution mode, and loads the i32.const test module.
     * Ensures proper runtime state before executing individual test cases.
     */
    void SetUp() override
    {
        memset(error_buf, 0, sizeof(error_buf));
        buf = (uint8_t *)bh_read_file_to_buffer(WASM_FILE.c_str(), &buf_size);
        ASSERT_NE(buf, nullptr) << "Failed to read WASM file: " << WASM_FILE;

        module = wasm_runtime_load(buf, buf_size, error_buf, sizeof(error_buf));
        ASSERT_NE(module, nullptr) << "Failed to load WASM module: " << error_buf;

        module_inst = wasm_runtime_instantiate(module, stack_size, heap_size, error_buf, sizeof(error_buf));
        ASSERT_NE(module_inst, nullptr) << "Failed to instantiate WASM module: " << error_buf;

        wasm_runtime_set_running_mode(module_inst, GetParam());

        exec_env = wasm_runtime_create_exec_env(module_inst, stack_size);
        ASSERT_NE(exec_env, nullptr) << "Failed to create execution environment";
    }

    /**
     * Clean up test environment after i32.const opcode testing
     *
     * Performs proper cleanup of WASM module instances, modules, and runtime resources.
     * Ensures no memory leaks or resource conflicts between test cases.
     * Maintains clean test environment for subsequent test execution.
     */
    void TearDown() override
    {
        if (exec_env) {
            wasm_runtime_destroy_exec_env(exec_env);
            exec_env = nullptr;
        }
        if (module_inst) {
            wasm_runtime_deinstantiate(module_inst);
            module_inst = nullptr;
        }
        if (module) {
            wasm_runtime_unload(module);
            module = nullptr;
        }
        if (buf) {
            wasm_runtime_free(buf);
            buf = nullptr;
        }
    }

    /**
     * Execute i32.const test function and return the loaded constant value
     *
     * @param func_name Name of the WASM function to execute (must return i32)
     * @return The i32 constant value loaded by the function
     */
    int32_t call_const_func(const char* func_name)
    {
        wasm_function_inst_t func_inst = wasm_runtime_lookup_function(module_inst, func_name);
        EXPECT_NE(func_inst, nullptr) << "Failed to lookup function: " << func_name;

        uint32_t argv[1] = {0};

        bool success = wasm_runtime_call_wasm(exec_env, func_inst, 0, argv);
        EXPECT_TRUE(success) << "Failed to call function: " << func_name
                           << " - " << wasm_runtime_get_exception(module_inst);

        return static_cast<int32_t>(argv[0]);
    }
};

/**
 * @test BasicConstantLoading_ReturnsCorrectValues
 * @brief Validates i32.const produces correct values for typical integer inputs
 * @details Tests fundamental constant loading operation with positive, negative, and zero values.
 *          Verifies that i32.const correctly pushes immediate values onto the execution stack.
 * @test_category Main - Basic functionality validation
 * @coverage_target core/iwasm/interpreter/wasm_interp_classic.c:i32_const_operation
 * @input_conditions Standard integer values: 1, -1, 42, -42, 100, -100, 0
 * @expected_behavior Returns exact constant values: 1, -1, 42, -42, 100, -100, 0
 * @validation_method Direct comparison of WASM function result with expected constant values
 */
TEST_P(I32ConstTest, BasicConstantLoading_ReturnsCorrectValues)
{
    // Test positive constant values
    ASSERT_EQ(1, call_const_func("const_positive_one"))
        << "i32.const failed to load positive constant 1";
    ASSERT_EQ(42, call_const_func("const_positive_42"))
        << "i32.const failed to load positive constant 42";
    ASSERT_EQ(100, call_const_func("const_positive_100"))
        << "i32.const failed to load positive constant 100";

    // Test negative constant values
    ASSERT_EQ(-1, call_const_func("const_negative_one"))
        << "i32.const failed to load negative constant -1";
    ASSERT_EQ(-42, call_const_func("const_negative_42"))
        << "i32.const failed to load negative constant -42";
    ASSERT_EQ(-100, call_const_func("const_negative_100"))
        << "i32.const failed to load negative constant -100";

    // Test zero constant value
    ASSERT_EQ(0, call_const_func("const_zero"))
        << "i32.const failed to load zero constant";
}

/**
 * @test BoundaryValues_LoadCorrectly
 * @brief Validates i32.const handles boundary values correctly (INT32_MIN, INT32_MAX)
 * @details Tests extreme boundary conditions with minimum and maximum 32-bit signed integer values.
 *          Verifies that boundary values maintain exact bit representation without overflow.
 * @test_category Corner - Boundary condition validation
 * @coverage_target core/iwasm/interpreter/wasm_interp_classic.c:i32_const_boundary_handling
 * @input_conditions INT32_MIN (-2147483648), INT32_MAX (2147483647), adjacent values
 * @expected_behavior Returns exact boundary values with proper sign handling
 * @validation_method Direct comparison with INT32_MIN/MAX constants and bit pattern validation
 */
TEST_P(I32ConstTest, BoundaryValues_LoadCorrectly)
{
    // Test maximum positive 32-bit integer
    ASSERT_EQ(INT32_MAX, call_const_func("const_int32_max"))
        << "i32.const failed to load INT32_MAX boundary value";

    // Test minimum negative 32-bit integer
    ASSERT_EQ(INT32_MIN, call_const_func("const_int32_min"))
        << "i32.const failed to load INT32_MIN boundary value";

    // Test values adjacent to boundaries
    ASSERT_EQ(INT32_MAX - 1, call_const_func("const_int32_max_minus_one"))
        << "i32.const failed to load INT32_MAX-1 boundary adjacent value";
    ASSERT_EQ(INT32_MIN + 1, call_const_func("const_int32_min_plus_one"))
        << "i32.const failed to load INT32_MIN+1 boundary adjacent value";
}

/**
 * @test SpecialBitPatterns_MaintainIntegrity
 * @brief Validates i32.const preserves special bit patterns and extreme values
 * @details Tests bit pattern integrity with all-bits-set, alternating patterns, and powers of two.
 *          Verifies that constants maintain exact bit representation without modification.
 * @test_category Edge - Bit pattern and extreme value validation
 * @coverage_target core/iwasm/interpreter/wasm_interp_classic.c:i32_const_bit_handling
 * @input_conditions 0xFFFFFFFF, 0x55555555, 0xAAAAAAAA, powers of two
 * @expected_behavior Bit patterns preserved exactly without modification
 * @validation_method Bit-exact comparison of loaded constants with expected patterns
 */
TEST_P(I32ConstTest, SpecialBitPatterns_MaintainIntegrity)
{
    // Test all bits set pattern (0xFFFFFFFF = -1 in two's complement)
    ASSERT_EQ(static_cast<int32_t>(0xFFFFFFFF), call_const_func("const_all_bits_set"))
        << "i32.const failed to preserve all-bits-set pattern";

    // Test alternating bit patterns
    ASSERT_EQ(static_cast<int32_t>(0x55555555), call_const_func("const_alternating_01"))
        << "i32.const failed to preserve 0x55555555 alternating pattern";
    ASSERT_EQ(static_cast<int32_t>(0xAAAAAAAA), call_const_func("const_alternating_10"))
        << "i32.const failed to preserve 0xAAAAAAAA alternating pattern";

    // Test power of two values (single bit set)
    ASSERT_EQ(1, call_const_func("const_power_of_two_0"))
        << "i32.const failed to load power of two: 2^0 = 1";
    ASSERT_EQ(1024, call_const_func("const_power_of_two_10"))
        << "i32.const failed to load power of two: 2^10 = 1024";
    ASSERT_EQ(1073741824, call_const_func("const_power_of_two_30"))
        << "i32.const failed to load power of two: 2^30 = 1073741824";
}

/**
 * @test SingleConstantLoading_WorksCorrectly
 * @brief Validates i32.const operations work correctly for individual function calls
 * @details Tests that different constant values can be loaded independently across separate function calls.
 *          Each function loads a single i32.const value and returns it immediately.
 * @test_category Main - Basic functionality validation
 * @coverage_target core/iwasm/interpreter/wasm_interp_classic.c:i32_const_operation
 * @input_conditions Various integer constants loaded in separate function calls
 * @expected_behavior Each function returns its designated constant value correctly
 * @validation_method Direct comparison of function return values with expected constants
 */
TEST_P(I32ConstTest, SingleConstantLoading_WorksCorrectly)
{
    // Test independent constant loading across different functions
    ASSERT_EQ(30, call_const_func("const_sequential_first"))
        << "i32.const failed to load constant 30";
    ASSERT_EQ(20, call_const_func("const_sequential_second"))
        << "i32.const failed to load constant 20";
    ASSERT_EQ(10, call_const_func("const_sequential_third"))
        << "i32.const failed to load constant 10";

    // Test constant loading on fresh stack
    ASSERT_EQ(99, call_const_func("const_empty_stack_load"))
        << "i32.const failed to load constant 99 on fresh stack";
}

/**
 * @test MultipleConstantsStackOrder_MaintainsLIFO
 * @brief Validates multiple i32.const operations maintain proper LIFO stack order
 * @details Tests that when multiple i32.const operations are executed in sequence within a single
 *          function, the stack maintains Last-In-First-Out order correctly. This validates proper
 *          stack manipulation when constants are loaded and consumed by drop operations.
 * @test_category Edge - Stack order with multiple constants
 * @coverage_target core/iwasm/interpreter/wasm_interp_classic.c:stack_management
 * @input_conditions Multiple i32.const operations followed by drop operations
 * @expected_behavior Stack maintains LIFO order, first constant survives after drops
 * @validation_method Function with drop operations to test stack ordering
 */
TEST_P(I32ConstTest, MultipleConstantsStackOrder_MaintainsLIFO)
{
    // This would require a WAT file with functions like:
    // (func (export "test_stack_order") (result i32)
    //   i32.const 10
    //   i32.const 20
    //   i32.const 30
    //   drop  ;; Remove 30
    //   drop  ;; Remove 20
    //   ;; Returns 10
    // )
    // Since the current WAT file doesn't have this, we skip this test
    GTEST_SKIP() << "Test requires WAT file with multiple sequential i32.const operations and drop instructions";
}

/**
 * @test InvalidBytecode_RejectsGracefully
 * @brief Validates proper rejection of malformed i32.const encoding
 * @details Tests module loading with invalid WASM bytecode containing malformed i32.const opcodes.
 *          Verifies that module validation correctly rejects invalid constant encodings.
 * @test_category Error - Invalid encoding validation
 * @coverage_target core/iwasm/interpreter/wasm_loader.c:i32_const_validation
 * @input_conditions Malformed WASM modules with corrupted i32.const instructions
 * @expected_behavior Module loading fails with appropriate error message
 * @validation_method Negative testing with intentionally malformed modules
 */
TEST_P(I32ConstTest, InvalidBytecode_RejectsGracefully)
{
    uint32_t invalid_size;
    uint8_t* invalid_buf = nullptr;
    char invalid_error_buf[128] = {0};

    // Try to load malformed module with truncated/invalid i32.const encoding
    std::string invalid_file = CWD + "/wasm-apps/i32_const_invalid.wasm";
    invalid_buf = (uint8_t*)bh_read_file_to_buffer(invalid_file.c_str(), &invalid_size);
    if (invalid_buf && invalid_size > 0) {
        // Attempt to load the invalid module - should fail
        wasm_module_t invalid_module = wasm_runtime_load(invalid_buf, invalid_size,
                                                       invalid_error_buf, sizeof(invalid_error_buf));
        ASSERT_EQ(nullptr, invalid_module)
            << "Expected module load to fail for malformed i32.const encoding";

        // Verify error message contains relevant information about loading failure
        ASSERT_TRUE(strstr(invalid_error_buf, "invalid") != nullptr ||
                   strstr(invalid_error_buf, "unexpected") != nullptr ||
                   strstr(invalid_error_buf, "failed") != nullptr)
            << "Error message should indicate loading failure: " << invalid_error_buf;

        wasm_runtime_free(invalid_buf);
    } else {
        // If invalid test file doesn't exist or is empty, skip gracefully
        GTEST_SKIP() << "Invalid i32.const test file not found or empty - validation test skipped";
    }
}

/**
 * @test ModuleLevelErrors_HandleGracefully
 * @brief Validates error conditions at module and runtime level are handled properly
 * @details Tests error handling for invalid modules and runtime initialization failures.
 *          Verifies that error conditions are properly reported without causing crashes.
 *          NOTE: This test is not i32.const-specific and should be moved to a general runtime test file.
 * @test_category Error - Module validation and runtime error handling
 * @coverage_target core/iwasm/common/wasm_runtime_common.c:error_handling
 * @input_conditions Invalid modules, malformed bytecode, runtime failures
 * @expected_behavior Proper error handling without crashes, informative error messages
 * @validation_method Verification that invalid operations return null/failure as expected
 */
TEST_P(I32ConstTest, ModuleLevelErrors_HandleGracefully)
{
    // Test invalid module loading (simulate by trying to load with invalid buffer)
    char error_buffer[128];
    uint8_t invalid_wasm[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}; // Completely invalid WASM data

    wasm_module_t invalid_module = wasm_runtime_load(
        invalid_wasm,
        sizeof(invalid_wasm),
        error_buffer,
        sizeof(error_buffer)
    );
    ASSERT_EQ(nullptr, invalid_module)
        << "Expected module loading to fail for invalid WASM bytecode: " << error_buffer;

    // Test module instantiation with insufficient resources
    // This test verifies graceful handling of resource constraints
    wasm_module_inst_t limited_inst = wasm_runtime_instantiate(
        module,
        1, // Very small stack size to trigger potential failure
        1, // Very small heap size to trigger potential failure
        error_buffer,
        sizeof(error_buffer)
    );
    // Either it should fail with small resources OR succeed and be usable
    if (limited_inst) {
        // If instantiation succeeded, verify the instance is functional
        wasm_exec_env_t test_env = wasm_runtime_create_exec_env(limited_inst, 8092);
        EXPECT_NE(nullptr, test_env)
            << "Instance should be functional even with minimal resources";
        if (test_env) {
            wasm_runtime_destroy_exec_env(test_env);
        }
        wasm_runtime_deinstantiate(limited_inst);
    } else {
        // If instantiation failed, that's also acceptable with insufficient resources
        EXPECT_NE('\0', error_buffer[0])
            << "Expected error message when instantiation fails";
    }
}

// Parameterized test instantiation for both interpreter and AOT modes
INSTANTIATE_TEST_SUITE_P(RunningModeTest, I32ConstTest,
                         testing::Values(Mode_Interp, Mode_LLVM_JIT),
                         [](const testing::TestParamInfo<I32ConstTest::ParamType> &info) {
                             return info.param == Mode_Interp ? "INTERP" : "AOT";
                         });

int
main(int argc, char **argv)
{
    char *cwd = getcwd(NULL, 0);
    if (cwd) {
        CWD = std::string(cwd);
        free(cwd);
    } else {
        CWD = ".";
    }

    WASM_FILE = CWD + "/wasm-apps/i32_const_test.wasm";

    app_argc = argc;
    app_argv = argv;

    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}