import aiohttp

BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

COUNTRY_USA = 12
SERVICE_GOOGLE = "go"


class HeroSMSError(Exception):
    pass


async def _request(api_key: str, action: str, as_json: bool = False, **kwargs) -> str | dict | list:
    params = {"api_key": api_key, "action": action, **kwargs}
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as resp:
            if as_json:
                return await resp.json(content_type=None)
            return (await resp.text()).strip()


async def get_number(
    api_key: str, service: str = SERVICE_GOOGLE, country: int = COUNTRY_USA
) -> tuple[int, str]:
    text = await _request(api_key, "getNumber", service=service, country=country)
    if text.startswith("ACCESS_NUMBER"):
        parts = text.split(":")
        return int(parts[1]), parts[2]
    raise HeroSMSError(text)


async def get_status(api_key: str, activation_id: int) -> tuple[str, str | None]:
    text = await _request(api_key, "getStatus", id=activation_id)
    if text.startswith("STATUS_OK"):
        return "ok", text.split(":")[1]
    return text, None


async def set_status(api_key: str, activation_id: int, status: int) -> str:
    return await _request(api_key, "setStatus", id=activation_id, status=status)


async def get_balance(api_key: str) -> float:
    text = await _request(api_key, "getBalance")
    if text.startswith("ACCESS_BALANCE"):
        return float(text.split(":")[1])
    raise HeroSMSError(text)


async def get_services_list(api_key: str, country: int | None = None) -> list[dict]:
    kwargs = {}
    if country is not None:
        kwargs["country"] = country
    return await _request(api_key, "getServicesList", as_json=True, **kwargs)


async def get_countries(api_key: str) -> dict:
    return await _request(api_key, "getCountries", as_json=True)


async def get_prices(api_key: str, service: str | None = None, country: int | None = None) -> dict:
    kwargs = {}
    if service is not None:
        kwargs["service"] = service
    if country is not None:
        kwargs["country"] = country
    return await _request(api_key, "getPrices", as_json=True, **kwargs)
