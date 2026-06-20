# tests/manual_ws_test.py
import asyncio
import json
import websockets
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--user', action="store", dest='user', default=1, type=int)
args = parser.parse_args()

user = args.user
ROOM_ID = "494ffe03-a371-45af-9be3-995bd29b81f7"
TOKEN1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4NjJkZjNjZC00MTU4LTQ0MjUtYjQzYy1jNDAwOGM0YWRlNzgiLCJleHAiOjE3ODQ1NjgwODV9.vxlpeCSL6_Sdb5Frr_ToWbE1I-l2hYQlfTfM89kUTbk"
TOKEN2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmZDVjM2YzOC0zN2Y1LTQwMjUtYWUyMy1hYzAyNWQwMTExMWIiLCJleHAiOjE3ODQ1ODkwMzF9.FaK9MWPHxkcOhPZh_eP6Y2LAOxsSk9UBIvINY-WYFBI"

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