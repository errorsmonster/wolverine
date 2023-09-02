import aiohttp

async def get_shortlink(link, api_key=None):
    url = f'https://api.shareus.io/easy_api'
    default_api_key = "VLuKAPjHgrahNY2zTcWM16lFyTJ2"

    if api_key is None:
        api_key = default_api_key

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
    default_shortner = "https://sharezone.live/api"
    default_api_key = "9054119f1e0c6332b2fd694fc1c3ffa3b31c590e"
    if shortner is None:
        shortner = default_shortner
    if api_key is None:
        api_key = default_api_key 

    params = {'api': api_key, 'url': link, 'format': 'text'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(shortner, params=params, raise_for_status=True) as response:
                return await response.text()
    except Exception as e:
        print(e)
        return f"{shortner}?api={api_key}&url={link}&format=text"