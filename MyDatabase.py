import sqlite3
import os
import json


conn = sqlite3.connect('WoWs_DB')
c = conn.cursor()



def ship_tbl_select_name_type(ship_id):

	c.execute("""
	SELECT
		ship_name,
		type
	FROM
		tbl_ships
	WHERE
		ship_id=?
	""", (ship_id,)
	)
	rows = c.fetchall()
	for row in rows:
		return(row)