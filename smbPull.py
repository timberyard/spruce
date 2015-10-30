# -*- coding: utf-8 -*-
import os
import sys
import argparse
import traceback
from smb.SMBConnection import SMBConnection	# Use it this way: https://pythonhosted.org/pysmb/api/smb_SMBConnection.html


def main(files, branch, commit, dist, directory, addPath="bin"):
	try:
		if not os.path.exists(directory):
			os.makedirs(directory)

		for f in files:
			conn = SMBConnection("", "", "", "") # Samba credentials
			conn.connect("") #Samba IP

			folder = conn.listPath("ci-builds", 'backend/{}/'.format(branch), pattern='*') # Example path
			foldername = None
			for filename in folder:
				if commit in filename.filename:
					foldername = filename.filename

			if foldername == None:
				raise IOError("The given commit could not be found on the samba server!")

			myFile = open("{}/{}".format(directory, f), 'w+')
			file_attributes, filesize = conn.retrieveFile("ci-builds", 'backend/{0}/{1}/{2}/build/{4}/{3}'.format(branch, foldername, dist, f, addPath), myFile)
			print("Got " + f + " from " + commit + " -> " + directory)

	except Exception:
		print("An error occured whilst getting files from an Samba server!")
		raise

if __name__ == "__main__":
	main(["someFilename"], "master", "b726tza", "linux_ubuntu-14.04_x86-64_release", "/") #An example smbPull


## Syntax example: python smbPull.py -b master -c d8066ca -d linux_ubuntu-14.04_x86-64_gcc_release -f everbase_filesystem everbase_kernel ##

		# parser = argparse.ArgumentParser(description="This small tool downloads branch and commit specific files from the Everbase Samba Server")
		# parser.add_argument('-f', '--files', nargs='+', help="Files to pull from server", required=True)
		# parser.add_argument('-b', '--branch', help="Branch to pull from", required=True, type=str)
		# parser.add_argument('-c', '--commit', help="Commit to pull from", required=True, type=str)
		# parser.add_argument('-d', '--dist', help="Target distribution", required=True, type=str)

		# parser.add_argument('-u', '--user', help="Samba Username", default="builds")
		# parser.add_argument('-p', '--password', help="Samba Password", default="builds")
		# parser.add_argument('-l', '--local', help="Local Name (can be choosen freely)", default="phoenix")
		# parser.add_argument('-r', '--remote', help="Remote Name", default="EVERBASE")
		# parser.add_argument('-t', '--address', help="Remote IP Address", default="192.168.55.60")
		# parser.add_argument('-s', '--share', help="Remote Share", default="ci-builds")

		# args = parser.parse_args()
