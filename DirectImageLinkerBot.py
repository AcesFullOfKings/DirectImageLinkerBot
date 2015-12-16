import praw
import time
import re
import shelve

appID = 'Removed' #This information is removed as it should not be in the public domain. The bot won't work without it, but you can replace it with your own private data
refreshToken = 'Removed'
secret = 'Removed'
URI = 'Removed'
userAgent = 'Removed'

nonreplyusers = ["directimagelinkerbot", "imgurtranscriber", "automoderator", "apicontraption", "masterjts", "nightmirrormoon"] #make sure all in lower case
bannedRegex = re.compile("you've been banned from /r/(.*)")
bannedRegex2 = re.compile("Your ban from /r/(.*) has changed")
data = shelve.open('data4', 'c', writeback=True) # is a dictionary
imgurRegex = re.compile("(((http|https)\:\/\/)?(www\.|i\.|m\.)?imgur\.com\/[a-zA-Z0-9]{6,7}?(?!(\.jpg|\.gif|\.gifv|\.png|\.jpeg))(?=[^a-zA-Z0-9]|$| ))") #finds indirect imgur links only.
filetypes = [".png", ".gif", ".jpg", "gifv", "jpeg"]
url = ""

data["banned"] = ['funny','aww','gaming','pics','pokemontrades','BreedingDittos','AskReddit','newzealand','redditgetsdrawn','BloodGulchRP','Jokes','nba','anime','mylittlepony','motorcycles',
'xboxone','army','photoshopbattles','Fallout','reactiongifs','DealsReddit','CollegeBasketball','MechanicalKeyboards','MarioMaker','Watches','StardustCrusaders','Torontobluejays','Denmark',
'HighQualityGifs','Minecraft','depression','guns','malefashionadvice','SoapboxBanhammer','TheLeftovers','Cardinals','AnimeFigures','politics','AskHistorians','Fitness','WTF','Random_Acts_Of_Amazon',
'StarlightGlimmer','sunsetshimmer','EquestriaGirls','eagles','newzealandfood','Glocks','Android','MMA','vancouver','QuotesPorn','MilitaryPorn','MapPorn','iphone','FoodPorn','drawing',
'EarthPorn','carporn','Cameras','bestof','awDiet','bucktick','CSURams','woahdude','cats','Dualsport','unitedkingdom','blackops3','visualnovels','supermoto','MillerPlanetside','thenetherlands',
'hardwareswap','swtor','4chan','funkopop','Parenting','CODZombies','PoliticalDiscussion','ImagesOfThe1800s','history','GetMotivated','LifeProTips','biology','photoshop','Vive','kancolle','books',
'ForgottenWeapons','ArtistLounge','PokemonShuffle','wheredidthesodago','Military','lowlevelaware','todayilearned','xkcd','AutoModerator','fatlogic','Trucks','Wet_Shavers','ClashOfClans','Wishlist',
'Horses','beer','DestinyTheGame','pcgaming','androidgaming','youdontsurf','gentlemanboners','fantasyfootball','TV_ja','electricians','RWBYGore','TrollXChromosomes','StarWars','rwbyRP','Buttcoin',
'SketchDaily','AskWomen','ShitRedditSays','weekendgunnit','science','tattoos','GameDeals','AskCulinary','whatisthisthing','TwoXChromosomes','Romania','de','torrents','gifs','SubredditDrama','Unexpected',
'InternetIsBeautiful','rage','nottheonion','cringepics','memes','tifu','Makemeagif','camping','BlackPeopleTwitter','Futurology','AnimalsBeingBros','holdmybeer','MakeupAddiction','wwesupercard',
'breakingmom','DBZDokkanBattle','GODZILLA','dbz','Philippines','Harley','wweimmortals','FutureFight','talesfromtechsupport','nrlrll3','RWBY','Advice','creepyPMs','wsgy','dailysketch','AlienBlue',
'VoteTrumpYouLoser','REBL','2007scape','Tribes','evangelion','The_Donald','Diablo','PowerMetal','ynab','DuelingCorner','ReDWMA','dogs','goodyearwelt','AppHookup','Likha','vexillology','Portland',
'SandersForPresident','CompetitiveHS','millionairemakers','australia','dataisbeautiful','actuallesbians','OutOfTheLoop','Excision','hearthstone','CoCBot','chicagobulls','ShinJimin','sanfrancisco',
'listentothis','stuckRPG','spacex','interestingasfuck','AskMen','CasualConversation','ladybonersgw','JUSTNOMIL','losangeleskings','RedditDads','Conservative','TheRedLion','Damnthatsinteresting',
'FemBoys','business','CherokeeXJ', 'PuzzleAndDragons','Calligraphy','DickButt','blunderyears','humor', 'food', 'tifu', 'Showerthoughts']

def login():
    print("Logging in..")
    r = praw.Reddit(userAgent)
    r.set_oauth_app_info(appID, secret, URI)
    r.refresh_access_information(refreshToken)
    print("Logged in as " + r.user.name)
    return r

r = login()
data["loops"] = 31 #so that it checks mail on launch.
#print data["banned"]
data['doneSubmissions'] = []
data['spam'] = []
data.sync()

while True:

    try:

############# Shelve Management ############

        if len(data["doneSubmissions"]) > 10000: #larger number means fewer disk accesses but slightly slower key access time
            old_ds = data["doneSubmissions"]
            new_ds = old_ds[len(old_ds)-2001:]
            data["doneSubmissions"] = new_ds
            data.sync()

