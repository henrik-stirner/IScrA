import os

from dotenv import load_dotenv
from os import getenv

import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt


# ----------
# environment variables, user credentials
# ----------


load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


# ----------
# Worker
# ----------


class Worker:
    def __init__(self):
        pass

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def fetch_completion(self, prompt, engine: str = 'text-davinci-003') -> openai.Completion:
        """creates a completion for a given prompt"""
        return openai.Completion.create(engine=engine, prompt=prompt)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def fetch_embedding(self, text: str, model: str = 'text-embedding-ada-002') -> list[float]:
        """computes an embedding for a given text"""
        return openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']


if __name__ == '__main__':
    engines = openai.Engine.list()

    my_worker = Worker()

    print(my_worker.fetch_completion(
        'Sind Waldbrände in Kalifornien abwendbar oder eine unvermeidbare Folge des Klimawandels?'
    ).choices[0].text)

    # TODO: fix length
