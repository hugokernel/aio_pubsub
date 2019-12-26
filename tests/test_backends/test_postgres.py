import aiopg
import pytest

from aio_pubsub.backends.postgresql import PostgreSQLPubSub, PostgreSQLSubscriber


@pytest.fixture()
async def pg_pool():
    pool = await aiopg.create_pool(
        "dbname=aiopg user=aiopg password=example host=127.0.0.1 port=5433"
    )
    yield pool
    pool.terminate()


@pytest.mark.asyncio
async def test_init(pg_pool):
    pubsub = PostgreSQLPubSub(pg_pool)
    async with pg_pool.acquire() as pool:
        async with pool.cursor() as cursor:
            await cursor.execute("DROP table {};".format(pubsub.table_name))

    await pubsub.init()

    async with pg_pool.acquire() as pool:
        async with pool.cursor() as cursor:
            await cursor.execute("select * from {};".format(pubsub.table_name))
    subscriber = await pubsub.subscribe("a_chan")
    assert isinstance(subscriber, PostgreSQLSubscriber)


@pytest.mark.asyncio
async def test_subscriber_isinstance(pg_pool):
    pubsub = PostgreSQLPubSub(pg_pool)
    await pubsub.init()
    subscriber = await pubsub.subscribe("a_chan")
    assert isinstance(subscriber, PostgreSQLSubscriber)


@pytest.mark.asyncio
async def test_iteration_protocol(pg_pool):
    pubsub = PostgreSQLPubSub(pg_pool)
    await pubsub.init()
    subscriber = await pubsub.subscribe("a_chan")
    await pubsub.publish("a_chan", "hello world!")
    subscriber = subscriber.__aiter__()
    assert await subscriber.__anext__() == "hello world!"


@pytest.mark.asyncio
async def test_pubsub(pg_pool):
    pubsub = PostgreSQLPubSub(pg_pool)
    await pubsub.init()
    subscriber = await pubsub.subscribe("a_chan")
    await pubsub.publish("a_chan", "hello world!")
    await pubsub.publish("a_chan", "hello universe!")
    assert await subscriber.__anext__() == "hello world!"
    assert await subscriber.__anext__() == "hello universe!"


@pytest.mark.asyncio
async def test_not_subscribed_chan(pg_pool):
    pubsub = PostgreSQLPubSub(pg_pool)
    await pubsub.init()
    subscriber_a_chan = await pubsub.subscribe("a_chan")
    subscriber_c_chan = await pubsub.subscribe("c_chan")
    await pubsub.publish("a_chan", "hello world!")
    await pubsub.publish("b_chan", "junk message")
    await pubsub.publish("c_chan", "hello universe!")
    assert await subscriber_a_chan.__anext__() == "hello world!"
    assert await subscriber_c_chan.__anext__() == "hello universe!"
