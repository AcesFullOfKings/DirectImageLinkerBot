import praw
import time
import re
import shelve
import bot_data as d

app_id = d.app_id
refresh_token = d.refresh_token
app_secret = d.app_secret
app_uri = d.app_uri
user_agent = d.user_agent

del d

nonreplyusers = ["directimagelinkerbot", "imgurtranscriber", "automoderator", "apicontraption"] #make sure all in lower case
bannedRegex = re.compile("You've been banned from participating in /r/(.*)")
bannedRegex2 = re.compile("Your ban from /r/(.*) has changed")
data = shelve.open("data", "c") # is a dictionary
imgurRegex = re.compile("((((http|https)\:\/\/)|^|(?<= ))(www\.|i\.|m\.)?imgur\.com\/[a-zA-Z0-9]{6,7}?(?!(\.jpg|\.gif|\.gifv|\.png|\.jpeg|\.webm|,))(?=[^a-zA-Z0-9]|$| |\)))") #finds indirect imgur links only.
filetypes = [".png", ".gif", ".jpg", "gifv", "jpeg", "webm"]
url = ""
short_footer = "\n\n---\n[^Feedback](https://goo.gl/ChDHYn) ^| [^Already ^a ^direct ^link?](https://goo.gl/JVo094) ^| [^Why ^do ^I ^exist?](https://goo.gl/8WwAcJ) ^| [^Source](https://goo.gl/SBWyvz)"
footer = "\n\n---\n[^Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkBot&subject=Feedback&message=Don%27t%20forget%20to%20include%20a%20link%20to%20your/my%20comment) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)  ^| [^Source](https://github.com/Theonefoster/DirectImageLinkerBot/blob/master/DirectImageLinkerBot.py)"
short_footer = footer #keeps tripping the spam filter so they're both the same for now
no_shortlink_subs = {}

if "banned" not in data.keys():
    data["banned"] ={'books', 'SubredditDrama', 'Minecraft', 'history', 'japanlife', 'NASCAR', 'mylittleandysonic1', 'weareportadelaide', 'Firefighting', 'mylittlepony', 'DIY', 'funny', 'imagesofthe1990s', 'photoshopbattles', 'cycling', 'EatCheapAndHealthy', 'talesfromtechsupport', 'atheism', 'DaystromInstitute', 'gifs', 'GetMotivated', 'redditgetsdrawn', 'Denmark', 'pics', 'sunsetshimmer', 'aww', 'creepy', 'politics', 'TheSimpsons', 'EarthPorn', 'food', 'PercyJacksonRP', 'anime', 'gaming', 'Watches', 'Romania', 'PoliticalDiscussion', 'movies', 'Wishlist', 'battlestations', 'Futurology', 'weekendgunnit', 'OhCumOn', 'wtf', 'AskReddit', 'RedditMinusMods'}

#data["doneSubmissions"] = set() #reset done submissions
#data.sync()

#b = {'', 'books', 'SubredditDrama', 'Minecraft', 'history', 'japanlife', 'NASCAR', 'mylittleandysonic1', 'weareportadelaide', 'Firefighting', 'mylittlepony', 'DIY', 'funny', 'imagesofthe1990s', 'photoshopbattles', 'cycling', 'EatCheapAndHealthy', 'talesfromtechsupport', 'atheism', 'DaystromInstitute', 'gifs', 'GetMotivated', 'redditgetsdrawn', 'Denmark', 'pics', 'sunsetshimmer', 'aww', 'creepy', 'politics', 'TheSimpsons', 'EarthPorn', 'food', 'PercyJacksonRP', 'anime', 'gaming', 'Watches', 'Romania', 'PoliticalDiscussion', 'movies', 'Wishlist', 'battlestations', 'Futurology', 'weekendgunnit', 'OhCumOn', 'wtf', 'AskReddit', 'RedditMinusMods'}
#data["banned"] = b
#data.sync()
#input("success")

print("Bot is banned from: " + str(data["banned"]))

def login():
    print("Logging in..")
    r = praw.Reddit(user_agent, disable_update_check=True)
    r.set_oauth_app_info(app_id, app_secret, app_uri)
    r.refresh_access_information(refresh_token)
    print("Logged in as " + r.user.name)
    return r

r = login()
data["loops"] = 31 #so that it checks mail on launch.
#data['doneSubmissions'] = set() #reset doneSubmissions
data.sync()

def mail():
    data["loops"] = data["loops"] + 1
    if data["loops"] > 5:
        data["loops"] = 0
        msgs = list(r.get_unread(unset_has_mail=False, update_user=False))
        for msg in msgs:
            if msg.author is not None and msg.author.name == "AutoModerator":
                msg.mark_as_read()
            else:
                match = re.findall(bannedRegex, msg.subject)
                if not match:
                    match = re.findall(bannedRegex2, msg.subject)
                if match:
                    if match[0] not in data['banned'] and msg.author is None: #subreddit ban messages have no author
                        sublist = data['banned']
                        sublist.add(str(match[0]))
                        data['banned'] = sublist
                        data.sync()
                        msg.reply("/r/" + str(match[0]) + " has been added to my ignore list. I won't bother you again.")
                        msg.mark_as_read()
                        print ("Added /r/" +  str(match[0]) + " to ignore list.")

