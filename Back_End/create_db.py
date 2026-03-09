import asyncio, asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://postgres:dark$citrus@localhost:5432/postgres')
    try:
        await conn.execute('CREATE DATABASE timeweaver_test')
        print('Created DB')
    except Exception as e:
        print(e)
    finally:
        await conn.close()
asyncio.run(main())
