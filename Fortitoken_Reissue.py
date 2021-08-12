import requests
import sys
import json
import warnings
import time

newToken = {
    "active": True,
    'token_auth': True,
    'token_serial': '',
    'token_type': 'ftm'
}

SkipIf = 'OU=Disabled'

warnings.filterwarnings("ignore")
FortiAuth = sys.argv[1]
user = sys.argv[2]
apiKey = sys.argv[3]

logfile = open('token_reissue.log', 'a')
logfile.write(f'\n\n=============={time.asctime(time.localtime())}================\n\n')

logfile.write('Getting a list of inactive users\n')
response = requests.get(f'https://{FortiAuth}/api/v1/ldapusers/?format=json&limit=10000&active=false',
                        auth=(user, apiKey),
                        verify=False)

if response.status_code > 299:
    logfile.write(f"Error, got {response.status_code}\n")
    logfile.close()
    exit(1)

userList = response.json()['objects']

while response.json()['meta']['next']:
    nextData = response.json()['meta']['next']
    response = requests.get(f'https://{FortiAuth}{nextData}',
                        auth=(user, apiKey),
                        verify=False)
    userList.extend(response.json()['objects'])

logfile.write(f'Found {len(userList)} inactive users\n')

usersToReissue = list()

for _ in userList:
    if SkipIf not in _['dn']:
        usersToReissue.append(_)

if not usersToReissue:
    logfile.write('No users eligible for token reissue\n')
    logfile.close()
    exit(0)

logfile.write(f'Found {len(usersToReissue)} inactive users that will have their Tokens reissued\n')

response = requests.get(f'https://{FortiAuth}/api/v1/fortitokens/?format=json&limit=10000&status=available',
                      auth=(user, apiKey),
                      verify=False)
if response.status_code > 299:
    logfile.write(f"Error, got {response.status_code}\n")
    logfile.close()
    exit(1)

tokens = response.json()['objects']

while response.json()['meta']['next']:
    nextData = response.json()['meta']['next']
    response = requests.get(f'https://{FortiAuth}{nextData}',
                        auth=(user, apiKey),
                        verify=False)
    tokens.extend(response.json()['objects'])


logfile.write(f'Found {len(tokens)} available tokens\n')

freetokens = list()

for token in tokens:
    if not token['locked']:
        freetokens.append(token)

logfile.write(f'Found {len(freetokens)} available and unlocked tokens\n')

logfile.write('Reissuing tokens...\n')

usercounter = 0
for nextuser in usersToReissue:
    newToken['token_serial'] = freetokens[usercounter]['serial']
    done = requests.patch(f"https://{FortiAuth}/api/v1/ldapusers/{nextuser['id']}/",
                          data=json.dumps(newToken),
                          auth=(user, apiKey),
                          verify=False)
    usercounter = usercounter + 1
    if done.status_code < 300:
        logfile.write(f'Ok, token reissued for {nextuser["username"]}\n')
    else:
        logfile.write(f'Got error {done.status_code} for user {nextuser["username"]}\n')
        logfile.write(done.content)

logfile.write(f'Reissued tokens for {usercounter} users\n')
logfile.close()
