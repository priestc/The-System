# enter the default password below
password = ''

import os
from optparse import OptionParser
from tsclient.core import VERSION

parser = OptionParser(usage="%prog [PATH] [options]", version=str(VERSION))

parser.add_option('-p', "--password",
                  dest="password",
                  metavar="PASS",
                  default=None,
                  help="The password for the whole thing to work (gotten from you-know-where)")

parser.add_option('-k', "--skip-verify",
                  dest="skip_verify",
                  action="store_true",
                  help="Skip Verification before uploading")
                  
parser.add_option('-a', "--artist",
                  dest="artist",
                  metavar="ARTIST",
                  help="Manually set the artist name (ignore ID3 tags)")
                  
parser.add_option('-b', "--album",
                  dest="album",
                  metavar="ALBUM",
                  help="Manually set the album name (ignore ID3 tags)")

parser.add_option('-d', "--date",
                  dest="date",
                  metavar="DATE",
                  help="Manually set the date (ignore ID3 tags)")

parser.add_option('-m', "--meta",
                  dest="meta",
                  metavar="META",
                  help="Album meta data (such as 'remastered 2003')")

parser.add_option("--just-archive",
                  dest="just_archive",
                  action="store_true",
                  default=False,
                  help="Outputs archive to the current working directory for inspection, and skips upload")

parser.add_option("--leave-archive",
                  dest="leave_archive",
                  action="store_true",
                  default=False,
                  help="Outputs archive to the current working directory for inspection, and still does upload")

parser.add_option("--bootleg",
                  dest="bootleg",
                  action="store_true",
                  default=False,
                  help="This album is a bootleg (disables bitrate checks)")

parser.add_option("-q", "--silent",
                  dest="silent",
                  action="store_true",
                  default=False,
                  help="No output except for the server response")

parser.add_option("--local",
                  dest="local",
                  action="store_true",
                  default=False,
                  help="Use local dev server (testing only)")
            
(options, args) = parser.parse_args()

########################

if options.password:
    password = options.password

if (not options.just_archive) and password == '':
    print "Password Required"
    raise SystemExit

if options.local:
    setattr(options, 'url', 'http://localhost:8000')
else:
    setattr(options, 'url', 'http://thesystem.chickenkiller.com')

# get the path to the directory to upload.
try:
    setattr(options, 'path', args[0])
except IndexError:
    # if no path was specified, then use the current working directory
    setattr(options, 'path', os.getcwd())
