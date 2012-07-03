#!/opt/local/bin/python

import optparse
import sys
import base64
import os
import xml.sax
from simple_data_handler import SimpleDataHandler
import shutil
import unicodedata
import urllib2
from urlparse import urlparse
from stat import *
import subprocess

playlist="XPeria Sola"
destination="/Volumes/Beta/test/"

rcmd="rsync --human-readable --size-only -progress"

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-l", '--library-file', dest='library_file', 
                      default=os.path.expanduser('~/Music/iTunes/iTunes Library.xml'),
                      help='Location of iTunes library xml file')
    parser.add_option("--test", action='store_true', dest='test',
                      default=False, help='Run parser against test.xml')
    options, args = parser.parse_args()

    if options.test:
        file_loc = 'test.xml'
    else:
        file_loc = options.library_file
   
    print "Loading iTunes Library... ", 
    f = open(file_loc, 'r')
    handler = SimpleDataHandler()
    
    xml.sax.parse(f, handler)

    final_item = handler.final_item

    library = final_item
    #num_tracks = len(library['Tracks'])
    #num_playlists = len(library['Playlists'])
    
    print "done."
    #print "Library Summary"
    #print "%i tracks and %i playlists" % (num_tracks, num_playlists)

    trackids=[]
    for item in library['Playlists']:
        if item['Name'] == playlist:
            tracks = item['Playlist Items']
            for elem in tracks:
                trackids.append(elem['Track ID'])

    print os.path.supports_unicode_filenames
    print sys.getfilesystemencoding()

    for item in trackids:
        cur = library['Tracks'][item]
        print "Syncing ", cur['Artist'], "-", cur['Name']
        url = cur['Location']
        (scheme, netloc, path, ignored, ignored, ignored)  = urlparse(url)
        print scheme, netloc, path
        if scheme == "file" and netloc == "localhost":
            pathstr = path.encode('ascii')
            pathstr = urllib2.unquote(pathstr)
            #print "os.path.isfile:", os.path.isfile(pathstr)

            pathelem = pathstr.split('/')

            destpath = destination + pathelem[-3] + "/" + pathelem[-2] + "/"
            if os.path.isdir(destpath) == False:
                os.makedirs(destpath)

            srcstr = "\"" + pathstr + "\"" 
            deststr = "\"" + destpath + "/" + pathelem[-1] + "\""

            newcmd = rcmd + " " + srcstr + " " + deststr
            print newcmd
            ret = subprocess.Popen(newcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print ret.stdout.read()
            print ret.stderr.read()
        else:
            print "skipping: not a local file!"


        print "done."

