#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""

--Channel Allocation for EEG, EMG, LFP
If you want to set a specific EEG channel as EEG.mat 
(and it's not the first 'e' in the allocation string), then use capital E, M, or L.
If all e's, m's, or l's are lower- or uppper-case, the first e,m,l will be used as primary
EEG, EMG, LFP
For example, emEm, will use the second EEG for EEG.mat, and will use the first EMG as EMG.mat

--Notes
For the notes (generated by the intan system), I assume the following syntax:
Notes start with the following string:
#Notes:
(followed by newline)
Individual notes start with //
To designate a note to a specific mouse use '@MOUSE_ID'.
For example, the note
//@S10 sleeping well today
will be assigned to mouse S10. But the note
//lights problems today
will go to all recorded mice 

@author: FW

"""
import sys
import re
import os.path
import numpy as np
import scipy.io as so
import tkFileDialog as tkf
import Tkinter as Tk
from shutil import copy2
import pdb
# to do: copy video file, process video file, time.dat
# Channel allocation
# introduce colleague field and port number


def get_infoparam(ppath, name):
    """
    name is a parameter/info text file, saving parameter values using the following
    syntax:
    field:   value 
    
    in regular expression:
    [\D\d]+:\s+.+    
    
    The function return the value for the given string field
    """
    fid = open(os.path.join(ppath, name), 'rU')    
    lines = fid.readlines()
    params = {}
    in_note = False
    fid.close()
    for l in lines :
        if re.search("^#[nN]otes:(.*)", l):
            #a = re.search("^#\s*(.*)", l)
            #params['note'] = [a.group(1)]
            #continue
            in_note = True
            params['note'] = []
            continue
        if in_note == True:
            if re.match("^[A-z_]+:", l):
                in_note=False
             
            if in_note and not(re.search("^\s+$", l)):
                params['note'].append(l)
        if re.search("^\s+$", l):
            continue
        if re.search("^[A-z_]+:" ,l):
            a = re.search("^(.+):" + "\s+(.*$)", l)
            if a :
                v = a.group(2).rstrip()
                v = re.split('\s+', v)
                params[a.group(1)] = v    
      
    # further process 'note' entry
    tmp = [i.strip() for i in params['note']]
    tmp = [i + ' ' for i in tmp]    
    if len(tmp)>0:
        f = lambda x,y: x+y
        tmp = reduce(f, tmp)
        tmp = re.split('//', tmp)
        tmp = ['#'+i for i in tmp if len(i)>0]

    #tmp = os.linesep.join(tmp)    
    params['note'] = assign_notes(params, tmp)
            
    return params


def assign_notes(params, notes):
    """
    check for each comment whether it was assigned to a specific mouse/mice using the 
    @ special sign; or (if not) assign it to all mice
    """
    comment = {} 
    
    mice = params['mouse_ID']
    for m in mice:
        comment[m] = []
    
    #notes = params['note']
    for l in notes:
        if re.match('@', l):
            for m in mice:
                if re.match('@' + m, l):
                    comment[m].append(l)
        else:
            comment[m].append(l)
                            
    #params['note'] = comment
    return comment


def file_time(filename):
    """
    get time stamp of file; 
    @RETURN:
        string of the format month+day+year, month, day and year each allocated 
        only two chars
    """
    import datetime
    t = os.path.getmtime(filename)
    d = datetime.datetime.fromtimestamp(t)
    day = str(d.day)
    month = str(d.month)
    year = str(d.year)
    
    if len(day) < 2:
        day = '0' + day
    if len(month) < 2:
        month = '0' + month
    year = year[2:]
        
    return month+day+year
    


def get_param_file(ppath):
    """
    get the parameter file, i.e. the only .txt file within the specified
    folder $ppath
    """
    
    files = [f for f in os.listdir(ppath) if re.search('\.txt$', f)]
    if len(files)>1:
        print("Error more than one .txt files in specified folder %s" % ppath)
        sys.exit(1)
    if len(files) == 0:
        print("Error no parameter file in specified folder %s" % ppath)
    else:
        return files[0]
    


def get_lowest_filenum(path, fname_base):
    """
    I assume that path contains files/folders with the name fname_base\d+
    find the file/folder with the highest number i at the end and then 
    return the filename fname_base(i+1)
    """
    files = [f for f in os.listdir(path) if re.match(fname_base, f)]
    l = []
    for f in files :
        a = re.search('^' + fname_base + "(\d+)", f)
        if a :
            l.append(int(a.group(1)))           
    if l: 
        n = max(l) + 1
    else:
        n = 1

    return fname_base+str(n)    



def parse_challoc(ch_alloc):
    """
    the channel allocation string must have one capital E,M,L (if present).
    If there are only lower-case e's, m's, or l's or only capital E's, M's, or L's,
    set the first e,m,l to upper-case and the rest to lower-case
    """
    
    # search for e's
    neeg = len(re.findall('[eE]', ch_alloc))
    nemg = len(re.findall('[mM]', ch_alloc))
    nlfp = len(re.findall('[lL]', ch_alloc))
    
    # only small e's
    if neeg == len(re.findall('e', ch_alloc)):
        ch_alloc = re.sub('e', 'E', ch_alloc, count=1)
    # only large E
    if neeg == len(re.findall('E', ch_alloc)):
        ch_alloc = re.sub('E', 'e', ch_alloc)
        ch_alloc = re.sub('e', 'E', ch_alloc, count=1)
    
    # only small m's
    if nemg == len(re.findall('m', ch_alloc)):
        ch_alloc = re.sub('m', 'M', ch_alloc, count=1)
    # only large M
    if nemg == len(re.findall('M', ch_alloc)):
        ch_alloc = re.sub('M', 'm', ch_alloc)
        ch_alloc = re.sub('m', 'M', ch_alloc, count=1)

    # only small l's
    if nlfp == len(re.findall('l', ch_alloc)):
        ch_alloc = re.sub('l', 'L', ch_alloc, count=1)
    # only large L
    if nlfp == len(re.findall('L', ch_alloc)):
        ch_alloc = re.sub('L', 'l', ch_alloc)
        ch_alloc = re.sub('l', 'L', ch_alloc, count=1)

    return ch_alloc



#######################################################################################  
### START OF SCRIPT ###################################################################
#######################################################################################
# Parameters to set at each computer:
PPATH = '/Volumes/Transcend/Miniscope'
ndig = 16

# chose directory with intan raw files to be processed:
root = Tk.Tk()
intan_dir = tkf.askdirectory()
root.update()
# load all parameters from *.txt file, located in intan recording dir
param_file = get_param_file(intan_dir)

params = get_infoparam(intan_dir, param_file)
mice = params['mouse_ID']
print "We have here the following mice: %s" % (' '.join(mice))

# total number of recorded channels
ntotal_channels = sum([len(a) for a in params['ch_alloc']])
print('In total, %d channels were used' % ntotal_channels)
# get time stamp of recording
if params.has_key('date'):
    date = params['date'][0]  
    dtag = re.sub('/', '', date)
else:
    dtag = file_time(os.path.join(intan_dir, 'amplifier.dat'))
print "Using %s as date tag" % dtag

# load all data
print("Reading data file...")
data_amp = np.fromfile(os.path.join(intan_dir, 'amplifier.dat'), 'int16')
print("Processing digital inputs...")
data_din = np.fromfile(os.path.join(intan_dir, 'digitalin.dat'), 'int16')

# convert data_in to Array which each column corresponding to one digital input
#Din = np.fliplr(np.array([np.array(list(np.binary_repr(x, width=16))).astype('int16') for x in data_din]))
SR = int(params['SR'][0])
Din = np.zeros((data_din.shape[0], 16), dtype='int16')
ihour = 0
nhour = data_din.shape[0] / (3600 * SR)

dinmap = {}
for i in range(0, 2**ndig):
    dinmap[i] = np.array(list(np.binary_repr(i, width=ndig)[::-1])).astype('int16')

for j in range(data_din.shape[0]):
    if int(((j+1) % (3600*SR))) == 0:
        ihour += 1
        print "Done with %d out of %d hours" % (ihour, nhour)
    if data_din[j] < 0:
        Din[j,:ndig] = dinmap[0]
    else:
        Din[j,:ndig] = dinmap[data_din[j]]


# consistency test: Number of data points in Din should match with data_amp:
if Din.shape[0] != data_amp.shape[0]/ntotal_channels:
    sys.exit('Something wrong: most likely some error in the channel allocation')

recording_list = []
# save data to individual mouse folders
imouse = 0
ch_offset = 0 # channel offset; 
first_cl = 3
first_dep = 11
for mouse in mice:
    print "Processing Mouse %s" % mouse
    ch_alloc = parse_challoc(params['ch_alloc'][imouse])
    nchannels = len(ch_alloc)
    fbase_name = mouse + '_' + dtag + 'n' 
    name = get_lowest_filenum(PPATH, fbase_name)
    recording_list.append(name)
    
    if not(os.path.isdir(os.path.join(PPATH,name))):
        print "Creating directory %s\n" % name
        os.mkdir(os.path.join(PPATH,name))        
    
    neeg = 1
    nemg = 1
    nlfp = 1
     # channel offset
    for c in ch_alloc:
        dfile = ''
        if re.match('E', c):
            dfile = 'EEG'
        if re.match('e', c):
            dfile = 'EEG' + str(neeg+1)
            neeg += 1
        if re.match('M', c):
            dfile = 'EMG'
        if re.match('m', c):
            dfile = 'EMG' + str(nemg+1)
            nemg += 1
        if re.match('L', c):
            dfile = 'LFP'
        if re.match('l', c):
            dfile = 'LFP' + (str(nlfp+1))
            nlfp += 1
        
        # Save EEG EMG
        if len(dfile) > 0:
            print "Saving %s of mouse %s" % (dfile, mouse)
            so.savemat(os.path.join(PPATH, name, dfile + '.mat'), {dfile: data_amp[ch_offset::ntotal_channels]})
        ch_offset += 1 # channel offset
    
    so.savemat(os.path.join(PPATH, name, 'laser_' + name + '.mat'), {'laser':Din[:,11]})        
    # save Laser
    try:
        if params['mode'][0] == 'ol':
            so.savemat(os.path.join(PPATH, name, 'laser_' + name + '.mat'), {'laser':Din[:,1]})
        elif params['mode'][0] == 'cl':
            so.savemat(os.path.join(PPATH, name, 'laser_' + name + '.mat'), {'laser':Din[:,first_cl]})
            so.savemat(os.path.join(PPATH, name, 'rem_trig_' + name + '.mat'), {'rem_trig':Din[:,first_cl+4]})
            if 'X' not in name:
               first_cl += 1
               
    except KeyError:
        if any(Din[:,1]):
            so.savemat(os.path.join(PPATH, name, 'laser_' + name + '.mat'), {'laser':Din[:,1]})
        elif any(Din[:,first_cl]):
            so.savemat(os.path.join(PPATH, name, 'laser_' + name + '.mat'), {'laser':Din[:,first_cl]})
            so.savemat(os.path.join(PPATH, name, 'rem_trig_' + name + '.mat'), {'rem_trig':Din[:,first_cl+4]})
            first_cl += 1


    so.savemat(os.path.join(PPATH, name, 'pull_' + name + '.mat'), {'pull':Din[:,first_dep]})
    # if 'S38' in name:
    #     first_dep += 2
    # else:
    first_dep += 1

    
    # save Video signal
    # Note: till 12/11/2017 I accidentally called the dictionary entry 'laser'
    so.savemat(os.path.join(PPATH, name, 'videotime_' + name + '.mat'), {'video':Din[:,2]})

    
    # save on/off signal (signal indicate when the recording started and ended)
    # only save first and last index, when signal is on
    onoff = np.where(Din[:,0]>0.1)[0][[0,-1]]
    so.savemat(os.path.join(PPATH, name, 'onoff_' + name + '.mat'), {'onoff':onoff})
    
    # save info file - I do this to split the parameter.txt file into
    # individual info.txt files for each recorded mouse
    fid = open(os.path.join(PPATH, name, 'info.txt'), 'w')    
    # first write notes
    comments = params['note'][mouse]
    for l in comments:
        fid.write(l + os.linesep)
    # write all other info tags
    for k in params.keys():
        v = params[k]
        if k == 'note':
            continue
        if len(v) == 1:
            # shared attribute
            fid.write(k + ':' + '\t' + v[0] + '\n')
        else:
            # individual attribute
            fid.write(k + ':' + '\t' + v[imouse] + '\n')
    # add a colleagues tag, i.e. other mice recorded together with mouse
    colleagues = mice[:]
    colleagues.remove(mouse)
    fid.write('colleagues:\t' + ' '.join(colleagues) + os.linesep)        
    fid.close()

    # copy info.rhd from intan_dir to PPATH/name
    copy2(os.path.join(intan_dir, 'info.rhd'), os.path.join(PPATH, name))
    
    # end of loop over mice
    imouse += 1
    



