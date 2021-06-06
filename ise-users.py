import sys, getopt
import json
import requests   
from datetime import datetime
from requests.auth import HTTPBasicAuth

# Function definition
def myPrint(text, logfile, eol):
  """
  Prints given text to the stdout and appends it to the logfile provided.
  eol is a flag to select wether we add a \n or not to the line.
  :return: 0
  :rtype: int
  """
  # Print to screen
  if eol:
    print(text)
  else:
    print(text, end=" ")
  
  # Open the file in append & read mode ('a+')
  with open(logfile, 'a+') as f:
    # Move read cursor to the start of file.
    #f.seek(0)
    # If file is not empty then append '\n'
    #data = f.read(100)
    #if len(data) > 0:
    #  f.write("\n")
    # If eol exists then append '\n'
    if eol:
      f.write(text + "\n")
    # Append text at the end of file
    else:
      f.write(text)
  return 0

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
    myPrint("Wrong arguments. Use '-l' or '--list' to list all users on ISE, '-d' or '--delete' to delete the users on the users.txt file.", logfile, True)
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      myPrint("Use '-l' or '--list' to list all userson ISE, '-d' or '--delete' to delete the users on the users.txt file.", logfile, True)
      sys.exit()
    elif opt in ("-l", "--list"):
      del_users = False
      arg_flag = True
      myPrint("You chose only to list users.\n", logfile, True)
    elif opt in ("-d", "--delete"):
      del_users = True
      arg_flag = True
      myPrint("You chose to delete users form user.txt file.\n", logfile, True)
  if arg_flag :
    return del_users
  else : 
    myPrint("No arguments used. Use '-l' or '--list' to list all users on ISE, '-d' or '--delete' to delete the users on the users.txt file.", logfile, True)
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
  
""" Begining of the script."""
# Gets time and date to name the logfile in YYmmdd-HM format.
now = datetime.now()
timestamp = now.strftime("%Y%m%d-%H%M")

logfile = 'ise-users_'+timestamp+'.log'
myPrint("Started on {} at {}\n".format(now.strftime("%B %d, %Y"),now.strftime("%H:%M:%S")), logfile, True)

delete_enabled = False
myPrint("This scritp will either list current users on ISE server or delete users provided on users.txt file.", logfile, True)
delete_enabled = main(sys.argv[1:])

""" We still need to connect to the server and retreive the users to get the id in order to delete them."""

# Open a file called "server.txt" with server ip/name and API key for ISE separated by newlines.
keyFile = open('server.txt', 'r')
server = keyFile.readline().strip()
api_key = keyFile.readline().strip()
keyFile.close()
myPrint("Connecting to server " + server + " using API Key provided on file.", logfile, True)

# Connecting to server to read all users.
requests.packages.urllib3.disable_warnings() # ignoring certificate validation
auth = HTTPBasicAuth("APIUser", api_key)
headers = {'Accept': 'application/json',
           'Content-Type': 'application/json' }
url = 'https://' + server + ':9060/ers/config/internaluser'
try:
  response = requests.get(url, headers=headers, auth=auth, verify=False).json()
except:
  myPrint("Connection to server " + server + " failed. Exiting...", logfile, True)
  sys.exit(2)
    
# Extracting user information from api response.
users = response["SearchResult"]["resources"]

# ISE returns by default 20 users per page. Here we cycle through the pages while the nextPage key is returned and append results to users.
f = True
while f:
  try:
    url = response["SearchResult"]["nextPage"]["href"]
    response = requests.get(url, headers=headers, auth=auth, verify=False).json()
    users.extend(response["SearchResult"]["resources"])
  except:
    f = False

# Here we extract user name and id.
user_list = {}
for i, user in enumerate(users):
    user_list[user['name']] = user['id']

# Delete was selected with arguments when the script was run.
if delete_enabled:

  # Open a file called "users.txt" containing usernames (one on each newline) to be deleted.
  fo = open("users.txt", "r+")
  myPrint ("\nDeleting users contained in the file {}...".format(fo.name), logfile, True)
  line = fo.readlines()
  delete_list = []
  for i in line:
    delete_list.append(i.strip())
  myPrint ("\nI will try to delete this users on server {}:\n{}".format(server, delete_list), logfile, True)
  # Close opened file
  fo.close()

  # Check to see if user on the list is present on ISE Server.
  delete_dic={}
  not_found=[]
  for user in delete_list:
    if user in user_list:
      delete_dic[user] = user_list[user]
    else:
      not_found.append(user)
  myPrint("\nI couldn't find this users on server {}:\n{}".format(server, not_found), logfile, True)
  myPrint("\nI will delete this users:\n{}".format(delete_dic), logfile, True)

  # Check if there are users on the dic to be deleted.
  if delete_dic:
    # Ask for confirmation before actually deleting the users.
    if confirm("\n\nDo you still want to delete this users? (y/n): "): 
      myPrint("\nDeleting...", logfile, True)
      url = 'https://' + server + ':9060/ers/config/internaluser/'    
      for user in delete_dic:
        myPrint("Deleting user {}...".format(user), logfile, False)
        response = requests.delete(url + str(delete_dic[user]), headers=headers, auth=auth, verify=False)
        if response.ok:
          ans="OK"
        else:
          ans="Fail"
        myPrint(ans, logfile, True)
      myPrint("\nJob done. Bye!", logfile, True)
    else:
      myPrint("\nExiting without deleting. Bye!", logfile, True)
  else:
    myPrint("\nNothing to delete. Bye!", logfile, True)

# List was selected with arguments when the script was run.
else:
  myPrint("\nHere is the list of the existing users on ISE Server {}.\n".format(server), logfile, True)
    
  # Print the names of the columns.
  myPrint(" ------------+-------------------------------------- ", logfile, True)
  myPrint ("| {:<10} | {:<36} |".format('USERNAME', 'ID'), logfile, True)
  myPrint(" ------------+-------------------------------------- ", logfile, True)
  
  # Print each data item.
  for key, value in user_list.items():
    myPrint ("| {:<10} | {:<36} |".format(key, value), logfile, True)
  
  myPrint(" ------------+-------------------------------------- ", logfile, True)
  myPrint("\nJob done. Bye!", logfile, True)