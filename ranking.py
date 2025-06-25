import os
import json
import pandas as pd
from content import extract_tables_and_legends
from benchmarks import get_benchmarks


class Cache:
    def __init__(self, method: str):
        method = method.lower().replace(' ', '_')
        self.cache_file = f'.cache/{method}.json'
        os.makedirs('.cache', exist_ok=True)
    
    def is_cached(self) -> bool:
        return os.path.exists(self.cache_file)

    def dump_cache(self, benchmarks: dict[str, list[str]], cost: float, simple_extract: bool) -> None:
        if not benchmarks:
            pass
        with open(self.cache_file, 'w') as f:
            json.dump({
                'benchmarks': benchmarks,
                'cost': cost,
                'simple_extract': simple_extract
            }, f, indent=2)
    
    def load_cache(self) -> tuple[dict]:
        with open(self.cache_file, 'r') as f:
            data = json.load(f)
            return data['benchmarks'], data['cost'], data['simple_extract']


class PaperRanking:
    def __init__(self, method: str, url: str, year: int | None, title: str | None = None, num_comparisons: int = 4):
        self.method = method
        self.url = url
        self.year = year
        self.title = title
        self.num_comparisons = num_comparisons

        self.cache = Cache(method)
        self.extract_benchmarks()

    def extract_benchmarks(self) -> None:
        if self.cache.is_cached():
            self.benchmarks, self.cost, self.simple_extract = self.cache.load_cache()
            return
        
        self.simple_extract = True
        content = extract_tables_and_legends(self.url, cut=True, distance=400)
        self.benchmarks, self.cost = get_benchmarks(self.method, content, self.num_comparisons, input_cost_limit=0.01, output_limit=300)

        if not self.benchmarks:
            self.simple_extract = False
            content = extract_tables_and_legends(self.url, cut=False, distance=600)
            self.benchmarks, self.cost = get_benchmarks(self.method, content, self.num_comparisons, input_cost_limit=0.02, output_limit=500)
        
        if not self.benchmarks:
            raise ValueError(f'No benchmarks found for {self.method}')

        self.cache.dump_cache(self.benchmarks, self.cost, self.simple_extract)
        
    def get_ranking(self) -> list[dict[str, str | int]]:
        if not self.benchmarks:
            raise ValueError('No benchmarks found for this paper')

        ranking = []
        for methods in self.benchmarks.values():
            other_methods = [m for m in methods if self.method.lower() not in m.lower() and m.lower() != 'ours']
            for rank, method in enumerate(other_methods, start=2):
                ranking.append({'method': method, 'rank': rank})

        return ranking
    
    def __str__(self) -> str:
        message = f'{self.method}:'
        for comparison, methods in self.benchmarks.items():
            message += f'\n{comparison}: {', '.join(methods)}'
        return message
    
    def get_cost(self) -> str:
        if not hasattr(self, 'cost'):
            raise ValueError('Benchmarks must be extracted before getting cost')
        return f'{self.cost:.3f}$ ({'simple' if self.simple_extract else 'full'} extraction)'


def get_rankings(papers: list[PaperRanking]) -> pd.DataFrame:
    rankings = []
    for paper in papers:
        for rank_info in paper.get_ranking():
            rankings.append({
                'paper': paper.method,
                'year': paper.year if paper.year else -1,
                'method': rank_info['method'],
                'rank': rank_info['rank']
            })
            
    rankings = pd.DataFrame(rankings)
    rankings['method'] = [m.replace(' ', '') for m in rankings['method']]
    return rankings
