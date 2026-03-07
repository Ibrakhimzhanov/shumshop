import aiohttp

BASE_URL = "https://www.smmraja.com/api/v3"


class SMMRajaError(Exception):
    pass


async def _request(api_key: str, **params) -> dict | list:
    payload = {"key": api_key, **params}
    async with aiohttp.ClientSession() as session:
        async with session.post(BASE_URL, data=payload) as resp:
            data = await resp.json(content_type=None)
    if isinstance(data, dict) and "error" in data:
        raise SMMRajaError(data["error"])
    return data


async def get_services(api_key: str) -> list[dict]:
    return await _request(api_key, action="services")


async def get_youtube_services(api_key: str) -> dict[str, list[dict]]:
    services = await get_services(api_key)

    type_filters = {
        "views": lambda c: "view" in c and "live" not in c,
        "likes": lambda c: "like" in c and "dislike" not in c,
        "subscribers": lambda c: "subscrib" in c,
        "comments": lambda c: "comment" in c,
        "shorts": lambda c: "short" in c,
        "shares": lambda c: "share" in c,
    }

    yt_services = [
        s for s in services
        if isinstance(s, dict) and "youtube" in s.get("category", "").lower()
    ]

    result: dict[str, list[dict]] = {}
    for type_name, match_fn in type_filters.items():
        filtered = [
            s for s in yt_services
            if match_fn(s.get("category", "").lower())
            and float(s.get("rate", 0)) > 0
        ]
        filtered.sort(key=lambda s: float(s["rate"]))
        result[type_name] = filtered[:5]

    return result


async def add_order(api_key: str, service_id: int, link: str, quantity: int) -> dict:
    return await _request(
        api_key,
        action="add",
        service=service_id,
        link=link,
        quantity=quantity,
    )


async def order_status(api_key: str, order_id: int) -> dict:
    return await _request(api_key, action="status", order=order_id)


async def get_balance(api_key: str) -> dict:
    return await _request(api_key, action="balance")
