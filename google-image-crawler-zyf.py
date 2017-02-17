#Searching and Downloading Google Images/Image Links

#Import Libraries

import time       #Importing the time library to check the time of code execution
import sys    #Importing the System Library

import os
import os.path as osp

import fnmatch

#import json

#import urllib2
from urllib import urlencode

from urllib2 import Request,urlopen
from urllib2 import URLError, HTTPError

import datetime

import hashlib

########### Edit From Here ###########
# How many images you want to download. Google will only return 100 images at most for one search
target_items_for_each_keyword = 200

# image type to search
#file_type = ['jpg', 'bmp', 'png']
file_type = 'jpg'
#file_type = 'bmp'
#file_type = 'png'

# Because google only returns at most 100 results for each search query,
# we must send many search queries to get more than 100 results.
# We need to set cdr (date range, in the form of "tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}") to tell google
# we want to search images in some date range (start_date, end_date),
# so as to get different results for each search query.
# cdr_interval_days is the days between cd_min and cd_max.
cdr_interval_days = 60

#This list is used to search keywords. You can edit this list to search for google images of your choice. You can simply add and remove elements of the list.
search_keyword = ['Cat', 'dog']
search_keywords_dicts = {'animal':['cat', 'dog']}
#search_keywords_dicts = {'TibetanFlags':['Tibetan Flag', 'Tibetan National Flag', u'雪山狮子旗'],
#                         'IslamicFlags':['east turkestan flag', 'Islamic flag', 'muslim flag', 'Star And Crescent Flag', 'Flag with star and cresent', 'star and moon flag', 'flag with star and moon flag'],
#                         'Guns':['gun', 'rifle', u'枪'],
#                         'Knives':['knife', 'knives', 'dagger', 'daggers'],
#                         'MuslimVeils':['Muslim veils', 'Islamic veils', 'black hijab', 'Islamic Women', 'Islamic woman']
#                         }
#                         

#This list is used to further add suffix to your search term. Each element of the list will help you download 100 images. First element is blank which denotes that no suffix is added to the search keyword of the above list. You can edit the list by adding/deleting elements from it.So if the first element of the search_keyword is 'Australia' and the second element of keywords is 'high resolution', then it will search for 'Australia High Resolution'
#aux_keywords = [' high resolution']

save_dir = './downloads' + '/'

output_urls_file_prefix = 'google_download_urls_'

if not osp.exists(save_dir):
    os.mkdir(save_dir)

#output_urls_file_prefix = save_dir + output_urls_file_prefix  
########### End of Editing ###########

#Load downloaded urls
def load_url_files(_dir, file_name_prefix):
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
    
#Downloading entire Web Document (Raw Page Content)
def download_page(url):
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
def _images_get_next_item(s):
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
def _images_get_all_items(page):
    items = []
    while True:
        item, end_content = _images_get_next_item(page)
        if item == "no_links":
            break
        else:
            items.append(item)      #Append all the links in the list named 'Links'
            time.sleep(0.1)        #Timer could be used to slow down the request for image downloads
            page = page[end_content:]
    return items

#Get real url of a input url    
def _get_real_url(url):
    real_url = None
    response = None
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req)
        
        real_url = response.geturl()
    except IOError as e:   #If there is any IOError
        print("IOError on url "+str(url))
        print e
    except HTTPError as e:  #If there is any HTTPError
        print("HTTPError on url "+str(url))
        print e
    except URLError as e:
        print("URLError on url "+str(url))
        print e
    finally:
        if response:
            response.close()    
        
    return real_url

def download_image(url, save_dir):
    real_url = None
    response = None
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"})
        response = urlopen(req)
        
        real_url = response.geturl()
        
        print 'Real_url is: ' + str(real_url)
        #img_name = str(k) + '_' + real_url.rsplit('/')[-1]
        img_name = hashlib.md5(real_url).hexdigest()
        save_image_name = save_dir + '/' + img_name + '.' + file_type
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
    finally:
        if response:
            response.close()
        
    return real_url
    
    
############## Main Program ############
t0 = time.time()   #start the timer

#Download Image Links
i= 0

