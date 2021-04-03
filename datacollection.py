from bs4 import BeautifulSoup
import numpy as np
import sklearn
import pandas as pd
from urllib.request import urlopen
from selenium import webdriver
import os
from unidecode import unidecode
import time

#this class will use BeautifulSoup to parse anime data from
#myanimelist.net into a file, will probably choose approximately the
#2000 highest rated titles
class AnimeCollection:
    def __init__(self):
        self.pageurl = "https://myanimelist.net/topanime.php"
        self.number = 0
        self.pages = 0
        self.failedVals = []
        self.frame = pd.DataFrame(index=np.arange(1,2001),columns=['Name','Rating','Popularity','Studio','Type','Date','Genres'])

    def isAscii(self,s):
        return all(ord(c) < 128 for c in s)

    #uses BeautifulSoup to parse html of pages and find the desired info ie. Name, Rating, Popularity, Studio, Type, Date, Genres
    def getData(self):
        while(self.number < 2000):
            if self.pages > 0:
                url = self.pageurl + '?limit=' + str(50*self.pages)
            else:
                url = self.pageurl
            self.pages += 1
            html = urlopen(url)
            bsObj = BeautifulSoup(html)
            #for i in range(20):
            threadlist = bsObj.findAll("a", class_="fs14") #selects anime pages
            print(threadlist)
            for thread in threadlist:
                newpage = thread.attrs['href']
                if not self.isAscii(newpage):
                    self.failedVals.append(self.number)
                    self.number += 1
                    continue
                newhtml = urlopen(newpage)
                newObj = BeautifulSoup(newhtml)
                name = newObj.find("h1",class_="h1").getText()
                rating = newObj.find("div",class_="score").getText()
                popularity = newObj.find("span",class_="members").find("strong").getText()
                print(popularity)
                studiospan = newObj.find("span",text="Studios:")
                studioparent = studiospan.parent
                studio = studioparent.find("a").getText()
                print(studio)
                typespan = newObj.find("span",text="Type:")
                typeparent = typespan.parent
                typeval = typeparent.getText().split()[1]
                datespan = newObj.find("span",text="Aired:")
                dateparent = datespan.parent
                dateval = dateparent.getText().strip()
                datelist = dateval.split()
                if len(datelist) > 3:
                    date = datelist[3]
                else:
                    date = datelist[len(datelist)-1]
                print(date)
                genrespan = newObj.find("span",text="Genres:")
                genreparent = genrespan.parent
                genrelist = genreparent.findAll("a")
                genres = ""
                for val in genrelist:
                    genres = genres + val.getText() + '/'
                genres = genres[0:len(genres)-1]
                print(genres)
                self.frame.iloc[self.number]['Name'] = name
                self.frame.iloc[self.number]['Rating'] = float(rating)
                self.frame.iloc[self.number]['Popularity'] = float(popularity.replace(',',''))
                self.frame.iloc[self.number]['Studio'] = studio
                self.frame.iloc[self.number]['Type'] = typeval
                self.frame.iloc[self.number]['Date'] = date
                self.frame.iloc[self.number]['Genres'] = genres

                self.frame.to_csv('animes.csv')
                self.number += 1

class dataManipulation:
    def __init__(self):
        self.users = pd.read_table('users.txt',sep='\n',header=None,squeeze=True)
        self.animes = pd.read_csv('animes2.csv')

    def getEra(self,val):
        if int(val) < 1995:
            return 'Old'
        if int(val) > 1994 and int(val) < 2007:
            return 'Classic'
        if int(val) > 2006:
            return 'New'
        
    def adjustAnimes(self):
        self.animes = self.animes.dropna(axis=0,how='any')
        self.animes = self.animes.where((self.animes['Type'] == 'TV') | (self.animes['Type'] == 'Movie'))
        self.animes = self.animes.dropna(axis=0,how='any')
        self.animes['Era'] = self.animes['Date'].apply(lambda x: self.getEra(x))
        self.animes = self.animes.drop('Date',axis=1)
        self.animes = self.animes.drop('Unnamed: 0',axis=1)
        print(self.animes.columns)
        self.animes.to_csv('animes3.csv')

    def adjustGenres(self):
        animes = pd.read_csv('animes3.csv')
        genres = []
        for i, val in animes['Genres'].iteritems():
            genrelist = val.split('/')
            genres = genres + genrelist
        for genre in set(genres):
            animes[genre] = 0
        for i, val in pd.Series(animes['Genres']).iteritems():
            genrelist = val.split('/')
            print(i)
            for genreval in genrelist:
                #print(animes.iloc[i])
                animes.set_value(i,genreval,1)
                #print(animes.iloc[i])
        animes = animes.drop('Unnamed: 0',axis=1)
        animes = animes.drop('Genres',axis=1)
        animes.to_csv('newanimes.csv')
        print(set(genres))

