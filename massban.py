import aiohttp
import asyncio
import random
import time
import json
import sys
import os
import base64
import string
import re
import ssl
from yarl import URL
from colorama import Fore, init
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple, Set, Any

HAS_HTTP2 = False
try:
    import aiohttp.http2
    import h2
    HAS_HTTP2 = True
except ImportError:
    pass

HAS_AIO_DNS = False
try:
    import aiodns
    if sys.platform != 'win32':
        HAS_AIO_DNS = True
except ImportError:
    pass

init(autoreset=True)

r = Fore.RED
p = Fore.MAGENTA
w = Fore.WHITE
g = Fore.GREEN
y = Fore.YELLOW
c = Fore.CYAN
lr = Fore.LIGHTRED_EX
lg = Fore.LIGHTGREEN_EX
lm = Fore.LIGHTMAGENTA_EX
lc = Fore.LIGHTCYAN_EX
lb = Fore.LIGHTBLUE_EX
ly = Fore.LIGHTYELLOW_EX

BANNER = [
    " ███▄ ▄███▓ ▄▄▄        ██████   ██████     ▄▄▄▄    ▄▄▄       ███▄    █ ",
    "▓██▒▀█▀ ██▒▒████▄    ▒██    ▒ ▒██    ▒    ▓█████▄ ▒████▄     ██ ▀█   █ ",
    "▓██    ▓██░▒██  ▀█▄  ░ ▓██▄   ░ ▓██▄      ▒██▒ ▄██▒██  ▀█▄  ▓██  ▀█ ██▒",
    "▒██    ▒██ ░██▄▄▄▄██   ▒   ██▒  ▒   ██▒   ▒██░█▀  ░██▄▄▄▄██ ▓██▒  ▐▌██▒",
    "▒██▒   ░██▒ ▓█   ▓██▒▒██████▒▒██████▒▒   ░▓█  ▀█▓ ▓█   ▓██▒▒██░   ▓██░",
    "░ ▒░   ░  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░▒ ▒▓▒ ▒ ░   ░▒▓███▀▒ ▒▒   ▓▒█░░ ▒░   ▒ ▒ ",
    "░  ░      ░  ▒   ▒▒ ░░ ░▒  ░ ░░ ░▒  ░ ░   ▒░▒   ░   ▒   ▒▒ ░░ ░░   ░ ▒░",
    "░      ░     ░   ▒   ░  ░  ░  ░  ░  ░      ░    ░   ░   ▒      ░   ░ ░ ",
    "       ░         ░  ░      ░        ░      ░            ░  ░         ░ ",
    "                                                ░                      "
]

def get_ssl_ctx() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    except AttributeError:
        pass
    try:
        ctx.set_ciphers('DEFAULT:!aNULL:!MD5')
    except ssl.SSLError:
        pass
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


class UserAgentGenerator:

    CHROME_VERSIONS = list(range(128, 145))
    FIREFOX_VERSIONS = list(range(130, 145))
    EDGE_VERSIONS = list(range(128, 145))
    OPERA_VERSIONS = list(range(118, 135))
    SAFARI_VERSIONS = ["17.5", "18.0", "18.1", "18.2", "18.3", "19.0", "19.1", "19.2", "20.0"]

    PLATFORMS: List[Tuple[str, str, str]] = [
        ("Windows NT 10.0; Win64; x64", "Windows", "10.0"),
        ("Windows NT 11.0; Win64; x64", "Windows", "11.0"),
        ("Macintosh; Intel Mac OS X 10_15_7", "macOS", "10.15.7"),
        ("Macintosh; Intel Mac OS X 11_6_0", "macOS", "11.6.0"),
        ("Macintosh; Intel Mac OS X 12_5_0", "macOS", "12.5.0"),
        ("Macintosh; Intel Mac OS X 13_4_0", "macOS", "13.4.0"),
        ("Macintosh; Intel Mac OS X 14_3_0", "macOS", "14.3.0"),
        ("Macintosh; Intel Mac OS X 15_2_0", "macOS", "15.2.0"),
        ("X11; Linux x86_64", "Linux", "unknown"),
        ("X11; Linux aarch64", "Linux", "unknown"),
        ("Macintosh; ARM64 Mac OS X 14_3_0", "macOS", "14.3.0"),
        ("Macintosh; ARM64 Mac OS X 15_2_0", "macOS", "15.2.0"),
    ]

    DISCORD_WIN = "Mozilla/5.0 (Windows NT {winver}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.{discord_build} Chrome/{chrome_ver}.0.{chrome_build}.{chrome_patch} Electron/{electron_ver}.0.{electron_patch} Safari/537.36"
    DISCORD_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_ver}) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.{discord_build} Chrome/{chrome_ver}.0.{chrome_build}.{chrome_patch} Electron/{electron_ver}.0.{electron_patch} Safari/537.36"
    DISCORD_ARM = "Mozilla/5.0 (Macintosh; ARM64 Mac OS X {mac_ver}) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.{discord_build} Chrome/{chrome_ver}.0.{chrome_build}.{chrome_patch} Electron/{electron_ver}.0.{electron_patch} Safari/537.36"

    def generate_ua(self, browser: str = "discord") -> Tuple[str, str, str, str, str]:
        platform_str, os_name, os_ver = random.choice(self.PLATFORMS)
        chrome_ver = random.choice(self.CHROME_VERSIONS)
        chrome_build = random.randint(0, 9999)
        chrome_patch = random.randint(0, 999)

        if browser == "discord" or random.random() < 0.60:
            discord_build = random.randint(9000, 9999)
            electron_ver = random.choice([32, 33, 34, 35, 36])
            electron_patch = random.randint(0, 9)

            if "ARM64" in platform_str or "arm64" in platform_str:
                mac_ver = os_ver.replace("_", ".") if os_ver != "unknown" else "14_3_0"
                ua = self.DISCORD_ARM.format(mac_ver=mac_ver, discord_build=discord_build,
                                             chrome_ver=chrome_ver, chrome_build=chrome_build,
                                             chrome_patch=chrome_patch, electron_ver=electron_ver,
                                             electron_patch=electron_patch)
            elif "Macintosh" in platform_str:
                mac_ver = os_ver.replace("_", ".") if "Mac OS X" in platform_str else "10_15_7"
                ua = self.DISCORD_MAC.format(mac_ver=mac_ver, discord_build=discord_build,
                                             chrome_ver=chrome_ver, chrome_build=chrome_build,
                                             chrome_patch=chrome_patch, electron_ver=electron_ver,
                                             electron_patch=electron_patch)
            else:
                win_ver = os_ver
                ua = self.DISCORD_WIN.format(winver=win_ver, discord_build=discord_build,
                                             chrome_ver=chrome_ver, chrome_build=chrome_build,
                                             chrome_patch=chrome_patch, electron_ver=electron_ver,
                                             electron_patch=electron_patch)
            return ua, os_name, os_ver, "Discord Client", f"{chrome_ver}.0.0.0"

        if browser == "chrome" or random.random() < 0.20:
            ua = f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver}.0.{chrome_build}.{chrome_patch} Safari/537.36"
            return ua, os_name, os_ver, "Chrome", f"{chrome_ver}.0.0.0"

        if browser == "firefox" or random.random() < 0.10:
            firefox_ver = random.choice(self.FIREFOX_VERSIONS)
            ua = f"Mozilla/5.0 ({platform_str}; rv:{firefox_ver}.0) Gecko/20100101 Firefox/{firefox_ver}.0"
            return ua, os_name, os_ver, "Firefox", f"{firefox_ver}.0"

        if browser == "edge" or random.random() < 0.07:
            edge_ver = random.choice(self.EDGE_VERSIONS)
            ua = f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver}.0.{chrome_build}.{chrome_patch} Safari/537.36 Edg/{edge_ver}.0.{random.randint(0,9999)}.{random.randint(0,999)}"
            return ua, os_name, os_ver, "Edge", f"{edge_ver}.0.0.0"

        if browser == "safari" or random.random() < 0.03:
            safari_ver = random.choice(self.SAFARI_VERSIONS)
            platform_safari = "Macintosh; Intel Mac OS X 10_15_7"
            ua = f"Mozilla/5.0 ({platform_safari}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{safari_ver} Safari/605.1.15"
            return ua, os_name, "10.15.7", "Safari", safari_ver

        ua = f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver}.0.{chrome_build}.{chrome_patch} Safari/537.36"
        return ua, os_name, os_ver, "Chrome", f"{chrome_ver}.0.0.0"

    def get_next(self) -> Tuple[str, str, str, str, str]:
        return self.generate_ua()

    @staticmethod
    def extract_chrome_version(ua: str) -> str:
        m = re.search(r'Chrome/(\d+)', ua)
        return m.group(1) if m else "135"


