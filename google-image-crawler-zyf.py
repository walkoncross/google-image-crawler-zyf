#!/usr/bin/env python
#-*- coding: UTF-8 -*-

#Searching and Downloading Google Images/Image Links

#Import Libraries

import time       #Importing the time library to check the time of code execution
import sys    #Importing the System Library

import os
import os.path as osp

import fnmatch

import json

#import urllib2
from urllib import urlencode

from urllib2 import Request,urlopen
from urllib2 import URLError, HTTPError

import datetime

import hashlib

from collections import OrderedDict

########### CONFIGS ###########
# Path to config_file
config_file = './config.json'

########### Default CONFIGS ###########
CONFIGS = {}

# How many images you want to download for each class. Google will only return 100 images at most for one search
CONFIGS[u'num_downloads_for_each_class'] = 200

# image type to search
CONFIGS[u'search_file_type'] = 'jpg'
#CONFIGS[u'search_file_type'] = 'bmp'
#CONFIGS[u'search_file_type'] = 'png'

# Because google only returns at most 100 results for each search query,
# we must send many search queries to get more than 100 results.
# We need to set cdr (date range, in the form of "tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}") to tell google
# we want to search images in some date range (start_date, end_date),
# so as to get different results for each search query.
# CONFIGS[u'search_cdr_days'] is the days between cd_min and cd_max.
CONFIGS[u'search_cdr_days'] = 60

#This dict is used to search keywords. You can edit this dict to search for google images of your choice. You can simply add and remove elements of the list.
#{class1:[list of related keywords], class2:[list of related keywords]...}
CONFIGS[u'search_keywords_dict'] = {'animal':[u'猫', 'cat', 'dog'],
                                    'fruit':[u'apple', u'banaba']}

#This list is used to further add suffix to your search term. Each element of the list will help you download 100 images. First element is blank which denotes that no suffix is added to the search keyword of the above list. You can edit the list by adding/deleting elements from it.So if the first element of the search_keyword is 'Australia' and the second element of keywords is 'high resolution', then it will search for 'Australia High Resolution'
#aux_keywords = [' high resolution']

CONFIGS[u'save_dir'] = './downloads'

CONFIGS[u'output_prefix'] = 'download_urls'
CONFIGS[u'output_suffix'] = 'google'

print '==>Default CONFIGS:'
print CONFIGS
########### End of Default CONFIGS ###########

########### Load config.json if there is one ###########
if osp.exists(config_file):
    print "Load CONFIGS from " + config_file
    fp = open(config_file, 'a+')
    CONFIGS_loaded = json.load(fp, object_pairs_hook=OrderedDict)
    
    print '==>Loaded CONFIGS:'
    print CONFIGS_loaded

    for k,v in CONFIGS_loaded.iteritems():
		if k in CONFIGS:
			CONFIGS[k] = v
   
    fp.close()
    
    print '==>CONFIGS after loading:'
    print CONFIGS   
########### End of Load config.json ###########


#CONFIGS[u'output_prefix'] = CONFIGS[u'output_prefix'] + '_'
#CONFIGS[u'output_suffix'] = '_' + CONFIGS[u'output_suffix']

CONFIGS[u'save_dir'] = CONFIGS[u'save_dir']+'/'
if not osp.exists(CONFIGS[u'save_dir']):
    os.mkdir(CONFIGS[u'save_dir'])

########### End of CONFIGS ###########

########### Functions to Load downloaded urls ###########
def load_url_files(_dir, file_name_prefix):
    url_list = []
    
    ttl_url_list_file_name = osp.join(_dir, file_name_prefix +'_all.txt')
    if osp.exists(ttl_url_list_file_name):
        fp_urls = open(ttl_url_list_file_name, 'r')        #Open the text file called database.txt
        print 'load URLs from file: ' + ttl_url_list_file_name
        
        i = 0
        for line in fp_urls:
            line = line.strip()
            if len(line)>0:
                url_list.append(line.strip())
                i=i+1
                
        print str(i) + ' URLs loaded'
        fp_urls.close()             
    else:
        url_list = load_all_url_files(_dir, file_name_prefix)
            
    return url_list     

def load_all_url_files(_dir, file_name_prefix):
    url_list = []
    
    for file_name in os.listdir(_dir):
        if fnmatch.fnmatch(file_name, file_name_prefix +'*.txt'):
            file_name = osp.join(_dir, file_name)
            fp_urls = open(file_name, 'r')        #Open the text file called database.txt
            print 'load URLs from file: ' + file_name
            
            i = 0
            for line in fp_urls:
                line = line.strip()
                if len(line)>0:
                    url_list.append(line.strip())
                    i=i+1
            print str(i) + ' URLs loaded'
            fp_urls.close()
            
    return url_list         
########### End of Functions to Load downloaded urls ###########

############## Functions to get date/time strings ############       
def get_current_date():
    tm = time.gmtime()
    date = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)   
    return date
    
def get_new_date_by_delta_days(date, delta_days):
    delta = datetime.timedelta(delta_days)
    new_date = date+delta
    return new_date
    
