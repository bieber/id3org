#!/usr/bin/env python
 ###############################################################################
 # id3org
 # Copyright (C) 2011 Robert Bieber
 #
 # This program is free software: you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation, either version 3 of the License, or
 # (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 # GNU General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License
 # along with this program.  If not, see <http://www.gnu.org/licenses/>.
 #
 ###############################################################################
 # Accepts a single command-line argument identifying the base directory
 # Organizes mp3 and flac files into src/ according to metadata
 # Organizes ogg into ogg/ according to metadata, transcodes if doesn't exist
 ###############################################################################

import sys
import os

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

# Strip '"' out of command-line metadata strings
def escape_metadata(str):
    return str.replace('"', '\\"').encode('ascii', 'ignore')

# Strip any non-alphanumeric characters from song path names
def escape_path(str):
    retval = ""
    for c in str:
        if c.isalnum() or c == ' ':
            retval += c
    return retval

def process_dir(out_list, directory, files):
    for f in files:
        path = os.path.join(directory, f)
        if os.path.isdir(path):
            return
        else:
            ext = f.split('.').pop().lower()
            metadata = {}
            if ext == 'mp3':
                metadata = EasyID3(path)
            elif ext == 'flac':
                metadata = FLAC(path)
            else:
                return
            out_data = {'tracknumber': metadata.get('tracknumber', ['0'])[0],
                        'title': metadata.get('title', ['Untitled'])[0],
                        'album': metadata.get('album', ['Untitled'])[0],
                        'artist': metadata.get('artist', ['Unknown'])[0],
                        'genre': metadata.get('genre', ['Unknown'])[0],
                        'date': metadata.get('date', ['Unknown'])[0],
                        'extension': ext,
                        'path': path}
            song_path = os.path.join(escape_path(out_data['artist']),
                                     escape_path(out_data['album']))
            song_name = "%02d-%s" % (int(out_data['tracknumber'].split('/')[0]),
                                     escape_path(out_data['title']))
            out_data['song_path'] = song_path
            out_data['song_name'] = song_name
            out_list.append(out_data)
                    

if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
    sys.exit("usage: id3org.py base-dir")

# Gathering up the source files
print 'Scanning files...'
source_files = []
os.path.walk(sys.argv[1], process_dir, source_files)

print 'Moving files...'
convert_files = []
for f in source_files:
    # Calculating ideal paths
    src_path = os.path.join(sys.argv[1], 
                            'src',
                            f['song_path'],
                            "%s.%s" % (f['song_name'], 
                                       f['extension'])).encode('ascii',
                                                               'ignore')
    ogg_path = os.path.join(sys.argv[1],
                            'ogg',
                            f['song_path'],
                            "%s.ogg" % f['song_name']).encode('ascii',
                                                              'ignore')

    # Moving the file if the path isn't correct
    if src_path != f['path']:
        os.renames(f['path'], src_path)
        f['path'] = src_path

    # Building a list of files to convert
    if not os.path.exists(ogg_path):
        f['ogg_path'] = ogg_path
        convert_files.append(f)

print "Converting %d files..." % len(convert_files)
for i in range(0, len(convert_files)):
    f = convert_files[i]
    # First decode to a wav file
    if f['extension'] == 'mp3':
        os.system('mpg321 -w .id3org_temp.wav "%s"'
                  % escape_metadata(f['path']))
    elif f['extension'] == 'flac':
        os.system('flac -d -o .id3org_temp.wav "%s"' 
                  % escape_metadata(f['path']))
    else:
        continue # This should never occur
    
    # Then encode as ogg
    os.system(('oggenc -o "%s" -N "%s" -t "%s" -l "%s" -a "%s" -G "%s" ' + 
               '-d "%s" .id3org_temp.wav') % (f['ogg_path'], 
                                              escape_metadata(f['tracknumber']),
                                              escape_metadata(f['title']),
                                              escape_metadata(f['album']),
                                              escape_metadata(f['artist']),
                                              escape_metadata(f['genre']),
                                              escape_metadata(f['date'])))
                                
    os.remove('.id3org_temp.wav')
    print 'Converted file %d/%d...' % (i + 1, len(convert_files))

print 'Finished.'