class BuildNumberManager:

    BUILD_NUMBERS = [
        291234, 292456, 293678, 294890, 296012, 297134, 298256, 299378,
        300500, 301622, 302744, 303866, 304988, 306110, 307232, 308354,
        309476, 310598, 311720, 312842, 313964, 315086, 316208, 317330,
        318452, 319574, 320696, 321818, 322940, 324062, 325184, 326306,
        327428, 328550, 329672, 330794, 331916, 333038, 334160, 335282,
        336404, 337526, 338648, 339770, 340892, 342014, 343136, 344258,
        345380, 346502, 347624, 348746, 349868, 350990, 352112, 353234,
        354356, 355478, 356600, 357722, 358844, 359966, 361088, 362210,
        363332, 364454, 365576, 366698, 367820, 368942, 370064, 371186,
        372308, 373430, 374552, 375674, 376796, 377918, 379040, 380162,
        381284, 382406, 383528, 384650, 385772, 386894, 388016, 389138,
        390260, 391382, 392504, 393626, 394748, 395870, 396992, 398114,
        399236, 400358, 401480, 402602, 403724, 404846, 405968, 407090,
        408212, 409334, 410456, 411578, 412700, 413822, 414944, 416066,
        417188, 418310, 419432, 420554, 421676, 422798, 423920, 425042,
        426164, 427286, 428408, 429530, 430652, 431774, 432896, 434018,
        435140, 436262, 437384, 438506, 439628, 440750, 441872, 442994,
        444116, 445238, 446360, 447482, 448604, 449726, 450848, 451970,
    ]

    def __init__(self):
        self._cached = list(self.BUILD_NUMBERS)
        self._last_fetch = 0.0
        self._fetch_lock = asyncio.Lock()
        self._fetch_task: Optional[asyncio.Task] = None

    async def get_build_number(self) -> int:
        now = time.time()
        if now - self._last_fetch > 3600:
            if self._fetch_task is None or self._fetch_task.done():
                self._fetch_task = asyncio.create_task(self._try_fetch())
        return random.choice(self._cached)

    async def _try_fetch(self):
        async with self._fetch_lock:
            now = time.time()
            if now - self._last_fetch < 3600:
                return
            self._last_fetch = now  # set immediately to prevent thundering herd
            fetch_succeeded = False
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
                headers = {"User-Agent": ua, "Accept": "text/html,application/xhtml+xml"}
                fetch_conn_kwargs = {"ssl": get_ssl_ctx(), "limit": 1, "force_close": True}
                try:
                    from aiohttp.resolver import ThreadedResolver
                    fetch_conn_kwargs["resolver"] = ThreadedResolver()
                except Exception:
                    pass
                conn2 = aiohttp.TCPConnector(**fetch_conn_kwargs)
                async with aiohttp.ClientSession(connector=conn2, timeout=timeout) as session:
                    try:
                        async with session.get("https://discord.com/app", headers=headers) as resp:
                            if resp.status == 200:
                                html = await resp.text()
                                patterns = [
                                    r'build_number["\':\s]+(\d{5,6})',
                                    r'BUILD_NUMBER["\':\s]+(\d{5,6})',
                                    r'client_build_number["\':\s]+(\d{5,6})',
                                ]
                                for pat in patterns:
                                    m = re.search(pat, html, re.IGNORECASE)
                                    if m:
                                        bn = int(m.group(1))
                                        if 200000 < bn < 999999 and bn not in self._cached:
                                            self._cached.insert(0, bn)
                                            if len(self._cached) > 250:
                                                self._cached = self._cached[:200]
                                        fetch_succeeded = True
                                        return
                    except Exception:
                        pass

                    update_headers = {"User-Agent": "Discord/1.0", "Accept": "application/json"}
                    async with session.get("https://discord.com/api/updates/stable", headers=update_headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if isinstance(data, dict):
                                for key in ("build", "build_number", "version"):
                                    val = data.get(key)
                                    if val:
                                        try:
                                            bn = int(str(val))
                                            if 200000 < bn < 999999 and bn not in self._cached:
                                                self._cached.insert(0, bn)
                                                if len(self._cached) > 250:
                                                    self._cached = self._cached[:200]
                                            fetch_succeeded = True
                                            break
                                        except (ValueError, TypeError):
                                            continue
            except Exception:
                pass
            finally:
                if not fetch_succeeded:
                    self._last_fetch = 0.0  # reset so retry can happen sooner, not wait 3600s


class SuperPropertiesGenerator:

    def __init__(self, build_manager: BuildNumberManager, ua_gen: UserAgentGenerator):
        self.build_manager = build_manager
        self.ua_gen = ua_gen
        self._cache: Dict[str, Tuple[float, str]] = {}

    async def build(self, ua: str, os_name: str, os_ver: str, browser_name: str, browser_ver: str) -> str:
        bn = await self.build_manager.get_build_number()
        locale = random.choice(["en-US", "en-GB", "en", "ja-JP", "de-DE", "fr-FR",
                                "ko-KR", "pt-BR", "es-ES", "zh-CN", "ru-RU"])

        referrer = "https://discord.com/channels/@me" if random.random() > 0.2 else "https://discord.com/login"
        referring_domain = "discord.com"

        sp = OrderedDict()
        sp["os"] = os_name
        sp["browser"] = browser_name
        sp["device"] = ""
        sp["system_locale"] = locale
        sp["browser_user_agent"] = ua
        sp["browser_version"] = browser_ver
        sp["os_version"] = os_ver
        sp["referrer"] = referrer
        sp["referring_domain"] = referring_domain
        sp["referrer_current"] = referrer
        sp["referring_domain_current"] = referring_domain
        sp["release_channel"] = "stable"
        sp["client_build_number"] = bn
        sp["client_event_source"] = None

        if random.random() > 0.5:
            sp["client_version"] = f"1.0.{bn}"
        if random.random() > 0.6:
            sp["native_build_number"] = random.choice([0, bn - random.randint(1, 100)])
        if random.random() > 0.7:
            sp["os_arch"] = random.choice(["x64", "arm64", "x86"])
        if random.random() > 0.8:
            sp["design_version"] = random.randint(1, 5)

        encoded = base64.b64encode(json.dumps(sp, separators=(",", ":")).encode()).decode()
        return encoded


class XContextPropertiesGenerator:

    @staticmethod
    def generate(guild_id: str = "") -> str:
        data = {"location": "GuildHeader", "location_guild_id": guild_id, "location_channel_id": ""}
        if random.random() > 0.3:
            data["location"] = random.choice(["GuildHeader", "ContextMenu", "MemberList", "ModerationView"])
        return base64.b64encode(json.dumps(data, separators=(",", ":")).encode()).decode()


class XTrackGenerator:

    def __init__(self):
        self._fingerprint = self._generate_fingerprint()

    @staticmethod
    def _generate_fingerprint() -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))

    def generate(self) -> str:
        timestamp = int(time.time() * 1000)
        track_data = {
            "timestamp": timestamp,
            "fingerprint": self._fingerprint,
            "session_id": ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)),
            "sequence": random.randint(1, 9999),
            "sample": random.randint(0, 100),
        }
        return base64.b64encode(json.dumps(track_data, separators=(",", ":")).encode()).decode()


