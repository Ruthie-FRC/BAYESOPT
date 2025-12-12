#!/usr/bin/env python3
"""
Performance benchmarking script for BAYESOPT tuner.

This script measures the performance of key operations to help identify
bottlenecks and validate optimizations.

Run with: python benchmark_performance.py
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bayesopt.tuner.config import TunerConfig, CoefficientConfig
from bayesopt.tuner.optimizer import BayesianOptimizer
from bayesopt.tuner.logger import TunerLogger
from bayesopt.tuner.nt_interface import ShotData


def benchmark_logger_writes():
    """Benchmark logger write performance."""
    print("\n=== Logger Write Performance ===")
    
    config = TunerConfig()
    logger = TunerLogger(config)
    
    # Create sample shot data
    shot_data = ShotData(
        hit=True,
        distance=5.0,
        angle=0.5,
        velocity=15.0,
        timestamp=time.time(),
        yaw=0.1,
        target_height=2.0,
        launch_height=1.0,
        drag_coefficient=0.47,
        air_density=1.225,
        projectile_mass=0.27,
        projectile_area=0.0143,
    )
    
    all_coefficients = {
        'kDragCoefficient': 0.47,
        'kAirDensity': 1.225,
        'kProjectileMass': 0.27,
    }
    
    # Benchmark logging performance
    num_iterations = 1000
    start = time.perf_counter()
    
    for i in range(num_iterations):
        logger.log_shot(
            coefficient_name='kDragCoefficient',
            coefficient_value=0.47,
            step_size=0.01,
            iteration=i,
            shot_data=shot_data,
            nt_connected=True,
            match_mode=False,
            tuner_status='Benchmarking',
            all_coefficient_values=all_coefficients,
        )
    
    elapsed = time.perf_counter() - start
    
    logger.close()
    
    print(f"Total time: {elapsed:.3f}s")
    print(f"Per-shot time: {elapsed/num_iterations*1000:.3f}ms")
    print(f"Shots per second: {num_iterations/elapsed:.1f}")


def benchmark_optimizer_convergence():
    """Benchmark optimizer convergence checking."""
    print("\n=== Optimizer Convergence Check Performance ===")
    
    config = TunerConfig()
    coeff_config = CoefficientConfig(
        name='kDragCoefficient',
        nt_key='/FiringSolver/Coefficients/kDragCoefficient',
        min_value=0.3,
        max_value=0.6,
        default_value=0.47,
        initial_step_size=0.01,
        step_decay_rate=0.95,
        is_integer=False,
        enabled=True,
    )
    
    optimizer = BayesianOptimizer(coeff_config, config)
    
    # Add some history to make convergence checks meaningful
    for i in range(10):
        optimizer.report_result(0.47 + i * 0.001, i % 2 == 0)
    
    # Benchmark convergence checking
    num_iterations = 10000
    start = time.perf_counter()
    
    for _ in range(num_iterations):
        optimizer.is_converged()
    
    elapsed = time.perf_counter() - start
    
    print(f"Total time: {elapsed:.3f}s")
    print(f"Per-check time: {elapsed/num_iterations*1000:.3f}ms")
    print(f"Checks per second: {num_iterations/elapsed:.1f}")


def benchmark_dict_operations():
    """Benchmark dictionary operations used in hot paths."""
    print("\n=== Dictionary Operations Performance ===")
    
    # Create sample coefficient dictionary
    coefficients = {
        f'coeff_{i}': float(i) * 0.1 
        for i in range(10)
    }
    
    # Benchmark dict.copy()
    num_iterations = 100000
    start = time.perf_counter()
    for _ in range(num_iterations):
        _ = coefficients.copy()
    elapsed_copy = time.perf_counter() - start
    
    # Benchmark dict() constructor
    start = time.perf_counter()
    for _ in range(num_iterations):
        _ = dict(coefficients)
    elapsed_dict = time.perf_counter() - start
    
    print(f".copy() method:")
    print(f"  Total time: {elapsed_copy:.3f}s")
    print(f"  Per-operation: {elapsed_copy/num_iterations*1000000:.3f}µs")
    
    print(f"dict() constructor:")
    print(f"  Total time: {elapsed_dict:.3f}s")
    print(f"  Per-operation: {elapsed_dict/num_iterations*1000000:.3f}µs")
    
    speedup = (elapsed_copy - elapsed_dict) / elapsed_copy * 100
    print(f"Speedup: {speedup:.1f}%")


def benchmark_attribute_access():
    """Benchmark different attribute access patterns."""
    print("\n=== Attribute Access Performance ===")
    
    # Create sample object
    class SampleObject:
        def __init__(self):
            self.attr1 = 1.0
            self.attr2 = 2.0
    
    obj = SampleObject()
    
    num_iterations = 100000
    
    # Benchmark hasattr + getattr
    start = time.perf_counter()
    for _ in range(num_iterations):
        if hasattr(obj, 'attr1'):
            _ = obj.attr1
        if hasattr(obj, 'attr3'):  # Missing attribute
            _ = obj.attr3
    elapsed_hasattr = time.perf_counter() - start
    
    # Benchmark getattr with default
    start = time.perf_counter()
    for _ in range(num_iterations):
        _ = getattr(obj, 'attr1', 0.0)
        _ = getattr(obj, 'attr3', 0.0)  # Missing attribute
    elapsed_getattr = time.perf_counter() - start
    
    print(f"hasattr() + getattr():")
    print(f"  Total time: {elapsed_hasattr:.3f}s")
    print(f"  Per-operation: {elapsed_hasattr/num_iterations*1000000:.3f}µs")
    
    print(f"getattr() with default:")
    print(f"  Total time: {elapsed_getattr:.3f}s")
    print(f"  Per-operation: {elapsed_getattr/num_iterations*1000000:.3f}µs")
    
    speedup = (elapsed_hasattr - elapsed_getattr) / elapsed_hasattr * 100
    print(f"Speedup: {speedup:.1f}%")


def benchmark_string_formatting():
    """Benchmark string formatting patterns."""
    print("\n=== String Formatting Performance ===")
    
    # Create sample data
    data = {f'key_{i}': float(i) * 0.123456 for i in range(10)}
    
    num_iterations = 10000
    
    # Benchmark list comprehension
    start = time.perf_counter()
    for _ in range(num_iterations):
        _ = "; ".join([f"{k}={v:.6f}" for k, v in data.items()])
    elapsed_list = time.perf_counter() - start
    
    # Benchmark generator expression
    start = time.perf_counter()
    for _ in range(num_iterations):
        _ = "; ".join(f"{k}={v:.6f}" for k, v in data.items())
    elapsed_gen = time.perf_counter() - start
    
    print(f"List comprehension:")
    print(f"  Total time: {elapsed_list:.3f}s")
    print(f"  Per-operation: {elapsed_list/num_iterations*1000:.3f}ms")
    
    print(f"Generator expression:")
    print(f"  Total time: {elapsed_gen:.3f}s")
    print(f"  Per-operation: {elapsed_gen/num_iterations*1000:.3f}ms")
    
    speedup = (elapsed_list - elapsed_gen) / elapsed_list * 100
    print(f"Speedup: {speedup:.1f}%")


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("BAYESOPT Performance Benchmarks")
    print("=" * 60)
    
    try:
        benchmark_logger_writes()
        benchmark_optimizer_convergence()
        benchmark_dict_operations()
        benchmark_attribute_access()
        benchmark_string_formatting()
    except Exception as e:
        print(f"\nError running benchmarks: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    print("Benchmarks complete!")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
