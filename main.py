from screen_devtools import ScreenDevtools

app = ScreenDevtools("http://localhost:9222")

"""
event format:
{
    "pages": {
        "tab_id1": {
            "raw_content", 
            "meta"
        },
        "tab_id2": {
            "raw_content", 
            "meta"
        }
    },
    "event_data": {
        "event_type": ["DELETED" or "CREATED" or "UPDATED"]
        "meta"
    }
}
"""


@app.event_handler
def hello(event):
    print(event["event_data"]["event_type"])
    for page_id, page in event["pages"].items():
        print(page["meta"]["url"], ":", len(page["raw_content"]))
    print()


if __name__ == "__main__":
    app.run()