class RateLimitTracker:

    def __init__(self):
        self.buckets: Dict[str, Dict] = {}
        self.global_event = asyncio.Event()
        self.global_event.set()
        self.global_reset_at = 0.0
        self.lock = asyncio.Lock()
        self._request_times: List[float] = []
        self._global_task: Optional[asyncio.Task] = None

    def update_from_headers(self, headers: Dict[str, str], endpoint: str = ""):
        remaining = headers.get("X-RateLimit-Remaining")
        reset_after = headers.get("X-RateLimit-Reset-After")
        limit = headers.get("X-RateLimit-Limit")
        bucket = headers.get("X-RateLimit-Bucket", endpoint)
        is_global = headers.get("X-RateLimit-Global", "false").lower() == "true"
        scope = headers.get("X-RateLimit-Scope", "")

        now = time.time()

        if is_global or scope == "global":
            if self._global_task is not None and not self._global_task.done():
                self._global_task.cancel()
            self.global_event.clear()
            ra = float(reset_after or 1)
            self.global_reset_at = now + ra
            self._global_task = asyncio.create_task(self._clear_global_after(ra))
            return

        if bucket and remaining is not None:
            self.buckets[bucket] = {
                "remaining": int(remaining),
                "reset_after": float(reset_after or 1),
                "reset_at": now + float(reset_after or 1),
                "limit": int(limit or 50),
            }

    async def _clear_global_after(self, delay: float):
        try:
            await asyncio.sleep(delay + 0.1)
            self.global_event.set()
        except asyncio.CancelledError:
            pass

    def get_remaining(self) -> int:
        if not self.buckets:
            return 5  # endpoint-specific default limit for ban/kick endpoints
        now = time.time()
        min_remaining = 50  # upper bound, reduced by min() with actual bucket values
        for bname, bdata in self.buckets.items():
            remaining = bdata["remaining"]
            reset_at = bdata["reset_at"]
            if now < reset_at:
                min_remaining = min(min_remaining, max(0, remaining))
            else:
                min_remaining = min(min_remaining, bdata["limit"])
        return min_remaining

    def log_request(self):
        now = time.time()
        self._request_times.append(now)
        cutoff = now - 3
        self._request_times = [t for t in self._request_times if t > cutoff]

    def get_request_rate(self) -> int:
        now = time.time()
        recent = [t for t in self._request_times if t > now - 1]
        return len(recent)


