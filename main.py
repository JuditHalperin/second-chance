import argparse
import pandas as pd
from ranking import PaperRanking, get_rankings
from score import compute_score, plot_score


def main(path: str, rank: int, min_count: int, output: str) -> pd.DataFrame:
    papers = [
        PaperRanking(method=row.method, url=row.url, year=row.year if hasattr(row, 'year') else None)
        for row in pd.read_csv(path).itertuples(index=False) 
    ]
    rankings = get_rankings(papers)
    scores = compute_score(rankings, rank, min_count)
    plot_score(scores, output)
    return scores


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Second Chance Benchmark')
    parser.add_argument(
        '--papers', '-p', type=str, default='example/time_series_forecasting_benchmark.csv',
        help='Path to CSV file containing benchmark data, with columns: method, url, year (optional)'
    )
    parser.add_argument(
        '--plot', '-o', type=str, default='example/time_series_forecasting_benchmark.png',
        help='Output file path for the score plot'
    )
    parser.add_argument(
        '--rank', '-k', type=int, default=4,
        help='Number of top methods to consider for scoring (from 2 to k)'
    )
    parser.add_argument(
        '--min_count', '-c', type=int, default=6,
        help='Minimum number of appearances for a method to be scored'
    )
    args = parser.parse_args()
    main(args.papers, args.rank, args.min_count, args.plot)
