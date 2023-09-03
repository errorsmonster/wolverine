import aiohttp

async def get_shortlink(link, api_key=None, shortner=None):
    url = f'https://api.shareus.io/easy_api'
    default_api_key = "VLuKAPjHgrahNY2zTcWM16lFyTJ2"

    if api_key is None:
        api_key = default_api_key

    if shortner is not None:
        return await adlinkfly(link, shortner, api_key)  # Return the result from adlinkfly

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