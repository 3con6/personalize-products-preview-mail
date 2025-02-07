import aiohttp
import asyncio
from user_agent import generate_user_agent  # https://github.com/lorien/user_agent  pip install -U user_agent
import time
import traceback
import motor.motor_asyncio
import os
import logging 
from logging.handlers import RotatingFileHandler



# Asyncio ===================================================
class rate_limit_conf:
    def __init__ (self, number, second):
        self.updated_at = time.monotonic()
        self.NUMBER = number
        self.SECOND = second
        self.TOKEN = 0
async def rate_limit(g):
    def add_token():
        if time.monotonic() - g.updated_at > (g.SECOND / g.NUMBER):
            g.TOKEN = 1

    while g.TOKEN < 1:
        add_token()
        await asyncio.sleep(0.001)
    g.updated_at = time.monotonic()
    g.TOKEN = 0

async_limit = rate_limit_conf(4, 1)
mongo_find_async_limit = rate_limit_conf(200, 1)
discord_limit = rate_limit_conf(1, 2)

async def async_request_(session, url, method, type, payload=None, proxy=None, auth_info=None, headers=None):
    if headers == None: headers = {'user-agent': generate_user_agent()}
    else: headers.update({'user-agent': generate_user_agent()})
    http_proxy = "http://" + proxy if proxy != None else None
    try:
        if 'graph.microsoft.com' in url:
            await rate_limit(async_limit)
        elif    'discord.com/api/' in url :
            await rate_limit(discord_limit)
        if method == "GET": 
            try:
                async with session.get(url, headers=headers, proxy=http_proxy) as response:
                    if type == "JSON": html = await response.json()
                    elif type == "FILE":
                        html = await response.read()
                    else: html = await response.text()
                    return response.status, response.headers, response.request_info, html
            except asyncio.CancelledError:
                print('loiiiiiiiiiiiiiiiiiiiiiii',url)

        
        elif method == "POST": 
            if type == "JSON":
                async with session.post(url, headers=headers, json=payload, proxy=http_proxy) as response:
                    html = await response.json()
                    return response.status, response.headers, response.request_info, html
            elif type == "FILE":
                async with session.post(url, headers=headers, data=payload, proxy=http_proxy,allow_redirects=False) as response:
                    html = await response.json()
                    return response.status, response.headers, response.request_info, html
            else: 
                async with session.post(url, headers=headers, data=payload, proxy=http_proxy) as response:
                    html = await response.text()
                    return response.status, response.headers, response.request_info, html
        
        elif method == "PUT": 
            async with session.put(url, headers=headers, json=payload, proxy=http_proxy) as response:
                if type == "JSON": html = await response.json()
                else: html = await response.text()
                return response.status, response.headers, response.request_info, html
        
        elif method == "DELETE": 
            async with session.delete(url, headers=headers, proxy=http_proxy) as response:
                if type == "JSON": html = await response.json()
                else: html = await response.text()
                return response.status, response.headers, response.request_info, html
                
    except aiohttp.ClientResponseError as ex:
        status = ex.status
        return status, '', '', ''
    except aiohttp.ClientConnectionError:
        status = 'ErrConn'
        # logger_async.exception("logger_async ClientConnectionError")
        return status, '', '', ''
    except asyncio.TimeoutError:
        status = 'asyncio.TimeoutError'
        return status, '', '', ''
    except:
        # logger_async.exception("logger_async error")
        return str(traceback.format_exc()), '', '', ''

def db_itnit(db_user, db_password, db_host, db_name):
    conn = f"mongodb://{db_user}:{db_password}@{db_host}/admin"
    mongoClient = motor.motor_asyncio.AsyncIOMotorClient(conn, retryWrites=False)
    async_db = mongoClient[db_name]
    return async_db        
async def do_find_many(async_db, collection_, document_, filter_):
    await rate_limit(mongo_find_async_limit)
    db = async_db[collection_].find(document_, filter_).sort("_id", -1)
    all_ =[]
    async for document in db:
        all_.append(document)
    return all_        


def b_log(log_name, stream = True):
    os.makedirs('./logs/') if not os.path.exists('./logs/') else True
    logger = logging.getLogger(log_name)

    hnd_all = RotatingFileHandler(f"./logs/{log_name}.log", maxBytes=10000000, backupCount=5)
    # hnd_all.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s ''[in %(pathname)s:%(lineno)d]'))
    hnd_all.setFormatter(logging.Formatter('%(asctime)s %(levelname)s in %(filename)s:%(lineno)d: %(message)s ', datefmt='%Y%m%d %H:%M:%S'))
    # hnd_all.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s ''[in %(filename)s:%(lineno)d]', datefmt='%Y%m%d %H:%M:%S'))
    hnd_all.setLevel(logging.DEBUG)
    logger.addHandler(hnd_all)

    if stream == True:
        hnd_stream = logging.StreamHandler()
        # hnd_stream.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s ''[in %(pathname)s:%(lineno)d]'))
        hnd_stream.setFormatter(logging.Formatter('%(asctime)s %(levelname)s in %(filename)s:%(lineno)d: %(message)s ', datefmt='%Y%m%d %H:%M:%S'))
        # hnd_stream.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s ''[in %(filename)s:%(lineno)d]', datefmt='%Y%m%d %H:%M:%S'))
        hnd_stream.setLevel(logging.DEBUG)
        logger.addHandler(hnd_stream)

    logger.setLevel(logging.DEBUG)

    return logger

