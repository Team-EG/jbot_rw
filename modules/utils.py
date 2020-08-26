def parse_second(time: int):
    parsed_time = ""
    if time // (60 * 60) != 0:
        hour = time // (60 * 60)
        time -= hour * (60 * 60)
        parsed_time += f"{hour}시간 "
    if time // 60 != 0:
        minute = time // 60
        time -= minute * 60
        parsed_time += f"{minute}분 "
    parsed_time += f"{time}초"
    return parsed_time
