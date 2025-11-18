Mood (can be null):
{
    type: str,
    intensity: int
}

Intercourse
(can be null, if quantity>0 then all other fields are optional):
{
    condom: True|False|None,
    orgasm: True|False|None
    quantity: int
}

Medicine in {pill, v-ring, patch, injection, IUD, implant, other(can add)}
