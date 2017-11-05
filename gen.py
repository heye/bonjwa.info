#!/usr/bin/python
import MySQLdb
from datetime import datetime, date
import calendar


def main():
    workingDate = date(2017, 11, 4)
    dayStart = calendar.timegm(workingDate.timetuple()) + 60*60*8
    dayEnd = calendar.timegm(workingDate.timetuple()) + 60*60*8 + 60*60*24
    print dayStart
    print dayEnd


    # my code here
    db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="root",         # your username
                     passwd="ct012015",  # your password
                     db="bonjwa_stats")        # name of the data base

    # you must create a Cursor object. It will let
    #  you execute all the queries you need
    cur = db.cursor()

    queryStringStart = "SELECT time FROM bonjwa_stats WHERE time > " + str(dayStart) + " AND time < 1509865200 ORDER BY time ASC LIMIT 1"
    # Use all the SQL you like
    cur.execute(queryStringStart)

    # print all the first cell of all the rows
    #for row in cur.fetchall():
    #    print row[0]
    streamStart = dayStart
    if cur.rowcount > 0:
        streamStart = cur.fetchone()[0]


    

    queryStringEnd = "SELECT time FROM bonjwa_stats WHERE time < " + str(dayEnd) + " AND time < 1509865200 ORDER BY time DESC LIMIT 1"
    # Use all the SQL you like
    cur.execute(queryStringEnd)

    # print all the first cell of all the rows
    #for row in cur.fetchall():
    #    print row[0]
    streamEnd = dayEnd
    if cur.rowcount > 0:
        streamEnd = cur.fetchone()[0]

    print streamStart
    print streamEnd

    db.close()

    wget "http://127.0.0.1:3000/render/dashboard-solo/db/views?orgId=1&from=1509791222&to=1509826562&panelId=1&width=1000&height=500&timeout=30000" -O test.png -T 30

    #SELECT time FROM bonjwa_stats WHERE time > 1509778800 AND time < 1509865200 ORDER BY time ASC LIMIT 1
    #SELECT time FROM bonjwa_stats WHERE time > 1509778800 AND time < 1509865200 ORDER BY time DESC LIMIT 1;


if __name__ == "__main__":
    main()