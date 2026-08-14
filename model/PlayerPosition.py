from enum import Enum

class PlayerPosition(str, Enum):
    ST = 'ST'
    LW = 'LW'
    RW = 'RW'
    CF = 'CF'
    CAM = 'CAM'
    CM = 'CM'
    CDM = 'CDM'
    LM = 'LM'
    RM = 'RM'
    CB = 'CB'
    LB = 'LB'
    RB = 'RB'
    GK = 'GK'

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"PlayerPosition.{self.name}"

def get_position(pos: str) -> PlayerPosition:
    pos = pos.upper()
    match pos:
        case "ST": return PlayerPosition.ST
        case "LW": return PlayerPosition.LW
        case "RW": return PlayerPosition.RW
        case "CF": return PlayerPosition.CF
        case "CAM": return PlayerPosition.CAM
        case "CM": return PlayerPosition.CM
        case "CDM": return PlayerPosition.CDM
        case "LM": return PlayerPosition.LM
        case "RM": return PlayerPosition.RM
        case "CB": return PlayerPosition.CB
        case "LB": return PlayerPosition.LB
        case "RB": return PlayerPosition.RB
        case "GK": return PlayerPosition.GK
        case _: raise ValueError(f"Invalid position: {pos}")


