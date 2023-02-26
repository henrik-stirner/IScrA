from dotenv import load_dotenv
from os import getenv

import openai
import tiktoken
from tenacity import retry, wait_random_exponential, stop_after_attempt


# ----------
# environment variables, user credentials
# ----------


load_dotenv()

openai.api_key = getenv('OPENAI_API_KEY')


# ----------
# utility
# ----------

# ===============================================================================
# |      Encoding name      |                   OpenAI models                   |
# -------------------------------------------------------------------------------
# | gpt2 (or r50k_base)     |   Most GPT-3 models                               |
# | p50k_base               |   Code models, text-davinci-002, text-davinci-003 |
# | cl100k_base             |   text-embedding-ada-002                          |
# ===============================================================================

def determine_number_of_tokens(string: str, encoding_name: str = 'gpt2') -> int:
    """returns the number of tokens that are in a text string"""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))


# ----------
# Worker
# ----------


class Worker:
    def __init__(self):
        pass

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def fetch_completion(self, prompt, engine: str = 'text-davinci-003', max_tokens: int = 0, n: int = 1,
                         temperature: float = 0.5) -> openai.Completion:
        """creates a completion for a given prompt"""
        return openai.Completion.create(
            engine=engine,
            prompt=prompt,
            max_tokens=max_tokens,
            n=n,
            temperature=temperature
        )

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def fetch_embedding(self, text: str, model: str = 'text-embedding-ada-002') -> list[float]:
        """computes an embedding for a given text"""
        return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']


# ----------
# run
# ----------


def main(prompt: str, completion_max_tokens: int) -> str or None:
    if not prompt:
        return

    prompt_tokens = determine_number_of_tokens(prompt, 'gpt2')

    highest_possible_cost = (prompt_tokens + completion_max_tokens) * (0.02 / 1000)  # for text-davinci-003

    yield f"""{100 * "="}
Prompt Tokens: \t\t\t\t\t{prompt_tokens}
Max Completion Tokens: \t\t\t{completion_max_tokens}
{25 * "-"}
Highest Possible Token Usage: \t{prompt_tokens + completion_max_tokens}
{75 * "="}
Highest Possible Price: \t\t${highest_possible_cost}
{100 * "="}


"""

    print(f'PROMPT: {prompt}')
    while True:
        actually_run = input('Actually create completion (y / n)?: ')
        if actually_run == 'y':
            print('Creating completion...')
            break
        elif actually_run == 'n':
            print('Aborting...')
            return
        else:
            print('Invalid input.')

    my_worker = Worker()
    my_completion = my_worker.fetch_completion(prompt, max_tokens=completion_max_tokens)

    completion_used_tokens = determine_number_of_tokens(my_completion.choices[0].text, 'gpt2')

    actual_price = (prompt_tokens + completion_used_tokens) * (0.02 / 1000)  # for text-davinci-003

    yield f"""{100 * "="}
Used Prompt Tokens: \t\t\t{prompt_tokens}
Used Completion Tokens: \t\t{completion_used_tokens}
{25 * "-"}
Total Used Tokens: \t\t\t\t{prompt_tokens + completion_used_tokens}
{75 * "="}
Actual Price: \t\t\t\t\t${actual_price}
{100 * "="}


{100 * "="}
Generated completion: 
{25 * "-"}
{my_completion.choices[0].text.strip()}
{100 * "="}"""


if __name__ == '__main__':

    prompt = 'Beantwort folgende Frage in einem kurzen Aufsatz mit einem Umfang von etwa 250 Wörtern. ' \
             'Sind Waldbrände in Kalifornien abwendbar, oder eine unvermeidbare Folge des Klimawandels?'

    completion_max_tokens = 10 ** 3

    with open('./dump.txt', 'w', encoding='utf-8') as dump_file:
        for output in main(prompt=prompt, completion_max_tokens=completion_max_tokens):
            dump_file.write(output)
            print(output)
