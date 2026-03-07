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


def _extract_features(name: str) -> str:
    """Extract short feature label from service name.

    E.g. 'YTL1 Youtube Likes (Life Time) [Instant] (100/100k) [500/day]' -> 'Lifetime | Instant'
    """
    import re
    features = []

    lower = name.lower()
    if "life" in lower and "time" in lower:
        features.append("Umrbod")
    elif "r30" in lower or "30 day" in lower:
        features.append("30 kun kafolat")
    elif "[nr]" in lower:
        features.append("Kafolatsiz")

    if "instant" in lower:
        features.append("Tezkor")
    elif "guaranteed" in lower:
        features.append("Kafolatli")

    # Extract speed like {10k/day} or [1k/day]
    speed = re.search(r"[\[{(](\d+k?/day)[\]})]]", lower)
    if speed:
        features.append(speed.group(1) + "/day" if "/day" not in speed.group(1) else speed.group(1))

    return " | ".join(features) if features else ""


async def get_youtube_services(api_key: str) -> dict[str, list[dict]]:
    services = await get_services(api_key)

    type_filters = {
        "views": lambda c: "view" in c and "live" not in c,
        "likes": lambda c: "like" in c,
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

        picked = filtered[:5]

        # Add feature labels
        for s in picked:
            s["features"] = _extract_features(s.get("name", ""))

        result[type_name] = picked

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
