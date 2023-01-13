import subprocess, os
from time import sleep
from datetime import datetime
servers = ['mc-mountaintop', 'mc-creativetop', 'mc-gregtech']
banned_chars = ['sudo', '>', '<', "'", '{', '}', '[', ']', '=', '-', '(', ')', '.', ',', '/', 'left', 'right', 'up', 'down']
def get_log(server, lines = 5):
	log = subprocess.check_output(['tmux','capture-pane','-S',str(28 - lines),'-p','-t',server]).decode('utf-8').split('\n')
	while '' in log:
		log.remove('')
	return log

def get_chat(server, lines = 5):
	log = get_log(server, lines)
	chat = []
	for item in log:
		msgtype = filter_msg(item)
		if msgtype != None:
			chat.append((item, msgtype))
	return chat

def get_players(server):
	os.system('tmux send-keys -t {} /list Enter'.format(server))
	plist = None
	while 'players online:' not in '\n'.join(get_log(server)):
		sleep(0.1)
	log = get_log(server)
	for line in log:
		if 'players online:' in line and '>' not in line:
			plist = line.split('e: ')
			if len(plist) > 1:
				return plist[1].split(', ')
			else:
				return []

def run_network_tellraw(origin_server, tellraw):
	for server in servers:
		if server != origin_server:
			os.system(f'tmux send-keys -t {server} ' + tellraw)

def safe_tellraw(origin_server, tellraw, alt_tellraw = None, override_empty = False):
	for server in servers:
		if len(server_players[server]) > 0 or override_empty:
			if origin_server != server:
				os.system(f'tmux send-keys -t {server} ' + tellraw)
			elif origin_server == server and alt_tellraw != None:
				os.system(f'tmux send-keys -t {origin_server} ' + alt_tellraw)

def get_network_players(trust = True):
	plist = []
	if trust:
		for server in servers:
			plist.extend(server_players[server])
		return plist
	else:
		for server in servers:
			splist = get_players(server)
			if splist != None and type(splist) == list:
				plist.extend(splist)
	return plist

def get_running_servers():
	slist = subprocess.check_output(['tmux','ls']).decode('utf-8').split('\n')
	slist.remove('')
	for server in slist:
		slist[slist.index(server)] = server.split(':')[0]
	return slist

def cull_servers():
	global servers
	crs = get_running_servers()
	for server in servers:
		if server not in crs:
			servers.remove(server)

def filter_msg(message):
	if '/tellraw @' in message:
		return None
	rulesheet = {'chat': ['>','com.mojang.authlib'], 'leave_msg': ['left', '>'], 'join_msg': ['joined', '>']}
	for rule in rulesheet:
		if rulesheet[rule][0] in message and rulesheet[rule][1] not in message:
			return rule
	return None

print('Starting Chatlink\nMade by Jellxy\nInitializing...')
cull_servers()
server_chatlogs = {}
server_players = {}
for server in servers:
	server_chatlogs[server] = []
	server_players[server] = get_players(server)
	if len(server_players[server]) > 0:
		print('Current {} players: {}'.format(server, ', '.join(server_players[server])))
	else:
		print(f'{server} is empty')

for server in servers: #Cache pre-existing chat to reduce spam when program starts
		chatlog = get_chat(server, 10)
		for chat in chatlog:
			if chat[0] not in server_chatlogs[server]:
				server_chatlogs[server].append(chat[0])

pcheck_timer = 0
while True:
	cull_servers()

	for server in servers:
		chatlog = get_chat(server, 10)
		for chat_tuples in chatlog:
			chat = chat_tuples[0]
			if chat not in server_chatlogs[server]:
				if filter_msg(chat) == 'chat':
					username = chat.split('<')[1].split('>')[0]
					message = chat.split('> ')[1]
					print(chat[33:])
					edited_message = message
					for char in banned_chars:
						if char in ['up', 'down', 'left', 'right']:
							edited_message = edited_message.replace(char, '​'.join([*char]))
							print('​'.join([*char]))
						edited_message = edited_message.replace(char, f'"{char}"')
					safe_tellraw(server, '/tellraw Space @a Space [{{\\"text\\":\\"\\<\\"}},{{\\"text\\":\\"{}\\",\\"color\\":\\"yellow\\"}},{{\\"text\\":\\"\\> Space {}\\"}}] Enter'.format(username, ' Space '.join(edited_message.split(' '))))
					server_chatlogs[server].append(chat)
				else:
					username = chat.split(': ')[1].split(' ')[0]
					if filter_msg(chat) == 'leave_msg':
						#LEFT
						safe_tellraw(server, '/tellraw Space @a Space [{{\\"color\\":\\"yellow\\",\\"text\\":\\"{} Space has Space unjoined Space \\"}},{{\\"color\\":\\"aqua\\",\\"text\\":\\"{}\\"}}] Enter'.format(username, server.split('-')[1]))
						if username in server_players[server]:
							server_players[server].remove(username)
					elif filter_msg(chat) == 'join_msg':
						#JOINED
						if username not in server_players[server]:
							server_players[server].append(username)
						ft = '/tellraw Space @a Space [{{\\"color\\":\\"yellow\\",\\"text\\":\\"{} Space has Space joined Space \\"}},{{\\"color\\":\\"aqua\\",\\"text\\":\\"{}\\"}}] Enter'.format(username, server.split('-')[1])
						at = '/tellraw Space {} Space [{{\\"text\\":\\"Players Space on Space the Space network:\\\\n\\",\\"color\\":\\"aqua\\"}},{{\\"text\\":\\" Space {}\\",\\"color\\":\\"white\\"}}] Enter'.format(username, ' Space \\\\n Space '.join(get_network_players()))
						safe_tellraw(server, ft, at, True)
					server_chatlogs[server].append(chat)
		while len(server_chatlogs[server]) > 9:
			server_chatlogs[server].pop(0)
	pcheck_timer += 1

	if pcheck_timer >= 3599:
		pcheck_timer = 0
		print('RUNNING PCHECK:')
		for server in servers:
			server_players[server] = get_players(server)
			if len(server_players[server]) > 0:
				print('	PCHECK: Current {} players: {}'.format(server, ', '.join(server_players[server])))
			else:
				print(f'	PCHECK: {server} is empty')
	sleep(1)