class WebSocketKeeper:

    GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

    def __init__(self, token: str, proxy: Optional[str] = None,
                 sp_gen: Optional[SuperPropertiesGenerator] = None,
                 ua_gen: Optional[UserAgentGenerator] = None,
                 build_manager: Optional[BuildNumberManager] = None):
        self.token = token
        self.proxy = proxy
        self._ws = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._run_task: Optional[asyncio.Task] = None
        self._running = False
        self._stopped = False
        self._seq = 0
        self._session_id: Optional[str] = None
        self._heartbeat_interval = 41250.0
        self._close_lock = asyncio.Lock()
        self.ua_gen = ua_gen or UserAgentGenerator()
        self.build_manager = build_manager or BuildNumberManager()
        self.sp_gen = sp_gen or SuperPropertiesGenerator(self.build_manager, self.ua_gen)
        self._current_ua_info: Optional[Tuple[str, str, str, str, str]] = None
        self._member_chunks: Dict[str, List[Dict]] = {}
        self._member_futures: Dict[str, asyncio.Future] = {}
        self._member_callbacks: Dict[str, Any] = {}
        self._ready_event = asyncio.Event()

    async def _get_identify_payload(self, ua_info: Optional[Tuple[str, str, str, str, str]] = None) -> Dict:
        if ua_info:
            ua, os_name, os_ver, browser_name, browser_ver = ua_info
        else:
            ua, os_name, os_ver, browser_name, browser_ver = self.ua_gen.generate_ua()
        sp_encoded = await self.sp_gen.build(ua, os_name, os_ver, browser_name, browser_ver)
        bn = await self.build_manager.get_build_number()
        return {
            "op": 2,
            "d": {
                "token": self.token,
                "capabilities": 16383,
                "properties": {
                    "os": os_name,
                    "browser": browser_name,
                    "device": "",
                    "system_locale": "en-US",
                    "browser_user_agent": ua,
                    "browser_version": browser_ver,
                    "os_version": os_ver,
                    "referrer": "https://discord.com/channels/@me",
                    "referring_domain": "discord.com",
                    "referrer_current": "https://discord.com/channels/@me",
                    "referring_domain_current": "discord.com",
                    "release_channel": "stable",
                    "client_build_number": bn,
                },
                "presence": {
                    "status": random.choice(["online", "idle", "dnd"]),
                    "since": 0,
                    "activities": [],
                    "afk": False,
                },
                "compress": False,
                "guild_subscriptions": True,
            },
        }

    async def start(self):
        if self._running:
            return
        self._running = True
        self._stopped = False
        self._run_task = asyncio.create_task(self._run_forever())

    async def request_guild_members(self, guild_id: str, on_chunk: Optional[Any] = None) -> List[Dict]:
        future = asyncio.get_event_loop().create_future()
        self._member_futures[guild_id] = future
        self._member_chunks[guild_id] = []
        if on_chunk is not None:
            self._member_callbacks[guild_id] = on_chunk
        payload = {
            "op": 8,
            "d": {
                "guild_id": guild_id,
                "query": "",
                "limit": 0,
                "presences": False,
            }
        }
        try:
            await self._ws.send_json(payload)
            result = await asyncio.wait_for(future, timeout=60.0)
            return result
        except asyncio.TimeoutError:
            return []
        finally:
            self._member_futures.pop(guild_id, None)
            self._member_chunks.pop(guild_id, None)
            self._member_callbacks.pop(guild_id, None)

    async def wait_until_ready(self, timeout: float = 15.0) -> bool:
        if self._ready_event is None:
            self._ready_event = asyncio.Event()
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def _run_forever(self):
        attempt = 0
        while self._running and not self._stopped:
            try:
                await self._connect_and_handle()
                attempt = 0
            except asyncio.CancelledError:
                break
            except Exception as e:
                attempt += 1
                err_msg = str(e)[:80] if str(e) else "unknown error"
                print(f"  {r}!{w} WS reconnect attempt {attempt} due to: {err_msg}", flush=True)

            if self._running and not self._stopped:
                delay = min(60, 3 * (1.5 ** attempt))
                await asyncio.sleep(random.uniform(delay, delay * 1.2))

    async def _connect_and_handle(self):
        old_session = self._session
        if old_session and not old_session.closed:
            await old_session.close()
        self._session = None

        self._current_ua_info = self.ua_gen.generate_ua()
        ua, os_name, os_ver, browser_name, browser_ver = self._current_ua_info

        ws_conn_kwargs = {
            "limit": 1, "force_close": True, "ssl": get_ssl_ctx(),
            "use_dns_cache": True, "ttl_dns_cache": 300,
        }
        # Use ThreadedResolver for reliable DNS on Windows
        try:
            from aiohttp.resolver import ThreadedResolver
            ws_conn_kwargs["resolver"] = ThreadedResolver()
        except Exception:
            pass
        connector = aiohttp.TCPConnector(**ws_conn_kwargs)
        self._session = aiohttp.ClientSession(
            connector=connector,
            cookie_jar=aiohttp.CookieJar(),
            timeout=aiohttp.ClientTimeout(total=30, sock_connect=30, sock_read=60),
        )

        chrome_ver = UserAgentGenerator.extract_chrome_version(ua)
        sp_encoded = await self.sp_gen.build(ua, os_name, os_ver, browser_name, browser_ver)
        ws_headers = OrderedDict()
        ws_headers["User-Agent"] = ua
        ws_headers["Origin"] = "https://discord.com"
        ws_headers["Accept"] = "*/*"
        ws_headers["Accept-Language"] = "en-US,en;q=0.9"
        ws_headers["sec-ch-ua"] = f'"Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}", "Not)A;Brand";v="99"'
        ws_headers["sec-ch-ua-mobile"] = "?0"
        ws_headers["sec-ch-ua-platform"] = f'"{os_name}"'
        ws_headers["X-Super-Properties"] = sp_encoded
        ws_headers = dict(ws_headers)

        ws_kwargs = {
            "headers": ws_headers,
            "heartbeat": 30.0,
            "max_msg_size": 0,
            "timeout": 15.0,
        }
        if self.proxy:
            proxy_url = self.proxy
            if proxy_url.startswith("socks://"):
                proxy_url = "socks5://" + proxy_url[7:]
            elif not proxy_url.startswith(("http://", "https://", "socks5://", "socks4://")):
                proxy_url = "http://" + proxy_url
            ws_kwargs["proxy"] = proxy_url

        ws = None
        try:
            ws = await self._session.ws_connect(self.GATEWAY_URL, **ws_kwargs)
            self._ws = ws
            await self._handle_ws_messages(ws)
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            raise Exception(f"ws_connect: {type(e).__name__}: {str(e)[:100]}") from e
        finally:
            if ws is not None and not ws.closed:
                try:
                    await ws.close()
                except Exception:
                    pass
            self._ws = None

    async def _handle_ws_messages(self, ws):
        self._heartbeat_task = None
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    op = data.get("op")

                    if op == 10:
                        d = data.get("d", {})
                        self._heartbeat_interval = float(d.get("heartbeat_interval", 41250))

                        if self._heartbeat_task and not self._heartbeat_task.done():
                            self._heartbeat_task.cancel()
                        self._heartbeat_task = asyncio.create_task(
                            self._heartbeat_loop(ws, self._heartbeat_interval)
                        )

                        self._ready_event.clear()
                        payload = await self._get_identify_payload(self._current_ua_info)
                        await ws.send_json(payload)

                    elif op == 0:
                        self._seq = data.get("s", self._seq)
                        t = data.get("t", "")
                        if t == "READY":
                            self._session_id = data["d"].get("session_id", "")
                            self._ready_event.set()
                        elif t == "RESUMED":
                            pass
                        elif t == "GUILD_MEMBERS_CHUNK":
                            d = data.get("d", {})
                            gid = d.get("guild_id", "")
                            members = d.get("members", [])
                            chunk_index = d.get("chunk_index", 0)
                            chunk_count = d.get("chunk_count", 1)
                            if gid in self._member_futures:
                                if gid not in self._member_chunks:
                                    self._member_chunks[gid] = []
                                self._member_chunks[gid].extend(members)
                                if gid in self._member_callbacks and members:
                                    cb = self._member_callbacks[gid]
                                    if asyncio.iscoroutinefunction(cb):
                                        asyncio.ensure_future(cb(members))
                                    else:
                                        cb(members)
                                if chunk_index + 1 >= chunk_count:
                                    future = self._member_futures.pop(gid, None)
                                    if future and not future.done():
                                        future.set_result(self._member_chunks.pop(gid, []))

                    elif op == 1:
                        await ws.send_json({"op": 1, "d": self._seq})

                    elif op == 7:
                        break

                    elif op == 9:
                        d_val = data.get("d", False)
                        await asyncio.sleep(2 if d_val else 3)
                        self._ready_event.clear()
                        payload = await self._get_identify_payload(self._current_ua_info)
                        try:
                            await ws.send_json(payload)
                        except Exception:
                            break

                except (json.JSONDecodeError, KeyError):
                    continue

            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                break

        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except (asyncio.CancelledError, Exception):
                pass
        self._heartbeat_task = None

    async def _wait_for_ready(self):
        if self._ready_event is None:
            self._ready_event = asyncio.Event()
        else:
            self._ready_event.clear()
        await self._ready_event.wait()

    async def _heartbeat_loop(self, ws, interval_ms: float):
        interval = interval_ms / 1000.0
        try:
            while self._running and not self._stopped:
                jitter = random.uniform(-0.05 * interval, 0.05 * interval)
                await asyncio.sleep(interval + jitter)
                if ws.closed:
                    break
                try:
                    await ws.send_json({"op": 1, "d": self._seq})
                except Exception:
                    break
        except asyncio.CancelledError:
            pass

    async def stop(self):
        async with self._close_lock:
            if self._stopped:
                return
            self._stopped = True
            self._running = False

            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except (asyncio.CancelledError, Exception):
                    pass
            self._heartbeat_task = None

            if self._ws and not self._ws.closed:
                await self._ws.close()
            self._ws = None

            if self._run_task and not self._run_task.done():
                self._run_task.cancel()
                try:
                    await self._run_task
                except (asyncio.CancelledError, Exception):
                    pass
            self._run_task = None

            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None


