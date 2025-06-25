import re
import json
import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)


PRICE_PER_1M = {
    'gpt-4.1': {'input': 2.00, 'output': 8.00},
    'gpt-4o': {'input': 5.00, 'output': 20.00},
}


PROMPT = """
From the following academic paper content, extract lists of benchmarked
methods or models that are evaluated in performance tables or results sections.

Your goal is to find all benchmark comparisons — across different tables, datasets, or tasks —
and return a separate ordered list of methods for each one, where methods are ordered from
best-performing to worst-performing based on how they are ranked or described in the paper.

- Do NOT include unrelated table content such as dataset summaries or experimental setup.
- Do NOT include dataset names, metric values, or any numerical scores.
- Return ranked lists of method or model names. Prefer the most commonly
used or cited name of each method — not full technical names or detailed variants.
- If there are multiple benchmark comparisons in the paper, extract only the NUM_COMPARISONS **most important** comparisons, and return a separate list for each one.
- Do NOT list multiple sizes or configurations of the same method separately.
- Do NOT include ablation studies, hyperparameter tuning, or other non-benchmark comparisons.
- For each benchmark, include a descriptive title, and the label the table number or section it came from, if available.
- If multiple variants of the same method are listed (e.g., "Chronos-T5 (Large)", "Chronos-GPT", "Chronos/64") —
especially variants of the method introduced in the current paper — group them into a single entry by name (e.g., "Chronos")
and include only the first occurrence in each benchmark list.
- Note that some comparison rows in tables may span multiple lines.
- If no clear benchmark ranking is found, indicate that.

Return your response as JSON with the following structure:

{
  "success": true or false,
  "methods": {
    "benchmark descriptive title": [ordered list of method names],
    ...
  },
  "message": "short explanation or error reason"
}

Here is the name of the paper and its content:

"""


def process_json(raw: str) -> dict:
    raw = re.sub(r'^```json\s*', '', raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r'```$', '', raw.strip())
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            'success': False,
            'methods': {},
            'message': 'Failed to parse LLM response as JSON. Raw output:\n' + raw
        }


def estimate_cost(text: str, model: str, side: str = 'input', round_to: int = 3) -> float | None:
    tokens = len(text.split())
    if model in PRICE_PER_1M:
        price_per_token = PRICE_PER_1M[model][side]
        cost = tokens / 1_000_000 * price_per_token
        return round(cost, round_to)
    return None
       

def get_benchmarks(
        method_name: str,
        content: str,
        num_comparisons: int = 4,
        model: str = 'gpt-4.1',
        input_cost_limit: float = 0.01,
        input_limit: int | None = None,
        output_limit: int = 300
    ) -> tuple[dict[str, list[str]], float]:
    
    cost = estimate_cost(content, model)
    if cost > input_cost_limit:
        raise ValueError(f'Estimated cost of {cost}$ exceeds limit for method {method_name}')
    if input_limit and len(content) > input_limit:
        raise ValueError(f'Content exceeds token limit of {input_limit} characters for method {method_name}')

    prompt = PROMPT.replace('NUM_COMPARISONS', str(num_comparisons))
    prompt = f'{prompt}\n\n {method_name}\n\n {content}'

    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.2,
        max_tokens=output_limit,
    )

    raw = response.choices[0].message.content.strip()
    result = process_json(raw)
    
    total_cost = estimate_cost(prompt, model, side='input') + estimate_cost(raw, model, side='output')

    if not result.get('success'):
        return {}, total_cost    
    return result.get('methods', {}), total_cost
