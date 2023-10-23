import aiohttp
import json

async def get_shortlink(link):
    url = f'https://api.shareus.io/easy_api'
    api_key = "VLuKAPjHgrahNY2zTcWM16lFyTJ2"

    params = {'key': api_key, 'link': link}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        print(e)
        shortlink = f"{url}?key={api_key}&link={link}"
        return shortlink
    

async def adlinkfly(link, shortner=None, api_key=None):
    params = {'api': api_key, 'url': link, 'format': 'text'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(shortner, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        print(e)
        return f"{shortner}?api={api_key}&url={link}&format=text"

# primehub shortner
async def linkgen(link):
    shortner = f'https://urlshare.onrender.com/?create&url={link}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(shortner, raise_for_status=True) as response:
                data = await response.json()
                return data["short_url"]
    except Exception as e:
        print(e)