class PreFlightValidator:

    @staticmethod
    async def validate_token(session: aiohttp.ClientSession, token: str, headers: Dict) -> Tuple[bool, Optional[Dict]]:
        try:
            async with session.get(
                "https://discord.com/api/v9/users/@me",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return True, data
                if resp.status in (403, 401):
                    try:
                        body = await resp.json()
                        msg = body.get("message", "").lower()
                        if "locked" in msg or "disabled" in msg or "phone" in msg:
                            return False, {"error": "locked_or_disabled", "detail": msg}
                    except Exception:
                        pass
                    return False, {"error": "invalid_token"}
                return False, {"error": f"status_{resp.status}"}
        except Exception as e:
            return False, {"error": str(e)[:60]}

    @staticmethod
    async def validate_permissions(session: aiohttp.ClientSession, token: str, guild_id: str,
                                    headers: Dict, check_ban: bool = True) -> Tuple[bool, str]:
        try:
            async with session.get(
                f"https://discord.com/api/v9/users/@me/guilds/{guild_id}/member",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    perms = int(data.get("permissions", 0))
                    if perms & 8:
                        return True, "administrator"
                    if check_ban and perms & 4:
                        return True, "ban_members"
                    if not check_ban and perms & 2:
                        return True, "kick_members"
                    return False, "missing_permissions"
                elif resp.status == 404:
                    return False, "not_in_guild"
                else:
                    return False, f"check_failed ({resp.status})"
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            return False, f"network_error: {str(e)[:50]}"
        except Exception as e:
            return False, f"error: {str(e)[:50]}"


class ModerationEngine:

    REASONS = [
        "raid cleanup", "server maintenance", "mass moderation", "inactive removal",
        "term violation", "spam cleanup", "security sweep", "member review",
        "server restructuring", "policy enforcement", "abuse prevention",
        "community guidelines", "suspicious activity", "unauthorized access",
        "TOS violation", "rule breaker", "automated sweep",
    ]

    @staticmethod
    def _generate_nonce() -> str:
        now = int(time.time() * 1000)
        return str((now - 1420070400000) << 22 | random.getrandbits(22))

    def __init__(self, tokens: List[str], guild_id: str,
                 proxies: Optional[List[str]] = None, action: str = "ban"):
        self.tokens = tokens
        self.guild_id = guild_id
        self.proxies = proxies or []
        self.action = action

        self.ua_gen = UserAgentGenerator()
        self.build_manager = BuildNumberManager()
        self.sp_gen = SuperPropertiesGenerator(self.build_manager, self.ua_gen)
        self.xt_gen = XTrackGenerator()
        self.xctx_gen = XContextPropertiesGenerator()

        self.rl_trackers = [RateLimitTracker() for _ in tokens]

        self.ws_keepers: List[Optional[WebSocketKeeper]] = [None] * len(tokens)

        self._sessions: List[Optional[aiohttp.ClientSession]] = [None] * len(tokens)

        self.success_count = 0
        self.fail_count = 0
        self.total_processed = 0
        self.total_members = 0
        self.stats_lock = asyncio.Lock()

        self.token_health = [True] * len(tokens)
        self.token_cooldown_until = [0.0] * len(tokens)
        self.token_consecutive_fails = [0] * len(tokens)
        self.token_lock = asyncio.Lock()

        self.members: List[Dict] = []

        self._print_batch: List[str] = []
        self._print_lock = asyncio.Lock()
        self._last_print = 0.0

    async def _get_or_create_session(self, token_idx: int, proxy: Optional[str] = None) -> aiohttp.ClientSession:
        session = self._sessions[token_idx]
        if session is not None and not session.closed:
            # Connection health check: recreate if too many consecutive fails
            if self.token_consecutive_fails[token_idx] >= 3:
                await session.close()
                self._sessions[token_idx] = None
            else:
                return session

        conn_kwargs: Dict[str, Any] = {
            "limit": 100,
            "limit_per_host": 25,
            "force_close": True,
            "ttl_dns_cache": 300,
            "ssl": get_ssl_ctx(),
            "use_dns_cache": True,
        }

        if HAS_AIO_DNS:
            try:
                resolver = aiohttp.AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])
                conn_kwargs["resolver"] = resolver
            except Exception:
                pass
        else:
            # On Windows, default asyncio DNS resolver often fails; use ThreadedResolver
            try:
                from aiohttp.resolver import ThreadedResolver
                resolver = ThreadedResolver()
                conn_kwargs["resolver"] = resolver
            except Exception:
                pass

        use_http2 = HAS_HTTP2 and not proxy
        if use_http2:
            try:
                conn = aiohttp.TCPConnector(http2=True, **conn_kwargs)
            except TypeError:
                conn = aiohttp.TCPConnector(**conn_kwargs)
        else:
            conn = aiohttp.TCPConnector(**conn_kwargs)

        dcfduid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        sdcfduid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        cookie_jar = aiohttp.CookieJar()
        cookie_jar.update_cookies(
            {"__dcfduid": dcfduid, "__sdcfduid": sdcfduid, "locale": "en-US"},
            URL("https://discord.com")
        )

        session_kwargs: Dict[str, Any] = {
            "connector": conn,
            "cookie_jar": cookie_jar,
            "timeout": aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=60),
        }
        if proxy:
            session_kwargs["proxy"] = proxy

        session = aiohttp.ClientSession(**session_kwargs)
        self._sessions[token_idx] = session
        return session

    async def _close_sessions(self):
        for i, session in enumerate(self._sessions):
            if session is not None and not session.closed:
                try:
                    await session.close()
                except Exception:
                    pass
                self._sessions[i] = None

    async def _build_headers(self, token: str, ua: str, os_name: str, os_ver: str,
                              browser_name: str, browser_ver: str) -> Dict[str, str]:
        chrome_ver = UserAgentGenerator.extract_chrome_version(ua)
        sp_encoded = await self.sp_gen.build(ua, os_name, os_ver, browser_name, browser_ver)

        headers = OrderedDict()
        headers["User-Agent"] = ua
        headers["Accept"] = "*/*"
        headers["Accept-Language"] = random.choice([
            "en-US,en;q=0.9",
            "en-US,en;q=0.9,en-GB;q=0.8",
            "en-US,en;q=0.8",
            "en,en-US;q=0.9,en-GB;q=0.7",
        ])
        headers["Accept-Encoding"] = "gzip, deflate, br"
        headers["Content-Type"] = "application/json"
        headers["Origin"] = "https://discord.com"
        headers["Referer"] = random.choice([
            "https://discord.com/channels/@me",
            f"https://discord.com/channels/{self.guild_id}",
            "https://discord.com/login",
        ])
        headers["Sec-Fetch-Dest"] = "empty"
        headers["Sec-Fetch-Mode"] = "cors"
        headers["Sec-Fetch-Site"] = "same-origin"
        headers["Cache-Control"] = "no-cache"
        headers["Pragma"] = "no-cache"

        if random.random() > 0.2:
            headers["Connection"] = "keep-alive"

        if random.random() > 0.4:
            headers["DNT"] = random.choice(["1", "0"])

        headers["sec-ch-ua"] = f'"Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}", "Not)A;Brand";v="99"'
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = f'"{os_name}"'

        xctx = self.xctx_gen.generate(self.guild_id)

        headers["X-Super-Properties"] = sp_encoded
        headers["X-Context-Properties"] = xctx
        headers["X-Discord-Locale"] = random.choice(["en-US", "en-GB", "en", "ja-JP"])
        headers["X-Debug-Options"] = "bugReporterEnabled"
        headers["X-Track"] = self.xt_gen.generate()
        headers["Authorization"] = token

        return dict(headers)

    async def _deferred_print(self, message: str):
        async with self._print_lock:
            self._print_batch.append(message)
            now = time.time()
            batch_size = len(self._print_batch)
            if batch_size >= 15 or (now - self._last_print > 0.3 and batch_size > 0):
                out = "\n".join(self._print_batch)
                self._print_batch.clear()
                self._last_print = now
                sys.stdout.write(out + "\n")
                sys.stdout.flush()

    async def _flush_print(self):
        async with self._print_lock:
            if self._print_batch:
                out = "\n".join(self._print_batch)
                self._print_batch.clear()
                self._last_print = time.time()
                sys.stdout.write(out + "\n")
                sys.stdout.flush()

    async def _get_next_token_weighted(self) -> Tuple[int, str, Optional[str]]:
        max_retries = 30
        retries = 0
        while True:
            retries += 1
            async with self.token_lock:
                now = time.time()
                candidates = []
                for i in range(len(self.tokens)):
                    if self.token_health[i] and now >= self.token_cooldown_until[i]:
                        remaining = self.rl_trackers[i].get_remaining()
                        candidates.append((remaining, i))

                if candidates:
                    candidates.sort(key=lambda x: -x[0])
                    best_idx = candidates[0][1]
                    proxy = self.proxies[best_idx % len(self.proxies)] if self.proxies else None
                    return best_idx, self.tokens[best_idx], proxy

            if retries > max_retries:
                async with self.token_lock:
                    now = time.time()
                    best_idx = min(
                        range(len(self.tokens)),
                        key=lambda i: self.token_cooldown_until[i]
                    )
                    self.token_health[best_idx] = True
                    self.token_consecutive_fails[best_idx] = 0
                    self.token_cooldown_until[best_idx] = now
                    proxy = self.proxies[best_idx % len(self.proxies)] if self.proxies else None
                    return best_idx, self.tokens[best_idx], proxy

            async with self.token_lock:
                earliest_idx = min(
                    range(len(self.tokens)),
                    key=lambda i: self.token_cooldown_until[i]
                )
                wait_time = self.token_cooldown_until[earliest_idx] - now

            if wait_time > 0:
                await asyncio.sleep(min(wait_time, 3))
                continue

            async with self.token_lock:
                if not self.token_health[earliest_idx]:
                    self.token_health[earliest_idx] = True
                    self.token_consecutive_fails[earliest_idx] = 0
                proxy = self.proxies[earliest_idx % len(self.proxies)] if self.proxies else None
                return earliest_idx, self.tokens[earliest_idx], proxy

    def _get_assigned_token(self, worker_id: int) -> Tuple[int, str, Optional[str]]:
        idx = worker_id % len(self.tokens)
        proxy = self.proxies[idx % len(self.proxies)] if self.proxies else None
        return idx, self.tokens[idx], proxy

    async def _moderate_member(self, token_idx: int, token: str,
                                proxy: Optional[str], member: Dict) -> bool:
        user_id = member.get("user", {}).get("id")
        username = member.get("user", {}).get("username", "unknown")
        discriminator = member.get("user", {}).get("discriminator", "0")

        if not user_id:
            return False

        rl_tracker = self.rl_trackers[token_idx]

        if self.action == "ban":
            url = f"https://discord.com/api/v9/guilds/{self.guild_id}/bans/{user_id}"
            method = "PUT"
            delete_days = random.choice([0, 0, 0, 0, 1, 1, 2])
            reason = random.choice(self.REASONS) + f" [{random.choice(string.ascii_uppercase)}{random.randint(100,999)}]"
            payload: Optional[Dict] = {"delete_message_days": delete_days, "reason": reason, "nonce": self._generate_nonce()}
        else:
            url = f"https://discord.com/api/v9/guilds/{self.guild_id}/members/{user_id}"
            method = "DELETE"
            payload = {"nonce": self._generate_nonce()} if random.random() > 0.3 else None

        await asyncio.sleep(random.uniform(0.01, 0.04))

        ua, os_name, os_ver, browser_name, browser_ver = self.ua_gen.generate_ua()
        headers = await self._build_headers(token, ua, os_name, os_ver, browser_name, browser_ver)

        max_retries = 5
        base_delay = 0.3

        for attempt in range(max_retries):
            await rl_tracker.global_event.wait()

            try:
                session = await self._get_or_create_session(token_idx, proxy=proxy)
            except Exception:
                return False

            kwargs: Dict[str, Any] = {
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=30, sock_read=30),
            }
            if payload is not None:
                kwargs["json"] = payload
            # proxy is already set at session level via _get_or_create_session, no need per-request

            try:
                async with session.request(method, url, **kwargs) as resp:
                    rl_tracker.log_request()
                    rl_tracker.update_from_headers(dict(resp.headers), endpoint=self.action)

                    if resp.status in (200, 201, 204):
                        await self._update_stats(True)
                        display_name = f"{username}#{discriminator}" if discriminator != "0" else username
                        action_past = "banned" if self.action == "ban" else "kicked"
                        await self._deferred_print(
                            f"  {lg}+{w} {action_past} {display_name} [{await self._get_stats_str()}]"
                        )
                        self.token_consecutive_fails[token_idx] = 0
                        return True

                    elif resp.status == 429:
                        try:
                            body_text = await resp.text()
                            j = json.loads(body_text)
                            retry = float(j.get("retry_after", base_delay * (1.5 ** attempt)))
                            is_global = j.get("global", False)
                        except (json.JSONDecodeError, ValueError, TypeError):
                            retry = base_delay * (1.5 ** attempt)
                            is_global = False

                        if is_global:
                            if rl_tracker._global_task and not rl_tracker._global_task.done():
                                rl_tracker._global_task.cancel()
                            rl_tracker.global_event.clear()
                            delay = retry + random.uniform(0.1, 0.3)
                            rl_tracker._global_task = asyncio.create_task(
                                rl_tracker._clear_global_after(delay)
                            )
                            await rl_tracker.global_event.wait()
                        else:
                            await asyncio.sleep(retry + random.uniform(0, 0.2))
                        continue

                    elif resp.status in (403, 401):
                        self.token_health[token_idx] = False
                        self.token_consecutive_fails[token_idx] += 1
                        cooldown = min(60, 15 * (1.5 ** self.token_consecutive_fails[token_idx]))
                        self.token_cooldown_until[token_idx] = time.time() + cooldown
                        await self._update_stats(False)
                        display_name = f"{username}#{discriminator}" if discriminator != "0" else username
                        error_msg = "no perms" if resp.status == 403 else "unauthorized"
                        await self._deferred_print(
                            f"  {r}-{w} failed {self.action} {display_name} ({error_msg})"
                        )
                        return False

                    elif resp.status == 404:
                        self.token_health[token_idx] = False
                        self.token_consecutive_fails[token_idx] += 1
                        cooldown = min(30, 5 * (1.5 ** self.token_consecutive_fails[token_idx]))
                        self.token_cooldown_until[token_idx] = time.time() + cooldown
                        await self._update_stats(False)
                        display_name = f"{username}#{discriminator}" if discriminator != "0" else username
                        await self._deferred_print(
                            f"  {r}-{w} failed {self.action} {display_name} (not found/user left)"
                        )
                        return False

                    else:
                        if attempt < max_retries - 1:
                            delay = min(base_delay * (1.5 ** attempt) + random.uniform(0, 0.3), 10)
                            await asyncio.sleep(delay)
                            continue
                        self.token_health[token_idx] = False
                        self.token_consecutive_fails[token_idx] += 1
                        cooldown = min(30, 5 * (1.5 ** self.token_consecutive_fails[token_idx]))
                        self.token_cooldown_until[token_idx] = time.time() + cooldown
                        await self._update_stats(False)
                        display_name = f"{username}#{discriminator}" if discriminator != "0" else username
                        await self._deferred_print(
                            f"  {r}-{w} failed {self.action} {display_name} (HTTP {resp.status})"
                        )
                        return False
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                if attempt < max_retries - 1:
                    delay = min(base_delay * (1.5 ** attempt) + random.uniform(0, 0.3), 10)
                    await asyncio.sleep(delay)
                    continue
                self.token_health[token_idx] = False
                self.token_consecutive_fails[token_idx] += 1
                cooldown = min(15, 3 * (1.5 ** self.token_consecutive_fails[token_idx]))
                self.token_cooldown_until[token_idx] = time.time() + cooldown
                await self._update_stats(False)
                display_name = f"{username}#{discriminator}" if discriminator != "0" else username
                await self._deferred_print(
                    f"  {r}-{w} failed {self.action} {display_name} (network err)"
                )
                return False

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = min(base_delay * (1.5 ** attempt) + random.uniform(0, 0.3), 10)
                    await asyncio.sleep(delay)
                    continue
                await self._update_stats(False)
                display_name = f"{username}#{discriminator}" if discriminator != "0" else username
                await self._deferred_print(
                    f"  {r}-{w} failed {self.action} {display_name} (err)"
                )
                return False

        return False

    async def _update_stats(self, success: bool):
        async with self.stats_lock:
            if success:
                self.success_count += 1
            else:
                self.fail_count += 1
            self.total_processed += 1

    async def _get_stats_str(self) -> str:
        async with self.stats_lock:
            return f"{self.success_count}/{self.total_members}"

    async def _worker(self, worker_id: int, queue: asyncio.Queue):
        assigned_idx, assigned_token, assigned_proxy = self._get_assigned_token(worker_id)

        while True:
            member = await queue.get()

            if member is None:
                queue.task_done()
                break

            try:
                idx, tkn, proxy = assigned_idx, assigned_token, assigned_proxy
                now_local = time.time()
                if (not self.token_health[idx] or
                        now_local < self.token_cooldown_until[idx]):
                    idx, tkn, proxy = await self._get_next_token_weighted()
                    assigned_idx, assigned_token, assigned_proxy = idx, tkn, proxy

                await self._moderate_member(idx, tkn, proxy, member)
            except Exception as e:
                await self._update_stats(False)
                display_name = member.get("user", {}).get("username", "unknown")
                await self._deferred_print(
                    f"  {r}-{w} failed {self.action} {display_name} (worker err)"
                )
            finally:
                queue.task_done()

    async def run(self, num_workers: int = 30) -> Tuple[int, int]:
        start_time = time.time()

        idx, self_token, _ = await self._get_next_token_weighted()
        proxy = self.proxies[idx % len(self.proxies)] if self.proxies else None

        # Get self ID first
        session = await self._get_or_create_session(idx, proxy=proxy)
        ua, os_name, os_ver, bn, bv = self.ua_gen.generate_ua()
        hdrs = await self._build_headers(self_token, ua, os_name, os_ver, bn, bv)
        self_id = None
        try:
            async with session.get(
                "https://discord.com/api/v9/users/@me",
                headers=hdrs,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    self_data = await resp.json()
                    self_id = self_data.get("id")
        except Exception:
            pass

        ws_start_tasks = []
        for i, tkn in enumerate(self.tokens):
            proxy_w = self.proxies[i % len(self.proxies)] if self.proxies else None
            keeper = WebSocketKeeper(tkn, proxy_w, self.sp_gen, self.ua_gen, self.build_manager)
            self.ws_keepers[i] = keeper
            try:
                task = asyncio.create_task(keeper.start())
                ws_start_tasks.append(task)
            except Exception:
                pass

        effective_workers = max(num_workers, len(self.tokens) * 2)
        effective_workers = min(effective_workers, 150)

        queue: asyncio.Queue = asyncio.Queue(maxsize=effective_workers * 3)

        workers = []
        for i in range(effective_workers):
            worker = asyncio.create_task(self._worker(i, queue))
            workers.append(worker)

        # Producer: fetch members via WebSocket op 8 (REST API doesn't list members with user tokens)
        async def fetch_producer():
            total_fetched = 0
            print(f"  {y}!{w} fetching members via WebSocket...", flush=True)

            ready_keeper = None
            for keeper in self.ws_keepers:
                if keeper is not None:
                    if await keeper.wait_until_ready(timeout=30.0):
                        ready_keeper = keeper
                        break

            if ready_keeper is None:
                print(f"  {r}-{w} WebSocket connection failed, aborting", flush=True)
                self.total_members = 0
                for _ in range(effective_workers):
                    await queue.put(None)
                return

            async def on_member_chunk(members):
                nonlocal total_fetched
                for m in members:
                    uid = m.get("user", {}).get("id")
                    if uid and uid != self_id:
                        await queue.put(m)
                        total_fetched += 1

            await ready_keeper.request_guild_members(self.guild_id, on_chunk=on_member_chunk)

            self.total_members = total_fetched
            for _ in range(effective_workers):
                await queue.put(None)
            print(f"  {lg}+{w} fetch done, {total_fetched} members queued. waiting for workers...", flush=True)

        fetch_task = asyncio.create_task(fetch_producer())

        await fetch_task
        await queue.join()

        gather_results = await asyncio.gather(*workers, return_exceptions=True)
        for i, result in enumerate(gather_results):
            if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                await self._deferred_print(
                    f"  {y}!{w} worker {i} exited: {str(result)[:60]}"
                )

        await self._flush_print()

        for keeper in self.ws_keepers:
            if keeper:
                try:
                    await asyncio.wait_for(keeper.stop(), timeout=5.0)
                except (asyncio.TimeoutError, Exception):
                    pass

        await self._close_sessions()

        elapsed = time.time() - start_time
        print(f"\n  {c}{"-" * 50}{w}", flush=True)
        action_name = self.action.upper()
        print(f"  {lm}MASS {action_name} COMPLETE!{w}", flush=True)
        print(f"  {lg}+{w} success: {self.success_count}", flush=True)
        print(f"  {r}-{w} failed: {self.fail_count}", flush=True)
        print(f"  {c}@{w} time: {elapsed:.2f}s ({self.total_members / max(elapsed, 0.1):.1f} mem/s)", flush=True)

        return self.success_count, self.fail_count


def get_term_width() -> int:
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def center_block(lines: List[str]) -> List[str]:
    tw = get_term_width()
    ml = max(len(l) for l in lines) if lines else 0
    pad = max(0, (tw - ml) // 2)
    return [" " * pad + l for l in lines]


def show_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        from pystyle import Colors, Colorate
        tw = get_term_width()
        for line in center_block(BANNER):
            print(Colorate.Horizontal(Colors.purple_to_red, line, 1))
        print()
        sep = Colorate.Horizontal(Colors.purple_to_red, "─" * min(tw, 100), 1)
        print(sep)
    except Exception:
        for line in center_block(BANNER):
            print(f"\033[95m{line}\033[0m")
        print()
        print("─" * min(get_term_width(), 100))
    print()


def parse_tokens(raw: str) -> List[str]:
    tokens = re.split(r'[\s,;]+', raw.strip())
    return [t.strip() for t in tokens if t.strip()]


def parse_proxies(raw: str) -> List[str]:
    proxies = re.split(r'[\s,;]+', raw.strip())
    normalized = []
    for p in proxies:
        p = p.strip()
        if not p:
            continue
        if p.startswith("socks://"):
            p = "socks5://" + p[7:]
        elif not p.startswith(("http://", "https://", "socks5://", "socks4://")):
            p = "http://" + p
        normalized.append(p)
    return normalized


async def validate_single_token(session: aiohttp.ClientSession, token: str,
                                 index: int, ua_gen: UserAgentGenerator,
                                 build_manager: BuildNumberManager,
                                 sp_gen: SuperPropertiesGenerator) -> Tuple[bool, str, Optional[str]]:
    ua, os_name, os_ver, bn, bv = ua_gen.generate_ua()
    sp = await sp_gen.build(ua, os_name, os_ver, bn, bv)
    headers = {
        "Authorization": token,
        "User-Agent": ua,
        "X-Super-Properties": sp,
        "Content-Type": "application/json",
        "Accept": "*/*",
    }
    try:
        async with session.get(
            "https://discord.com/api/v9/users/@me",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status == 200:
                user_data = await resp.json()
                username = user_data.get('username', '?')
                disc = user_data.get('discriminator', '0')
                display = f"{username}#{disc}"
                return True, display, token
            elif resp.status in (403, 401):
                try:
                    body = await resp.json()
                    msg = body.get("message", "").lower()
                    if "locked" in msg or "disabled" in msg:
                        return False, "locked/disabled", token
                except Exception:
                    pass
                return False, f"invalid ({resp.status})", token
            else:
                return False, f"invalid ({resp.status})", token
    except Exception as e:
        return False, f"error: {str(e)[:30]}", token


async def validate_tokens_concurrent(tokens_raw: List[str]) -> List[str]:
    ua_gen = UserAgentGenerator()
    build_manager = BuildNumberManager()
    sp_gen = SuperPropertiesGenerator(build_manager, ua_gen)

    valid_tokens: List[str] = []
    total = len(tokens_raw)

    print(f"  {y}!{w} validating {total} token(s)...", flush=True)

    conn_kwargs: Dict[str, Any] = {
        "limit": 20, "limit_per_host": 10, "force_close": True, "ssl": get_ssl_ctx()
    }
    # Use ThreadedResolver for DNS on Windows
    try:
        from aiohttp.resolver import ThreadedResolver
        conn_kwargs["resolver"] = ThreadedResolver()
    except Exception:
        pass
    use_http2 = HAS_HTTP2
    if use_http2:
        try:
            conn = aiohttp.TCPConnector(http2=True, **conn_kwargs)
        except TypeError:
            conn = aiohttp.TCPConnector(**conn_kwargs)
    else:
        conn = aiohttp.TCPConnector(**conn_kwargs)
    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=30, connect=30)) as session:
        tasks = []
        for i, token in enumerate(tokens_raw):
            parts = token.split(".")
            if len(parts) != 3:
                print(f"  {r}-{w} token {i+1}: invalid format (not 3 parts)", flush=True)
                continue
            if not all(parts):
                print(f"  {r}-{w} token {i+1}: invalid format (empty parts)", flush=True)
                continue

            task = validate_single_token(session, token, i, ua_gen, build_manager, sp_gen)
            tasks.append((i, token, task))

        results = []
        for start in range(0, len(tasks), 10):
            batch = tasks[start:start+10]
            batch_results = await asyncio.gather(
                *[t[2] for t in batch], return_exceptions=True
            )
            for (idx, token_orig, _), result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"  {r}-{w} token {idx+1}: validation error", flush=True)
                    continue
                is_valid, display, _ = result
                if is_valid:
                    valid_tokens.append(token_orig)
                    print(f"  {lg}+{w} token {idx+1}: valid ({display})", flush=True)
                else:
                    print(f"  {r}-{w} token {idx+1}: {display}", flush=True)
            if start + 10 < len(tasks):
                await asyncio.sleep(0.1)

    return valid_tokens


