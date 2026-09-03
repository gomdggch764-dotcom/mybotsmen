# -*- coding: utf-8 -*-
import aiohttp

async def show_advert(user_id, api_key):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "user_id": user_id
            }
            async with session.post("https://api.gramads.net/v1/advert", json=data, headers=headers) as resp:
                if resp.status == 200:
                    return True
                return False
    except:
        return False
