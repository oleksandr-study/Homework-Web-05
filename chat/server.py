import asyncio
import json
import logging
import re
from datetime import datetime, timedelta

import aiohttp
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)


class HttpError(Exception):
    pass


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


async def currency_list(curr_dict: dict) -> dict:
    basic_curr = ['EUR', 'USD']
    exchangeRate = curr_dict['exchangeRate']
    result = {}
    for currency in exchangeRate:
        for cur in basic_curr:
            if cur == currency['currency']:
                result.update({currency['currency']: {'sale': currency['saleRate'], 'purchase': currency['purchaseRate']}})
    return result


async def get_exchange():
    response = await request(f'https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=5')
    print(response)
    return str(response)


async def get_archive_exchange(index_day: str):
    response = []
    datelist = [datetime.now() - timedelta(days=x+1) for x in range(int(index_day))]
    for d in datelist:
        shift = d.strftime("%d.%m.%Y")
        try:
            response.append({shift: await currency_list(await request(f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}'))})
        except HttpError as err:
            print(err)
            return None
    return str(response)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == "exchange":
                exchange = await get_exchange()
                await self.send_to_clients(exchange)
            elif re.fullmatch(r'exchange \d', message):
                exchange = await get_archive_exchange(message[-1])
                await self.send_to_clients(exchange)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
