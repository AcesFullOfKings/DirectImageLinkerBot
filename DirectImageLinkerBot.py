
import praw
import time
import re



appID = removed #This information is removed as it should not be in the public domain. The bot won't work without it, but you can replace it with your own private data
refreshToken = removed
secret = removed
URI = 'https://127.0.0.1:65010/authorize_callback'
userAgent = removed

filetypes = [".png", ".gif", ".jpg", "gifv"]
doneSubmissions = []
bannedsubs = ["funny", "aww", "gaming", "pics", "pokemontrades"]
nonreplyusers = ["directimagelinkerbot", "imgurtranscriber", "automoderator"]

imgurRegex = re.compile("(((http|https)://)?(www\.|i\.|m\.)?imgur\.com\/[a-zA-Z0-9]{6,7}?(?!(\.jpg|\.gif|\.gifv|\.png))(?=[^a-zA-Z0-9]|$| ))") #finds indirect imgur links only. What if there's more than one?

def login():
    print("Logging in..")
    r = praw.Reddit(userAgent)
    r.set_oauth_app_info(appID, secret, URI)
    r.refresh_access_information(refreshToken)
    print("Logged in as " + r.user.name)

    return r

r = login()



while True:

############# SUBMISSIONS ############
    try:
        submissions = list(r.get_new(limit=50))
        for submission in submissions:
            if not ((submission.author in nonreplyusers) or (submission.id in doneSubmissions)):
                doneSubmissions.append(submission.id)
                if (submission.subreddit.display_name not in bannedsubs) and (submission.domain == "imgur.com") and not ("/a/" in submission.url) and not ("/gallery/" in submission.url) and (not submission.url[-4:] in filetypes):
                    submission.add_comment("[Here is a direct link to the submitted image for the benefit of mobile users](" + submission.url + """.jpg)
                    
---

[^Feedback](https://www.reddit.com/message/compose/?to=DirectImageLinkerBot) ^| [^Already ^a ^direct ^link?](https://www.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://www.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
                    print "Submission reply sent to " + submission.author.name + "!"


############# COMMENTS ##############

        subreddit = r.get_subreddit('all')
        comments = list(subreddit.get_comments(limit=100, fetch=True)) #around 22 comments come in per second
        for comment in comments:
            if not ((comment.author in nonreplyusers) or (comment.id in doneSubmissions)):
                doneSubmissions.append(comment.id)
                commentText = comment.body
                match = list(re.findall(imgurRegex, commentText))

                if (len(match) > 0) and (".png" not in commentText) and (".jpg" not in commentText) and (".gif" not in commentText):
                    if (comment.subreddit.display_name not in bannedsubs):
                          comment.reply("[Here is a direct link to that image for the benefit of mobile users](" + match[0][0] + """.jpg)
             
---

^[Feedback](https://www.reddit.com/message/compose/?to=DirectImageLinkerBot) ^| [^Already ^a ^direct ^link?](https://www.reddit.com/r/DirectImageLinkerBot/wiki/res_links) ^| [^Why ^do ^I ^exist?](https://www.reddit.com/r/DirectImageLinkerBot/wiki/index)""")
                        print "Comment reply sent to   " + comment.author.name + "!"



        
        r.handler.clear_cache()
        time.sleep(1)
    except praw.errors.RateLimitExceeded:
        print "Rate limit exceeded! Sleeping.."
        time.sleep(119)
        print "Resuming!"
    except praw.errors.HTTPException:
        print "HTTP Error."
        pass
    except Exception,e:
        print str(e)
        print "Sleeping.."
        time.sleep(30)
