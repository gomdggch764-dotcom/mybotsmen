import logging
import aiohttp

log = logging.getLogger('adverts')

async def show_advert(user_id: int, api_key: str):
    """Отправляет рекламу пользователю через GramAds"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.gramads.net/ad/SendPost',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={'SendToChatId': user_id}
            ) as response:
                # Читаем ответ как текст (не JSON)
                text_result = await response.text()
                log.info(f"GramAds ответ: {text_result}")
                
                if response.status == 200:
                    log.info(f"Реклама показана пользователю {user_id}")
                    return True
                else:
                    log.error(f"GramAds ошибка: {response.status} - {text_result}")
                    return False
    except Exception as e:
        log.error(f"Ошибка при показе рекламы: {e}")
        return False