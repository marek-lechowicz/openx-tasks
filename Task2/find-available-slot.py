#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Marek Lechowicz
from __future__ import annotations
import fnmatch
import getopt
import os
import os.path
import sys
from datetime import datetime, timedelta
from typing import List

import numpy as np


class BusyTimeslot:
    def __init__(self, start_time, end_time, people_busy):
        self.start_time = start_time
        self.end_time = end_time
        self.people_busy = people_busy


def merge_timeslots(first: BusyTimeslot, second: BusyTimeslot) -> (List[BusyTimeslot], BusyTimeslot):
    """
    Merges two objects of BusyTimeslot

    Parameters:
        first (BusyTimeslot): BusyTimeslot object to be merged
        second (BusyTimeslot): BusyTimeslot object to be merged

    Returns:
        Tuple:
            merged - List of non-overlapping first, overlapping part and non-overlapping second but before first
            residual - Non-overlapping second happening after first or overlapping part. If no residue left,
            returns BusyTimeslot with start_time == end_time and people_busy == 0
    """

    # second overlaps with the end of first
    if first.start_time < second.start_time < first.end_time:
        merged = [BusyTimeslot(first.start_time, second.start_time, first.people_busy),
                  BusyTimeslot(second.start_time, first.end_time, first.people_busy + second.people_busy)]

        residual = BusyTimeslot(first.end_time, second.end_time, second.people_busy)

    # second overlaps with start of first
    elif first.start_time < second.end_time < first.end_time:
        merged = [BusyTimeslot(second.end_time, first.end_time, first.people_busy),
                  BusyTimeslot(first.start_time, second.end_time, first.people_busy + second.people_busy),
                  BusyTimeslot(second.start_time, first.start_time, second.people_busy)]

        # non-residual, BusyTimeslot object instead of None to avoid errors later
        residual = BusyTimeslot(second.end_time, second.end_time, 0)

    # one is a subset of the other
    elif (first.start_time < second.start_time and first.end_time > second.end_time) or \
         (first.start_time > second.start_time and first.end_time < second.end_time):

        if first.start_time < second.start_time:
            merged = [BusyTimeslot(first.start_time, second.start_time, first.people_busy),
                      BusyTimeslot(second.start_time, second.end_time, first.people_busy + second.people_busy),
                      BusyTimeslot(second.end_time, first.end_time, first.people_busy)]

            # non-residual, BusyTimeslot object instead of None to avoid errors later
            residual = BusyTimeslot(second.end_time, second.end_time, 0)

        elif first.start_time > second.start_time:
            merged = [BusyTimeslot(second.start_time, first.start_time, second.people_busy),
                      BusyTimeslot(first.start_time, first.end_time, first.people_busy + second.people_busy)]

            residual = BusyTimeslot(first.end_time, second.end_time, second.people_busy)

    else:
        merged = [first]
        residual = second

    return merged, residual


def get_num_of_ppl(dir_path):
    return len(fnmatch.filter(os.listdir(dir_path), '*.txt'))


def insert_timeslot(time_arr, start_date, end_date):
    np.where(time_arr)


def find_free_slot(calendar_dir, duration, min_ppl):
    date_format = "%Y-%m-%d %H:%M:%S"
    time_lst = list()

    for filename in os.listdir(calendar_dir):
        with open(os.path.join(calendar_dir, filename), 'r') as file:
            for line in file:
                date = line.split(' - ')
                if len(date) == 2:
                    start_date = datetime.strptime(date[0], date_format)
                    end_date = datetime.strptime(date[1], date_format)
                elif len(date) == 1:
                    start_date = datetime.strptime(date[0]+" 00:00:00", date_format)
                    end_date = datetime.strptime(date[0]+" 23:59:59", date_format)

                # if the line contained viable date
                if start_date is not None and end_date is not None:
                    new_timeslot = BusyTimeslot(start_date, end_date, 1)
                    to_append = list()     # temp list of elements, to avoid pushing time_lst during iteration
                    for timeslot in time_lst:
                        merged, residual = merge_timeslots(timeslot, new_timeslot)
                        # save merged to append them later
                        for elem in merged:
                            to_append.append(elem)

                        new_timeslot = residual

                        if (new_timeslot.end_time - new_timeslot.start_time)/timedelta(minutes=1) <= 0:
                            break

                    # if new elem is the latest append it
                    if (new_timeslot.end_time - new_timeslot.start_time)/timedelta(minutes=1) > 0:
                        to_append.append(new_timeslot)

                    time_lst = to_append

                    # sort to avoid multiple residuals
                    time_lst.sort(key=lambda x: x.start_time)

    all_people = get_num_of_ppl(calendar_dir)
    for timeslot in time_lst:
        if all_people - timeslot.people_busy > min_ppl:
            time_lst.remove(timeslot)

    # date for example in email
    # current_time = datetime.strptime("2022-07-01 09:00:00", date_format)
    current_time = datetime.now()
    if (time_lst[0].start_time - current_time)/timedelta(minutes=1) >= duration:
        return current_time

    else:
        for i in range(len(time_lst)-1):
            if (time_lst[i].end_time - time_lst[i+1].start_time)/timedelta(minutes=1) >= duration:
                return time_lst[i].end_time+timedelta(seconds=1)
        return time_lst[-1].end_time+timedelta(seconds=1)


def terminal_handler(argv):
    arg_calendar_dir = ""
    arg_duration = ""
    arg_min_ppl = ""
    arg_help = "{0} --calendars <calendar_dir_path> --duration-in-minutes <num_of_minutes> --minimum-people <num_of_people>".format(
        argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hc:d:m:", ["help", "calendars=",
                                                         "duration-in-minutes=", "minimum-people="])
    except getopt.GetoptError:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-c", "--calendars"):
            arg_calendar_dir = arg
        elif opt in ("-d", "--duration-in-minutes"):
            arg_duration = int(arg)
        elif opt in ("-m", "--minimum-people"):
            arg_min_ppl = int(arg)

    # check if required arguments were passed
    if arg_calendar_dir and arg_duration and arg_min_ppl:
        all_ppl = get_num_of_ppl(arg_calendar_dir)

        if all_ppl - arg_min_ppl < 0:
            print(f"Too few people in the company. Required: {arg_min_ppl}, All: {all_ppl}")
            sys.exit(2)
        else:
            print(find_free_slot(arg_calendar_dir, arg_duration, arg_min_ppl))
    else:
        print("Wrong command, proper command should follow this pattern:")
        print(arg_help)


if __name__ == "__main__":
    terminal_handler(sys.argv)

    # for easy debug
    # msg = find_free_slot("in", 30, 2)
    # print(msg)