#Make a string from current GMT time
def get_gmttime_string():
    _str = time.strftime("GMT%Y%m%d_%H%M%S", time.gmtime())
    return _str
 
#Make a string from current local time
def get_localtime_string():
    _str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return _str
############## End of Functions to get date/time strings ############          
    
############## Google Image Search functions ############    
# Get Image URL list form Google image search by keyword
def google_get_query_url(keyword, file_type, cdr):
    url = None
    
    # if keyword is unicode, we need to encode it into utf-8
    if isinstance(keyword, unicode):
        keyword = keyword.encode('utf-8')
        
    query = dict(q = keyword, 
                 tbm = 'isch',
                 tbs=cdr+',ift:'+file_type)
    
    #url = 'https://www.google.com/search?q=' + keyword + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
    #url = 'https://www.google.com/search?as_oq=' + keyword + '&as_st=y&tbm=isch&safe=images&tbs=ift:jpg'
    url = 'https://www.google.com/search?'+urlencode(query)
			
    print "\t==>Google Query URL is: " + url
    return url
    
#Downloading entire Web Document (Raw Page Content)
def google_download_page(url):
    version = (3,0)
    cur_version = sys.version_info
    if cur_version >= version:     #If the Current Version of Python is 3.0 or above
        import urllib.request    #urllib library for Extracting web pages
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
            req = urllib.request.Request(url, headers = headers)
            resp = urllib.request.urlopen(req)
            respData = str(resp.read())
            return respData
        except Exception as e:
            print(str(e))
    else:                        #If the Current Version of Python is 2.x
        import urllib2
        try:
            headers = {}
            headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
            req = urllib2.Request(url, headers = headers)
            response = urllib2.urlopen(req)
            page = response.read()
            return page
        except:
            return"Page Not found"

#Finding 'Next Image' from the given raw page
def google_images_get_next_item(s):
    start_line = s.find('rg_di')
    if start_line == -1:    #If no links are found then give an error!
        end_quote = 0
        link = "no_links"
        return link, end_quote
    else:
        start_line = s.find('"class="rg_meta"')
        start_content = s.find('"ou"',start_line+1)
        end_content = s.find(',"ow"',start_content+1)
        content_raw = str(s[start_content+6:end_content-1])
        return content_raw, end_content

#Getting all links with the help of '_images_get_next_image'
def google_images_get_all_items(page):
    items = []
    while True:
        item, end_content = google_images_get_next_item(page)
        if item == "no_links":
            break
        else:
            items.append(item)      #Append all the links in the list named 'Links'
            time.sleep(0.1)        #Timer could be used to slow down the request for image downloads
            page = page[end_content:]
    return items
   
def google_search_keyword(keyword, file_type, cdr):  
    query_url = google_get_query_url(keyword, file_type, cdr)
    raw_html =  (google_download_page(query_url))
    time.sleep(0.1)
    image_url_list = google_images_get_all_items(raw_html)    
    return image_url_list    
############## End of Google Image Search functions ############    
    
############## Functions to get real urls and download images ############       
#Get real url of a input url    
def get_real_url(url, loaded_urls):
    real_url = None
    response = None
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req)
        
        real_url = response.geturl()
        print 'Real_url is: ' + str(real_url)
        
        if real_url in loaded_urls:
            print 'URL had been downloaded in previous '
            real_url = None
        
    except IOError as e:   #If there is any IOError
        print("IOError on url "+str(url))
        print e
    except HTTPError as e:  #If there is any HTTPError
        print("HTTPError on url "+str(url))
        print e
    except URLError as e:
        print("URLError on url "+str(url))
        print e

    if response:
        response.close()    
        
    return real_url

def download_image(url, save_dir, loaded_urls=None):
    real_url = None
    response = None
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req)
        
        real_url = response.geturl()
        
        if loaded_urls and real_url in loaded_urls:
            print 'URL had been downloaded in previous searching'
            real_url = None
        else:
            img_name = hashlib.md5(real_url).hexdigest()
            save_image_name = save_dir + '/' + img_name + '.' + CONFIGS[u'search_file_type']
            print 'Try to save image ' + real_url + ' into file: ' +  save_image_name
            output_file = open(save_image_name,'wb')
            data = response.read()
            output_file.write(data)
        
        #response.close()
    except IOError as e:   #If there is any IOError
        print("IOError on url "+str(url))
        print e
    except HTTPError as e:  #If there is any HTTPError
        print("HTTPError on url "+str(url))
        print e
    except URLError as e:
        print("URLError on url "+str(url))
        print e

    if response:
        response.close()
        
    return real_url
############## End of Functions to get real urls and download images ############         
    
############## Main Program ############
t0 = time.time()   #start the timer

#Download Image Links
i= 0

cur_date = get_current_date()
print "Today is: " + cur_date.strftime("%Y/%m/%d")

time_str = get_gmttime_string()

