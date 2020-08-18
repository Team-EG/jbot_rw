"""
    jbot_rw
    Copyright (C) 2020 Team EG

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


async def calc_req_exp(curr_lvl):
    desired_lvl = curr_lvl + 1
    lvl_up_req = 5 / 6 * desired_lvl * (2 * desired_lvl * desired_lvl + 27 * desired_lvl + 91)
    return lvl_up_req


async def calc_curr_exp(curr_lvl):
    lvl_up_req = 5 / 6 * curr_lvl * (2 * curr_lvl * curr_lvl + 27 * curr_lvl + 91)
    return lvl_up_req


async def calc_old(curr_lvl):
    lvl_up_req = 200 + 50 * curr_lvl ** 2
    return lvl_up_req


async def calc_lvl(curr_exp):
    for x in reversed(range(100)):
        if (await calc_curr_exp(x)) < curr_exp:
            return x


async def can_lvl_up(curr_lvl, curr_exp):
    val = await calc_req_exp(curr_lvl)
    if val <= curr_exp:
        return True
    return False


if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(calc_lvl(771)))
