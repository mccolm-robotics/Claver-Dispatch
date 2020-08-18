# https://docs.aiohttp.org/en/v3.0.1/


import aiohttp
import asyncio

import timer as timer

URL = 'http://....'

async def fetch(session, url):
    with session.get(url) as response:
        json_response = await response.json()
        print(json_response['uuid'])


async def main():
    async with aiohttp.ClientSession as session:
        tasks = [fetch(session, URL) for _ in range(100)]
        await asyncio.gather(*tasks)

@timer(1, 1)
def func():
    asyncio.run(main())
