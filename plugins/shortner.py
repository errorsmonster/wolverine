import aiohttp
import json

async def atglib(link):
    url = f'https://api.shareus.io/easy_api'
    api_key = "UVZ5NmnAZkNdK6azyMoTP9Ij3n62"

    params = {'key': api_key, 'link': link}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        print(e)
        shortlink = f"{url}?key={api_key}&link={link}"
        return shortlink
    

async def short_link(link):
    url = f'https://atglinks.com/api'
    api_key = "a2c025bc3bfbb0907f422350f4b920b15ee85e09"

    params = {'api': api_key, 'url': link, 'format': 'text'}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        print(e)
        shortlink = f"{url}?api={api_key}&url={link}&format=text"
        return shortlink
    
async def get_shortlink(link):
    shortlink = await short_link(link)
    base_link = f"https://atglinks.com/"
    code = shortlink.split("/")[-1]
    output_link = f"{base_link}{code}"
    return output_link
    

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