for class_name,search_keywords in CONFIGS[u'search_keywords_dict'].iteritems():
    print "Class no.: " + str(i+1) + " -->" + " Class name = " + str(class_name)
   
    class_urls_file_prefix = CONFIGS[u'output_prefix'] + '_' + str(class_name).strip()
    
    items = load_url_files(CONFIGS[u'save_dir'], class_urls_file_prefix)    
    loaded_urls_num = len(items)
    print 'Loaded URLs in total is: ', loaded_urls_num

    # load pre-saved download parameters, actually cd_min for date range
    cd_max = cur_date

    params_file = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix + '_params_' + CONFIGS[u'output_suffix'] + '.txt')
    print 'Loaded pre-saved download parameters from: ' + params_file
    params_list = []
    fp_params = open(params_file, 'a+')
    for line in fp_params:
        line = line.strip()
        if line!='':
            params_list.append(line)
            print "\t-->loaded parameters: ", line
            
    if len(params_list)>0:
        splits = params_list[-1].split('/')
        if len(splits)==3:
            cd_max = datetime.date(int(splits[0]), int(splits[1]), int(splits[2]))
    
    cd_min = get_new_date_by_delta_days(cd_max, -CONFIGS[u'search_cdr_days'])   
    print 'cd_max: ', cd_max
    print 'cd_min: ', cd_min
            
    print ("Crawling Images...")
    
    class_save_dir = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix + '_' + time_str + '_' + CONFIGS[u'output_suffix'])
    if not osp.exists(class_save_dir):
        os.mkdir(class_save_dir)
    
    output_all_urls_file  = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix +'_all.txt')        
    fp_all_urls = open(output_all_urls_file, 'a+')
    
    output_urls_file = osp.join(CONFIGS[u'save_dir'], class_urls_file_prefix + '_' + time_str + '_' + CONFIGS[u'output_suffix'] + '.txt')
    fp_urls = open(output_urls_file, 'a+')
    
#    if osp.exists(output_urls_file):
#        fp_urls = open(output_urls_file, 'a+')        #Open the text file called database.txt
#        for line in fp_urls:
#            items.append(line.strip())
#    else:
#        fp_urls = open(output_urls_file, 'w+')        #Open the text file called database.txt
#    
    cdr_enabled = False
    
    while True:        
        if cdr_enabled:
            cdr = 'cdr:1,cd_min:{},cd_max:{}'.format(cd_min.strftime('%m/%d/%Y'), cd_max.strftime('%m/%d/%Y'))
            print "==>Search for Images between " + cd_min.strftime("%Y/%m/%d") + \
                    ' and ' + cd_max.strftime("%Y/%m/%d")
        else:
            cdr = ''
            print "==>Search for Images in any time"

        j = 0
                
        # Google only return 100 images at most for one search. So we may need to try many times
        while j<len(search_keywords):
            print "\t==>Class name=" + str(class_name) + ', search keywords=' + search_keywords[j]
            keyword = search_keywords[j]#.replace(' ','%20')
            
#            # if keyword is unicode, we need to encode it into utf-8
#            if isinstance(keyword, unicode):
#                keyword = keyword.encode('utf-8')
            
#            query = dict(q = keyword, 
#                         tbm = 'isch',
#                         tbs=tbs+',ift:'+CONFIGS[u'search_file_type'])
#            
#            #url = 'https://www.google.com/search?q=' + keyword + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
#            #url = 'https://www.google.com/search?as_oq=' + keyword + '&as_st=y&tbm=isch&safe=images&tbs=ift:jpg'
#            url = 'https://www.google.com/search?'+urlencode(query)
#			
#            print "\t==>Query URL is: " + url
#			
#            raw_html =  (download_page(url))
#            time.sleep(0.1)
#            new_items = _images_get_all_items(raw_html)
            
            new_items = google_search_keyword(keyword, CONFIGS[u'search_file_type'], cdr)

            for url in new_items:
                #real_url = get_real_url(url)
                real_url = download_image(url, class_save_dir, items)
                
                if real_url and real_url not in items:
                    items.append(real_url)
                    fp_all_urls.write(real_url + "\n")
                    fp_urls.write(real_url + "\n")

            fp_all_urls.flush()                    
            fp_urls.flush()

            print 'len(items)=', len(items)
            j = j + 1
        
        if cdr_enabled:
            fp_params.write('{}/{}/{}\n'.format( cd_min.year, cd_min.month, cd_min.day))
            cd_max = cd_min
            cd_min = get_new_date_by_delta_days(cd_max, -CONFIGS[u'search_cdr_days'])               
        else:
            fp_params.write('{}/{}/{}\n'.format( cd_max.year, cd_max.month, cd_max.day))
            cdr_enabled = True

        fp_params.flush()      
            
        print 'len(items)=', len(items)
        if len(items) >= loaded_urls_num + CONFIGS[u'num_downloads_for_each_class']:          
            break

    fp_params.close()
    fp_all_urls.close()
    fp_urls.close()

    #print ("Image Links = "+str(items))
    print ("Total New Image Links = " + str(len(items) - loaded_urls_num))
    print ("\n")
    i = i+1

    t1 = time.time()    #stop the timer
    total_time = t1-t0   #Calculating the total time required to crawl, find and download all the links of 60,000 images
    print("Total time taken: "+str(total_time)+" Seconds")

print("\n")
print("===All are downloaded")
#----End of the main program ----#