cur_date = get_current_date()
print "Today is: " + cur_date.strftime("%Y/%m/%d")

time_str = get_gmttime_string()

for class_name,search_keywords in search_keywords_dicts.iteritems():
    print "Class no.: " + str(i+1) + " -->" + " Class name = " + str(class_name)
   
    class_urls_file_prefix = output_urls_file_prefix + str(class_name).strip()
    
    items = load_url_files(save_dir, class_urls_file_prefix)    
    loaded_urls_num = len(items)
    print 'Loaded URLs in total is: ', loaded_urls_num

    # load pre-saved download parameters, actually cd_min for date range
    cd_max = cur_date

    params_file = osp.join(save_dir, class_urls_file_prefix + '_params.txt')
    params_list = []
    fp_params = open(params_file, 'a+')
    for line in fp_params:
        line = line.strip()
        if line!='':
            params_list.append(line)
            
    if len(params_list)>0:
        splits = params_list[-1].split('/')
        if len(splits)==3:
            cd_max = datetime.date(int(splits[0]), int(splits[1]), int(splits[2]))
    
    cd_min = get_new_date_by_delta_days(cd_max, -cdr_interval_days)   
    print 'cd_max: ', cd_max
    print 'cd_min: ', cd_min
            
    print ("Crawling Images...")
    
    class_save_dir = osp.join(save_dir, class_urls_file_prefix + '_' + time_str)
    if not osp.exists(class_save_dir):
        os.mkdir(class_save_dir)
        
    output_urls_file = osp.join(save_dir, class_urls_file_prefix + '_' + time_str + '.txt')
    fp_urls = open(output_urls_file, 'a+')
    
#    if osp.exists(output_urls_file):
#        fp_urls = open(output_urls_file, 'a+')        #Open the text file called database.txt
#        for line in fp_urls:
#            items.append(line.strip())
#    else:
#        fp_urls = open(output_urls_file, 'w+')        #Open the text file called database.txt
#    
    cdr_enabled = 0
    
    while True:        
        if cdr_enabled:
            tbs = 'cdr:1,cd_min:{},cd_max:{}'.format(cd_min.strftime('%m/%d/%Y'), cd_max.strftime('%m/%d/%Y'))
            print "==>Search for Images between " + cd_min.strftime("%Y/%m/%d") + \
                    ' and ' + cd_max.strftime("%Y/%m/%d")
        else:
            tbs = ''
            print "==>Search for Images in any time"

        j = 0
                
        # Google only return 100 images at most for one search. So we may need to try many times
        while j<len(search_keywords):
            print "\t==>Class name=" + str(class_name) + ', search keywords=' + search_keywords[j]
            keyword = search_keywords[j]#.replace(' ','%20')
            
            query = dict(q = keyword, 
                         tbm = 'isch',
                         tbs=tbs+',ift:'+file_type)
            
            #url = 'https://www.google.com/search?q=' + keyword + '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&tbm=isch&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'
            #url = 'https://www.google.com/search?as_oq=' + keyword + '&as_st=y&tbm=isch&safe=images&tbs=ift:jpg'
            url = 'https://www.google.com/search?'+urlencode(query)
            raw_html =  (download_page(url))
            time.sleep(0.1)
            new_items = _images_get_all_items(raw_html)
            
            for url in new_items:
                #real_url = _get_real_url(url)
                real_url = download_image(url, class_save_dir)
                if real_url and real_url not in items:
                    items.append(real_url)
                    fp_urls.write(real_url + "\n")
                    
            fp_urls.flush()

            print 'len(items)=', len(items)
            j = j + 1
        
        if cdr_enabled:
            fp_params.write('%d/%d/%d', cd_min.year, cd_min.month, cd_min.day)
            cd_max = cd_min
            cd_min = get_new_date_by_delta_days(cd_max, -cdr_interval_days)               
        else:
            cdr_enabled = 1
            
        print 'len(items)=', len(items)
        if len(items) >= loaded_urls_num + target_items_for_each_keyword:          
            break

    fp_params.close()
    fp_urls.close()                            #Close the file
        
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