def submissions():
    submissions = list(r.get_new(limit=100)) #4 per second
    for submission in submissions:
        if submission.id not in data["doneSubmissions"]:

            donelist = data["doneSubmissions"]
            donelist.add(submission.id)
            data["doneSubmissions"] = donelist
            data.sync()

            if (submission.author.name.lower() not in nonreplyusers) and (submission.subreddit.display_name not in data['banned']):
                if (submission.domain == "imgur.com") and not ("/a/" in submission.url) and not ("gallery" in submission.url) and (not submission.url[-4:] in filetypes):               
                    if not submission.url.startswith("http"):
                        url = "https://" + submission.url
                    else:
                        if submission.url.startswith("http:/"):
                            url = "https" + submission.url[4:]
                        else:
                            url = submission.url
                    try:
                        if submission.subreddit.display_name.lower() in no_shortlink_subs:
                            submission.add_comment("[Here is a direct link to the image OP submitted for the benefit of mobile users](" + url + ".jpg)" + footer)
                        else:
                            submission.add_comment("[Here is a direct link to the image OP submitted for the benefit of mobile users](" + url + ".jpg)" + short_footer)
                    except Exception as e:
                        print ("Error trying to post to /r/" + submission.subreddit.display_name)
                        print (str(e))
                    else:
                        print ("Submission reply sent to " + submission.author.name + "!")

def comments():
    subreddit = r.get_subreddit("all")
    comments = list(subreddit.get_comments(limit=100, fetch=True)) #around 22 comments come in per second at peak time according to a single sample and my very reliable rough estimate
    for comment in comments:
        if comment.id not in data["doneSubmissions"]:

            donelist = data["doneSubmissions"]
            donelist.add(comment.id)
            data["doneSubmissions"] = donelist
            data.sync()

            if (comment.author.name.lower() not in nonreplyusers) and (comment.subreddit.display_name not in data['banned']):
                
                commentText = comment.body
                match = list(re.findall(imgurRegex, commentText))
                if (len(match) > 0):
                        
                    if len(match) == 1: #one link in comment
                        if not match[0][0].startswith("http"):
                            url = "https://" + match[0][0]
                        else:
                            if match[0][0].startswith("http:/"):
                                url = "https" + match[0][0][4:]
                            else:
                                url = match[0][0]

                        if "gallery" not in url and "/a/" not in url: 
                            try:
                                if comment.subreddit.display_name.lower() in no_shortlink_subs:
                                    comment.reply("[Here is a direct link to your image for the benefit of mobile users](" + url + ".jpg)" + footer)
                                else:
                                    comment.reply("[Here is a direct link to your image for the benefit of mobile users](" + url + ".jpg)" + short_footer)
                            except Exception as e:
                                print ("Error trying to post comment reply in /r/" + comment.subreddit.display_name)
                                print (str(e))
                            else:
                                print ("Comment reply sent to " + comment.author.name + "!")
                    elif len(match) < 10:
                        reply = ("Here are direct links to those images for the benefit of mobile users: \n\n")
                        for submatch in match:
                            if "gallery" not in submatch[0] and "/a/" not in submatch[0]: #what if gallery is in every match? It outputs an empty comment. TODO
                                if not submatch[0].startswith("http"):
                                    url = "https://" + submatch[0]
                                else:
                                    if submatch[0].startswith("http:/"):
                                        url = "https" + submatch[0][4:]
                                    else:
                                        url = submatch[0]   
                                    
                                reply = reply + (url + ".jpg\n\n")
                        if comment.subreddit.display_name.lower() in no_shortlink_subs:
                            reply += footer
                        else:
                            reply += short_footer
                        
                        if len(reply) > (len(footer) + 100): #73 is len() of header ^ so this should cover there being at least 2 links
                            comment.reply(reply)
                            print ("Comment reply sent to " + comment.author.name + "!")

while True:
    try:
        r.handler.clear_cache()
        mail()
        comments() 
        submissions()
        data.sync()
    except praw.errors.RateLimitExceeded as e:
        print ("Rate limit exceeded! - " + str(e))
    except praw.errors.HTTPException as e:
        print ("HTTP Error - " + str(e._raw.status_code) + e._raw.reason)
        pass
    except Exception as e:
        print (str(e))
        try:
            r = login()
        except Exception as e:
            print (str(e))
            print ("Login Error. Sleeping..") # Mostly for when reddit is returning 503 on most requests.
            time.sleep(30)
