from pydantic import BaseModel

class GameConfig(BaseModel):
    time_control: str
    color_preference: str

class LobbyChallenge(BaseModel):
    id: str
    host_id: int
    host_username: str
    host_rating: int
    time_control: str
    color_preference: str