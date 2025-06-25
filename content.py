import fitz
import requests
from io import BytesIO
import re


def get_pages(url: str, max_pages: int = None) -> fitz.Document:
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f'Failed to download PDF: {response.status_code}')
    doc = fitz.open(stream=BytesIO(response.content), filetype='pdf')
    return doc if max_pages is None else doc[:max_pages]


def extract_tables_and_legends(pdf_url: str, cut: bool = True, distance: int = 400) -> str:
    pages = get_pages(pdf_url)
    table_texts = []
    for page in pages:
        blocks = page.get_text('blocks')
        blocks.sort(key=lambda b: b[1])
        used_indices = set()
        for i, block in enumerate(blocks):
            text = block[4].strip()
            y0 = block[1]

            if cut and re.match(r'^\s*(references|appendix|acknowledg(?:ement|ments)|supplementary\s+material|ablation)\b', text.lower()):
                return '\n\n'.join(table_texts).strip()

            if re.match(r'^(Table|TABLE)\s*\d+[:.\s]', text):
                table = [text]
                used_indices.add(i)

                # Collect blocks below caption
                for j in range(i + 1, len(blocks)):
                    if j in used_indices:
                        continue
                    b_text = blocks[j][4].strip()
                    if b_text and (blocks[j][1] - y0) < distance:
                        table.append(b_text)
                        used_indices.add(j)
                    else:
                        break

                # Collect blocks above caption
                for j in range(i - 1, -1, -1):
                    if j in used_indices:
                        continue
                    b_text = blocks[j][4].strip()
                    if b_text and (y0 - blocks[j][1]) < distance:
                        table.insert(0, b_text)
                        used_indices.add(j)
                    else:
                        break

                table_texts.append('\n'.join(table))

    return '\n\n'.join(table_texts).strip()
