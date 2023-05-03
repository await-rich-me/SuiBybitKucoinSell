import asyncio
import datetime
from loguru import logger
import services



async def get_last_prices(exchanges_set):

    """Получаем цены нашего коина с каждой биржи"""
    tasks = [exchange[0].fetch_ticker('SUI/USDT') for exchange in exchanges_set]
    results = await asyncio.gather(*tasks)
    return results

async def check_price(exchanges, exchanges_set, range_start, range_end,insta_sell,percent, max_time_in_range):
    """
    Выставялем ордера на продажу,
    если цена превысила диапазон или цена находится в диапазоне max_time_in_range секунд
    """

    prices = await get_last_prices(exchanges_set)

    to_sell = []

    for count, price in enumerate(prices):
        current_price = price['last']

        exchange_id = exchanges_set[count][0].id

        if current_price >= insta_sell:
            logger.info(f'{exchange_id} --- {current_price} --- Сливаю по инста прайсу')

            for exchange in exchanges[exchange_id]:
                to_sell.append(limit_sell_order(exchange, 'SUI/USDT', current_price*percent))

        elif range_start <= current_price <= range_end:
            datetime_now = datetime.datetime.now()

            if exchanges_set[count][1] == 0:
                lst = list(exchanges_set[count])
                lst[1] = datetime_now
                exchanges_set[count] = tuple(lst)

            duration_time = (datetime_now - exchanges_set[count][1]).seconds
            logger.info(f'{exchange_id} --- {current_price} --- Цена в диапазоне {duration_time}с / {max_time_in_range}c')


            if duration_time > max_time_in_range:
                for exchange in exchanges[exchange_id]:
                    to_sell.append(limit_sell_order(exchange, 'SUI/USDT', current_price*percent))
        elif insta_sell > current_price > range_end:
            logger.info(f'{exchange_id} --- {current_price} --- Цена больше диапазона')
        else:
            logger.info(f'{exchange_id} --- {current_price} --- Цена меньше диапазона')

    await asyncio.gather(*to_sell)


async def limit_sell_order(exchange, symbol, price):
    """Создаём ордер на продажу всего баланса по текущей цене минус какой то процент"""

    balance = await exchange[1].fetch_balance({'type':'spot'})

    amount = balance.get('SUI').get('free')

    if amount > 0.1:


        try:
            logger.info(f'{exchange[0]} cоздаём ордер на продажу в {exchange[1].id}. Amount = {amount} Price = {price}')

            await exchange[1].create_limit_sell_order(
                symbol,
                amount,
                price,
            )
            balance = await exchange[1].fetch_balance({'type': 'spot'})
            availableamount = balance.get('SUI').get('free')
            usdtamount = balance.get('USDT').get('free')
            logger.info(F'{exchange[0]} {exchange[1]} остаток SUI - {availableamount}, баланс USDT - {usdtamount}')
        except Exception as e:
            return logger.error(f'Не удалось создать ордер в {exchange[1].id}. {e}')


async def main():
    exchanges, exchanges_set = await services.api_settings()
    if not exchanges:
        return  logger.error('Добавьте данные о биржах в файл `api.json`')

    range_start, range_end, insta_sell, max_time_in_range, percent = services.price_settings()
    if not range_start or not range_end or not max_time_in_range:
        return logger.error('Добавьте данные о ценах в файл `prices.json`')


    while True:
        await check_price(exchanges, exchanges_set, range_start, range_end,insta_sell, percent,max_time_in_range)


if __name__ == '__main__':
    asyncio.run(main())
