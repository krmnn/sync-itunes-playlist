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
import wx
import wx.animate
import threading

rcmd="rsync --size-only"

trackids=[]

class MyPanel(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        caption = wx.StaticText(self, id, label="Loading iTunes Library", pos=(10, 10))
        self.SetBackgroundColour("white")
        gif_fname = "waiting.gif"
        gif = wx.animate.GIFAnimationCtrl(self, id, gif_fname, pos=(10, 30))
        gif.GetPlayer().UseBackgroundColour(True)
        gif.Play()

def start(func, *args): # helper method to run a function in another thread
    thread = threading.Thread(target=func, args=args)
    thread.setDaemon(True)
    thread.start()

def progressbar_update(dialog, value, msg):
    cont, skip = dialog.Update(value, msg) 
    if not cont:
        sys.exit(1)
 
def copyworker(dialog, library, trackids, destination): # put your logic here
    keepGoing = True
    for pos, item in enumerate(trackids):
        if not keepGoing:
            sys.exit(False)
        cur = library['Tracks'][item]
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

            print "Track: '" + cur['Artist'] + " - " + cur['Name'] + "'...",
            if os.path.isfile(dest):
                print "skipped (already exists)"
                continue

            wx.CallAfter(progressbar_update, dialog, pos, pathelem[-1])

            newcmd = "%s %s %s" % (rcmd, srcstr, deststr)
            ret = subprocess.Popen(newcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ret.wait()
            print "copied." 
        else:
            print "Track: '" + path.encode('ascii') + "'...",
            print "skipped (not a local file)"

    wx.CallAfter(dialog.Destroy)


def parse_TunesXML(XMLfile):
    print "Loading iTunes Library... ", 
    f = open(XMLfile, 'r')
    handler = SimpleDataHandler()
    xml.sax.parse(f, handler)
    final_item = handler.final_item
    library = final_item
    num_tracks = len(library['Tracks'])
    num_playlists = len(library['Playlists'])
    print "done. (%i tracks and %i playlists)" % (num_tracks, num_playlists)
    return library

def parse_Playlist(library, playlist):    
    # reading playlist
    for item in library['Playlists']:
        if item['Name'] == playlist:
            if 'Playlist Items' in item:
                tracks = item['Playlist Items']
                for elem in tracks:
                    trackids.append(elem['Track ID'])
            else: 
                print "Playlist '%s' empty or non-existent!" % playlist
                sys.exit(False)


def main():
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
        print "Destination '%s' doesn't exist!" % destination
        sys.exit(False)

    app = wx.PySimpleApp()

    frame = wx.Frame(None, -1, "wx.animate.GIFAnimationCtrl()", size = (300, 300))
    MyPanel(frame, -1)

    frame.Show(True)
    frame.Center()
    library = parse_TunesXML(file_loc)
    tracks = parse_Playlist(library, playlist)
    frame.Show(False)

    progressMax = len(trackids)
    dialog = wx.ProgressDialog("Copying Files", "test", progressMax, style=wx.PD_CAN_ABORT)
    dialog.SetSize((500,100))
    dialog.Center()
    start(copyworker, dialog, library, trackids, destination)
    dialog.ShowModal()
    app.MainLoop()
    
if __name__ == "__main__":
    main() 
