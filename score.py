import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


def get_rank_weights(k: int) -> float:
    return max(1.0 - 0.1 * (k - 2), 0)


def get_time_weights(year: int) -> float:
    if year == -1:
        return 1.0
    current_year = datetime.now().year
    return max(1.0 - 0.1 * (current_year - year), 0)


def compute_score(
    rankings: pd.DataFrame,
    k: int = 2,
    min_count: int = 4,
    eps: float = 1e-6
):
    scores = {}
    for method in rankings['method'].unique():
        method_df = rankings[rankings['method'] == method]

        # Filter methods with at least min_count appearances and at least two papers
        if method_df.shape[0] < min_count:
            continue
        if method_df['paper'].nunique() == 1:
            continue
        
        numerator, denominator = 0, 0

        for year in rankings['year'].unique():
            year_weight = get_time_weights(year)
            year_appearances = method_df[method_df['year'] == year]

            for rank in range(2, k + 1):
                rank_weight = get_rank_weights(rank)
                numerator += year_weight * rank_weight * year_appearances[year_appearances['rank'] == rank].shape[0]
            
            denominator += year_weight * year_appearances.shape[0]

        scores[method] = numerator / (denominator + eps)
    
    return pd.DataFrame.from_dict(scores, orient='index', columns=['score']).sort_values(by='score', ascending=False)


def plot_score(score_df: pd.DataFrame, path: str) -> None:
    score_df = score_df[score_df['score'] > 0]
    plt.figure(figsize=(7, 5))
    plt.bar(score_df.index, score_df['score'], color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Method')
    plt.ylabel('SecScore')
    plt.title(path.split('/')[-1].split('.')[0].replace('_', ' ').title(), fontsize=18)
    plt.tight_layout()
    plt.savefig(path if path.endswith('.png') else path + '.png')