async def main_async():
    while True:
        show_banner()
        print(f"  {p}[{w}1{p}] Mass Ban")
        print(f"  {p}[{w}2{p}] Mass Kick")
        print(f"  {p}[{w}3{p}] Exit")
        print()
        choice = (await asyncio.to_thread(input, f"  {p}[{w}>{p}] chon: {w}")).strip()

        if choice in ('1', '2'):
            action = "ban" if choice == '1' else "kick"

            os.system('cls' if os.name == 'nt' else 'clear')
            show_banner()

            print(f"  {c}?{w} nhap token(s) (nhieu token cach nhau boi space/comma/enter):")
            token_input = (await asyncio.to_thread(input, f"  {p}[{w}>{p}] token(s): {w}")).strip()
            tokens_raw = parse_tokens(token_input)

            if not tokens_raw:
                print(f"  {r}-{w} khong co token hop le!", flush=True)
                await asyncio.to_thread(input, f"\n  {p}[{w}>{p}] enter de quay ve menu...{w}")
                continue

            guild = (await asyncio.to_thread(input, f"  {p}[{w}>{p}] guild id: {w}")).strip()
            if not guild:
                print(f"  {r}-{w} guild id khong duoc de trong!", flush=True)
                await asyncio.to_thread(input, f"\n  {p}[{w}>{p}] enter de quay ve menu...{w}")
                continue

            proxy_input = (await asyncio.to_thread(input, f"  {p}[{w}>{p}] proxies (enter de bo qua): {w}")).strip()
            proxies = parse_proxies(proxy_input) if proxy_input else []

            worker_input = (await asyncio.to_thread(input, f"  {p}[{w}>{p}] workers [{w}20{p}]: {w}")).strip()
            try:
                workers_per_token = max(1, min(200, int(worker_input)))
            except ValueError:
                workers_per_token = 20

            valid_tokens = await validate_tokens_concurrent(tokens_raw)

            if not valid_tokens:
                print(f"\n  {r}-{w} khong co token hop le!", flush=True)
                await asyncio.to_thread(input, f"\n  {p}[{w}>{p}] enter de quay ve menu...{w}")
                continue

            print(f"\n  {y}!{w} checking guild access...", flush=True)
            try:
                ua_gen = UserAgentGenerator()
                build_manager = BuildNumberManager()
                sp_gen = SuperPropertiesGenerator(build_manager, ua_gen)
                ua, os_name, os_ver, bn, bv = ua_gen.generate_ua()
                sp = await sp_gen.build(ua, os_name, os_ver, bn, bv)
                hdrs = {
                    "Authorization": valid_tokens[0],
                    "User-Agent": ua,
                    "X-Super-Properties": sp,
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                }
                check_conn_kwargs = {"ssl": get_ssl_ctx(), "force_close": True}
                try:
                    from aiohttp.resolver import ThreadedResolver
                    check_conn_kwargs["resolver"] = ThreadedResolver()
                except Exception:
                    pass
                conn = aiohttp.TCPConnector(**check_conn_kwargs)
                async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=30, connect=30)) as sess:
                    async with sess.get(
                        f"https://discord.com/api/v9/guilds/{guild}",
                        headers=hdrs,
                    ) as gresp:
                        if gresp.status == 200:
                            guild_data = await gresp.json()
                            guild_name = guild_data.get('name', '?')
                            guild_members = guild_data.get('member_count', '?')
                            print(f"  {lg}+{w} guild: {guild_name} ({guild_members} members)", flush=True)
                        else:
                            print(f"  {r}-{w} cannot access guild (status {gresp.status})", flush=True)
                            print(f"  {y}!{w} continuing anyway...", flush=True)
            except Exception as e:
                print(f"  {r}-{w} guild check error, continuing...", flush=True)

            print(f"  {y}!{w} checking permissions...", flush=True)
            try:
                ua_gen = UserAgentGenerator()
                build_manager = BuildNumberManager()
                sp_gen = SuperPropertiesGenerator(build_manager, ua_gen)
                ua, os_name, os_ver, bn, bv = ua_gen.generate_ua()
                sp = await sp_gen.build(ua, os_name, os_ver, bn, bv)
                hdrs = {
                    "Authorization": valid_tokens[0],
                    "User-Agent": ua,
                    "X-Super-Properties": sp,
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                }
                check_conn_kwargs = {"ssl": get_ssl_ctx(), "force_close": True}
                try:
                    from aiohttp.resolver import ThreadedResolver
                    check_conn_kwargs["resolver"] = ThreadedResolver()
                except Exception:
                    pass
                conn = aiohttp.TCPConnector(**check_conn_kwargs)
                async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=30, connect=30)) as sess:
                    has_perms, perm_detail = await PreFlightValidator.validate_permissions(
                        sess, valid_tokens[0], guild, hdrs, check_ban=(action == "ban")
                    )
                    if has_perms:
                        print(f"  {lg}+{w} permission check: {perm_detail}", flush=True)
                    else:
                        print(f"  {y}!{w} permission: {perm_detail} (may still work)", flush=True)
            except Exception as e:
                print(f"  {r}-{w} permission check error, continuing...", flush=True)

            total_workers = workers_per_token * len(valid_tokens)
            print(f"  {y}!{w} starting mass {action} with {len(valid_tokens)} token(s), "
                  f"{total_workers} workers...\n", flush=True)

            engine = ModerationEngine(
                tokens=valid_tokens,
                guild_id=guild,
                proxies=proxies,
                action=action,
            )

            try:
                await engine.run(num_workers=total_workers)
            except asyncio.CancelledError:
                print(f"\n  {r}!{w} operation cancelled", flush=True)
            except Exception as e:
                print(f"\n  {r}!{w} error: {str(e)}", flush=True)
                import traceback
                traceback.print_exc()

            await asyncio.to_thread(input, f"\n  {p}[{w}>{p}] enter de quay ve menu...{w}")

        elif choice == '3':
            print(f"\n  {r}!{w} thoat...", flush=True)
            tasks = [t for t in asyncio.all_tasks()
                     if t is not asyncio.current_task()]
            for t in tasks:
                t.cancel()
            sys.exit(0)


def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n  {r}!{w} interrupt", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"\n  {r}!{w} fatal: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
