from line_profiler import LineProfiler


def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = LineProfiler()
        profiler.add_function(func)
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Save profiling results to a file named after the function
        file_name = f"{func.__name__}_profile.txt"
        with open(file_name, "w") as f:
            profiler.print_stats(stream=f)
        
        print(f"Profiling results saved to {file_name}")
        return result
    return wrapper

@profile_function
def slow_function():
    total = 0
    for i in range(1, 10000):
        total += i ** 2
    return total


slow_function()

