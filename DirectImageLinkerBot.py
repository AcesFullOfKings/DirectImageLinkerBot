import praw
import time
import re
import shelve

appID = 'Removed' #This information is removed as it should not be in the public domain. The bot won't work without it, but you can replace it with your own private data
refreshToken = 'Removed'
secret = 'Removed'
URI = 'Removed'
userAgent = 'Removed'

doneSubmissions = []
nonreplyusers = ["directimagelinkerbot", "imgurtranscriber", "automoderator", "apicontraption", "masterjts"] #make sure all in lower case
bannedRegex = re.compile("you've been banned from /r/(.*)")
bannedRegex2 = re.compile("Your ban from /r/(.*) has changed")
bannedsubs = shelve.open('bannedSubs', 'c') # is a dictionary
imgurRegex = re.compile("(((http|https)\:\/\/)?(www\.|i\.|m\.)?imgur\.com\/[a-zA-Z0-9]{6,7}?(?!(\.jpg|\.gif|\.gifv|\.png|\.jpeg))(?=[^a-zA-Z0-9]|$| ))") #finds indirect imgur links only.
filetypes = [".png", ".gif", ".jpg", "gifv", "jpeg"]
url = ""

def login():
    print("Logging in..")
    r = praw.Reddit(userAgent)
    r.set_oauth_app_info(appID, secret, URI)
    r.refresh_access_information(refreshToken)
    print("Logged in as " + r.user.name)
    return r

r = login()
loops = 31

while True:

    try:

############# Mail ############

        loops = loops + 1
        if loops > 30:
            loops = 0
            msgs = list(r.get_unread(unset_has_mail=False, update_user=False))
            for msg in msgs:
                if msg.author is not None and msg.author.name == "AutoModerator":
                    msg.mark_as_read()
                elif ("thanks" in msg.body.lower() or "thank you" in msg.body.lower()) and len(msg.body) < 39:
                    msg.reply("You're welcome, human. Don't forget to direct link!")
                    msg.mark_as_read()
                else:
                    match = re.findall(bannedRegex, msg.subject)
                    if not match:
                        match = re.findall(bannedRegex2, msg.subject)
                    if match:
                        if match[0] not in bannedsubs['banned']:
                            sublist = []
                            sublist =  bannedsubs['banned']
                            sublist.append(str(match[0]))
                            bannedsubs['banned'] = sublist
                            bannedsubs.sync()
                            msg.reply("/r/" + str(match[0]) + " has been added to my ignore list. I won't bother you again.")
                            msg.mark_as_read()
                            print "Added /r/" +  str(match[0]) + " to ignore list."

############# SUBMISSIONS ############
    
        submissions = list(r.get_new(limit=40))
        for submission in submissions:
            if not ((submission.author.name.lower() in nonreplyusers) or (submission.id in doneSubmissions)):
                if (submission.subreddit.display_name not in bannedsubs['banned']):
                    doneSubmissions.append(submission.id)
                    if (submission.domain == "imgur.com") and not ("/a/" in submission.url) and not ("gallery" in submission.url) and (not submission.url[-4:] in filetypes):               
                        if not submission.url.startswith("http"):
                            url = "https://" + submission.url
                        else:
                           url = submission.url
                        submission.add_comment("[Here is a direct link to the image OP submitted for the benefit of mobile users](" + url + """.jpg)\n\n---\n[^Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot&subject=Feedback&message=Don%27t%20forget%20to%20Include%20a%20link%20to%20your/my%20comment) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
                        print "Submission reply sent to " + submission.author.name + "!"

############# COMMENTS ##############

        subreddit = r.get_subreddit('all')
        comments = list(subreddit.get_comments(limit=100, fetch=True)) #around 22 comments come in per second
        for comment in comments:
            if not ((comment.author.name.lower() in nonreplyusers) or (comment.id in doneSubmissions) or (comment.subreddit.display_name in bannedsubs['banned'])):
                doneSubmissions.append(comment.id)
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
                            comment.reply("[Here is a direct link to your image for the benefit of mobile users](" + url + """.jpg)\n\n---\n\n^[Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot&subject=Feedback&message=Don%27t%20forget%20to%20Include%20a%20link%20to%20your/my%20comment) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
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
                                links.append(submatch[0])

                        if len(links) < 3: #if number of link is >= 10 and number of unique URLs is <3 then message admins
                            r.send_message("/r/spam", "Automatic comment report", "This message was automatically submitted because the comment below contained a large number of links, but few unique images. This usually means it's a spammy message. If you'd like not to receive these messages, please reply letting me know - /u/theonefoster checks this bot's PM's daily.\n\n Link to probably-spammy comment: " + comment.permalink + "?context=3")
                            print "Messaged admins about comment at " + comment.permalink
                   
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
