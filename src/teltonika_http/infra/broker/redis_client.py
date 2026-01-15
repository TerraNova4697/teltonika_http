import asyncio
from dataclasses import dataclass
import json
from typing import Any, Callable, Optional, Iterable, Union, List
import logging

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError


logger = logging.getLogger("RedisClient")


@dataclass
class ScanPage:
    cursor: int
    has_more: bool
    total: Optional[int]  # None если не подсчитывали
    keys: List[str]
    returned: int


class RedisClient:
    """
    Асинхронный инкапсулированный клиент для Redis.

    Поддерживает:
     - подключение через connection pool
     - автоматическую сериализацию (JSON)
     - базовые операции: get/set/delete, hget/hset, lpush/rpop
     - publish и простой subscribe с обработчиком
     - контекстный менеджер async with
    """
    def __init__(
        self,
        url: str = "redis://redis:6379/0",
        decode_responses: bool = False,
        max_connections: int = 10,
        reconnect_attempts: int = 5,
        reconnect_backoff: float = 0.5,  # базовый backoff в секундах
    ):
        self._url = url
        self._decode = decode_responses
        self._max_connections = max_connections
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._redis: Optional[aioredis.Redis] = None
        self._reconnect_attempts = reconnect_attempts
        self._reconnect_backoff = reconnect_backoff
        self._pubsub_tasks = set()
        self._closed = True
        self._dumps = json.dumps
        self._loads = json.loads

    async def connect(self) -> None:
        """Создать pool и клиент. Можно вызывать несколько раз — будет безопасно."""
        if self._redis and not self._closed:
            return
        self._pool = aioredis.ConnectionPool.from_url(
            self._url,
            max_connections=self._max_connections,
            decode_responses=self._decode,
        )
        self._redis = aioredis.Redis(connection_pool=self._pool, decode_responses=self._decode)
        # пробный запрос для проверки подключения
        await self._ensure_connected()
        self._closed = False

    async def startup(self):
        await self.connect()

    async def ping(self) -> bool:
        return await self._redis.ping()

    async def shutdown(self):
        await self.close()

    async def close(self) -> None:
        """Закрыть клиент и pool."""
        # отменяем задачи pubsub
        for t in list(self._pubsub_tasks):
            t.cancel()
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass
            self._redis = None
        if self._pool:
            try:
                await self._pool.disconnect()
            except Exception:
                pass
            self._pool = None
        self._closed = True

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _ensure_connected(self) -> None:
        """Проверка подключения с попытками повторного подключения."""
        last_exc = None
        for attempt in range(1, self._reconnect_attempts + 1):
            try:
                # PING как проверка
                if self._redis is None:
                    raise RedisConnectionError("redis client is None")
                pong = await self._redis.ping()
                if pong:
                    return
            except Exception as e:
                last_exc = e
                wait = self._reconnect_backoff * attempt
                await asyncio.sleep(wait)
                # recreate pool/client
                try:
                    if self._pool:
                        await self._pool.disconnect()
                except Exception:
                    pass
                self._pool = aioredis.ConnectionPool.from_url(
                    self._url,
                    max_connections=self._max_connections,
                    decode_responses=self._decode,
                )
                self._redis = aioredis.Redis(connection_pool=self._pool, decode_responses=self._decode)
        raise last_exc or RedisConnectionError("failed to connect to redis")

    def _to_bytes(self, obj: Any) -> bytes:
        # ensure bytes for redis (if using decode_responses=False)
        return self._dumps(obj).encode('utf-8')
    
    def _from_bytes(self, b: bytes) -> Any:
        if b is None:
            return None
        if isinstance(b, bytes):
            return self._loads(b.decode('utf-8'))
        return self._loads(b)

    # ---- basic commands ----
    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        Сохраняет значение. Сериализует Python объекты через JSON/orjson.
        ex — TTL в секундах.
        """
        await self.connect()
        try:
            if isinstance(value, (str, bytes)) and self._decode:
                # если decode_responses=True, redis принимает/возвращает строки
                payload = value
            else:
                payload = self._to_bytes(value)
            return await self._redis.set(key, payload, ex=ex)
        except (RedisConnectionError, OSError) as e:
            # попытка переподключиться и повторить один раз
            await self._ensure_connected()
            return await self._redis.set(key, payload, ex=ex)

    async def get(self, key: str) -> Any:
        """
        Возвращает распарсенный объект (если данные были сериализованы JSON).
        Если ключ отсутствует — None.
        """
        await self.connect()
        try:
            raw = await self._redis.get(key)
        except (RedisConnectionError, OSError):
            await self._ensure_connected()
            raw = await self._redis.get(key)

        if raw is None:
            return None
        if self._decode:
            # decode_responses=True -> raw is str
            try:
                return self._loads(raw)
            except Exception:
                return raw  # не JSON
        else:
            # raw bytes
            try:
                return self._from_bytes(raw)
            except Exception:
                return raw

    async def delete(self, *keys: str) -> int:
        await self.connect()
        return await self._redis.delete(*keys)

    # ---- hash operations ----
    async def hset(self, name: str, mapping: dict, ttl: int | None = None) -> int:
        await self.connect()
        res = await self._redis.hset(name, mapping=mapping)
        if ttl is not None:
            await self._redis.expire(name, ttl)
        return res

    async def hset_kv(self, name: str, key: str, value: Any) -> int:
        await self.connect()
        payload = self._to_bytes(value)
        return await self._redis.hset(name, key, payload)

    async def hgetall(self, name: str) -> dict:
        await self.connect()
        raw = await self._redis.hgetall(name)
        # If None return raw. If response decoded, return raw as well
        if raw is None:
            return None
        if self._decode:
            return raw
        else:
            # TODO: decode dict
            raise NotImplementedError

    async def hget(self, name: str, key: str) -> Any:
        await self.connect()
        raw = await self._redis.hget(name, key)
        if raw is None:
            return None
        return self._from_bytes(raw)

    # ---- list operations ----
    async def lpush(self, name: str, *values: Any) -> int:
        await self.connect()
        payloads = [self._to_bytes(v) for v in values]
        return await self._redis.lpush(name, *payloads)

    async def keys_exist(self, keys: list[str]) -> list[bool]:
        if not keys:
            return
        
        pipe = self._redis.pipeline(transaction=False)
        for key in keys:
            pipe.exists(key)
        result = await pipe.execute()
        logger.debug(f"requested if exists. Redis says: {result}")
        return [bool(x) for x in result]

    async def rpop(self, name: str) -> Any:
        await self.connect()
        raw = await self._redis.rpop(name)
        if raw is None:
            return None
        return self._from_bytes(raw)

    # ---- pub/sub ----
    async def publish(self, channel: str, message: Any) -> int:
        await self.connect()
        payload = self._to_bytes(message)
        return await self._redis.publish(channel, payload)

    async def subscribe(self, channel: str, handler: Callable[[Any], None]):
        """
        Подписка на канал. handler может быть асинхронной функцией или обычной.
        Запускает фоновую задачу, которую можно отменить (client.close() сделает cancel).
        """
        await self.connect()
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)

        async def _reader():
            try:
                async for msg in pubsub.listen():
                    # msg example: {'type': 'message', 'pattern': None, 'channel': b'chan', 'data': b'...'}
                    if msg is None:
                        continue
                    if msg.get("type") != "message":
                        continue
                    data = msg.get("data")
                    try:
                        data = self._from_bytes(data)
                    except Exception:
                        pass
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        # run blocking handler in threadpool
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, handler, data)
            except asyncio.CancelledError:
                pass
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception:
                    pass

        task = asyncio.create_task(_reader())
        self._pubsub_tasks.add(task)
        # cleanup on done
        def _on_done(t):
            self._pubsub_tasks.discard(t)
        task.add_done_callback(_on_done)
        return task  # пользователь может task.cancel() при необходимости
    
    async def delete_hashes_by_pattern(
        self,
        pattern: str = "connection:*",
        scan_count: int = 1000,   # hint для SCAN
        batch_size: int = 500     # сколько ключей обрабатывать в одном pipeline
    ) -> int:
        """
        Удалить все ключи типа 'hash' по шаблону pattern.
        Возвращает количество удалённых ключей.

        Аргументы:
        pattern    - шаблон поиска (по умолчанию "connections:*")
        scan_count - hint для SCAN (сколько элементов за один проход просить у сервера)
        batch_size - сколько ключей проверять/удалять за одну пачку
        """
        deleted = 0
        try:
            batch = []
            # scan_iter — асинхронный итератор
            async for key in self._redis.scan_iter(match=pattern, count=scan_count):
                batch.append(key)
                if len(batch) >= batch_size:
                    deleted += await self._process_batch(batch)
                    batch.clear()

            # остаток
            if batch:
                deleted += await self._process_batch(batch)
                batch.clear()
        except RedisError as e:
            # можно логировать или пробрасывать
            raise
        return deleted

    async def _process_batch(
            self, 
            keys: Iterable[Union[str, bytes]]
        ) -> int:
        """
        Для пачки keys: получаем TYPE для каждого ключа через pipeline,
        фильтруем только 'hash' и делаем UNLINK (faster, non-blocking delete).
        Возвращаем количество удалённых ключей в этой пачке.
        """
        # 1) Получаем типы пакетно
        pipe = self._redis.pipeline(transaction=False)
        for k in keys:
            pipe.type(k)
        types = await pipe.execute()

        # 2) Фильтруем ключи типа 'hash' (учитываем str и bytes)
        keys_to_delete = []
        for k, t in zip(keys, types):
            # t может быть 'hash' (str) или b'hash' (bytes) в зависимости от decode_responses
            if t == "hash" or t == b"hash":
                keys_to_delete.append(k)

        if not keys_to_delete:
            return 0

        # 3) Удаляем неблокирующе — UNLINK (fallback на DEL если UNLINK не поддерживается)
        try:
            # unlink принимает *args
            res = await self._redis.unlink(*keys_to_delete)
        except AttributeError:
            # старые клиенты/серверы могут не поддерживать UNLINK в API, используем delete
            res = await self._redis.delete(*keys_to_delete)

        # res обычно число удалённых ключей
        return int(res or 0)
