#!/usr/bin/python

import optparse
import sys
import os
import xml.sax
from simple_data_handler import SimpleDataHandler
import unicodedata
import urllib2
from urlparse import urlparse
import subprocess

rcmd="rsync --size-only"

if __name__ == "__main__":
    usage = "usage: %prog [options] <playlist> <destination>"
    parser = optparse.OptionParser(usage)
    parser.add_option("-l", '--library-file', dest='library_file', 
                      default=os.path.expanduser('~/Music/iTunes/iTunes Library.xml'),
                      help='Location of iTunes library xml file')
    options, args = parser.parse_args()

    if os.path.isfile(options.library_file):
        file_loc = options.library_file
    else:
        print "Could not find iTunes Library XML file '%s'!" % options.library_file
        parser.print_help()
        sys.exit(False)

    if len(args) != 2:
        parser.print_help() 
        sys.exit(1)

    playlist = args[0]
    destination = args[1]

    if os.path.isdir(destination) == False:
        print "Destination \'%s\' doesn't exist!" % destination
        sys.exit(False)

    print "Loading iTunes Library... ", 
    f = open(file_loc, 'r')
    handler = SimpleDataHandler()
    xml.sax.parse(f, handler)
    final_item = handler.final_item
    library = final_item
    num_tracks = len(library['Tracks'])
    num_playlists = len(library['Playlists'])
    print "done. (%i tracks and %i playlists)" % (num_tracks, num_playlists)

    trackids=[]
    for item in library['Playlists']:
        if item['Name'] == playlist:
            if 'Playlist Items' in item:
                tracks = item['Playlist Items']
                for elem in tracks:
                    trackids.append(elem['Track ID'])
            else: 
                print "Playlist '%s' empty or non-existent!" % playlist
                sys.exit(False)

    for item in trackids:
        cur = library['Tracks'][item]
        print "Track: '" + cur['Artist'] + " - " + cur['Name'] + "'...",
        url = cur['Location']
        (scheme, netloc, path, ignored, ignored, ignored)  = urlparse(url)
        if scheme == "file" and netloc == "localhost":
            pathstr = path.encode('ascii')
            pathstr = urllib2.unquote(pathstr)

            pathelem = pathstr.split('/')

            destpath = destination + pathelem[-3] + "/" + pathelem[-2] + "/"
            if os.path.isdir(destpath) == False:
                os.makedirs(destpath)

            srcstr = "\"" + pathstr + "\"" 

            dest = destpath + "/" + pathelem[-1]
            deststr = "\"" + destpath + "/" + pathelem[-1] + "\""

            if os.path.isfile(dest):
                print "skipped (already exists)"
                continue

            newcmd = rcmd + " " + srcstr + " " + deststr
            ret = subprocess.Popen(newcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print "copied." 
        else:
            print "skipped (not a local file)"

