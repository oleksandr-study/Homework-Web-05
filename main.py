import json
import sys
from datetime import datetime, timedelta

import aiohttp
import asyncio
import platform


CURRENCYS = ["AUD",
"AZN",
"BYN",
"CAD",
"CHF",
"CNY",
"CZK",
"DKK",
"GBP",
"GEL",
"HUF",
"ILS",
"JPY",
"KZT",
"MDL",
"NOK",
"PLN",
"SEK",
"SGD",
"TMT",
"TRY",
"UZS",
"XAU"]


class HttpError(Exception):
    pass


def params_check(c_list: list) -> list:
    params_list = ["EUR", "USD"]
    if len(c_list) < 2:
        print("Enter 2 or more arguments please!")
        quit()
    if len(c_list) > 2:
        params_list.insert(0, c_list[1])
        for param in c_list[2:]:
            if param == "EUR" or param == "USD":
                print(f"'{param}' have already in a list")
            elif param in CURRENCYS:
                params_list.append(param)
            else:
                print(f"'{param}' is not in a currency list")
    else:
        params_list.insert(0, c_list[1])
    return params_list


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f"Error status: {resp.status} for {url}")
        except (aiohttp.ClientConnectorError, aiohttp.InvalidURL) as err:
            raise HttpError(f'Connection error: {url}', str(err))


async def currency_list(basic_curr: dict, curr_dict: dict) -> dict:
    exchangeRate = curr_dict['exchangeRate']
    result = {}
    for currency in exchangeRate:
        for cur in basic_curr:
            if cur == currency['currency']:
                result.update({currency['currency']: {'sale': currency['saleRate'], 'purchase': currency['purchaseRate']}})
    return result
    

async def main(curr_dict: dict, index_day: int):
    response = []
    datelist = [datetime.now() - timedelta(days=x+1) for x in range(int(index_day))]
    print(datelist)
    for d in datelist:
        shift = d.strftime("%d.%m.%Y")
        try:
            response.append({shift: await currency_list(curr_dict, await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}'))})
        except HttpError as err:
            print(err)
            return None
    return response


if __name__ == '__main__':
    params_list = params_check(sys.argv)
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    date = params_list[0]
    currency = params_list[1:]
    r = asyncio.run(main(currency, date))
    print(json.dumps(r, indent=2))