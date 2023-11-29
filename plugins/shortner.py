import aiohttp

async def shareus(link):
    url = f'https://api.shareus.io/easy_api'
    api_key = "UVZ5NmnAZkNdK6azyMoTP9Ij3n62"

    params = {'key': api_key, 'link': link}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        shortlink = f"{url}?key={api_key}&link={link}"
        return shortlink
    
async def gplinks(link):
    url = f'https://gplinks.in/api'
    api_key = "2578d98dd859758740ff88707e6a45d05213d131"

    params = {'api': api_key, 'url': link, 'format': 'text'}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        shortlink = f"{url}?api={api_key}&url={link}&format=text"
        return shortlink


async def linkpass(link):
    shorner = f"https://linkpass.onrender.com/shorten?url={link}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(shorner, raise_for_status=True) as response:
                data = await response.json()
                return data["short_url"]
    except Exception as e:
        return f"{shorner}"
    
async def urlshare(link):
    shortner = f'https://urlshare.onrender.com/?create&url={link}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(shortner, raise_for_status=True) as response:
                data = await response.json()
                return data["short_url"]
    except Exception as e:
        return f"{shortner}"