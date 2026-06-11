from slack_sdk import WebClient


class SlackClient:
    def __init__(self, token: str):
        self.client = WebClient(token=token)

    def get_workspace_members(self) -> list[str]:
        response = self.client.users_list()
        return [
            user["profile"]["display_name"] or user["real_name"]
            for user in response["members"]
            if not user["is_bot"]
            and not user["deleted"]
            and user["id"] != "USLACKBOT"
        ]

    def get_messages_by_user(self, username: str, limit: int = 100) -> list[str]:
        response = self.client.search_messages(query=f"from:{username}", count=limit)
        matches = response.get("messages", {}).get("matches", [])
        return [match["text"] for match in matches]