class userCollection:
    def __init__(self):
        self.pageurl = "https://myanimelist.net/users.php"

    def remove_non_ascii(self,s):
        return s.encode('ascii','ignore').decode()

    #call this method 55 times to get 1100 users, and store them in a text file
    def getUserUrls(self):
        html = urlopen(self.pageurl)
        bsObj = BeautifulSoup(html)
        userList = bsObj.findAll("td",class_="borderClass")
        userfile = open('testusers.txt','a')
        for user in userList:
            val = user.find("a").getText()
            val = val + '\n'
            print(val)
            userfile.write(val)
            #useranimes = "https://myanimelist.net/animelist/" + val + "?status=2"

    def uniqueUsers(self):
        userdata = pd.read_table('testusers.txt',sep='\n',header=None,squeeze=True)
        unique = pd.Series(userdata.unique())
        unique.to_csv('uniquetestusers.txt',header=False,index=False,sep='\n')

    def getUserData(self):
        #userdata = pd.read_table('users.txt',sep='\n',header=None,squeeze=True)
        userdata = pd.read_table('uniquetestusers.txt',sep='\n',header=None,squeeze=True)
        print(userdata)
        for i,user in userdata.iteritems():
            i = int(i)
            if i < 459:
                continue
            self.getTestUser(user,i)

    #gets all animes in 'completed' list for a user
    def getTestUser(self,username,number):
        #driver = webdriver.Chrome()
        driver = webdriver.Chrome("C:\\chromedriver.exe")
        url = "https://myanimelist.net/animelist/" + username + "?status=2"
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") #####
        time.sleep(2)
        html = driver.page_source
        bsObj = BeautifulSoup(html,"lxml")
        badresult = bsObj.findAll(class_="badresult")
        if len(badresult) > 0:
            driver.close()
            print("Blocked")
            return
        animes = bsObj.findAll("a",class_="animetitle")
        print(len(animes))
        if len(animes) > 0:
            if len(animes[0].getText()) > 0:
                user = pd.DataFrame(columns=['Name','Score'])
                scores = bsObj.findAll("td",class_=["td1", "td2"],width="45")
                if len(scores) == 0:
                    print ('No Scores')
                    driver.close()
                    return
                for i in range(len(animes)):
                    name = animes[i].getText().strip('\n')
                    score = scores[i].getText().strip()
                    namescore = {'Name':name,'Score':score}
                    user = user.append(namescore,ignore_index=True)
        else:
            #print('lel')
            animes = bsObj.findAll("tr",class_="list-table-data")
            user = pd.DataFrame(columns=['Name','Score'])
        #print(animes)
            print(len(animes))
            for anime in animes:
                td = anime.findAll('td',class_=['clearfix'])
                name= ""
                for val in td:
                    val = val.find('a',class_=['link','sort'])
                    name = name + val.getText()
                    #score = anime.find('td',class_='score').getText().strip()
                    score = anime.find('td',class_='score')
                    if score is None:
                        print ('No Scores')
                        driver.close()
                        return
                    score = score.getText().strip()
                    namescore = {'Name':name,'Score':score}
                    user = user.append(namescore,ignore_index=True)
        print(user)
        driver.close()
        filestring = 'testUsers/User_' + str(number) + '.csv'
        user.to_csv(filestring)
            #animetext = anime.getText().split()
            #for i in range(len(animetext)):

    def is_number(self,s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    #removes animes that haven't been scored or aren't in the database
    def adjustUser(self,namefile):
        animes = pd.read_csv('newanimes3.csv')
        filepath = 'UsersV2/' + namefile
        #print(filepath)
        user = pd.read_csv(filepath,encoding='ISO-8859-1')
        user['Score'] = user['Score'].astype(str)
        user = user.where(lambda x: x['Score'] != '-')
        
        user = user[user.Score.apply(lambda x: self.is_number(x))]
        if 'Unnamed: 0' in user.columns:
            user = user.drop('Unnamed: 0',axis=1)
        if 'Unnamed: 0.1' in user.columns:
            user = user.drop('Unnamed: 0.1',axis=1)
        user = user.dropna(axis=0,how='any')
        try:
            user['Score'] = user['Score'].astype(int)
        except:
            return
        #user = user.dropna(subset=['Score'],how='any')
        rowlist = []
        #print(animes['Name'])
        for i,val in user.iterrows():
            #print(val['Name'])
            #y = self.remove_non_ascii(val['Name'])
            y = val['Name']
##            if y == 'Mahou Shoujo Madoka?Magica':
##                y = 'Mahou Shoujo Madoka Magica'
##            if y == 'Space?Dandy':
##                y = 'Space Dandy'
##            if y == 'Yuu?Yuu?Hakusho':
##                y = 'Yuu Yuu Hakusho'
            y = self.missingAnimes(y)
            if y not in animes.Name.values:
                rowlist.append(y)
        #print(namefile)
        #print(user)
        #print(rowlist)
        #for i, row in user.iterrows():
        if user.empty:
            return
        user = user[~user['Name'].isin(rowlist)]
        user = user.dropna(axis=0,how='any')
        for i,val in user.iterrows():
            user['Name'] = user['Name'].apply(lambda x: self.missingAnimes(x))
        if len(user.index) < 15:
            return
        newfilepath = 'newUsersV2/' + namefile
        user.to_csv(newfilepath)
        
        print(user)

    #account for a few non-ASCII anime names
    def missingAnimes(self,y):
        if y == 'Mahou Shoujo Madoka?Magica':
            return 'Mahou Shoujo Madoka Magica'
        elif y == 'Space?Dandy':
            return 'Space Dandy'
        elif y == 'Yuu?Yuu?Hakusho':
            return 'Yuu Yuu Hakusho'
        elif y == 'Lovely?Complex':
            return 'Lovely Complex'
        elif y == 'Lucky?Star':
            return 'Lucky Star'
        else:
            return y
        
    #converts each anime in a user's list to ASCII
    def convertUsers(self):
        for fn in os.listdir('UsersV2/'):
            filepath = 'UsersV2/' + fn
            user = pd.read_csv(filepath,encoding='ISO-8859-1')
            for i,val in user.iterrows():
                val['Name'] = self.remove_non_ascii(val['Name'])
            user.to_csv(filepath)
        
    def cleanUsers(self):
        for fn in os.listdir('UsersV2/'):
            print(fn)
            #if fn == 'User_687.csv':
                #continue
            self.adjustUser(fn)

    #calculates the z-score for each user's anime ratings so that data is less biased
    def zScore(self):
        for fn in os.listdir('newUsersV2/'):
            #if str(fn) == 'User_762.csv':
                #continue
            x = pd.read_csv('newUsersV2/' + fn)
            print(fn)
            if ('Unnamed: 0.1' in x.columns):
                x = x.drop('Unnamed: 0.1',axis=1)
            sd = x['Score'].std()
            if sd == 0:
                continue
            mean = x['Score'].mean()
            x['ZScore'] = x['Score'].apply(lambda x: (x - mean)/sd)
            x.to_csv('zUsersV2/' + fn)
        
class AnimeSeries:
    #def __init__(self):

    def createGraph(self):
        graphlist = []
        filename = "AnimeSeriesData.txt"
        with open(filename) as f:
            for line in f:
                animedict = {}
                splitline = line.split(' -> ')
                #print(splitline)
                for i in range(len(splitline)):
                    splitline[i] = splitline[i].strip('\n')
                for i in range(len(splitline) - 1):
                    animedict[splitline[i+1]] = splitline[i]
                graphlist.append(animedict)
        #print(graphlist)
        return graphlist

    #search anime series graph to see whether there are prequels to the suggested
    #anime that haven't been watched, if there are, return the earliest prequel that hasn't been watched
    def searchGraph(self,graph,anime,watched):
        done = []
        for i in range(len(graph)):
            done.append(False)
        
        while False in done:
            for j in range(len(graph)):
                animedict = graph[j]
                if anime in animedict.keys():
                    tempanime = animedict[anime]
                    if tempanime not in watched:
                        anime = tempanime
                        for k in range(len(done)):
                            done[k] = False
                    else:
                        done[j] = True
                else:
                    done[j] = True
        return anime

    #checks whether there are 2 animes from the same series in
    #a list
    def checkSeries(self,graph,anime1,anime2):
        for j in range(len(graph)):
            tempanime = anime1
            while (tempanime in graph[j].keys()):
                tempanime = graph[j][tempanime]
                if anime2 == tempanime:
                    return True
        return False
                    
        
        
    
            
        
    

def main():
   #x = AnimeCollection()
   #y = x.getData()
   #x = dataManipulation()
   #y = x.adjustAnimes()
   #z = x.adjustGenres()
    x = userCollection()
    #for i in range(25):
     #   time.sleep(10)
      #  x.getUserUrls()
    #x.uniqueUsers()
    #x.getUserData()
    #y = x.convertUsers()
    #z = x.cleanUsers()
    y = x.zScore()
    #z = x.cleanUsers()
    #a = AnimeSeries()
    #g = a.createGraph()
    #b = a.searchGraph(g,"Monogatari Series: Second Season",['Bakemonogatari'])
    #print(b)

#main()