############# Mail ############

        data["loops"] = data["loops"] + 1
        if data["loops"] > 30:
            data["loops"] = 0
            msgs = list(r.get_unread(unset_has_mail=False, update_user=False))
            for msg in msgs:
                if msg.author is not None and msg.author.name == "AutoModerator":
                    msg.mark_as_read()
                #elif ("thanks" in msg.body.lower() or "thank you" in msg.body.lower()) and len(msg.body) < 39:
                #    msg.reply("You're welcome, human. Don't forget to direct link!")
                #    msg.mark_as_read()
                #    print "Replied to inbox message with thank you"
                else:
                    match = re.findall(bannedRegex, msg.subject)
                    if not match:
                        match = re.findall(bannedRegex2, msg.subject)
                    if match:
                        if match[0] not in data['banned']:
                            sublist = []
                            sublist =  data['banned']
                            sublist.append(str(match[0]))
                            data['banned'] = sublist
                            data.sync()
                            msg.reply("/r/" + str(match[0]) + " has been added to my ignore list. I won't bother you again.")
                            msg.mark_as_read()
                            print "Added /r/" +  str(match[0]) + " to ignore list."

############# SUBMISSIONS ############  

        submissions = list(r.get_new(limit=100)) #4 per second
        for submission in submissions:
            if submission.id not in data["doneSubmissions"]:

                banlist = data["doneSubmissions"]
                banlist.append(submission.id)
                data["doneSubmissions"] = banlist

                if (submission.author.name.lower() not in nonreplyusers) and (submission.subreddit.display_name not in data['banned']):
                    if (submission.domain == "imgur.com") and not ("/a/" in submission.url) and not ("gallery" in submission.url) and (not submission.url[-4:] in filetypes):               
                        if not submission.url.startswith("http"):
                            url = "https://" + submission.url
                        else:
                            url = submission.url
                        try:
                            submission.add_comment("[Here is a direct link to the image OP submitted for the benefit of mobile users](" + url + """.jpg)\n\n---\n[^Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot&subject=Feedback&message=Don%27t%20forget%20to%20include%20a%20link%20to%20your/my%20comment) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
                        except Exception,e:
                            print "Error trying to post to /r/" + submission.subreddit.display_name
                            print str(e)
                        else:
                            print "Submission reply sent to " + submission.author.name + "!"

############# COMMENTS ##############

        subreddit = r.get_subreddit('all')
        comments = list(subreddit.get_comments(limit=100, fetch=True)) #around 22 comments come in per second at peak time according to a single sample and my very reliable rough estimate
        for comment in comments:
            if comment.id not in data["doneSubmissions"]:

                doneList = data["doneSubmissions"]
                doneList.append(comment.id)
                data["doneSubmissions"] = doneList

                if (comment.author.name.lower() not in nonreplyusers) and (comment.subreddit.display_name not in data['banned']):
                
                    commentText = comment.body
                    match = list(re.findall(imgurRegex, commentText))
                    if (len(match) > 0):
                        
                        if len(match) == 1: #one link in comment
                            if not match[0][0].startswith("http"):
                                url = "https://" + str(match[0][0])
                                print "Added 'https://' to comment at ID " + comment.id
                            else:
                                url = match[0][0]

                            if "gallery" not in url and "/a/" not in url:
                                try:
                                    comment.reply("[Here is a direct link to your image for the benefit of mobile users](" + url + """.jpg)\n\n---\n\n^[Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot&subject=Feedback&message=Don%27t%20forget%20to%20include%20a%20link%20to%20your/my%20comment) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
                                except Exception,e:
                                    print "Error trying to post comment reply in /r/" + submission.subreddit.display_name
                                    print str(e)
                                else:
                                    print "Comment reply sent to    " + comment.author.name + "!"
                        elif len(match) < 10:
                            reply = ("Here are direct links to those images for the benefit of mobile users: \n\n")
                            for submatch in match:
                                if "gallery" not in submatch[0] and "/a/" not in submatch[0]:
                                    if not submatch[0].startswith("http"):
                                        url = "https://" + str(submatch[0])
                                    else:
                                        url = submatch[0]
                                    reply = reply + (url + ".jpg\n\n")
                            reply = reply + "---\n\n[^Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)"
                        
                            if len(reply) > 340:
                                comment.reply(reply)
                                print "Comment reply sent to    " + comment.author.name + "!"

                        else: #many links in a comment usually indicate spam
                            links = []
                            for submatch in match:
                                if submatch[0] not in links:
                                    links.append(submatch[0])#
                    
                            if len(links) < 3: #if number of link is >= 10 and number of unique URLs is <3 then message admins
                                
                                data["spam"].append(comment.permalink)

                                if len(data["spam"]) > 10:
                                    message = "This message was automatically submitted because the comments below contain a large number of links, but few unique images. This usually means they're spammy messages. If you'd like not to receive these messages, please reply letting me know - /u/theonefoster checks this bot's PM's daily.\n\n Links to probably-spammy comments: \n\n"

                                    for item in data["spam"]:
                                        message = message + item + "/n/n"

                                    r.send_message("/r/spam", "Automatic comment report", message)

                                    data["spam"] = []
                                         
        data.sync()
        r.handler.clear_cache()
    except praw.errors.RateLimitExceeded,e:
        print "Rate limit exceeded! - " + str(e)
    except praw.errors.HTTPException,e:
        print "HTTP Error - " + str(e._raw.status_code) + e._raw.reason
        pass
    except Exception,e:
        print str(e)
        try:
            r = login()
        except Exception,e:
            print str(e)
            print "Sleeping.."
            time.sleep(30)
