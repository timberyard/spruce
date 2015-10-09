# -*- coding: utf-8 -*-
import os
import sys
import argparse
from smb.SMBConnection import SMBConnection


def main(files, branch, commit, dist, directory, addPath="bin"):
	try:
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

		if not os.path.exists(directory):
			os.makedirs(directory)

		for f in files:
			conn = SMBConnection("builds", "builds", "phoenix", "EVERBASE")
			conn.connect("192.168.55.60")

			folder = conn.listPath("ci-builds", 'backend/{}/'.format(branch), pattern='*')
			foldername = None
			for filename in folder:
				if commit in filename.filename:
					foldername = filename.filename

			myFile = open("{}/{}".format(directory, f), 'w+')
			file_attributes, filesize = conn.retrieveFile("ci-builds", 'backend/{0}/{1}/{2}/build/{4}/{3}'.format(branch, foldername, dist, f, addPath), myFile)
			print("Got " + f + " -> " + directory)

	except:
		e = sys.exc_info()[1]
		print "An error occured: \n" + str(e)

if __name__ == "__main__":
	main(["everbase_kernel"], "master", "d8066ca", "linux_ubuntu-14.04_x86-64_gcc_release", "/var/evertest/pulledFiles")

## Syntax example: python smbPull.py -b master -c d8066ca -d linux_ubuntu-14.04_x86-64_gcc_release -f everbase_filesystem everbase_kernel ##

