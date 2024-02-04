import functools
import time
from itertools import islice
import inspect

import httpx


def _stringify(args, kwargs):
    args = [str(arg) for arg in args if not isinstance(arg, httpx.AsyncClient)]
    args_str = ', '.join(args)
    kwargs_str = ', '.join(f'{name}={value}' for name, value in kwargs.items()) 
    if args_str and kwargs_str:
        return f'{args_str}, {kwargs_str}'
    if args_str:
        return args_str
    return kwargs_str


def timer(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapper_timer(*args, **kwargs):
            tic = time.perf_counter()
            value = await func(*args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            func_str = f'{func.__name__}({_stringify(args, kwargs)})'
            print(f'{func_str} run in: {elapsed_time:0.4f} seconds')
            return value
    else:
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            tic = time.perf_counter()
            value = func(*args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            func_str = f'{func.__name__}({_stringify(args, kwargs)})'
            print(f'{func_str} run in: {elapsed_time:0.4f} seconds')
            return value
    return wrapper_timer


def batched(iterable, n):
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch 