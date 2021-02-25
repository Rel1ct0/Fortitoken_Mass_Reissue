import requests
import sys
import json
import warnings


newToken = {
    "active": True,
    'token_auth': True,
    'token_serial': '',
    'token_type': 'ftm'
}


SkipIf = 'OU=Disabled'


if len(sys.argv) != 4:
    print("Syntax: ./Fortitoken_Reissue <FortiAuthIP> <ApiAdminUsername> <ApiAdminKey>")
    exit(1)

warnings.filterwarnings("ignore")
FortiAuth = sys.argv[1]
user = sys.argv[2]
apiKey = sys.argv[3]


print('Getting a list of inactive users')
userList = requests.get(f'https://{FortiAuth}/api/v1/ldapusers/?format=json&limit=10000&active=false',
                        auth=(user, apiKey),
                        verify=False)

if userList.status_code > 299:
    print(f"Error, got {userList.status_code}")
    exit(1)

userList = userList.json()['objects']
print(f'Found {len(userList)} inactive users')

usersToReissue = list()

for _ in userList:
    if SkipIf not in _['dn']:
        usersToReissue.append(_)

print(f'Found {len(usersToReissue)} inactive users that will have their Tokens reissued')

tokens = requests.get(f'https://{FortiAuth}/api/v1/fortitokens/?format=json&limit=10000&status=available',
                      auth=(user, apiKey),
                      verify=False)
if tokens.status_code > 299:
    print(f"Error, got {tokens.status_code}")
    exit(1)

tokens = tokens.json()['objects']
print(f'Found {len(tokens)} available tokens')

freetokens = list()

for token in tokens:
    if token['locked'] == False:
        freetokens.append(token)

print(f'Found {len(freetokens)} available and unlocked tokens')

print('Reissuing tokens...')

usercounter = 0
for nextuser in usersToReissue:
    newToken['token_serial'] = freetokens[usercounter]['serial']
    done = requests.patch(f"https://{FortiAuth}/api/v1/ldapusers/{nextuser['id']}/",
                    data=json.dumps(newToken),
                    auth=(user, apiKey),
                    verify=False)
    usercounter = usercounter + 1
    if done.status_code < 300:
        print(f'Ok, token reissued for {nextuser["username"]}')
    else:
        print(f"Got error {done.status_code} for user {nextuser['id']}")
        print(done.content)

print(f'Reissued tokens for {usercounter} users')