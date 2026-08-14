from enum import Enum
from model.PlayerPosition import PlayerPosition

class PlayerRole(Enum):
    FORWARD = 1
    MIDFIELD = 2
    DEFENSE = 3
    GOALKEEPER = 4

def get_role(pos: PlayerPosition) -> PlayerRole:
    match pos:
        case PlayerPosition.ST | PlayerPosition.LW | PlayerPosition.RW: 
            return PlayerRole.FORWARD
        case PlayerPosition.CM | PlayerPosition.CDM | PlayerPosition.CAM | PlayerPosition.LM | PlayerPosition.RM: 
            return PlayerRole.MIDFIELD
        case PlayerPosition.CB | PlayerPosition.LB | PlayerPosition.RB: 
            return PlayerRole.DEFENSE
        case PlayerPosition.GK: 
            return PlayerRole.GOALKEEPER
        case _: 
            return PlayerRole.GOALKEEPER # should never happen