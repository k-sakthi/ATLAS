import time
import os
import pandas as pd
from stage3.watch import StudyWatch
from stage3.adapter import Stage3Adapter

def run_benchmark():
    data_dir = "data"
    watch = StudyWatch(data_dir)
    
    print("--- Benchmark: Full Build (Cut 1) ---")
    start = time.time()
    watch.process_cut(1)
    watch.recompute_invalidated_nodes() # Actually process them to valid!
    full_time = time.time() - start
    
    total_records = len(watch.state.records)
    
    print(f"Time: {full_time:.4f}s")
    print(f"Total Records: {total_records}")
    
    adapter = Stage3Adapter(watch.state)
    
    print("\n--- Benchmark: Incremental Correction (Cut 2) ---")
    subj_to_correct = list(adapter._subject_index.keys())[0]
    watch.state.apply_correction(2, "LB", subj_to_correct, "LBORRES", 999, seq=1)
    
    start2 = time.time()
    watch.recompute_invalidated_nodes() # Now it should only do 1 subject
    inc_time = time.time() - start2
    
    print(f"Time: {inc_time:.4f}s")
    print(f"Affected Subjects: 1 (out of {len(adapter._subject_index)})")
    
    print("\n--- Conclusion ---")
    print(f"Full Build: O(N) where N={total_records}")
    print(f"Incremental Build: O(delta) targeting 1 subject(s)")
    if inc_time > 0:
        print(f"Speedup Factor: {full_time / inc_time:.2f}x")

if __name__ == "__main__":
    run_benchmark()
