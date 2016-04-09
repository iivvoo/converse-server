import sys
import asyncio
import websockets


def got_stdin_data(q):
    line = sys.stdin.readline()
    print("> {}".format(line))
    asyncio.async(q.put(line))

async def hello():
    async with websockets.connect('ws://localhost:5678') as websocket:
        print("Please type username password")
        q = asyncio.Queue()
        asyncio.get_event_loop().add_reader(sys.stdin, got_stdin_data, q)

        if len(sys.argv) == 2:
            await websocket.send(sys.argv[1])

        while True:
            listener_task = asyncio.ensure_future(websocket.recv())
            producer_task = asyncio.ensure_future(q.get())

            done, pending = await asyncio.wait(
                [listener_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            if listener_task in done:
                message = listener_task.result()
                print("< {}".format(message))
            else:
                listener_task.cancel()

            if producer_task in done:
                raw = producer_task.result()
                print("Sending {0}".format(raw))
                await websocket.send(raw)
            else:
                producer_task.cancel()

loop = asyncio.get_event_loop()

loop.run_until_complete(hello())
