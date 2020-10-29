import json
import os
import MyDatabase
import requests


# * Player account ID
URL_a = 'https://api.worldofwarships.eu/wows/account/list/?'

# * shipstats
URL_e = 'https://api.worldofwarships.eu/wows/encyclopedia/ships/?'

# * All player stats
URL_es = 'https://api.worldofwarships.eu/wows/account/info/?'

# * Player stats per ship
URL_PS = 'https://api.worldofwarships.eu/wows/ships/stats/?'


def open_log():
	with open('log.json') as f:
		logfile = json.load(f)
		return(logfile)

log = open_log()

def open_app_id():
	f = open("app_id", "r")
	return(f.read())

application_id = open_app_id()


AllData = []
Merged = []
# !


def check_if_bot(player_name):

	if player_name.startswith(':'):
		Bot = 'True'
	else:
		Bot = 'False'

	return(Bot)

def parse_relation(relation):

	if relation == 2:
		relation = 'B'
	else:
		relation = 'A'

	return(relation)

def parse_ship_type(ship_type):

	if ship_type == 'AirCarrier':
		ship_type = 'cv'

	elif ship_type == 'Battleship':
		ship_type = 'bb'

	elif ship_type == 'Cruiser':
		ship_type = 'cc'

	elif ship_type == 'Destroyer':
		ship_type = 'dd'

	return(ship_type)

def parse_logfile():

	for player in log['vehicles']:

		player_id = player['id']
		Bot = check_if_bot(player['name'])
		player_name = player['name']
		relation = parse_relation(player['relation'])

		ship_id = player['shipId']

		ship_NameAndData = MyDatabase.ship_tbl_select_name_type(ship_id)
		ship_name = ship_NameAndData[0]
		ship_type_long = ship_NameAndData[1]
		ship_type_short = parse_ship_type(ship_type_long)

		values = {
			'player_id': player_id,
			'player_name': player_name,
			'Bot': Bot,
			'relation': relation,
			'ship_name': ship_name,
			'ship_id': ship_id,
			'ship_type_short': ship_type_short,
			'ship_type_long': ship_type_long
			}
		AllData.append(values)

def get_account_id():

	PLAYER = []

	for row in AllData:
		if row['Bot'] != 'True':
			PLAYER.append(str(row['player_name']))

	joined_string = '%2C'.join(PLAYER)
	r = requests.get(URL_a + application_id + '&type=exact&search=' + joined_string + '&fields=account_id%2C+nickname')
	player_id = json.loads(r.text)

	return(player_id)

def request_all_playerstats(player_id):

	PvP_stats = []
	for account_id in player_id['data']:

		id = str(account_id['account_id'])
		PvP_stats.append(id)

	joined_string = '%2C+'.join(PvP_stats)
	r = requests.get(URL_es + application_id + '&account_id=' + joined_string +
			'&fields=nickname%2C+statistics.pvp.battles%2C+statistics.pvp.wins')
	pvp_stats = json.loads(r.text)
	return(pvp_stats)

def request_shipstats(id, nickname):
	id = str(id)
	nickname = nickname

	for field in AllData:
		if field['player_name'] == nickname:
			ship_id = str(field['ship_id'])

			ShipURL = (URL_PS + application_id + '&account_id=' + id +
				'&fields=pvp.battles%2C+pvp.wins&ship_id=' + ship_id)

	r = requests.get(ShipURL)
	PlayerShipStats = json.loads(r.text)
	return(PlayerShipStats)

def get_player_stats():
	PvP_stat_list = []
	PlayerList = []
	player_id = get_account_id()
	pvp_stats = request_all_playerstats(player_id)

	for stat in pvp_stats['data']:

		id = stat
		nickname = pvp_stats['data'][id]['nickname']

		PlayerShipStats = request_shipstats(id, nickname)

		statistics = pvp_stats['data'][id]['statistics']

		if statistics is not None:
			status = 'public'
			pvp = statistics['pvp']
			TotalBattles = pvp['battles']
			TotalWins = pvp['wins']
			TotalAvg = TotalWins / TotalBattles * 100
			TotalAvg_f = ("{:.2f}".format(TotalAvg) + '%')

			winrate_ship = PlayerShipStats['data'][id][0]['pvp']['wins']
			battles_ship = PlayerShipStats['data'][id][0]['pvp']['battles']
			avg_ship_t = winrate_ship / battles_ship * 100
			avg_ship = ("{:.2f}".format(avg_ship_t) + '%')

		else:
			status = 'private'
			TotalBattles = '0'
			TotalWins = '0'
			TotalAvg_f = '0'
			winrate_ship = '0'
			battles_ship = '0'
			avg_ship = '0'

		PlayerList ={
			'status': status,
			'account_id': id,
			'nickname': nickname,
			'total': 	{
					'TotalBattles': TotalBattles,
					'TotalWins': TotalWins,
					'TotalAvg_f': TotalAvg_f,
					'winrate_ship': winrate_ship,
					'battles_ship': battles_ship,
					'avg_ship': avg_ship }
			}

		PvP_stat_list.append(PlayerList)

	return(PvP_stat_list)

def merge(LIST):

	for row in LIST:
		for col in AllData:
			if row['nickname'] == col['player_name']:
				player_info = col
				player_total = row['total']
				player_info['total'] = player_total
				Merged.append(player_info)

def main():

	parse_logfile()
	get_player_stats()

	LIST = get_player_stats()

	merge(LIST)

	P_LIST = json.dumps(LIST, indent=2)
	P_Data = json.dumps(AllData, indent=2)
	P_Merged = json.dumps(Merged, indent=2)
	print(json.dumps(AllData, indent=4))

main()