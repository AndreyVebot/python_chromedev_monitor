import asyncio
import threading
import functools
import json
import time
import requests_async
from requests.exceptions import ConnectionError as RequestsConnectionError
import websockets

from .page import Page
from .exceptions import ChromeProtocolDevtoolsClosed

EVENT_TYPES = {
    0: "DELETED",
    1: "UPDATED",
    2: "CREATED"
}


def restart_periodic_decorator(f):
    @functools.wraps(f)
    async def wrapper(*args):
        await f(*args)
        await asyncio.sleep(args[0].interval_request_time)
        asyncio.create_task(restart_periodic_decorator(f)(*args))

    return wrapper


class ListenEvents:
    def __init__(self, browser_url, interval_request_time=0.1):
        self.browser_url = browser_url
        self.interval_request_time = interval_request_time

        self.websockets_table = {}
        self.urls = {}
        self.user_thread = None
        self.run_user_event_request = None

    def set_user_call_function(self, func):
        self.raise_event = func

    async def load_page_from_internet(self, url):
        if self.urls.get(url):
            return self.urls.get(url)
        try:
            response = await requests_async.get(url)
        except:
            return ""
        data = response.text
        self.urls[url] = data

        return data

    #
    #
    #
    async def get_page_content(self, ws_local_index):
        ws_local = self.websockets_table[ws_local_index]

        async with ws_local.socket_object as ws_local_connection:
            await ws_local_connection.send(json.dumps({
                "id": 1,
                "method": "Page.enable",
                "params": {}
            }))

            _ = await ws_local_connection.recv()

            await ws_local_connection.send(json.dumps({
                "id": 1,
                "method": "Page.getResourceContent",
                "params": {
                    "frameId": ws_local.frame_tree_content["frameTree"]["frame"]["id"],
                    "url": ws_local.frame_tree_content["frameTree"]["frame"]["url"]
                }
            }))

            data = json.loads(await ws_local_connection.recv())
            while data.get("method"):
                data = json.loads(await ws_local_connection.recv())

            if "result" not in data or data.get("result").get("content") == "":
                data = await self.load_page_from_internet(ws_local.frame_tree_content["frameTree"]["frame"]["url"])
                return data
            else:
                return data["result"]["content"]

    #
    #
    #
    async def run_user_event(self, ws_local_index=None, event_type=None, start=False):
        if not start:
            if not ws_local_index and not event_type:
                raise AttributeError
            self.run_user_event_request = (ws_local_index, event_type)
            return

        if not self.run_user_event_request:
            return

        ws_local_index, event_type = self.run_user_event_request

        ws_local = self.websockets_table[ws_local_index]
        event_handler_dict = {
            "pages": {},
            "event_data": {
                "event_type": event_type,
                "meta": ws_local.meta
            }
        }

        for page_index, page_object in self.websockets_table.items():
            if not hasattr(page_object, "frame_tree_content"):
                await self.get_frame_tree(page_index)

            try:
                page_object.content = await self.get_page_content(page_index)
            except (RequestsConnectionError, websockets.exceptions.ConnectionClosedError,
                    websockets.exceptions.InvalidStatusCode):
                continue

            page_data = {
                "meta": page_object.meta,
                "raw_content": page_object.content
            }
            event_handler_dict["pages"][page_index] = page_data

        self.user_thread = threading.Thread(target=self.raise_event, args=(event_handler_dict,))
        self.user_thread.daemon = True
        # run event in new task queue
        self.user_thread.start()

        self.run_user_event_request = None

        if event_type == EVENT_TYPES[0]:
            # remove unworked socket from websockets_list
            del self.websockets_table[ws_local_index]

    #
    #
    #
    async def get_frame_tree(self, ws_local_index):
        ws_local = self.websockets_table[ws_local_index]
        # get info use method Page.getFrameTree
        try:
            async with ws_local.socket_object as ws_local_connection:
                try:
                    # send sync request
                    await ws_local_connection.send(json.dumps({
                        "id": 1,
                        "method": "Page.getFrameTree",
                    }))
                except BrokenPipeError:
                    await self.run_user_event(ws_local_index, EVENT_TYPES[0])
                    return

                try:
                    # send sync request
                    data = json.loads(await ws_local_connection.recv()).get("result")
                    if data:
                        ws_local.update_frame_tree_content(data)
                    else:
                        await self.run_user_event(ws_local_index, EVENT_TYPES[0])
                        return

                    if ws_local.is_updated_page(data["frameTree"]["frame"]["loaderId"]):
                        await self.run_user_event(ws_local_index, EVENT_TYPES[1])

                except websockets.exceptions.ConnectionClosedError:
                    await self.run_user_event(ws_local_index, EVENT_TYPES[0])

                except KeyboardInterrupt:
                    pass

        except websockets.exceptions.InvalidStatusCode:
            await self.run_user_event(ws_local_index, EVENT_TYPES[0])

    # ==========================
    # MAIN WORK IN THIS FUNCTION
    # ==========================
    async def update_websockets(self):
        new_tab_created = {
            "status": False,
            "socket_index": None
        }
        try:
            active_urls_data = await requests_async.get(self.browser_url + "/json")
        except RequestsConnectionError:
            raise ChromeProtocolDevtoolsClosed(self.browser_url)
        except KeyboardInterrupt:
            pass

        active_urls_data = active_urls_data.json()

        pages = dict((row["id"], row) for row in active_urls_data if row["type"] == "page")

        for page_index in pages:
            page = pages[page_index]
            if not self.websockets_table.get(page_index):
                websocket_connection = websockets.connect(page["webSocketDebuggerUrl"])
                page_object = Page(socket_object=websocket_connection, meta=page)

                self.websockets_table[page_index] = page_object
                new_tab_created["status"] = True
                new_tab_created["socket_index"] = page_index
            else:
                self.websockets_table[page_index].update_meta(page)

        if new_tab_created["status"]:
            await self.run_user_event(page_index, EVENT_TYPES[2])

    @restart_periodic_decorator
    async def periodic_function(self):
        await self.run_user_event(start=True)
        await self.update_websockets()
        tasks = []
        for ws_local_index in self.websockets_table:
            # execute work with socket
            tasks.append(self.get_frame_tree(ws_local_index))
        # run pack of tasks
        await asyncio.gather(*tasks)

    # ===============
    # PRE-WORKER JOBS
    # ===============
    async def run_socket_http_worker(self):
        # create main task
        asyncio.get_event_loop().create_task(self.periodic_function())

    def run_worker(self):
        asyncio.get_event_loop().create_task(self.run_socket_http_worker())

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, ChromeProtocolDevtoolsClosed):
            print("Stopped...")
