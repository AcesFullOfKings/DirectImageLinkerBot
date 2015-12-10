import praw
import time
import re
import shelve

appID = 'Removed' #This information is removed as it should not be in the public domain. The bot won't work without it, but you can replace it with your own private data
refreshToken = 'Removed'
secret = 'Removed'
URI = 'Removed'
userAgent = 'Removed'

filetypes = [".png", ".gif", ".jpg", "gifv", "jpeg"]
doneSubmissions = []

url = ""
bannedsubs = shelve.open('bannedSubs', 'c') # is a dictionary
nonreplyusers = ["directimagelinkerbot", "imgurtranscriber", "automoderator", "apicontraption"] #make sure all in lower case
imgurRegex = re.compile("(((http|https)://)?(www\.|i\.|m\.)?imgur\.com\/[a-zA-Z0-9]{6,7}?(?!(\.jpg|\.gif|\.gifv|\.png|\.jpeg))(?=[^a-zA-Z0-9]|$| ))") #finds indirect imgur links only. What if there's more than one?
bannedRegex = re.compile("you've been banned from /r/(.*)")

def login():
    print("Logging in..")
    r = praw.Reddit(userAgent)
    r.set_oauth_app_info(appID, secret, URI)
    r.refresh_access_information(refreshToken)
    print("Logged in as " + r.user.name)

    return r

r = login()

loops = 51

while True:
    try:
        loops = loops + 1
        if loops > 50:
            loops = 0
            msgs = list(r.get_unread(unset_has_mail=False, update_user=False))
            for msg in msgs:
                if msg.author is not None and msg.author.name == "AutoModerator":
                    msg.mark_as_read()
                else:
                    match = re.findall(bannedRegex, msg.subject)
                    if match:
                        if match[0] not in bannedsubs['banned']:
                            sublist = []
                            sublist =  bannedsubs['banned']
                            sublist.append(str(match[0]))
                            bannedsubs['banned'] = sublist
                            bannedsubs.sync()
                            msg.reply("/r/" + str(match[0]) + " has been added to my ignore list. I won't bother you again.")
                            msg.mark_as_read()

############# SUBMISSIONS ############
    
        submissions = list(r.get_new(limit=50))
        for submission in submissions:
            if not ((submission.author.name.lower() in nonreplyusers) or (submission.id in doneSubmissions)):
                if (submission.subreddit.display_name not in bannedsubs['banned']):
                    doneSubmissions.append(submission.id)
                    if (submission.domain == "imgur.com") and not ("/a/" in submission.url) and not ("gallery" in submission.url) and (not submission.url[-4:] in filetypes):
                        
                        if not submission.url.startswith("http://"):
                            url = "https://" + submission.url
                        else:
                           url = submission.url

                        submission.add_comment("[Here is a direct link to the submitted image for the benefit of mobile users](" + url + """.jpg)\n\n---\n[^Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
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
                        if not match[0][0].startswith("http://"):
                            url = "http://" + str(match[0][0])
                        else:
                            url = match[0][0]

                        if "gallery" not in match and "/a/" not in match:
                            comment.reply("[Here is a direct link to that image for the benefit of mobile users](" + url + """.jpg)\n\n---\n\n^[Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
                            print "Comment reply sent to   " + comment.author.name + "!"

                    else:
                        reply = ("Here are direct links to those images for the benefit of mobile users: \n\n")

                        for submatch in match:
                            if "gallery" not in submatch and "/a/" not in submatch:
                               if not submatch[0].startswith("http://"):
                                   url = "http://" + str(submatch[0])
                               else:
                                   url = submatch[0]
                               reply = reply + (url + ".jpg\n\n")
                        reply = reply + "---\n\n[^Feedback](https://np.reddit.com/message/compose/?to=DirectImageLinkerBot) ^| [^Already ^a ^direct ^link?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://np.reddit.com/r/DirectImageLinkerBot/wiki/index)"

                        comment.reply(reply)
                        print "Comment reply sent to   " + comment.author.name + "!"

        r.handler.clear_cache()
    except praw.errors.RateLimitExceeded:
        print "Rate limit exceeded!"
    except praw.errors.HTTPException:
        print "HTTP Error."
        pass
    except Exception,e:
        print str(e)
        try:
            r = login()
        except Exception,e:
            print str(e)
            print "Sleeping.."
            time.sleep(30)
