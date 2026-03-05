from pydantic import BaseModel


class StatsSumOut(BaseModel):
    games: int

    goals: int
    assists: int
    errors: int
    won_balls: int
    lost_balls: int
    fouls: int
    passes: int
    won_duels: int
    lost_duels: int
    shots_on_goal: int
    shots_off_goal: int
    yellow_cards: int
    red_cards: int
    penalties: int