class Page:
    def __init__(self, socket_object, meta):
        self.socket_object = socket_object
        self.loader_id = None
        self.content = None

        self.update_meta(meta)

    def update_page_url(self, page_url):
        self.page_url = page_url

    def is_updated_page(self, load_id):
        if not self.loader_id:
            self.loader_id = load_id
            return
        status = False if self.loader_id == load_id else True
        self.loader_id = load_id

        return status

    def update_frame_tree_content(self, new_content):
        self.frame_tree_content = new_content

    def update_meta(self, meta):
        self.meta = {
            "id": meta.get("id"),
            "url": meta.get("url"),
            "title": meta.get("title"),
            "favicon": meta.get("faviconUrl"),
            "websocketUrl": meta.get("webSocketDebuggerUrl")
        }
