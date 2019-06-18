import praw  # Python Reddit API Wrapper
import datetime
import pytz


def check_condition(comment):
    tokens = comment.body.split()
    if len(tokens) < 2:
        return False

    if "!MuppetiersUpdateBot" in tokens:
        count = tokens[1]
        if count.isdigit():
            return True


def bot_action(comment, comment_limit, reddit):
    muppets = ['muppetiers']
    response = ''
    bst = pytz.timezone('Europe/London')
    for muppet in muppets:
        response += '\n#Latest comments by ' + muppet + '\n'
        i = 1
        for c in reddit.redditor(muppet).comments.new(limit=comment_limit):
            if c.subreddit.display_name == 'reddevils' and 'Transfer Muppets Thread' in c.link_title:
                utc_posted_time = datetime.datetime.utcfromtimestamp(c.created_utc).astimezone(pytz.utc)
                dttm_bst = utc_posted_time.astimezone(bst)
                response += '\n##Comment ' + str(i) + '\n'

                comm = str(c.body).replace('*', '').replace('#', '').replace('u/', 'u\\')
                response += comm + '\n'
                response += '\n^(Posted on ' + str((dttm_bst).strftime("%d-%m-%Y %H:%M")) + ' BST) '
                response += '\n[^(link)](' + str(c.permalink) + ')'
                i = i + 1

    #print(response)
    comment.reply(response)


praw_client_id = os.environ['praw_client_id']
praw_client_secret = os.environ['praw_client_secret']
praw_password = os.environ['praw_password']
praw_username = os.environ['praw_username']
reddit = praw.Reddit(client_id=praw_client_id, client_secret=praw_client_secret, password=praw_password,
               user_agent='web:com.muppetiers-update-bot:v0.1 (by /u/rajatsaxena)',
               username=praw_username)

subreddit = reddit.subreddit('test')

for comment in subreddit.stream.comments():
    if check_condition(comment):
        bot_action(comment, int(comment.body.split()[1]), reddit)
