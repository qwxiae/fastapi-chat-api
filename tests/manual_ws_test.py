# tests/manual_ws_test.py
import argparse
import asyncio
import json

import websockets

parser = argparse.ArgumentParser()
parser.add_argument("--user", action="store", dest="user", default=1, type=int)
args = parser.parse_args()

user = args.user
ROOM_ID = "c94a0aa2-cafc-4b7e-98ea-adb6d692baf1"
TOKEN1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjNmRjYWRmOS0xY2RhLTQ2ZjUtYmZlMy0wM2NhNDZkMTg4N2QiLCJleHAiOjE3ODQ2NDc5NzB9.eRrIFbYCUxJvOc74OmqHqNnEAzDku4JArFaF0vceLs0"
TOKEN2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjMjk2NzdiZS1lODI4LTQzOGMtOTVkOS02NGNiNTI2YzJmMGYiLCJleHAiOjE3ODQ2NTE0MTl9.2Yqo8pEdX8QlppiCwcz3WCkb7izK3ozD5uH1Y_gvzHk"


async def main():
    uri = f"ws://localhost:8000/ws/rooms/{ROOM_ID}"
    async with websockets.connect(uri) as ws:
        # first message: auth
        print(user)
        if user == 1:
            TOKEN = TOKEN1
        else:
            TOKEN = TOKEN2
        await ws.send(json.dumps({"type": "auth", "token": TOKEN}))

        # receive history
        history = await ws.recv()
        print("HISTORY:")
        print(json.dumps(json.loads(history), indent=2))

        # listen in the background while letting you type messages
        async def listen():
            async for message in ws:
                data = json.loads(message)
                if data["type"] == "user_joined":
                    print(f"\n=> {data['username']} joined\n")
                elif data["type"] == "user_left":
                    print(f"\n=> {data['username']} left\n")
                elif data["type"] == "typing":
                    print(f"\n=> {data['username']} is typing...\n")
                elif data["type"] == "message":
                    print(f"\n[{data['user_id'][:8]}] {data['content']}\n")
                elif data["type"] == "file_shared":
                    print(
                        f"\n{data['filename']} shared by {data['user_id'][:8]} ({data['file_size_kb']}kb)\n"
                    )
                else:
                    print(f"\n[RECEIVED] {data}\n")

        listen_task = asyncio.create_task(listen())

        while True:
            text = await asyncio.to_thread(input, "Type a message (or '(q)uit'): ")
            if text == "q":
                break
            await ws.send(json.dumps({"type": "message", "content": text}))

        listen_task.cancel()


asyncio.run(main())
