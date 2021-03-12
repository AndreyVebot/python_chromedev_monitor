"""
chrome --remote-debugging api test
"""

import json
import requests
import websocket
import time

TabList = []

def Navigate(URL:str, TabID = None) -> bool:
    """
    Navigate to URL. If TabID is't provided - use last active tab
    """
    return(True)

def send():
    # Setup websocket connection:
    geturl = json.loads(requests.get('http://localhost:1111/json').content)
    for page in range(0,len(geturl)-1):
        if geturl[page]["type"] == "page":
            websocket.enableTrace(True)
            asyncio.get_event_loop().run_until_complete(PageListener(geturl[page]['url'],geturl[page]['webSocketDebuggerUrl']))
    time.sleep(11111)
    for page in range(0,len(geturl)-1):
        if geturl[page]["type"] == "page":
            print(geturl[page]["url"])
            ws = websocket.create_connection(geturl[page]['webSocketDebuggerUrl'])
            ws.send(json.dumps({
                    "id" : 1,
                    "method" : "Page.getFrameTree",
                    "params" : {}
                }))
            geturl[page]["frames"] = json.loads(ws.recv())
            ws.send(json.dumps({"id" : 1, "method" : "Page.enable","params" : {}}))
            ws.send(json.dumps({"id" : 1, "method" : 'Page.getResourceContent', 'params' : {"frameId": geturl[page]["frames"]["result"]["frameTree"]["frame"]["id"] ,"url" : geturl[page]["url"] } }))
            geturl[page]["content"]=ws.recv()
            ws.send(json.dumps({"id" : 1, "method" : 'Page.getResourceContent', 'params' : {"frameId": geturl[page]["frames"]["result"]["frameTree"]["frame"]["id"] ,"url" : geturl[page]["url"] } }))
            geturl[page]["content"]=ws.recv()
            
            ws.close()

    # Navigate to global.bing.com:
#    request = {}
#    request['id'] = 1
#    request['method'] = 'Page.navigate'
#    request['params'] = {"url": 'http://global.bing.com'}
#    ws.send(json.dumps(request))
#    result = ws.recv()
#    print("Page.navigate: " + result)
#    frameId = json.loads(result)['result']['frameId']

    # Enable page agent:
    ws.send(json.dumps({"id" : 1, "method" : "Page.enable","params" : {}}))

    # Retrieve resource contents:
#    request = {}
#    request['id'] = 1
#    request['method'] = 'Page.getResourceContent'
#    request['params'] = {"frameId": frames["result"]["frameTree"]["frame"]["id"], "url": geturl[0]['url']}
#    request['params'] = {"frameId": frames["result"]["frameTree"]["frame"]["id"]}
    ws.send(json.dumps({"id" : 1, "method" : 'Page.getResourceContent', 'params' : {"frameId": frames["result"]["frameTree"]["frame"]["id"]} }))
    result = ws.recv()
    print("Page.getResourceContent: ", result)

    # Close websocket connection
    ws.close()

if __name__ == '__main__':
    send()