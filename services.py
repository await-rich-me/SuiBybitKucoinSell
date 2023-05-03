import asyncio
import ccxt.async_support as ccxt
import json
from loguru import logger
check_tasks = []


async def api_settings():
    global check_tasks
    count = 1

    exchanges = dict()
    exchanges_set = set()

    with open('api.json') as file:
        api_data = json.load(file)

    while api_data.get(f'account{count}'):
        account_data = api_data.get(f'account{count}', {})
        
        check_tasks = []

        kucoin_data = account_data.get('kucoin', {})
        if kucoin_data.get('apiKey') and kucoin_data.get('secret') and kucoin_data.get('password') and kucoin_data.get('proxies'):

            exchange = ccxt.kucoin(kucoin_data)
            check_tasks.append(checkAndTransfer(exchange))
            exchanges.setdefault('kucoin', []).append((f'account{count}', exchange))
            exchanges_set.add((ccxt.kucoin(), 0))

        bybit_data = account_data.get('bybit', {})
        if bybit_data.get('apiKey') and bybit_data.get('secret'):  # and bybit_data.get('proxies'):

            exchange = ccxt.bybit(bybit_data)
            check_tasks.append(checkAndTransfer(exchange))
            exchanges.setdefault('bybit', []).append((f'account{count}', exchange))
            exchanges_set.add((ccxt.bybit(), 0))

        count += 1

    await asyncio.gather(*check_tasks)

    return exchanges, list(exchanges_set)


async def checkAndTransfer(exchange):
    balance = await exchange.fetch_balance({'type': 'funding'})

    if 'SUI' in balance:
        amount = balance.get('SUI').get('free')

        if amount > 0:
            await exchange.transfer('SUI', amount, 'funding', 'spot')
            logger.info(f"Отправил SUI на спот")
        else:
            logger.info(f'SUI уже на споте')


def price_settings():
    with open('prices.json') as file:
        api_data = json.load(file)

    range_start = api_data.get('range_start')
    range_end = api_data.get('range_end')
    insta_sell = api_data.get('insta_sell')
    max_time_in_range = api_data.get('max_time_in_range')
    percent = api_data.get('percent')

    return range_start, range_end, insta_sell, max_time_in_range, percent
