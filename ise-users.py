import sys, getopt
import json
import requests   
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings() 

def main(argv):
  """
  Parses arguments and checks for specific options (-h -l -d or --list --delete) to decide wethere to list only or also delete users.
  :return: True to delete users, False to only list current users.
  :rtype: bool
  """
  del_users = False
  arg_flag = False
  try:
    opts, args = getopt.getopt(argv,"ldh",["list","delete"])
  except getopt.GetoptError:
    print("Wrong arguments. Use '-l' or '--list' to list all users on ISE, '-d' or '--delete' to delete the users on the users.txt file.")
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print("Use '-l' or '--list' to list all userson ISE, '-d' or '--delete' to delete the users on the users.txt file..")
      sys.exit()
    elif opt in ("-l", "--list"):
      del_users = False
      arg_flag = True
      print("Users will be listed...\n")
    elif opt in ("-d", "--delete"):
      del_users = True
      arg_flag = True
      print("Users will be deleted...\n")
  if arg_flag :
    return del_users
  else : 
    print("No arguments used. Use '-l' or '--list' to list all users on ISE, '-d' or '--delete' to delete the users on the users.txt file..")
    sys.exit(1)
  
def confirm(message):
  """
  Ask user to enter Y or N (case-insensitive).
  :return: True if the answer is Y.
  :rtype: bool
  """
  answer = ""
  while answer not in ["y", "n"]:
    answer = input(message).lower()
  return answer == "y"   

delete_enabled = False
print("This scritp will either only list current users on ISE server or delete users provided on users.txt file\n")
delete_enabled = main(sys.argv[1:])

# Open a file called "server.txt" with server ip/name and API key for ISE separated by newlines.
keyFile = open('server.txt', 'r')
server = keyFile.readline().strip()
api_key = keyFile.readline().strip()
keyFile.close()
print("Using server " + server)
print("Using API Key " + api_key)

auth = HTTPBasicAuth("APIUser", api_key)

headers = {'Accept': 'application/json',
           'Content-Type': 'application/json' }

url = 'https://' + server + ':9060/ers/config/internaluser'

response = requests.get(url, headers=headers, auth=auth, verify=False).json()
users = response["SearchResult"]["resources"]

# ISE returns by default 20 users per page. Here we cycle through the pages while the nextPage key is returned.
f = True
while f:
  try:
    url = response["SearchResult"]["nextPage"]["href"]
    print(url)
    response = requests.get(url, headers=headers, auth=auth, verify=False).json()
    users.extend(response["SearchResult"]["resources"])
  except:
    f = False

# Here we extract user name and id  
user_list = {}
for i, user in enumerate(users):
    user_list[user['name']] = user['id']

print(user_list)

# Open a file called "users.txt" containing usernames (one on each newline) to be deleted.
fo = open("users.txt", "r+")
print ("User list to be Deleting users in: ", fo.name)
line = fo.readlines()
delete_list = []
for i in line:
  delete_list.append(i.strip())
print ("Read Line: %s" % (delete_list))
# Close opened file
fo.close()

delete_dic={}
not_found=[]
for user in delete_list:
  if user in user_list:
    delete_dic[user] = user_list[user]
  else:
    not_found.append(user)

print("Users not found on ISE: {}".format(not_found))

print("Users to be deleted: {}".format(delete_dic))

if confirm("Do you want to delete this users? (y/n) "):
  print("Deleting users...")
  url = 'https://' + server + ':9060/ers/config/internaluser/'
  for user in delete_dic:
    print("Deleting user {}...".format(user), end =" ")
    response = requests.delete(url + str(delete_dic[user]), headers=headers, auth=auth, verify=False)
    print(response.ok)

else:
  print("Exiting without deleting. Bye!")